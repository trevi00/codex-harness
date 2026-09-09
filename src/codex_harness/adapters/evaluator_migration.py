"""Byte and AST proof for the narrowly scoped retention evaluator transition."""
import ast
import hashlib
import json
import subprocess
from importlib.resources import files

from codex_harness.domain.model import digest, require

SOURCE_BASE = '445fbc8859e896b90e974ed69447ce58e3446251'
EVALUATOR = '4055d2d0b2a21908abc803f243c97953d928d994'
PRESERVED = '87b1b36244e4371f53318b8d813ea8d42a2372a8'
FILE = 'tests/test_reference_kinds.py'
ALLOWED = {
    'test_clipped_diagnostic_json_excludes_only_complete_typed_image_tokens': 1,
    'test_partial_docker_word_needs_complete_local_identity_and_output_context': 2,
    'test_clipped_identity_tokens_bind_only_to_complete_declarations_in_same_artifact': 2,
}


FIXTURES = {
    'tests/test_workflow.py': (
        "'accepted': True, 'inspection_blocked': blocked,",
        "'accepted': True, 'inspection_blocked': blocked, 'command_inspection_succeeded': not blocked,"),
    'tests/test_git_workspace.py': (
        "return {'accepted': True, 'reason': 'unit fixture', 'execution_ref': 'fixture:review'}",
        "return {'accepted': True, 'reason': 'unit fixture', 'execution_ref': 'fixture:review',\n                'command_inspection_succeeded': True}"),
    'tests/test_model_routing.py': (
        "'execution_ref': 'sha256:review'})",
        "'execution_ref': 'sha256:review', 'command_inspection_succeeded': True})"),
}


def prove_fixture(path, old, new):
    left, right = (value.encode() for value in FIXTURES[path])
    prefix, sep, suffix = old.rpartition(left)
    require(bool(sep) and prefix + right + suffix == new, 'Unrelated review fixture edit')
    before = [ast.dump(n) for n in ast.walk(ast.parse(old)) if isinstance(n, ast.Assert)]
    after = [ast.dump(n) for n in ast.walk(ast.parse(new)) if isinstance(n, ast.Assert)]
    require(before == after, 'Review fixture assertions changed')
    return {'file': path, 'source_sha256': hashlib.sha256(old).hexdigest(),
            'evaluator_sha256': hashlib.sha256(new).hexdigest(),
            'change': 'Add successful command inspection to existing accepted-review fixture; assertions unchanged'}


def git_bytes(repository, *args):
    result = subprocess.run(['git', *args], cwd=repository, capture_output=True, check=False)
    require(result.returncode == 0, 'Git inspection failed: ' + result.stderr.decode(errors='replace'))
    return result.stdout


def prove_delta(old, new):
    before, after = ast.parse(old), ast.parse(new)
    changes = []
    require(len(before.body) == len(after.body), 'Evaluator structure changed')
    for left, right in zip(before.body, after.body):
        if ast.dump(left) == ast.dump(right):
            continue
        require(isinstance(left, ast.FunctionDef) and left.name in ALLOWED
                and isinstance(right, ast.FunctionDef) and left.name == right.name,
                'Unrelated evaluator edit')
        assertions = [n for n in ast.walk(left) if isinstance(n, ast.Assert)]
        replacements = [n for n in ast.walk(right) if isinstance(n, ast.Assert)]
        require(len(assertions) == len(replacements), 'Assertion count changed')
        count = 0
        for a, b in zip(assertions, replacements):
            if ast.dump(a) == ast.dump(b):
                continue
            require(isinstance(a.test, ast.Compare) and isinstance(b.test, ast.Compare)
                    and len(a.test.comparators) == len(b.test.comparators) == 1,
                    'Only expected expressions may change')
            original, updated = a.test.comparators[0], b.test.comparators[0]
            require((ast.unparse(original), ast.unparse(updated)) in
                    {('{EVIDENCE}', '{IMAGE, EVIDENCE}'), ('set()', '{IMAGE}')},
                    'Unexpected expected-set delta')
            changes.append({'test': left.name, 'line': original.lineno,
                            'old': ast.unparse(original), 'new': ast.unparse(updated)})
            a.test.comparators[0] = updated
            require(ast.dump(a) == ast.dump(b), 'Other assertion bytes changed')
            count += 1
        require(count == ALLOWED[left.name] and ast.dump(left) == ast.dump(right),
                'Other function behavior changed')
    require(len(changes) == 5 and ast.dump(before) == ast.dump(after), 'Incomplete delta')
    # Source equality after replacing only the five AST spans catches comments/format edits too.
    lines = old.decode().splitlines(keepends=True)
    for change in reversed(changes):
        line = change['line'] - 1
        require(lines[line].rstrip().endswith(change['old']), 'Unexpected assertion source')
        end = lines[line].rfind(change['old'])
        lines[line] = lines[line][:end] + change['new'] + lines[line][end + len(change['old']):]
    require(''.join(lines).encode() == new, 'Unrelated source bytes changed')
    return changes


