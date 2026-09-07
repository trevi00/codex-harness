import copy
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from codex_harness.adapters.artifacts import FileArtifacts
from codex_harness.adapters.git import GitWorkspace
from codex_harness.adapters.skill_import import import_file
from codex_harness.adapters.store import MemoryStore
from codex_harness.adapters.threshold_policy import POLICY_PATHS, current_policy
from codex_harness.adapters.threshold_proposals import main
from codex_harness.application.threshold_proposals import ThresholdProposals
from codex_harness.application.threshold_replay import ThresholdReplay
from codex_harness.domain.model import ContractError, digest


def events(empty=False):
    return [{'at': f'2026-01-01T00:00:{i:02d}Z',
             'top': [{'score': score, 'body_chars': 500} for score in ([3] if empty else [3, 5])]}
            for i in range(40)]


@pytest.fixture
def policy_repo(tmp_path):
    root = tmp_path / 'repo'
    root.mkdir()
    git = GitWorkspace(str(root), str(tmp_path / 'workspaces'))
    git._git('init', '-q')
    git._git('config', 'user.name', 'Fixture')
    git._git('config', 'user.email', 'fixture@localhost')
    candidate = Path(__file__).resolve().parents[1]
    for relative in POLICY_PATHS:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((candidate / relative).read_text(encoding='utf-8'), encoding='utf-8')
    git._git('add', '.')
    git._git('commit', '-qm', 'policy fixture')
    return root, git


def test_current_policy_is_bound_to_regular_committed_loaded_sources(policy_repo):
    root, git = policy_repo
    policy = current_policy(git)
    assert policy['values'] == {'skill_match.FULL_BODY_MIN_SCORE': 3}
    assert set(policy['sources']) == set(POLICY_PATHS)
    source = root / POLICY_PATHS[0]
    source.write_text(source.read_text(encoding='utf-8') + '\n# dirty\n', encoding='utf-8')
    assert current_policy(git) == policy  # uncommitted file is not the selected Git definition
    git._git('add', '.')
    git._git('commit', '-qm', 'different definition')
    with pytest.raises(ContractError, match='differs'):
        current_policy(git)
    assert current_policy(git, policy['revision']) == policy
    blob = git._git('rev-parse', 'HEAD:' + POLICY_PATHS[0])
    git._git('update-index', '--cacheinfo', f'120000,{blob},{POLICY_PATHS[0]}')
    git._git('commit', '-qm', 'symlink source')
    with pytest.raises(ContractError, match='regular'):
        current_policy(git)


def test_collection_records_exact_evidence_once_and_keeps_history(policy_repo, tmp_path):
    _, git = policy_repo
    policy = current_policy(git)
    store, artifacts = MemoryStore(), FileArtifacts(str(tmp_path / 'artifacts'))
    with store.transaction() as tx:
        tx.put('skill_history', 'project', {'events': events()})
    original = copy.deepcopy(store.data['skill_history', 'project'])
    service = ThresholdProposals(store, artifacts, lambda: policy)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: service.collect('project'), range(8)))
    assert all(result == results[0] for result in results)
    run = results[0]
    assert len(run['proposals']) == 1 and not run['activation_ready']
    document = artifacts.document(run['evidence_ref'])
    assert document['events'] == events() and document['policy'] == policy
    assert store.data['skill_history', 'project'] == original
    assert sum(bucket == 'threshold_proposals' for bucket, _ in store.data) == 1
    assert not any(bucket in {'deployment', 'decisions_pending'} for bucket, _ in store.data)
    assert service.collect('other')['id'] != run['id']


def test_vacuous_reference_acceptance_is_explicitly_blocked(policy_repo, tmp_path):
    _, git = policy_repo
    store, artifacts = MemoryStore(), FileArtifacts(str(tmp_path / 'artifacts'))
    with store.transaction() as tx:
        tx.put('skill_history', 'project', {'events': events(empty=True)})
    run = ThresholdProposals(store, artifacts, lambda: current_policy(git)).collect('project')
    row, = run['proposals']
    assert row['proposal']['reference_accepted']
    assert 'empty_admission' in row['activation_blockers'] and not row['activation_ready']
    for part in row['proposal']['report']['partitions'].values():
        assert part['current_admitted_entries'] > 0 and part['proposed_admitted_entries'] == 0


def test_import_to_replay_and_proposal_preserves_legacy_provenance(policy_repo, tmp_path):
    _, git = policy_repo
    store, artifacts = MemoryStore(), FileArtifacts(str(tmp_path / 'artifacts'))
    source = tmp_path / 'legacy.jsonl'
    source.write_text(''.join(json.dumps({'ts': event['at'], 'top': [
        {**entry, 'name': str(index)} for index, entry in enumerate(event['top'])]}) + '\n'
        for event in events()), encoding='utf-8')
    imported = import_file(source, 'project', 'segment', store, artifacts)
    before = copy.deepcopy(store.data)
    replay = ThresholdReplay(store).evaluate('project', legacy_source='segment', old_value=3,
        proposed_value=4, holdout_boundary='2026-01-01T00:00:28Z')
    assert replay['source_ref'] == imported['source_ref'] and replay['report']['gate']['accept']
    assert replay['report']['partitions']['holdout']['events'] == 12
    assert store.data == before
    run = ThresholdProposals(store, artifacts, lambda: current_policy(git)).collect('project', legacy_source='segment')
    row, = run['proposals']
    assert 'historical_policy_and_skill_versions_unknown' in row['activation_blockers']
    evidence = artifacts.document(run['evidence_ref'])
    assert evidence['source_ref'] == imported['source_ref'] and evidence['events'] == replay['events']
    for key, value in before.items():
        assert store.data[key] == value


def test_real_git_cli_collection_and_stale_code_rejection(policy_repo, tmp_path, capsys):
    root, git = policy_repo
    store = MemoryStore()
    with store.transaction() as tx:
        tx.put('skill_history', digest('github:owner/repo'), {'events': events()})
    args = ['--github-repo', 'owner/repo', '--harness-repo', str(root), '--artifacts', str(tmp_path / 'artifacts')]
    assert main(args, store=store) == 0
    run = json.loads(capsys.readouterr().out)
    assert len(run['proposals']) == 1
    source = root / POLICY_PATHS[0]
    source.write_text('FULL_BODY_MIN_SCORE = 99\n', encoding='utf-8')
    git._git('add', '.')
    git._git('commit', '-qm', 'mismatch')
    before = copy.deepcopy(store.data)
    assert main(args, store=store) == 2
    assert 'Traceback' not in capsys.readouterr().err and store.data == before


def test_nonfinite_source_metadata_cannot_enter_evidence(policy_repo, tmp_path):
    _, git = policy_repo
    store, artifacts = MemoryStore(), FileArtifacts(str(tmp_path / 'artifacts'))
    corpus = events()
    corpus[0]['extra'] = float('nan')
    with store.transaction() as tx:
        tx.put('skill_history', 'project', {'events': corpus})
    with pytest.raises(ContractError, match='finite JSON'):
        ThresholdProposals(store, artifacts, lambda: current_policy(git)).collect('project')
    assert not list(artifacts.root.glob('*.txt'))
    assert not any(bucket.startswith('threshold_') for bucket, _ in store.data)
