from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from codex_harness.adapters.artifacts import FileArtifacts
from codex_harness.adapters.store import MemoryStore
from codex_harness.application.measurements import Measurements
from codex_harness.domain.measurements import DEFINITIONS, evaluate

NOW = datetime(2026, 9, 7, tzinfo=timezone.utc)


def task(key='one', status='succeeded', attempt=1, outcome='succeeded'):
    return {'id': key, 'status': status, 'attempt': attempt,
            'created_at': (NOW - timedelta(hours=1)).isoformat(),
            'attempt_outcomes': [{'attempt': 1, 'status': outcome,
                                  'at': (NOW - timedelta(minutes=1)).isoformat()}]}


def evidence(*rows):
    return {'tasks': list(rows), 'decisions': [], 'observed_at': NOW.isoformat()}


def test_retries_do_not_improve_first_attempt_denominator():
    data = evidence(task(), task('retry', attempt=2, outcome='failed'),
                    task('cancel', 'cancelled', 0), task('expired', 'expired', 0))
    data['tasks'][2]['attempt_outcomes'] = []
    data['tasks'][3]['attempt_outcomes'] = []
    first, terminal = [evaluate(d, data, NOW) for d in DEFINITIONS[:2]]
    assert (first.numerator, first.denominator, first.value) == (1, 2, .5)
    assert (terminal.numerator, terminal.denominator, terminal.value) == (2, 4, .5)
    assert first.status == terminal.status == 'unknown'
    assert first.observational


@pytest.mark.parametrize('offset,reason', [(121, 'stale'), (-1, 'future-dated')])
def test_freshness(offset, reason):
    data = evidence(task())
    data['observed_at'] = (NOW - timedelta(seconds=offset)).isoformat()
    for definition in DEFINITIONS:
        result = evaluate(definition, data, NOW)
        assert result.status == 'unknown' and reason in result.reason
        assert result.value is None


def test_missing_invalid_zero_insufficient_and_legacy():
    for data in (None, {}, evidence(), evidence(task(), task())):
        assert evaluate(DEFINITIONS[0], data, NOW).value is None
    insufficient = evaluate(replace(DEFINITIONS[0], minimum_samples=2), evidence(task()), NOW)
    assert insufficient.value is None and insufficient.sample_count == 1
    row = task(attempt=2)
    row.pop('attempt_outcomes')
    assert 'missing attempt history' in evaluate(DEFINITIONS[0], evidence(row), NOW).reason
    row = task()
    row['created_at'] = 'not-a-time'
    assert evaluate(DEFINITIONS[1], evidence(row), NOW).reason == 'invalid evidence'


def test_capacity_counts_decisions_and_excludes_expired_leases():
    data = evidence()
    for i in range(3):
        data['decisions'].append({'id': str(i), 'status': 'running',
                                 'lease_until': (NOW + timedelta(seconds=1)).isoformat()})
    result = evaluate(DEFINITIONS[2], data, NOW)
    assert result.value == 3 and result.status == 'fail'
    data['decisions'][0]['lease_until'] = NOW.isoformat()
    assert evaluate(DEFINITIONS[2], data, NOW).status == 'pass'
    assert evaluate(DEFINITIONS[2], evidence(), NOW).value == 0
    data['decisions'][0]['lease_until'] = None
    assert evaluate(DEFINITIONS[2], data, NOW).status == 'unknown'


def test_observations_reproduce_and_retain_original_inputs(tmp_path):
    store, artifacts = MemoryStore(), FileArtifacts(str(tmp_path / 'artifacts'))
    with store.transaction() as tx:
        tx.put('tasks', 'one', task())
    results = Measurements(store, artifacts).collect('a' * 40, NOW)
    snapshot = artifacts.document(results[0]['evidence_refs'][0])
    assert evaluate(DEFINITIONS[0], snapshot, NOW).value == 1
    with store.transaction() as tx:
        tx.put('tasks', 'one', task(status='failed'))
        assert len(tx.scan('metric_observations')) == 3
    assert artifacts.document(results[0]['evidence_refs'][0]) == snapshot
    assert all(r['promotion_approval'] is False for r in results)


def test_attempt_failures_survive_retry_and_are_not_duplicated():
    from codex_harness.application.workflow import Workflow
    row = task(status='running')
    row['attempt_outcomes'] = []
    Workflow._attempt_outcome(row, 'failed', NOW.isoformat(), 'failure evidence')
    Workflow._attempt_outcome(row, 'failed', NOW.isoformat())
    row['attempt'] = 2
    Workflow._attempt_outcome(row, 'succeeded', NOW.isoformat())
    assert [r['status'] for r in row['attempt_outcomes']] == ['failed', 'succeeded']
    assert row['attempt_outcomes'][0]['error'] == 'failure evidence'


