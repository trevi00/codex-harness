"""Operator-authorized qualification, with publication disabled."""
from codex_harness.domain.evaluator_migration import validate_approvals
from codex_harness.domain.model import require


def qualify(runner, release_id, candidate_revision, policy_hash, controller_revision):
    require(runner.git.remote is None and runner.auto_merge is False,
            'Bootstrap qualification must disable publication and promotion')
    with runner.service.store.transaction() as tx:
        release = tx.get('releases', release_id)
    require(release is not None and release['status'] == 'reviewed', 'Fresh reviewed release required')
    require(release['candidate']['revision'] == candidate_revision
            and release['policy_hash'] == policy_hash, 'Bootstrap candidate/policy mismatch')
    validate_approvals(release, runner.service.org)
    require(release['policy'].get('migration', {}).get('controller_revision') == controller_revision,
            'Bootstrap controller is not independently approved')
    return runner.run(release_id)
