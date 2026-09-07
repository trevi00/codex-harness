import pytest
from test_threshold_collection import events
from test_threshold_collection import policy_repo as source_policy_repo

from codex_harness.adapters.artifacts import FileArtifacts
from codex_harness.adapters.executor import Executor
from codex_harness.adapters.store import MemoryStore
from codex_harness.adapters.threshold_policy import current_policy
from codex_harness.application.service import Harness
from codex_harness.application.threshold_proposals import ThresholdProposals
from codex_harness.application.threshold_reviews import ThresholdReviews
from codex_harness.bootstrap import organization
from codex_harness.domain.model import canonical, digest


@pytest.fixture
def policy_repo(tmp_path):
    return source_policy_repo.__wrapped__(tmp_path)


def setup_review(policy_repo, tmp_path):
    _, git = policy_repo
    store, artifacts = MemoryStore(), FileArtifacts(str(tmp_path / 'artifacts'))
    with store.transaction() as tx:
        tx.put('skill_history', 'project', {'events': events()})
    run = ThresholdProposals(store, artifacts, lambda: current_policy(git)).collect('project')
    executor = Executor(Harness(store, organization()), git, artifacts)
    reviews = ThresholdReviews(executor.workflow, artifacts)
    request = reviews.request(run['proposals'][0]['id'])
    assert reviews.request(run['proposals'][0]['id']) == request
    return executor, reviews, request


def runtime(executor, calls, *, accepted=True, blocked=False, wrong_actor=False, intervene=None):
    def run(actor, key, objective, evidence, cwd, schema, read_only, **kwargs):
        assert read_only and kwargs['stage'] == 'threshold_review'
        calls.append((actor, evidence))
        answer = {'accepted': accepted, 'reason': 'fixture assessment', 'blocked': blocked,
                  'risks': [], 'sre_assessment': 'fixture', 'arc42_assessment': 'fixture'}
        packet = executor.artifacts.put(canonical({'agent_id': 'wrong' if wrong_actor else actor,
            'task_id': key}), 'fixture-context')
        revision = executor.git._git('rev-parse', 'HEAD', cwd=cwd)
        receipt = executor.artifacts.put(canonical({'answer': answer, 'context_ref': packet['ref'],
            'research_binding': {'stage': 'threshold_review', 'evidence_ref': 'sha256:' + digest(evidence),
                                 'basis_revision': revision}}), 'fixture-execution')
        if intervene:
            intervene(kwargs['lease'])
        return {**answer, 'execution_ref': receipt['ref'], 'basis_revision': revision}
    return run


def test_executor_orders_independent_assessments_without_dispatch_or_activation(policy_repo, tmp_path, monkeypatch):
    executor, _, request = setup_review(policy_repo, tmp_path)
    calls = []
    monkeypatch.setattr(executor, '_run', runtime(executor, calls))
    assert executor.decide_one('conductor') is None
    assert executor.decide_one('lead:improvement')['status'] == 'succeeded'
    assert executor.decide_one('conductor')['status'] == 'succeeded'
    assert [actor for actor, _ in calls] == ['lead:improvement', 'conductor']
    assert calls[1][1]['review']['prior_reviews'][0]['actor'] == 'lead:improvement'
    with executor.service.store.transaction() as tx:
        finished = tx.get('threshold_review_requests', request['id'])
        assert finished['status'] == 'assessed' and not finished['activation_ready']
        assert len(finished['reviews']) == 2
        assert not tx.scan('outbox') and not tx.scan('releases') and not tx.scan('deployment')
    assert executor.decide_one('conductor') is None


@pytest.mark.parametrize('blocked', [False, True])
def test_rejection_or_blockage_cannot_queue_conductor(policy_repo, tmp_path, monkeypatch, blocked):
    executor, _, request = setup_review(policy_repo, tmp_path)
    monkeypatch.setattr(executor, '_run', runtime(executor, [], accepted=False, blocked=blocked))
    executor.decide_one('lead:improvement')
    assert executor.decide_one('conductor') is None
    with executor.service.store.transaction() as tx:
        assert tx.get('threshold_review_requests', request['id'])['status'] == ('blocked' if blocked else 'rejected')


def test_wrong_receipt_identity_cannot_complete_review(policy_repo, tmp_path, monkeypatch):
    executor, _, request = setup_review(policy_repo, tmp_path)
    monkeypatch.setattr(executor, '_run', runtime(executor, [], wrong_actor=True))
    assert executor.decide_one('lead:improvement')['status'] == 'retry'
    with executor.service.store.transaction() as tx:
        assert tx.get('threshold_review_requests', request['id'])['reviews'] == []


@pytest.mark.parametrize('change', ['lease', 'record', 'policy'])
def test_changed_basis_or_lease_during_execution_cannot_commit(policy_repo, tmp_path, monkeypatch, change):
    executor, _, request = setup_review(policy_repo, tmp_path)
    def intervene(lease):
        if change == 'policy':
            root = executor.git.repository
            (root / 'changed.txt').write_text('new revision')
            executor.git._git('add', '.')
            executor.git._git('commit', '-qm', 'advance basis')
        else:
            with executor.service.store.transaction() as tx:
                if change == 'lease':
                    row = tx.get('decisions_pending', lease['id'])
                    row.update(owner='other', lease_owner='other', generation=row['generation'] + 1)
                    tx.put('decisions_pending', row['id'], row)
                else:
                    row = tx.get('threshold_proposals', request['row_id'])
                    row['activation_blockers'].append('changed')
                    tx.put('threshold_proposals', row['id'], row)
    monkeypatch.setattr(executor, '_run', runtime(executor, [], intervene=intervene))
    assert executor.decide_one('lead:improvement')['status'] == 'retry'
    with executor.service.store.transaction() as tx:
        assert tx.get('threshold_review_requests', request['id'])['reviews'] == []
        assert not any(row['actor'] == 'conductor' for row in tx.scan('decisions_pending'))
