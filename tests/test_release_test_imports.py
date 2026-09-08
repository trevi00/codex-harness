"""Reproduce sibling-test imports in the incumbent release evaluator."""
import os
import subprocess
import sys


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
