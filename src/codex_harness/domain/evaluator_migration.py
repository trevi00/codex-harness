"""INV-RELEASE-001: migration is an explicit, independently reviewed policy."""
import json
from importlib.resources import files

from codex_harness.domain.model import digest, require


def validate_policy(candidate, policy):
    migration = policy.get('migration')
    if migration is None:
        require('evaluator_revision' not in policy, 'Evaluator override requires migration')
        return
    require(type(migration.get('version')) is int and migration['version'] == 1,
            'Unsupported evaluator migration')
    require(policy['revision'] == candidate['base'] == migration['source_base'],
            'Migration source base mismatch')
    require(policy.get('evaluator_revision') == migration['evaluator_revision'],
            'Migration evaluator mismatch')
    manifest = json.loads(files('codex_harness.resources').joinpath('evaluator-migration.v1.json').read_text())
    require(migration['manifest_digest'] == digest(manifest)
            and migration['source_base'] == manifest['source_base']
            and migration['evaluator_revision'] == manifest['evaluator_revision'],
            'Unrecognized evaluator migration contract')
    require(migration['controller_revision'], 'Migration controller binding missing')
    require(migration['controller_revision'] == candidate['revision'],
            'Migration controller must be the independently reviewed combined candidate')
    require({'tests', 'cli_start', 'cli_file_task'} <= set(policy['checks']),
            'Migration requires full suites and actual CLI canaries')
    require(len(policy['checks']) == len(set(policy['checks'])), 'Duplicate checks')


def approval_binding(record):
    return {'policy_hash': record['policy_hash'], 'candidate_digest': digest(record['candidate']),
            'manifest_digest': record['policy']['migration']['manifest_digest'],
            'controller_revision': record['policy']['migration']['controller_revision']}


def validate_approvals(record, organization):
    validate_policy(record['candidate'], record['policy'])
    if 'migration' not in record['policy']:
        return
    require(record['policy_hash'] == digest(record['policy']), 'Migration policy changed')
    require(record['id'] == digest({'candidate': record['candidate'], 'policy': record['policy']}),
            'Migration release identity changed')
    author = organization.actor(record['candidate']['author'], 'worker')
    expected = approval_binding(record)
    for actor in (author.parent, 'conductor'):
        reviews = [r for r in record['reviews'] if r['actor'] == actor]
        require(len(reviews) == 1, 'Migration approvals missing or duplicated')
        review = reviews[0]
        require(review['accepted'] is True and review['revision'] == record['candidate']['revision']
                and review.get('evidence') and review.get('migration_approval') == expected,
                'Explicit current migration approval required')
