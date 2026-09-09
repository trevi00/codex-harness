import copy
import json
from importlib.resources import files
from pathlib import Path
from types import SimpleNamespace

import pytest

from codex_harness.adapters.evaluator_migration import (
    EVALUATOR,
    SOURCE_BASE,
    inspect_manifest,
    prove_delta,
    validate_manifest,
)
from codex_harness.adapters.store import MemoryStore
from codex_harness.application.qualification import qualify
from codex_harness.application.releases import Releases
from codex_harness.bootstrap import organization
from codex_harness.domain.evaluator_migration import approval_binding, validate_approvals
from codex_harness.domain.model import ContractError, digest


def setup():
    service = Releases(MemoryStore(), organization())
    manifest = json.loads(files('codex_harness.resources').joinpath('evaluator-migration.v1.json').read_text())
    candidate = {'revision': 'candidate', 'tree': 'tree', 'base': SOURCE_BASE,
                 'author': 'worker:implementation'}
    policy = {'revision': SOURCE_BASE, 'checks': ['tests', 'cli_start', 'cli_file_task'],
              'evaluator_revision': EVALUATOR, 'migration': {'version': 1,
              'source_base': SOURCE_BASE, 'evaluator_revision': EVALUATOR,
              'manifest_digest': digest(manifest), 'controller_revision': 'candidate'}}
    return service, candidate, policy


def approved():
    service, candidate, policy = setup()
    record = service.propose(candidate, policy)
    for actor in ['lead:improvement', 'conductor']:
        record = service.review(record['id'], actor, candidate['revision'], True, 'fixture:' + actor,
                                migration_approval=approval_binding(record))
    return service, record


def test_exact_git_manifest_and_source_ast_proof():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads(files('codex_harness.resources').joinpath('evaluator-migration.v1.json').read_text())
    assert inspect_manifest(root) == manifest
    assert len(manifest['delta']) == 5
    assert len({c['test'] for c in manifest['delta']}) == 3


def test_source_proof_rejects_unrelated_bytes():
    from codex_harness.adapters.evaluator_migration import FILE, git_bytes
    root = Path(__file__).resolve().parents[1]
    old = git_bytes(root, 'show', SOURCE_BASE + ':' + FILE)
    new = git_bytes(root, 'show', EVALUATOR + ':' + FILE)
    with pytest.raises(ContractError):
        prove_delta(old, new + b'\n# unrelated edit\n')
    with pytest.raises(ContractError):
        prove_delta(old, new.replace(b'{IMAGE, EVIDENCE}', b'set()', 1))


@pytest.mark.parametrize('change', ['source', 'evaluator', 'checks', 'version'])
def test_policy_rejects_invalid_migration(change):
    service, candidate, policy = setup()
    if change == 'source':
        candidate['base'] = 'new-base'
    elif change == 'evaluator':
        policy['evaluator_revision'] = 'forged'
    elif change == 'checks':
        policy['checks'].remove('cli_file_task')
    else:
        policy['migration']['version'] = True
    with pytest.raises(ContractError):
        service.propose(candidate, policy)


def test_explicit_independent_approval_required_and_queued_once():
    service, candidate, policy = setup()
    record = service.propose(candidate, policy)
    assert service.request_migration_reviews(record['id']) == service.request_migration_reviews(record['id'])
    for actor, binding in [('lead:improvement', None), ('worker:implementation', approval_binding(record)),
                           ('conductor', approval_binding(record))]:
        with pytest.raises(ContractError):
            service.review(record['id'], actor, candidate['revision'], True, 'fixture',
                           migration_approval=binding)
    with pytest.raises(ContractError):
        validate_approvals(record, organization())


@pytest.mark.parametrize('change', ['candidate', 'policy', 'mixed', 'missing', 'generic', 'revision'])
def test_qualification_rejects_stale_or_mixed_approvals(change):
    service, record = approved()
    record = copy.deepcopy(record)
    if change == 'candidate':
        record['candidate']['tree'] = 'changed'
    elif change == 'policy':
        record['policy']['evaluator_revision'] = 'changed'
    elif change == 'mixed':
        record['reviews'][1]['migration_approval']['policy_hash'] = 'different-policy'
    elif change == 'missing':
        record['reviews'].pop()
    elif change == 'generic':
        record['reviews'][0].pop('migration_approval')
    else:
        record['reviews'][0]['revision'] = 'old'
    with pytest.raises(ContractError):
        validate_approvals(record, service.org)


