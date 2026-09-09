import pytest

from codex_harness.adapters.artifacts import FileArtifacts
from codex_harness.adapters.review_evidence import validate_review_evidence
from codex_harness.domain.model import ContractError


def test_published_review_evidence_is_verified(tmp_path):
    artifacts = FileArtifacts(str(tmp_path / 'shared'))
    ref = artifacts.put('real command output', 'test')['ref']
    validate_review_evidence(artifacts, {'accepted': True, 'reason': 'Measured ' + ref})


def test_temporary_artifact_handle_does_not_authorize_a_review(tmp_path):
    shared = FileArtifacts(str(tmp_path / 'shared'))
    scratch = FileArtifacts(str(tmp_path / 'scratch'))
    ref = scratch.put('real local output, not published', 'test')['ref']
    with pytest.raises(ContractError, match='unavailable or corrupt'):
        validate_review_evidence(shared, {'accepted': True, 'sre_assessment': ref})
    assert not (shared.root / (ref[7:] + '.txt')).exists()


def test_corrupt_shared_artifact_blocks_approval(tmp_path):
    artifacts = FileArtifacts(str(tmp_path))
    ref = artifacts.put('original receipt', 'test')['ref']
    (artifacts.root / (ref[7:] + '.txt')).write_text('changed')
    with pytest.raises(ContractError, match='unavailable or corrupt'):
        validate_review_evidence(artifacts, {'accepted': True, 'execution_ref': ref})


def test_rejection_is_not_converted_into_an_evidence_approval(tmp_path):
    validate_review_evidence(FileArtifacts(str(tmp_path)),
                             {'accepted': False, 'reason': 'missing sha256:' + 'a' * 64})


def test_typed_image_identity_is_not_a_published_artifact_requirement(tmp_path):
    validate_review_evidence(FileArtifacts(str(tmp_path)),
                             {'accepted': True, 'candidate': {}, 'image': 'sha256:' + 'a' * 64})


def test_unpublished_review_never_creates_approval_then_exact_publication_allows_retry(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from codex_harness.adapters.executor import Executor
    from codex_harness.adapters.store import MemoryStore
    from codex_harness.application.service import Harness
    from codex_harness.bootstrap import organization
    from codex_harness.domain.model import envelope

    service = Harness(MemoryStore(), organization())
    shared = FileArtifacts(str(tmp_path / 'shared'))
    scratch = FileArtifacts(str(tmp_path / 'scratch'))
    body = 'original local command receipt'
    ref = scratch.put(body, 'unit-fixture')['ref']
    git = SimpleNamespace(repository=tmp_path, inspect=lambda *a: {},
                          review_workspace=lambda *a: str(tmp_path),
                          _git=lambda *a, **k: '' if a[0] == 'status' else 'candidate')
    executor = Executor(service, git, shared)
    candidate = {'revision': 'candidate', 'base': 'base', 'tree': 'tree',
                 'author': 'worker:implementation'}
    message = envelope('task.assign', 'lead:improvement', 'worker:implementation',
                       'implement', {}, 'unit-fixture')
    with service.store.transaction() as tx:
        tx.put('decisions_pending', 'review', {'id': 'review', 'actor': 'lead:improvement',
               'phase': 'review_lead', 'input': {'candidate': candidate}, 'message': message,
               'status': 'pending', 'attempt': 0})
    monkeypatch.setattr(executor, '_run', lambda *a, **k: {
        'accepted': True, 'reason': ref, 'execution_ref': 'fixture:execution'})
    assert executor.decide_one('lead:improvement')['status'] == 'retry'
    with service.store.transaction() as tx:
        assert tx.scan('releases') == []
        assert tx.scan('outbox') == []
    assert shared.put(body, 'unit-fixture')['ref'] == ref
    assert executor.decide_one('lead:improvement')['status'] == 'succeeded'
    with service.store.transaction() as tx:
        assert len(tx.scan('releases')[0]['reviews']) == 1
