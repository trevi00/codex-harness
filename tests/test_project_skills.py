import json

import pytest

from codex_harness.adapters.artifacts import FileArtifacts
from codex_harness.adapters.executor import IMPLEMENTATION, Executor
from codex_harness.adapters.git import GitWorkspace
from codex_harness.adapters.project_skills import initialize, parse_profile, project_context
from codex_harness.adapters.store import MemoryStore
from codex_harness.application.service import Harness
from codex_harness.bootstrap import organization
from codex_harness.domain.model import ContractError
from codex_harness.domain.project_skills import eligible_paths, select_skill_paths


def test_multistack_legacy_yaml_preserves_version_spelling_and_extensions():
    profile = parse_profile('''backend:
  language: java
  framework: springboot
  version: 3.10
frontend:
  language: typescript
  framework: react
  version: 18
extensions: [flutter/outpos-agent, _gsd]
''')
    paths = eligible_paths(profile)
    assert paths[:4] == ['_common', 'java/springboot-3.10', 'java/springboot', 'java/3.10']
    assert 'typescript/18.x' in paths and paths[-2:] == ['flutter/outpos-agent', '_gsd']


@pytest.mark.parametrize('text', [
    'stack:\n  language: python\n  language: java',
    'extensions: [../outside]', 'extensions: [/absolute]', 'extensions: [C:\\escape]',
    'schema_version: 2', 'unexpected: field',
    'stacks: []\nstack: {language: python}',
    'stack: &recursive {language: *recursive}',
])
def test_invalid_profile_never_falls_back_to_all_skills(text):
    with pytest.raises(ContractError):
        parse_profile(text)


def test_selection_excludes_other_frameworks_and_preserves_packaged_skills():
    profile = parse_profile('stack: {language: python, framework: fastapi}')
    inventory = ['_common/base.md', 'python/style.md', 'python/fastapi/routes.md',
                 'python/fastapi/testing/SKILL.md', 'python/django/SKILL.md',
                 'java/lang/style.md', 'python/_index.md']
    assert set(select_skill_paths(profile, inventory)) == {
        '_common/base.md', 'python/style.md', 'python/fastapi/routes.md',
        'python/fastapi/testing/SKILL.md'}
    assert select_skill_paths(parse_profile('stacks: []'), inventory) == ['_common/base.md']


@pytest.fixture
def project(tmp_path):
    root = tmp_path / 'project'
    root.mkdir()
    git = GitWorkspace(str(root), str(tmp_path / 'workspaces'))
    git._git('init', '-q')
    git._git('config', 'user.name', 'Fixture')
    git._git('config', 'user.email', 'fixture@example.invalid')
    initialize(root, 'stack: {language: python, framework: fastapi}')
    for path, body in {'_common/base.md': 'COMMON_ONLY',
                       'python/fastapi/routes.md': 'FASTAPI_ELIGIBLE',
                       'java/lang/style.md': 'JAVA_MUST_NOT_LOAD'}.items():
        target = root / '.harness/skills' / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding='utf-8')
    git._git('add', '.')
    git._git('commit', '-qm', 'project definition')
    return root, git, FileArtifacts(str(tmp_path / 'artifacts'))


def test_init_is_exclusive_and_git_pin_ignores_uncommitted_configuration(project):
    root, git, artifacts = project
    revision = git._git('rev-parse', 'HEAD')
    with pytest.raises(FileExistsError):
        initialize(root, 'stack: {language: java}')
    (root / '.harness/tech-stack.yaml').write_text('stack: {language: java}')
    items, summary = project_context(git, artifacts, str(root), revision)
    assert {i.body for i in items} == {'COMMON_ONLY', 'FASTAPI_ELIGIBLE'}
    assert summary['count'] == 2
    assert artifacts.document(summary['manifest_ref'])['revision'] == revision
    nested = root / 'src'
    nested.mkdir()
    nested_items, _ = project_context(git, artifacts, str(nested), revision)
    assert nested_items == items


def test_actual_executor_context_contains_only_eligible_pinned_skills(project, monkeypatch):
    root, git, artifacts = project
    prompts = []
    class Runtime:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def run(self, prompt, *args, **kwargs):
            prompts.append(json.loads(prompt))
            return {'answer': {'summary': 'fixture', 'tests': []}, 'thread_id': 'fixture',
                    'usage': {}, 'rotate': False, 'interrupted': False, 'events': []}
    monkeypatch.setattr('codex_harness.adapters.executor.AppServer', Runtime)
    executor = Executor(Harness(MemoryStore(), organization()), git, artifacts)
    executor._run('worker:implementation', 'task', 'Test context routing', {}, str(root), IMPLEMENTATION)
    text = json.dumps(prompts[0])
    assert 'FASTAPI_ELIGIBLE' in text and 'COMMON_ONLY' in text
    assert 'JAVA_MUST_NOT_LOAD' not in text
    assert prompts[0]['required']['project_skills']['count'] == 2
    (root / '.harness/tech-stack.yaml').write_text('stack: {language: java}')
    git._git('add', '.harness/tech-stack.yaml')
    git._git('commit', '-qm', 'switch stack')
    executor._run('worker:implementation', 'task', 'Test context routing', {}, str(root), IMPLEMENTATION)
    assert 'JAVA_MUST_NOT_LOAD' in json.dumps(prompts[1])
    assert 'FASTAPI_ELIGIBLE' not in json.dumps(prompts[1])
    assert prompts[1]['required']['recovery']['sources'] == {}
    git._git('rm', '-r', '.harness')
    git._git('commit', '-qm', 'remove project skill configuration')
    executor._run('worker:implementation', 'task', 'Test context routing', {}, str(root), IMPLEMENTATION)
    assert prompts[2]['required']['project_skills']['status'] == 'not_configured'
    assert prompts[2]['required']['recovery']['sources'] == {}
    assert 'JAVA_MUST_NOT_LOAD' not in json.dumps(prompts[2])


def test_profile_symlink_in_git_is_rejected(project):
    root, git, artifacts = project
    blob = git._git('rev-parse', 'HEAD:.harness/tech-stack.yaml')
    git._git('update-index', '--cacheinfo', f'120000,{blob},.harness/tech-stack.yaml')
    git._git('commit', '-qm', 'fixture symlink mode')
    with pytest.raises(ContractError, match='regular Git file'):
        project_context(git, artifacts, str(root), git._git('rev-parse', 'HEAD'))
