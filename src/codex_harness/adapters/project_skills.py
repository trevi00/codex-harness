"""Git-pinned YAML profiles and skills; working-tree initialization is explicit."""
from pathlib import Path

import yaml

from codex_harness.domain.model import ContextItem, ContractError, canonical, require
from codex_harness.domain.project_skills import normalize_profile, select_skill_paths

PROFILE = '.harness/tech-stack.yaml'
SKILLS = '.harness/skills/'


class UniqueLoader(yaml.BaseLoader):
    pass


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        require(isinstance(key, str) and key not in result, 'Duplicate or non-string YAML key')
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def parse_profile(text):
    require(len(text.encode('utf-8')) <= 65536, 'Project profile exceeds size limit')
    try:
        value = yaml.load(text, Loader=UniqueLoader)
    except yaml.YAMLError as exc:
        raise ContractError('Invalid project YAML') from exc
    return normalize_profile(value)


def initialize(root, text):
    root = Path(root).resolve()
    require(root.is_dir(), 'Project root must exist')
    profile = parse_profile(text)
    path = root / PROFILE
    require(path.resolve().is_relative_to(root), 'Project profile escapes project root')
    path.parent.mkdir(parents=True, exist_ok=True)
    # INV-PROJECT-001: init never overwrites a user-authored project definition.
    with path.open('x', encoding='utf-8') as stream:
        yaml.safe_dump(profile, stream, sort_keys=False, allow_unicode=True)
    return {'path': str(path), 'profile': profile, 'commit_required': True}


def project_context(git, artifacts, cwd, revision):
    cwd = git._git('rev-parse', '--show-toplevel', cwd=cwd)
    raw = git._git('ls-tree', '-rz', revision, '--', '.harness', cwd=cwd, strip=False)
    inventory = {entry.split('\t', 1)[1]: entry.split(' ', 1)[0]
                 for entry in raw.split('\0') if '\t' in entry}
    if PROFILE not in inventory and not any(p.startswith(SKILLS) for p in inventory):
        return [], {'status': 'not_configured', 'count': 0}
    if PROFILE in inventory:
        require(inventory[PROFILE] in {'100644', '100755'}, 'Profile must be a regular Git file')
    text = git._git('show', revision + ':' + PROFILE, cwd=cwd, strip=False) if PROFILE in inventory else None
    profile = parse_profile(text) if text is not None else normalize_profile({})
    selection = select_skill_paths(profile, [p[len(SKILLS):] for p in inventory if p.startswith(SKILLS)])
    items, records = [], []
    for relative in selection:
        path = SKILLS + relative
        require(inventory[path] in {'100644', '100755'}, 'Skill must be a regular Git file')
        body = git._git('show', revision + ':' + path, cwd=cwd, strip=False)
        require(len(body.encode('utf-8')) <= 1024 * 1024, 'Skill exceeds input size limit')
        stored = artifacts.put(body, f'git:{revision}:{path}')
        records.append({'path': path, 'content_ref': stored['ref'], 'revision': revision})
        items.append(ContextItem('project-skill:' + path, body, stored['ref'], revision, 5))
    manifest = artifacts.put(canonical({'profile': profile, 'revision': revision, 'skills': records}),
                             'project-skill-selection')
    return items, {'status': 'configured' if text is not None else 'common_only',
                   'count': len(items), 'manifest_ref': manifest['ref']}
