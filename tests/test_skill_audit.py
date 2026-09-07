import copy
import json
from uuid import uuid4

import pytest

from codex_harness.adapters.skill_audit import main, render_text
from codex_harness.adapters.store import MemoryStore
from codex_harness.application.skill_history import SkillHistory
from codex_harness.domain.model import ContractError, digest
from codex_harness.domain.skill_audit import audit_history, duration_seconds, timestamp
from codex_harness.domain.skill_history import assess_history


def observation(index, score=1, content='v1', dimensions=None, at='2026-09-08T00:00:00Z'):
    return {'id': str(index), 'manifest_ref': 'manifest', 'context_ref': 'context', 'at': at,
            'top': [{'path': 'python/a.md', 'content_ref': content, 'score': score,
                     'dimensions': dimensions or ['kw:test']}]}


def test_audit_predicate_dimensions_versions_and_threshold_override():
    events = [observation(i, score) for i, score in enumerate([1, 2, 2, 1])]
    report = audit_history(events)
    row = report['skills'][0]
    assert (row['count'], row['score_min'], row['score_median'], row['score_max']) == (4, 1, 1.5, 2)
    assert row['dominant_dim'] == 'kw' and report['dim_weight'] == {'kw': 4}
    assert len(report['false_positive_candidates']) == 1
    assert assess_history(events, events[0]['top'])[0]['candidate']
    assert audit_history(events, min_samples=5)['false_positive_candidates'] == []
    report = audit_history(events + [observation('new', 6, 'v2', ['intent:x', 'path:y', 'pat:z', '???'])])
    assert len(report['skills']) == 2 and len(report['false_positive_candidates']) == 1
    assert report['dim_weight'] == {'kw': 4, 'intent': 1, 'path': 1, 'pat': 1, 'unknown': 1}
    assert 'Narrow the kw surface' in render_text(report)


def test_dates_legacy_dimensions_and_invalid_entries_are_explicit():
    old = observation('old', at='2020-01-01T00:00:00Z')
    unknown = observation('unknown', at=None)
    del unknown['top'][0]['dimensions']
    report = audit_history([old, unknown, observation('new')], cutoff=timestamp('2026-01-01T00:00:00Z'))
    assert report['invocations'] == 2 and report['unknown_timestamp_events'] == 1
    assert report['dim_weight'] == {'kw': 1}
    assert timestamp('2026-09-08T09:00:00+09:00') == timestamp('2026-09-08T00:00:00Z')
    invalid = observation('bool', True)
    invalid['top'].append(None)
    assert audit_history([invalid])['invalid_entries'] == 2
    assert 'no skill-match telemetry' in render_text(audit_history([]))


@pytest.mark.parametrize('value', ['0s', '-1d', 'NaNh', 'infh', '7x', ''])
def test_invalid_since_is_rejected(value):
    with pytest.raises(ContractError):
        duration_seconds(value)


def test_cli_reads_same_project_without_writes_and_replay_preserves_time(capsys):
    store = MemoryStore()
    project_id = str(uuid4())
    key = digest('uuid:' + project_id)
    history = SkillHistory(store)
    entry = observation('old')
    del entry['top'][0]['dimensions']
    history.record(key, entry)
    before = copy.deepcopy(store.data)
    entry['top'][0]['dimensions'] = ['kw:new-detail']
    assert not history.record(key, entry)
    assert store.data == before
    for index in range(3):
        history.record(key, observation(index))
    before = copy.deepcopy(store.data)
    assert main(['--project-id', project_id, '--json', '--since', '1h'], store=store) == 0
    report = json.loads(capsys.readouterr().out)
    assert report['invocations'] == 4 and report['dim_weight'] == {'kw': 3}
    assert report['unknown_timestamp_events'] == 0
    assert store.data == before
    assert main(['--project-id', str(uuid4()), '--json'], store=store) == 0
    assert json.loads(capsys.readouterr().out)['invocations'] == 0
    assert main(['--github-repo', '../sibling', '--json'], store=store) == 2
    assert main(['--project-id', project_id, '--since', 'invalid'], store=store) == 2
    assert main(['--project-id', project_id, '--min-samples', '0'], store=store) == 2
