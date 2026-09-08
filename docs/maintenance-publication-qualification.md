# Maintenance publication snapshot qualification

Candidate builds on f6d63130ec2685ca22da5e3e718d9cbf8ae9f6ab.

INV-RESOURCE-001: sample the filesystem generation under the publication lock,
outside database serialization. If a publisher owns the lock, defer the scan
without waiting; `deferred_scope=scan` distinguishes this from counted files.
File traversal remains outside database serialization. Existing generation checks,
tombstones and record reference validation remain required.

Evidence from 2026-09-08:
- New concurrent-publication regression fails against f6d6313 and passes here.
- Actual Linux maintenance tests: 21 passed with --runxfail, including symlinks.
- Actual disposable PostgreSQL: 5 passed. Incumbent traversal caused 10-second
  claim/heartbeat timeouts; candidate operations took approximately 5-9 ms.
  1,000 records / 100 deletions: maximum deletion transaction 0.032 seconds.
- Linux full suite in an isolated native Git repository: 574 passed, 32 skipped.
- Ruff passed.
- Windows full suite: 566 passed, 34 skipped, one failure due to symlink privilege.
- Initial Linux runner failures were caused by Windows worktree Git paths and a
  global GIT_DIR contaminating fixture repositories. Native temporary Git checkout
  fixes the runner, without excluding tests.

These checks are not an independent review, actual CLI release canary or deployed
release. Re-run qualification for the final reviewed revision before promotion.
The five PostgreSQL tests require HARNESS_INTEGRATION=1 and an isolated database;
never point them at a production database.