def test_positive_control_requires_all_checks_and_preserves_rejection():
    service, record = approved()
    validate_approvals(record, service.org)
    checks = {k: {'passed': True, 'evidence': 'fixture:' + k} for k in record['policy']['checks']}
    with pytest.raises(ContractError):
        service.verify(record['id'], 'candidate', record['policy_hash'], {'tests': checks['tests']})
    checks['tests']['passed'] = False
    rejected = service.verify(record['id'], 'candidate', record['policy_hash'], checks)
    assert rejected['status'] == 'rejected'
    assert service.propose(record['candidate'], record['policy']) == rejected
    with pytest.raises(ContractError):
        service.promote(record['id'], None)


def test_bootstrap_positive_control_and_publication_fence():
    service, record = approved()
    runner = SimpleNamespace(service=SimpleNamespace(store=service.store, org=service.org),
                             git=SimpleNamespace(remote=None), auto_merge=False,
                             run=lambda identity: {'fixture': identity})
    assert qualify(runner, record['id'], 'candidate', record['policy_hash'], 'candidate') == {
        'fixture': record['id']}
    runner.git.remote = 'owner/repository'
    with pytest.raises(ContractError):
        qualify(runner, record['id'], 'candidate', record['policy_hash'], 'candidate')


def test_manifest_digest_cannot_be_candidate_authorized():
    _, candidate, policy = setup()
    policy['migration']['manifest_digest'] = 'forged'
    with pytest.raises(ContractError, match='Forged'):
        validate_manifest(Path(__file__).resolve().parents[1], policy, candidate)


def test_legacy_policy_cannot_select_another_evaluator():
    service, candidate, _ = setup()
    with pytest.raises(ContractError):
        service.propose(candidate, {'revision': SOURCE_BASE, 'checks': ['tests'],
                                    'evaluator_revision': EVALUATOR})


@pytest.mark.parametrize('mode', ['explicit', 'generic', 'blocked', 'no_command'])
def test_executor_migration_reviews_bind_policy_before_model_and_require_bootstrap(tmp_path, monkeypatch, mode):
    from codex_harness.adapters.artifacts import FileArtifacts
    from codex_harness.adapters.executor import Executor
    from codex_harness.application.service import Harness

    releases, candidate, policy = setup()
    service = Harness(releases.store, releases.org)
    git = SimpleNamespace(repository=tmp_path, inspect=lambda *a: {},
                          review_workspace=lambda *a: str(tmp_path),
                          _git=lambda *a, **k: '' if a[0] == 'status' else 'candidate')
    executor = Executor(service, git, FileArtifacts(str(tmp_path / 'artifacts')))
    record = releases.propose(candidate, policy)
    releases.request_migration_reviews(record['id'])
    monkeypatch.setattr('codex_harness.adapters.evaluator_migration.validate_manifest', lambda *a: {})

    def review(*args, **kwargs):
        evidence, schema = args[3], args[5]
        assert evidence['migration_review']['policy'] == policy
        assert 'migration_approved' in schema['required']
        return {'accepted': True, 'blocked': False, 'inspection_blocked': mode == 'blocked',
                'reason': 'fixture only', 'execution_ref': 'fixture:review',
                'command_inspection_succeeded': mode != 'no_command',
                'migration_approved': mode in {'explicit', 'no_command'},
                'migration_binding': approval_binding(record)}

    monkeypatch.setattr(executor, '_run', review)
    result = executor.decide_one('lead:improvement')
    with service.store.transaction() as tx:
        current = tx.get('releases', record['id'])
        outbox = tx.scan('outbox')
    if mode != 'explicit':
        assert current['reviews'] == [] and not outbox
        assert result['status'] != 'succeeded'
        return
    assert len(current['reviews']) == 1
    assert result['result']['release_id'] == record['id']
    executor.workflow.handle(outbox[0]['message'])
    assert executor.decide_one('conductor')['status'] == 'succeeded'
    with service.store.transaction() as tx:
        current = tx.get('releases', record['id'])
        queue = tx.get('release_queue', record['id'])
    validate_approvals(current, organization())
    assert queue['status'] == 'awaiting_bootstrap'


