import subprocess

import pytest

from codex_harness.adapters.artifacts import FileArtifacts
from codex_harness.adapters.deployment import ReleaseRunner
from codex_harness.adapters.git import GitWorkspace
from codex_harness.adapters.maintenance import ArtifactMaintenance
from codex_harness.adapters.store import MemoryStore
from codex_harness.application.service import Harness
from codex_harness.bootstrap import organization


@pytest.mark.parametrize('tombstones,changed,expected', [
    (True, True, 'rollback_blocked'), (True, False, 'rolled_back'), (False, True, 'rolled_back'),
])
def test_rollback_checks_real_git_writer_identity(tmp_path, tombstones, changed, expected):
    repo = tmp_path / 'repo'
    repo.mkdir()

    def git(*args):
        return subprocess.check_output(['git', '-c', 'user.name=Test', '-c', 'user.email=test@localhost',
                                        *args], cwd=repo, text=True).strip()

    git('init', '-q')
    paths = ['src/codex_harness/adapters/store.py', 'src/codex_harness/adapters/record_references.py',
             'src/codex_harness/adapters/artifacts.py', 'src/codex_harness/application/rlm.py']
    for name in paths:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('# retained writer source\n')
    git('add', '.')
    git('commit', '-qm', 'previous writer')
    previous = git('rev-parse', 'HEAD')
    if changed:
        (repo / paths[0]).write_text('# changed writer protocol\n')
    (repo / 'README.md').write_text('next release')
    git('add', '.')
    git('commit', '-qm', 'current writer')
    revision = git('rev-parse', 'HEAD')
    service = Harness(MemoryStore(), organization())
    active = {'release_id': 'current', 'revision': revision, 'previous': {'release_id': 'previous'}}
    with service.store.transaction() as tx:
        tx.put('deployment', 'active', active)
        for key, rev in [('previous', previous), ('current', revision)]:
            tx.put('releases', key, {'id': key, 'status': 'active' if key == 'current' else 'superseded',
                                    'candidate': {'revision': rev}})
        if tombstones:
            tx.put('artifact_tombstones', 'deleted', {'ref': 'sha256:' + 'a' * 64})
    runner = ReleaseRunner(service, GitWorkspace(str(repo), str(tmp_path / 'workspaces')),
                           FileArtifacts(str(tmp_path / 'artifacts')), str(tmp_path / 'auth.json'))
    result = runner.rollback_if_compatible(active, 'CLI health failure')
    assert result['status'] == expected
    with service.store.transaction() as tx:
        assert tx.get('deployment', 'active')['release_id'] == ('current' if expected == 'rollback_blocked' else 'previous')
        assert tx.get('maintenance_control', 'collection')['status'] == 'paused'
    assert ArtifactMaintenance(service.store, runner.artifacts).collect(apply=True)['reason'] == 'collection_paused'
    if expected == 'rollback_blocked':
        assert runner.artifacts.inspect(result['evidence'])
        assert paths[0] in result['reason']
