import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from codex_harness.adapters.artifacts import FileArtifacts
from codex_harness.adapters.hooks import NativeHooks
from codex_harness.adapters.store import MemoryStore
from codex_harness.application.service import Harness
from codex_harness.bootstrap import organization
from codex_harness.domain.model import ContractError, digest, envelope

ROOT = Path(__file__).resolve().parents[1]
HOOK_ID = 'hook-ab97ba09554daa5aec289867'


@pytest.fixture(params=[
    (HOOK_ID, "codex-bubblewrap-namespace-creation-denied", "docker/linux/codex-read-only-review"),
    ("hook-572b2b90cf311ed31d66b108", "codex-output-schema-version-missing-type",
     "codex-harness/research-audit/output-schema"),
])
def native_candidate(tmp_path, request):
    hook_id, cause, scope = request.param
    service = Harness(MemoryStore(), organization())
    # Fixture diagnosis only. No automatic cause confirmation from error text.
    for occurrence in ['review-one', 'review-two']:
        message = envelope('incident.report', 'lead:improvement', 'conductor', 'record_incident',
                           {'occurrence_id': occurrence,
                            'root_cause': cause,
                            'scope': scope,
                            'evidence_refs': ['fixture:confirmed-diagnosis']}, 'fixture')
        service.record_incident(message)
        service.record_incident(message)
    def git_show(command, revision_path, **kwargs):
        assert command == 'show' and revision_path.startswith('fixture-revision:')
        return (ROOT / revision_path.split(':', 1)[1]).read_text()
    adapter = NativeHooks(service, SimpleNamespace(_git=git_show), FileArtifacts(str(tmp_path)))
    spec = adapter.candidate(hook_id, {'revision': 'fixture-revision', 'author': 'worker:implementation'})
    return service, adapter, spec, hook_id


def test_native_activation_gates_canary_and_rollback_exclusion(native_candidate):
    service, adapter, spec, hook_id = native_candidate
    assert adapter.configuration() == {}
    with pytest.raises(ContractError):
        service.activate(hook_id)
    for revision, spec_hash in [('stale', digest(spec)), ('fixture-revision', 'stale')]:
        with pytest.raises(ContractError, match='Stale review'):
            service.review(hook_id, 'lead:improvement', revision, spec_hash, True, 'fixture')
    for actor in ['conductor', 'lead:research', 'worker:implementation']:
        with pytest.raises(ContractError):
            service.review(hook_id, actor, 'fixture-revision', digest(spec), True, 'fixture')
    for actor in ['lead:improvement', 'conductor']:
        service.review(hook_id, actor, 'fixture-revision', digest(spec), True, 'fixture')
    checks = adapter.canary(hook_id)
    assert all(check['passed'] for check in checks.values())
    assert adapter.configuration() == {}
    service.record_canary(hook_id, 'fixture-revision', digest(spec),
                          {'reproduction': True, 'normal_case': True, 'cli_start': True})
    service.activate(hook_id)
    configuration = adapter.configuration()
    assert configuration['SessionStart'][0]['matcher'] == spec['matcher']
    service.rollback(hook_id, 'fixture rollback through existing use case')
    assert NativeHooks(service, adapter.git, adapter.artifacts).configuration() == {}
    assert service.get_hook(hook_id)['status'] == 'rolled_back'
    with service.store.transaction() as tx:
        assert len(tx.scan('incidents')) == 2


def test_materialization_checks_exact_git_content(native_candidate):
    service, adapter, _, hook_id = native_candidate
    adapter.git._git = lambda *a, **k: 'tampered'
    with pytest.raises(ContractError, match='Reviewed script changed'):
        adapter.materialize(service.get_hook(hook_id))


def test_manifest_replay_is_explicitly_not_native_failure_coverage():
    manifest = json.loads((ROOT / f'harness_hooks/{HOOK_ID}.json').read_text())
    assert manifest['spec']['event'] == 'SessionStart'
    assert all(c['input']['method'] == 'item/completed' for c in manifest['cases']['reproduction'])