def test_controller_rejects_different_revision_before_qualification():
    from codex_harness.adapters.evaluator_migration import validate_controller

    with pytest.raises(ContractError, match='controller revision mismatch'):
        validate_controller({'migration': {'controller_revision': 'not-this-controller'}})


def test_controller_rejects_dirty_source(monkeypatch):
    from codex_harness.adapters import evaluator_migration

    def read(root, *args):
        return b'candidate\n' if args[0] == 'rev-parse' else b' M src/changed.py\n'

    monkeypatch.setattr(evaluator_migration, 'git_bytes', read)
    with pytest.raises(ContractError, match='must be clean'):
        evaluator_migration.validate_controller({'migration': {'controller_revision': 'candidate'}})


@pytest.mark.parametrize('stale', [False, True])
def test_runner_selects_full_authorized_evaluator_and_original_ancestry(tmp_path, monkeypatch, stale):
    from codex_harness.adapters import deployment
    from codex_harness.adapters.artifacts import FileArtifacts

    releases, record = approved()
    visited = []
    def workspace(revision, name):
        visited.append(revision)
        return str(tmp_path)

    git = SimpleNamespace(repository=tmp_path, _git=lambda *a: 'stale' if stale else SOURCE_BASE,
                          inspect=lambda revision, base: {'tree': 'tree'} if base == SOURCE_BASE else {},
                          review_workspace=workspace)
    runner = deployment.ReleaseRunner(SimpleNamespace(store=releases.store, org=releases.org),
                                       git, FileArtifacts(tmp_path / 'artifacts'), str(tmp_path / 'auth'))
    monkeypatch.setattr(deployment, 'validate_manifest', lambda *a: None)
    monkeypatch.setattr(deployment, 'validate_controller', lambda *a: None)
    def stop(*args, **kwargs):
        raise RuntimeError('fixture stop after evaluator selection, before execution')
    monkeypatch.setattr(runner, '_check', stop)
    if stale:
        with pytest.raises(ContractError, match='source base is stale'):
            runner._run(record['id'])
        assert visited == []
        return
    with pytest.raises(RuntimeError, match='fixture stop'):
        runner._run(record['id'])
    assert visited == [EVALUATOR, 'candidate']
    with releases.store.transaction() as tx:
        assert tx.get('releases', record['id'])['status'] == 'reviewed'


@pytest.mark.parametrize('exit_code', [0, 1, None, False])
def test_command_inspection_is_derived_from_execution_not_model(tmp_path, monkeypatch, exit_code):
    from codex_harness.adapters.artifacts import FileArtifacts
    from codex_harness.adapters.executor import VERDICT, Executor
    from codex_harness.application.service import Harness

    event = {'method': 'item/completed', 'params': {'item': {
        'id': 'command', 'type': 'commandExecution', 'status': 'completed',
        'exitCode': exit_code, 'aggregatedOutput': 'fixture source inspection'}}}

    class Runtime:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def run(self, *args, **kwargs):
            return {'answer': {'accepted': True, 'command_inspection_succeeded': True},
                    'events': [event], 'thread_id': 'fixture', 'usage': {},
                    'rotate': False, 'interrupted': False}

    monkeypatch.setattr('codex_harness.adapters.executor.AppServer', Runtime)
    service = Harness(MemoryStore(), organization())
    artifacts = FileArtifacts(str(tmp_path / 'artifacts'))
    executor = Executor(service, SimpleNamespace(_git=lambda *a, **k: 'revision'), artifacts)
    result = executor._run('lead:improvement', 'fixture', 'Review source', {},
                           str(tmp_path), VERDICT, read_only=True)
    assert result['command_inspection_succeeded'] is (type(exit_code) is int and exit_code == 0)
    assert json.loads(artifacts.text(result['execution_ref'], 100000))['events'] == [event]
