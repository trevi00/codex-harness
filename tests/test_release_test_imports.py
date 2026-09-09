"""Reproduce sibling-test imports in the incumbent release evaluator."""
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def test_incumbent_sibling_imports_use_candidate_package(tmp_path):
    incumbent = tmp_path / 'incumbent' / 'tests'
    incumbent.mkdir(parents=True)
    (incumbent / 'helper.py').write_text('VALUE = 42\n')
    candidate = tmp_path / 'candidate'
    candidate.mkdir()
    package = candidate / 'release_fixture.py'
    package.write_text('VERSION = "candidate"\n')
    old_source = incumbent.parent / 'src'
    old_source.mkdir()
    (old_source / 'release_fixture.py').write_text('VERSION = "incumbent"\n')
    (incumbent / 'test_import.py').write_text(
        'from helper import VALUE\nimport release_fixture\n'
        'def test_source():\n    assert VALUE == 42\n    assert release_fixture.VERSION == "candidate"\n')
    config = candidate / 'pytest.ini'
    config.write_text('[pytest]\n')
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', str(incumbent), '-c', str(config),
         '--import-mode=importlib', '-q'], cwd=candidate,
        env={**os.environ, 'PYTHONPATH': str(incumbent)},
        capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


def test_incumbent_file_fixtures_and_imports_share_candidate_source(tmp_path):
    from pathlib import Path

    from codex_harness.adapters.deployment import incumbent_test_workspace

    original = tmp_path / 'incumbent'
    selected = tmp_path / 'candidate'
    for root, value in ((original, 'old'), (selected, 'new')):
        (root / 'src').mkdir(parents=True)
        (root / 'src' / 'policy_fixture.py').write_text(f'VALUE = "{value}"\n')
    subprocess.run(['git', 'init', '-q', str(original)], check=True)
    (original / 'tests').mkdir()
    test = original / 'tests/test_source.py'
    test.write_text(
        'from pathlib import Path\nimport policy_fixture\n'
        'def test_same_source():\n'
        '    source = Path(__file__).resolve().parents[1] / "src/policy_fixture.py"\n'
        '    assert source.read_text() == Path(policy_fixture.__file__).read_text()\n'
        '    assert policy_fixture.VALUE == "new"\n')
    (original / 'pyproject.toml').write_text('[tool.pytest.ini_options]\n')
    expected = test.read_bytes()
    with incumbent_test_workspace(str(original), str(selected)) as evaluator:
        assert (evaluator / 'tests/test_source.py').read_bytes() == expected
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', str(evaluator / 'tests'),
             '--import-mode=importlib', '-q'], cwd=evaluator,
            env={**os.environ, 'PYTHONPATH': os.pathsep.join(
                [str(evaluator / 'tests'), str(evaluator / 'src')])},
            capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
        scratch = Path(evaluator)
    assert not scratch.exists()
    assert test.read_bytes() == expected
    assert 'old' in (original / 'src/policy_fixture.py').read_text()
    assert 'new' in (selected / 'src/policy_fixture.py').read_text()


