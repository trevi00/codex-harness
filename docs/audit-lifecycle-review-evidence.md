# Audit lifecycle rework evidence

## Scope and provenance

Workspace base: `3ca50480f90c34e7ef3268b7245c44d489031b95`.
Restored lifecycle implementation: `032af73213e6482d164d24f80333b86cc83a4a4f`
(tree `4107b6b660c904328bdee06d96863dfec0c4175b`). The unrelated Guardian
reference review document from that candidate was not adopted. No upstream repository
was reviewed or executed during this rework.

Rejection evidence: `sha256:68fe4329f22324ea5204be1d5fb82021782c5a2045c06fbef34845b0b67adb7e`.
The supplied evidence was read from the task artifact; historical execution claims
are not independently repeated results from this workspace.

## Rollback containment (INV-RESEARCH-004)

`Releases.rollback()` restores the predecessor deployment while retaining the removed
release ID in the pause record. Previously, `reconcile_audits()` compared that removed
ID with the restored deployment ID and reactivated an audit-enabled predecessor.
The scheduler invokes reconciliation before checking activation, so its next pass
could queue work after rollback.

Reconciliation now treats a persisted pause as authoritative, including historical
records without a restored release ID. New rollback records also identify the
restored deployment. A new verified promotion explicitly replaces the pause.
All updates remain within the existing Store transaction; domain/application code
continues to use inner contracts and the standard library.

`test_rollback_between_audit_releases_keeps_dispatch_paused` covers both new and
historical pause shapes, repeated scheduler/reconciliation calls, retained audit
and dispatch records, and resumption through a later verified promotion.
Existing lifecycle tests cover approval invalidation, authorization, stale checkpoint
writes, continuation deduplication, context-budget continuation, blocked inspections,
and atomic promotion failure. These use fixtures, not actual independent reviewers.

## Verification limits

No independent review, actual Codex file-task canary, production deployment, or SLO
measurement was performed. PostgreSQL/Redis integration and Windows execution are
not verified by historical receipts. Full repository semantic coverage is not claimed.
Namespace-denial tests inject a failure and verify evidence retention; they do not
establish a host cause or repair. Actual required inspections that cannot execute
must remain inspection-blocked; no privileges or sandbox settings were changed.

## Executed local checks

Executed in this workspace on 2026-09-07, Linux / Python 3.13.15:

| Command | Exit | Result / log in `verification/` |
|---|---:|---|
| `uv run pytest tests/test_research_audits.py -k rollback_between_audit_releases` (before fix) | 1 | 2 failed; next schedule call queued 4 tasks. `audit-rollback-before.txt` |
| Same command after fix | 0 | 2 passed, 41 deselected. `audit-rollback-after.txt` |
| `uv run ruff check .` | 0 | All checks passed. `audit-ruff.txt` |
| `uv run pytest` (final code/tests) | 0 | 200 passed, 23 skipped. `audit-pytest.txt` |
| `uv run harness --help` | 0 | CLI startup only. `audit-cli-help.txt` |
| `git diff --check` | 0 | No whitespace errors. `audit-diff-check.txt` |

The final suite additionally parameterizes the existing positive lifecycle test for
both audit-disabled and audit-enabled predecessors, retaining nonempty evidence and
approval records through rollback. The 23 skipped tests require PostgreSQL/Redis
with `HARNESS_INTEGRATION=1`; that mode was not enabled. These checks do not resolve
service integration or production verification uncertainty.

`verification/audit-rework-sha256.txt` hashes changed implementation, configuration,
tests, documentation, and command logs (excluding the hash manifest itself).
Verify from the workspace root with `sha256sum -c docs/verification/audit-rework-sha256.txt`.
Changes are left in the workspace for independent review; nothing was pushed,
merged, or deployed.
