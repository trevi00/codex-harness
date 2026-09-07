"""Route eligible skills using prompt relevance and immutable project evidence."""
import re
from pathlib import PurePosixPath

from codex_harness.adapters.runtime_thresholds import effective_policy
from codex_harness.domain.model import ContextItem, canonical, digest, require
from codex_harness.domain.skill_ranking import (
    FULL_BODY_TOP_K,
    MAX_CONTEXT_CHARS,
    MAX_POINTERS,
    PER_BODY_CAP,
    apply_token_budget,
    extract_paths_from_prompt,
    fit_top_skill,
    score_skill,
)


def frontmatter(text):
    text = text.lstrip('\ufeff').replace('\r\n', '\n')
    if not text.startswith('---\n'):
        return None, text
    parts = re.split(r'\n---(?:\n|$)', text, maxsplit=1)
    require(len(parts) == 2, 'Malformed skill frontmatter fence')
    meta = {}
    for line in parts[0][4:].splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            require(key.strip() not in meta, 'Duplicate skill frontmatter key')
            meta[key.strip()] = value.strip()
    return meta, parts[1].strip()


def route_skills(git, artifacts, cwd, revision, objective, items, records):
    threshold_policy = effective_policy()
    min_full_score = threshold_policy['values']['skill_match.FULL_BODY_MIN_SCORE']
    prompt = objective.lower()
    mentioned = extract_paths_from_prompt(objective)
    raw = git._git('ls-tree', '-rz', revision, cwd=cwd, strip=False)
    inventory = {entry.split('\t', 1)[1]: entry.split(' ', 1)[0]
                 for entry in raw.split('\0') if '\t' in entry}
    evidence, evidence_refs = {}, {}
    # INV-SKILL-001: no absolute paths, untracked files or links can trigger host reads.
    for path in sorted(mentioned)[:64]:
        normalized = path.replace('\\', '/')
        if (PurePosixPath(normalized).is_absolute() or re.match(r'^[A-Za-z]:', normalized)
                or '..' in PurePosixPath(normalized).parts):
            continue
        normalized = PurePosixPath(normalized).as_posix()
        if inventory.get(normalized) not in {'100644', '100755'}:
            continue
        size = int(git._git('cat-file', '-s', revision + ':' + normalized, cwd=cwd))
        if size > 1024 * 1024:
            continue
        head = git._git('show', revision + ':' + normalized, cwd=cwd, strip=False)[:3000]
        evidence[path] = head
        evidence_refs[path] = artifacts.put(head, f'git:{revision}:{normalized}:head')['ref']
    bodies, ranked, legacy = {}, [], []
    by_path = {record['path']: record for record in records}
    for item in items:
        path = item.id.removeprefix('project-skill:')
        record = by_path[path]
        meta, body = frontmatter(item.body)
        if meta is None:
            record.update(tier='legacy', reason='Existing explicit project skill without matcher metadata')
            legacy.append(item)
            continue
        match, base, dims = score_skill(meta, prompt, sorted(mentioned), evidence.copy())
        boost = record['pipeline_boost']
        if boost:
            dims = [*dims, *(record.get('pipeline_dimensions') or ['pipeline:unknown'])]
        score = base + boost
        # INV-SKILL-HISTORY-001: preserve pre-budget Unicode character length;
        # rendered/truncated lengths cannot replay the upstream budget guard.
        record.update(base_score=base, score=score, dimensions=dims, body_chars=len(body),
                      description=meta.get('description', '')[:120],
                      tier='unmatched', metadata=meta)
        if match or boost:
            ranked.append((score, path, dims, body))
        bodies[path] = body
    ranked.sort(key=lambda row: (-row[0], row[1]))
    full = [row for row in ranked if by_path[row[1]]['base_score'] >= min_full_score][:FULL_BODY_TOP_K]
    capped = []
    truncated = False
    for score, path, dims, body in full:
        reduced, cut = fit_top_skill(body, PER_BODY_CAP)
        capped.append((score, path, dims, reduced))
        truncated = truncated or cut
    fitted, budget_cut = apply_token_budget(capped, MAX_CONTEXT_CHARS)
    truncated = truncated or budget_cut
    output, full_paths = list(legacy), set()
    for score, path, dims, body in fitted:
        full_paths.add(path)
        record = by_path[path]
        record.update(tier='full', rendered_characters=len(body), truncated=body != bodies[path])
        output.append(ContextItem('project-skill:' + path, body, record['content_ref'], revision, 18))
    pointers = [row for row in ranked if row[1] not in full_paths]
    for index, (_, path, _, _) in enumerate(pointers):
        record = by_path[path]
        record['tier'] = 'pointer' if index < MAX_POINTERS else 'external_pointer'
        if index < MAX_POINTERS:
            body = canonical({k: record[k] for k in ('path', 'description', 'score', 'file', 'content_ref')})
            output.append(ContextItem('project-skill:' + path, body, record['content_ref'], revision, 14))
    return output, {'objective_hash': digest(objective), 'pattern_evidence': evidence_refs,
                    'matched': len(ranked), 'full': len(full_paths),
                    'pointers': min(len(pointers), MAX_POINTERS),
                    'external_pointers': max(0, len(pointers) - MAX_POINTERS),
                    'legacy': len(legacy), 'truncated': truncated,
                    'threshold_definition': threshold_policy,
                    'policy': {'min_full_score': min_full_score, 'top_k': FULL_BODY_TOP_K,
                               'body_characters': MAX_CONTEXT_CHARS, 'per_body': PER_BODY_CAP}}
