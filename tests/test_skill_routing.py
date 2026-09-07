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
    for value in ['NaN', '?', '-1']:
        with pytest.raises(ContractError):
            score_skill({'min_score': value}, 'test', set(), {})
    assert score_skill({'keywords': '''["api", 'rest']'''}, 'api rest', set(), {})[1] == 2
    assert score_skill({'keywords': '''["", '', api]'''}, 'nothing here', set(), {})[1] == 0


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
    assert records['stage.md']['dimensions'] == ['pipeline:first']
    from codex_harness.domain.skill_audit import audit_history

    audit = audit_history([{'id': 'stage', 'top': [records['stage.md']]}])
    assert audit['dim_weight'] == {'unknown': 1}
    assert audit['skills'][0]['dominant_dim'] == 'unknown'
    assert records['irrelevant.md']['tier'] == 'unmatched'
    assert artifacts.read(records['weak.md']['content_ref']).endswith('HIDDEN_WEAK')
    (root / 'src/auth.py').write_text('changed', encoding='utf-8')
    assert project_context(git, artifacts, str(root), revision, query)[1] == summary
    changed = project_context(git, artifacts, str(root), revision, 'unrelated')[1]
    assert changed['manifest_ref'] != summary['manifest_ref']


def test_composed_budget_fills_lower_rank_and_bounds_pointer_tail(tmp_path):
    from codex_harness.adapters.skill_routing import route_skills
    from codex_harness.domain.model import ContextItem

    class EmptyGit:
        def _git(self, *args, **kwargs):
            return ''

    artifacts = FileArtifacts(str(tmp_path / 'artifacts'))
    items, records = [], []
    bodies = {'top': 'x' * 3500 + '\n## 의사결정 트리\n' + 'logic' * 12000,
              'second': 'SECOND', 'legacy': 'LEGACY'}
    bodies.update({f'weak{i}': 'HIDDEN' for i in range(10)})
    for name, body in bodies.items():
        keywords = 'alpha beta gamma delta' if name == 'top' else 'alpha beta gamma' if name == 'second' else 'alpha'
        source = body if name == 'legacy' else f'---\nkeywords: {keywords}\n---\n{body}'
        record = artifacts.put(source, 'fixture')
        path = f'.harness/skills/_common/{name}.md'
        records.append({'path': path, 'content_ref': record['ref'], 'file': str(tmp_path / name),
                        'revision': 'a' * 40, 'pipeline_boost': 0})
        items.append(ContextItem('project-skill:' + path, source, record['ref'], 'a' * 40, 15))
    rendered, summary = route_skills(EmptyGit(), artifacts, str(tmp_path), 'a' * 40,
        'alpha beta gamma delta', items, records)
    assert summary['full'] == 2
    assert summary['pointers'] == 8 and summary['external_pointers'] == 2
    assert summary['legacy'] == 1
    full = [item for item in rendered if item.priority == 18]
    assert sum(len(item.body) for item in full) <= 4000
    assert max(len(item.body) for item in full) <= 3000
    assert any(item.body == 'SECOND' for item in full)
    assert any(item.body == 'LEGACY' for item in rendered)
    assert all(record.get('tier') for record in records)


def test_frontmatter_requires_a_bare_closing_fence():
    from codex_harness.adapters.skill_routing import frontmatter
    with pytest.raises(ContractError, match='fence'):
        frontmatter('---\nkeywords: test\n---not-a-fence\nbody')
    assert frontmatter('---\nkeywords: test\n---\nBODY') == ({'keywords': 'test'}, 'BODY')
