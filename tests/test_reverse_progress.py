from concurrent.futures import ThreadPoolExecutor

import pytest

from codex_harness.adapters.artifacts import FileArtifacts
from codex_harness.adapters.commands import run_process
from codex_harness.adapters.reverse_source import observe_source
from codex_harness.adapters.store import MemoryStore
from codex_harness.application.reverse_progress import ReverseProgress
from codex_harness.domain.model import ContractError


@pytest.fixture
def progress(tmp_path):
    artifacts = FileArtifacts(str(tmp_path / 'artifacts'))
    ref = artifacts.put('verified generated document', 'fixture')['ref']
    return ReverseProgress(MemoryStore(), artifacts), ref


def source(commit='a'):
    return {'repository': 'source-project', 'commit': commit * 40,
            'tree': 'b' * 40, 'status': 'clean'}


def test_four_stages_survive_new_service_and_require_real_artifacts(progress):
    app, ref = progress
    for generation, stage in enumerate(('1-A', '1-B', '1-C', '2')):
        app = ReverseProgress(app.store, app.artifacts)
        row = app.record('p', stage, 'complete', source(), [ref], generation, stage)
    assert row['generation'] == 4
    assert list(row['releases']) == ['1-A', '1-B', '1-C', '2']
    assert app.status('p', source())['source_state'] == 'unchanged'
    with pytest.raises(ContractError, match='retained artifacts'):
        app.record('other', '1-A', 'complete', source(), [], 0, 'empty')
    with pytest.raises((ValueError, OSError, ContractError)):
        app.record('other', '1-A', 'complete', source(), ['sha256:' + 'f' * 64], 0, 'missing')


def test_retry_is_idempotent_but_conflicting_request_rejected(progress):
    app, ref = progress
    original = app.record('p', '1-A', 'complete', source(), [ref], 0, 'r')
    assert app.record('p', '1-A', 'complete', source(), [ref], 0, 'r') == original
    with pytest.raises(ContractError, match='Conflicting'):
        app.record('p', '1-A', 'partial', source(), [ref], 0, 'r')
    with app.store.transaction() as tx:
        assert len(tx.scan('reverse_history')) == 1


def test_unknown_dirty_and_moved_sources_do_not_inherit_completion(progress):
    app, ref = progress
    app.record('p', '1-A', 'complete', source(), [ref], 0, 'first')
    for state in ('unknown', 'dirty'):
        observation = {**source(), 'status': state}
        assert app.status('p', observation)['source_state'] == state
        with pytest.raises(ContractError, match='dirty or unknown'):
            app.record('p', '1-B', 'partial', observation, [], 1, state)
    assert app.status('p', source('c'))['source_state'] == 'changed'
    with pytest.raises(ContractError, match='rebaseline'):
        app.record('p', '1-B', 'partial', source('c'), [], 1, 'moved')
    row = app.record('p', '1-A', 'partial', source('c'), [], 1, 'restart', rebaseline=True)
    assert row['generation'] == 2 and row['releases']['1-A']['status'] == 'partial'
    with app.store.transaction() as tx:
        assert len(tx.scan('reverse_history')) == 2


def test_stage_order_and_completed_stage_immutability(progress):
    app, ref = progress
    with pytest.raises(ContractError, match='Previous'):
        app.record('p', '1-B', 'complete', source(), [ref], 0, 'skip')
    app.record('p', '1-A', 'complete', source(), [ref], 0, 'first')
    with pytest.raises(ContractError, match='immutable'):
        app.record('p', '1-A', 'pending', source(), [], 1, 'downgrade')


def test_missing_predecessor_evidence_blocks_continuation(progress):
    app, ref = progress
    app.record('p', '1-A', 'complete', source(), [ref], 0, 'first')
    (app.artifacts.root / (ref[7:] + '.txt')).unlink()
    with pytest.raises((ValueError, OSError, ContractError)):
        app.record('p', '1-B', 'partial', source(), [], 1, 'lost')
    assert app.status('p', source())['progress']['generation'] == 1


def test_racing_writers_cannot_lose_a_checkpoint(progress):
    app, _ = progress
    def record(request):
        try:
            app.record('p', '1-A', 'partial', source(), [], 0, request)
            return 'saved'
        except ContractError:
            return 'stale'
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(record, ['a', 'b'])) == ['saved', 'stale']
    assert app.status('p', source())['progress']['generation'] == 1


def test_git_observation_detects_dirty_and_unknown_sources(tmp_path):
    def git(*args):
        result = run_process(['git', '-C', str(tmp_path), *args])
        assert result.returncode == 0, result.stderr
    assert observe_source(tmp_path / 'missing')['status'] == 'unknown'
    git('init', '-q')
    git('-c', 'user.name=fixture', '-c', 'user.email=fixture@example.invalid',
        'commit', '--allow-empty', '-qm', 'base')
    clean = observe_source(tmp_path)
    assert clean['status'] == 'clean' and len(clean['tree']) == 40
    # An invalid configured helper must not execute or affect the observation.
    git('config', 'core.fsmonitor', '/nonexistent-migration-fsmonitor')
    assert observe_source(tmp_path)['status'] == 'clean'
    (tmp_path / 'nested').mkdir()
    assert observe_source(tmp_path / 'nested')['status'] == 'unknown'
    (tmp_path / 'new.txt').write_text('untracked change')
    assert observe_source(tmp_path)['status'] == 'dirty'
