"""Bind currently loaded threshold constants to inspected Git source text."""
from pathlib import Path

from codex_harness.adapters import skill_routing
from codex_harness.domain import skill_ranking
from codex_harness.domain.model import digest, require

POLICY_PATHS = (
    'src/codex_harness/domain/skill_ranking.py',
    'src/codex_harness/adapters/skill_routing.py',
    'src/codex_harness/domain/threshold_proposals.py',
    'src/codex_harness/domain/threshold_replay.py',
    'src/codex_harness/domain/skill_audit.py',
    'src/codex_harness/domain/skill_history.py',
    'src/codex_harness/domain/model.py',
    'src/codex_harness/application/threshold_proposals.py',
    'src/codex_harness/adapters/threshold_proposals.py',
    'src/codex_harness/adapters/threshold_policy.py',
    'src/codex_harness/adapters/threshold_reviews.py',
    'src/codex_harness/application/threshold_reviews.py',
    'src/codex_harness/adapters/executor.py',
    'src/codex_harness/application/workflow.py',
    'src/codex_harness/adapters/git.py',
    'src/codex_harness/adapters/commands.py',
    'src/codex_harness/adapters/artifacts.py',
    'src/codex_harness/adapters/store.py',
    'src/codex_harness/domain/policy.py',
    'src/codex_harness/resources/organization.json',
)


def current_policy(git, revision='HEAD'):
    # INV-THRESHOLD-PROPOSAL-001: a separate, unused policy file is not live policy.
    require(isinstance(revision, str) and not revision.startswith('-'), 'Invalid policy revision')
    commit = git._git('rev-parse', '--verify', revision + '^{commit}')
    raw = git._git('ls-tree', '-rz', commit, '--', *POLICY_PATHS, strip=False)
    inventory = {entry.split('\t', 1)[1]: entry.split(' ', 1)[0]
                 for entry in raw.split('\0') if '\t' in entry}
    root = Path(__file__).resolve().parents[1]
    sources = {}
    for path in POLICY_PATHS:
        require(inventory.get(path) in {'100644', '100755'}, 'Missing regular policy source')
        committed = git._git('show', commit + ':' + path, strip=False)
        loaded = (root / path.removeprefix('src/codex_harness/')).read_text(encoding='utf-8')
        require(committed == loaded, 'Loaded threshold source differs from selected Git revision')
        sources[path] = {'text': committed, 'hash': digest(committed)}
    require(skill_routing.FULL_BODY_MIN_SCORE == skill_ranking.FULL_BODY_MIN_SCORE,
            'Loaded routing threshold differs from definition')
    return {'revision': commit, 'values': {'skill_match.FULL_BODY_MIN_SCORE': skill_ranking.FULL_BODY_MIN_SCORE},
            'sources': sources, 'kind': 'current_native_source_constants',
            'encoding': 'UTF-8 text with normalized newlines'}