def inspect_manifest(repository):
    def read(*args):
        return git_bytes(repository, *args)
    require(read('rev-list', '--parents', '-n', '1', EVALUATOR).decode().split()
            == [EVALUATOR, SOURCE_BASE], 'Evaluator parent changed')
    require(read('diff', '--name-only', SOURCE_BASE, EVALUATOR).decode().splitlines() == sorted([FILE, *FIXTURES]),
            'Unrelated evaluator paths changed')
    old, new = (read('show', revision + ':' + FILE) for revision in (SOURCE_BASE, EVALUATOR))
    return {'version': 1, 'source_base': SOURCE_BASE, 'evaluator_revision': EVALUATOR,
            'preserved_candidate': PRESERVED,
            'review_fixtures': [prove_fixture(path, read('show', SOURCE_BASE + ':' + path),
                                             read('show', EVALUATOR + ':' + path))
                               for path in FIXTURES],
            'source_tree': read('rev-parse', SOURCE_BASE + '^{tree}').decode().strip(),
            'evaluator_tree': read('rev-parse', EVALUATOR + '^{tree}').decode().strip(),
            'file': FILE, 'source_blob': read('rev-parse', SOURCE_BASE + ':' + FILE).decode().strip(),
            'evaluator_blob': read('rev-parse', EVALUATOR + ':' + FILE).decode().strip(),
            'source_sha256': hashlib.sha256(old).hexdigest(),
            'evaluator_sha256': hashlib.sha256(new).hexdigest(), 'delta': prove_delta(old, new),
            'rationale': 'INV-RESOURCE-001: ambiguous clipped tokens remain artifact edges; '
                         'unrelated records cannot establish token provenance.'}


def validate_manifest(repository, policy, candidate):
    manifest = json.loads(files('codex_harness.resources').joinpath('evaluator-migration.v1.json').read_text())
    require(inspect_manifest(repository) == manifest, 'Evaluator manifest proof mismatch')
    migration = policy['migration']
    require(migration['manifest_digest'] == digest(manifest)
            and migration['source_base'] == SOURCE_BASE
            and migration['evaluator_revision'] == EVALUATOR, 'Forged evaluator manifest')
    require(git_bytes(repository, 'merge-base', PRESERVED, candidate['revision']).decode().strip()
            == PRESERVED, 'Prior final candidate must be preserved')
    return manifest


def validate_controller(policy):
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    revision = policy['migration']['controller_revision']
    require(git_bytes(root, 'rev-parse', 'HEAD').decode().strip() == revision,
            'Loaded controller revision mismatch')
    require(not git_bytes(root, 'status', '--porcelain', '--untracked-files=all'),
            'Loaded controller must be clean')
    tracked = git_bytes(root, 'ls-tree', '-r', '--name-only', revision, 'src').decode().splitlines()
    for name in tracked:
        require((root / name).read_bytes() == git_bytes(root, 'show', revision + ':' + name),
                'Loaded controller source mismatch: ' + name)
    return revision


def propose_migration(releases, git, candidate):
    """Explicit operator use case; never called from candidate capture or generic review."""
    manifest = inspect_manifest(git.repository)
    policy = {'revision': SOURCE_BASE, 'evaluator_revision': EVALUATOR,
              'checks': ['tests', 'cli_start', 'cli_file_task'],
              'migration': {'version': 1, 'source_base': SOURCE_BASE,
                            'evaluator_revision': EVALUATOR, 'manifest_digest': digest(manifest),
                            'controller_revision': candidate['revision']}}
    if candidate.get('hook_id'):
        policy['checks'] += ['hook_reproduction', 'hook_normal_case']
    validate_manifest(git.repository, policy, candidate)
    inspected = git.inspect(candidate['revision'], SOURCE_BASE)
    require(inspected['tree'] == candidate['tree'], 'Candidate tree mismatch')
    record = releases.propose(candidate, policy)
    releases.request_migration_reviews(record['id'])
    return record