def test_workflow_retry_history_is_fenced_and_cancellation_authorized():
    from codex_harness.application.workflow import Workflow
    from codex_harness.bootstrap import organization
    from codex_harness.domain.model import ContractError, envelope
    store = MemoryStore()
    workflow = Workflow(store, organization())
    message = envelope('task.assign', 'lead:improvement', 'worker:implementation',
                       'implement', {'objective': 'fixture'}, 'test')
    workflow.submit(message)
    first = workflow.claim('worker:implementation', 'first')
    workflow.fail(first, 'original failure')
    second = workflow.claim('worker:implementation', 'second')
    with pytest.raises(ContractError):
        workflow.fail(first, 'stale overwrite')
    with pytest.raises(ContractError):
        workflow.cancel(second['id'], 'worker:github', 'unauthorized')
    workflow.complete(second, {'summary': 'recovered'})
    with store.transaction() as tx:
        row = tx.get('tasks', first['id'])
    assert row['status'] == 'succeeded'
    assert [(r['attempt'], r['status']) for r in row['attempt_outcomes']] == [(1, 'failed'), (2, 'succeeded')]
    assert row['attempt_outcomes'][0]['error'] == 'original failure'


def test_monitor_collects_measurements_via_use_case(monkeypatch, tmp_path):
    from types import SimpleNamespace

    from codex_harness.adapters import monitoring
    from codex_harness.bootstrap import organization
    store = MemoryStore()
    service = SimpleNamespace(store=store, org=organization())
    monkeypatch.setattr(monitoring, 'run_process', lambda *a, **kw:
                        SimpleNamespace(returncode=0, stdout='a' * 40))
    monkeypatch.setattr(monitoring, 'docker_facts', lambda *a: [])
    monkeypatch.setattr(monitoring, 'redis_facts', lambda *a: [])
    result = monitoring.collect(service, FileArtifacts(str(tmp_path / 'artifacts')), '.', '')
    database = result['sources']['database']
    assert database['status'] == 'ok'
    assert len(database['data']['measurements']) == 3
    assert database['data']['measurements'][2]['value'] == 0
    assert not database['data']['measurements'][2]['promotion_approval']


@pytest.mark.parametrize('change', [
    {'created_at': (NOW + timedelta(seconds=1)).isoformat()},
    {'completed_at': (NOW + timedelta(seconds=1)).isoformat()},
    {'attempt': True},
    {'attempt': 0},
    {'status': 'made_up'},
])
def test_invalid_task_population_never_yields_a_ratio(change):
    row = task()
    row.update(change)
    for definition in DEFINITIONS[:2]:
        result = evaluate(definition, evidence(row), NOW)
        assert result.status == 'unknown' and result.value is None


def test_capacity_invalid_status_is_not_an_idle_snapshot():
    data = evidence({'id': 'bad', 'status': 'made_up'})
    assert evaluate(DEFINITIONS[2], data, NOW).value is None


@pytest.mark.parametrize('changes', [
    {}, {'attempt': True}, {'attempt_outcomes': None}, {'attempt_outcomes': [None]},
    {'attempt_outcomes': [{'attempt': 1}]}, {'status': 'unknown'},
    {'created_at': 'bad'}, {'completed_at': (NOW + timedelta(seconds=1)).isoformat()},
    {'status': 'running', 'lease_until': (NOW + timedelta(seconds=10)).isoformat()},
])
def test_compact_measurement_population_preserves_evaluation(changes):
    from codex_harness.domain.measurements import measurement_population
    row = {**task(), **changes, 'message': {'large': 'x' * 10000}, 'result': {'log': 'y' * 10000}}
    original = evidence(row)
    compact = {**original, 'tasks': measurement_population(original['tasks']),
               'decisions': measurement_population(original['decisions'], decisions=True)}
    assert all(evaluate(d, original, NOW) == evaluate(d, compact, NOW) for d in DEFINITIONS)
    assert 'message' not in compact['tasks'][0] and 'result' not in compact['tasks'][0]
    assert 'message' in row and 'result' in row


def test_compact_observations_keep_fresh_time_and_replay_lease_expiry(tmp_path):
    store, artifacts = MemoryStore(), FileArtifacts(str(tmp_path / 'artifacts'))
    with store.transaction() as tx:
        tx.put('decisions_pending', 'one', {'id': 'one', 'status': 'running',
               'lease_until': (NOW + timedelta(seconds=1)).isoformat(),
               'message': {'large': 'x' * 100000}})
    use_case = Measurements(store, artifacts)
    first, later = use_case.collect('a' * 40, NOW), use_case.collect('a' * 40, NOW + timedelta(seconds=2))
    assert first[2]['value'] == 1 and later[2]['value'] == 0
    assert first[2]['evidence_refs'] != later[2]['evidence_refs']
    for results, at in [(first, NOW), (later, NOW + timedelta(seconds=2))]:
        ref = results[2]['evidence_refs'][0]
        snapshot = artifacts.document(ref)
        assert evaluate(DEFINITIONS[2], snapshot, at).value == results[2]['value']
        assert len(artifacts._body(ref)) < 5000