@pytest.mark.parametrize("failure", ["body", "copy"])
def test_evaluator_preserves_history_config_and_cleans_failure(tmp_path, monkeypatch, failure):
    from codex_harness.adapters import deployment

    original = tmp_path / 'incumbent'
    selected = tmp_path / 'candidate'
    for root in (original, selected):
        (root / 'src').mkdir(parents=True)
        (root / 'src/source.py').write_text('VALUE = 1\n')
    (original / 'tests').mkdir()
    (original / 'tests/test_one.py').write_text('def test_one(): pass\n')
    config = b'[tool.pytest.ini_options]\naddopts = "--strict-markers"\n'
    (original / 'pyproject.toml').write_bytes(config)
    subprocess.run(['git', 'init', '-q', str(original)], check=True)
    subprocess.run(['git', '-C', str(original), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(original), '-c', 'user.name=Fixture',
                    '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'incumbent'],
                   check=True)
    def git(root, *args):
        return subprocess.check_output(['git', '-C', str(root), *args])
    revision = git(original, 'rev-parse', 'HEAD')
    tracked = {name: (original / name).read_bytes()
               for name in git(original, 'ls-files').decode().splitlines()}
    scratch = []
    copytree = deployment.shutil.copytree
    def copy(source, destination, *args, **kwargs):
        if Path(source) == original:
            scratch.append(Path(destination).parent)
        if failure == 'copy' and Path(source) == selected / 'src':
            raise OSError('injected copy failure')
        return copytree(source, destination, *args, **kwargs)
    monkeypatch.setattr(deployment.shutil, 'copytree', copy)
    with pytest.raises(OSError, match='injected'):
        with deployment.incumbent_test_workspace(str(original), str(selected)) as evaluator:
            assert git(evaluator, 'rev-parse', 'HEAD') == revision
            assert git(evaluator, 'log', '--format=%H') == git(original, 'log', '--format=%H')
            assert (evaluator / 'pyproject.toml').read_bytes() == config
            for name, content in tracked.items():
                assert (evaluator / name).read_bytes() == content
            raise OSError('injected body failure')
    assert scratch and all(not path.exists() for path in scratch)
    assert git(original, 'status', '--porcelain') == b''
    assert all((original / name).read_bytes() == content for name, content in tracked.items())
    assert (selected / 'src/source.py').read_text() == 'VALUE = 1\n'


def test_release_runner_invokes_ephemeral_incumbent_suite(tmp_path, monkeypatch):
    from contextlib import contextmanager

    from codex_harness.adapters.artifacts import FileArtifacts
    from codex_harness.adapters.deployment import ReleaseRunner
    from codex_harness.adapters.store import MemoryStore
    from codex_harness.bootstrap import organization

    @contextmanager
    def environment(*args):
        # Layout unit test only. Real Docker lifecycle is tested separately.
        yield {**os.environ, 'HARNESS_INTEGRATION': '1'}

    monkeypatch.setattr('codex_harness.adapters.deployment.isolated_release_services',
                        environment)

    original, selected = tmp_path / 'incumbent', tmp_path / 'candidate'
    for root, value in ((original, 'old'), (selected, 'new')):
        (root / 'src').mkdir(parents=True)
        (root / 'src/policy_fixture.py').write_text(f'VALUE = "{value}"\n')
        (root / 'tests').mkdir()
    subprocess.run(['git', 'init', '-q', str(original)], check=True)
    (original / 'pyproject.toml').write_text('[tool.pytest.ini_options]\n')
    test = original / 'tests/test_source.py'
    test.write_text('from pathlib import Path\nimport policy_fixture\n'
                    'def test_source():\n'
                    '    assert policy_fixture.VALUE == "new"\n'
                    '    assert Path.cwd() == Path(__file__).resolve().parents[1]\n'
                    '    assert (Path.cwd() / "src/policy_fixture.py").read_text() == '
                    'Path(policy_fixture.__file__).read_text()\n')
    store = MemoryStore()
    service = SimpleNamespace(store=store, org=organization())
    store.dsn = 'fixture-only'
    git = SimpleNamespace(_git=lambda *args: 'base', inspect=lambda *args: {'tree': 'tree'},
                          review_workspace=lambda revision, name: str(
                              original if revision == 'base' else selected))
    runner = ReleaseRunner(service, git, FileArtifacts(tmp_path / 'artifacts'),
                           str(tmp_path / 'auth'), auto_merge=False)
    release = runner.releases.propose(
        {'revision': 'candidate', 'base': 'base', 'tree': 'tree',
         'author': 'worker:implementation'}, {'checks': ['tests'], 'revision': 'base'})
    # INV-RELEASE-001: fixture state only; this test creates no independent review.
    with store.transaction() as tx:
        tx.put('releases', release['id'], {**release, 'status': 'reviewed'})
    visited = []
    real_check = runner._check
    def check(argv, cwd=None, timeout=300, env=None):
        if argv[1:3] == ['-m', 'pytest']:
            assert timeout == 900
        if '--import-mode=importlib' in argv:
            evaluator = Path(cwd)
            visited.append(evaluator)
            assert evaluator != original and evaluator != selected
            assert argv[3] == str(evaluator / 'tests')
            assert argv[5] == str(evaluator / 'pyproject.toml')
            assert env['HARNESS_INTEGRATION'] == '1'
            assert (evaluator / 'tests/test_source.py').read_bytes() == test.read_bytes()
            result = real_check([sys.executable, *argv[1:]], cwd, timeout, env)
            assert result['passed']
            return result
        if argv[1:3] == ['-m', 'pytest']:
            assert visited and not visited[0].exists()
            assert cwd == str(selected)
            raise RuntimeError('stop before canary or publishing')
        assert argv == ['uv', 'sync', '--frozen']
        return {'passed': True, 'evidence': 'fixture-install'}
    monkeypatch.setattr(runner, '_check', check)
    with pytest.raises(RuntimeError, match='stop before canary'):
        runner.run(release['id'])
    assert visited and not visited[0].exists()
    assert 'old' in (original / 'src/policy_fixture.py').read_text()
