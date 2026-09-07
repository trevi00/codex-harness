import pytest

from codex_harness.adapters.artifacts import FileArtifacts
from codex_harness.adapters.git import GitWorkspace
from codex_harness.adapters.project_skills import project_context
from codex_harness.domain.model import ContractError
from codex_harness.domain.skill_ranking import (
    apply_token_budget,
    intent_in_prompt,
    keyword_in_prompt,
    score_skill,
)


def test_concept_dedup_and_korean_false_positives():
    assert not intent_in_prompt('자간', '진행하자')
    assert intent_in_prompt('만들어', 'api 만들고')
    assert not keyword_in_prompt('api', 'rapidly')
    assert score_skill({'intent': '승인해', 'keywords': '승인'}, '승인할게', set(), {})[1] == 2
    assert score_skill({'intent': '구현해'}, '구현해', set(), {})[1] == 1


def test_path_boundaries_and_supplied_pattern_evidence():
    meta = {'paths': 'auth', 'patterns': 'token', 'min_score': '3'}
    assert score_skill(meta, '', {'src/authorized.py'}, {'src/authorized.py': 'token'})[1] == 1
    assert score_skill(meta, '', {'src/auth.py'}, {'src/auth.py': 'token'})[:2] == (True, 3)
    assert score_skill(meta, '', {'src/auth.py'}, {})[:2] == (False, 2)
    with pytest.raises(ContractError):
        score_skill({'min_score': 'NaN'}, 'test', set(), {})


def test_large_top_skill_cannot_bypass_shared_budget():
    rows = [(9, 'one', [], 'x' * 60000), (4, 'two', [], 'SMALL')]
    fitted, truncated = apply_token_budget(rows)
    assert truncated and sum(len(row[3]) for row in fitted) <= 4000


def test_actual_routing_tiers_filter_stack_and_keep_retrieval_handles(tmp_path):
    root = tmp_path / 'project'
    root.mkdir()
    git = GitWorkspace(str(root), str(tmp_path / 'workspaces'))
    git._git('init', '-q')
    git._git('config', 'user.name', 'Fixture')
    git._git('config', 'user.email', 'fixture@localhost')
    content = {
        '.harness/tech-stack.yaml': 'stack: {language: python}',
        '.harness/stages.yaml': 'stages: [{id: first, skills: [stage]}]',
        '.harness/skills/python/strong.md': '---\nkeywords: alpha beta gamma\n---\nSTRONG',
        '.harness/skills/python/weak.md': '---\nkeywords: alpha\n---\nHIDDEN_WEAK',
        '.harness/skills/python/stage.md': '---\nkeywords: unrelated\n---\nHIDDEN_STAGE',
        '.harness/skills/python/irrelevant.md': '---\nkeywords: unrelated\n---\nUNMATCHED',
        '.harness/skills/python/pattern.md': '---\npatterns: pinned\n---\nHIDDEN_PATTERN',
        '.harness/skills/java/strong.md': '---\nkeywords: alpha beta gamma\n---\nEXCLUDED',
        'src/auth.py': 'pinned',
    }
    for name, body in content.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding='utf-8')
    git._git('add', '.')
    git._git('commit', '-qm', 'fixture')
    revision = git._git('rev-parse', 'HEAD')
    artifacts = FileArtifacts(str(tmp_path / 'artifacts'))
    query = 'alpha beta gamma src/auth.py'
    items, summary = project_context(git, artifacts, str(root), revision, query)
    rendered = '\n'.join(item.body for item in items)
    assert 'STRONG' in rendered
    assert all(word not in rendered for word in ['HIDDEN_WEAK', 'HIDDEN_STAGE', 'HIDDEN_PATTERN', 'UNMATCHED', 'EXCLUDED'])
    manifest = artifacts.document(summary['manifest_ref'])
    records = {record['path'].split('/')[-1]: record for record in manifest['skills']}
    assert records['strong.md']['tier'] == 'full'
    assert records['stage.md']['tier'] == 'pointer' and records['stage.md']['base_score'] == 0
    assert records['irrelevant.md']['tier'] == 'unmatched'
    assert artifacts.read(records['weak.md']['content_ref']).endswith('HIDDEN_WEAK')
    (root / 'src/auth.py').write_text('changed', encoding='utf-8')
    assert project_context(git, artifacts, str(root), revision, query)[1] == summary
    changed = project_context(git, artifacts, str(root), revision, 'unrelated')[1]
    assert changed['manifest_ref'] != summary['manifest_ref']
