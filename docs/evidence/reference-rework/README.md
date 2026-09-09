# Reference decoder rework evidence

Task: `c496e620-d2bf-48ab-bf47-5d02a3413c6a`.
Base: `e68d5e157465b4b03193ee3feeb3a776473b8d40`.
Restored candidate: `5dc00f184a6bfff450d4fd090aa1bff13e1e036f`.
Assignment evidence: `sha256:caed2f9507b90e691c87aadb4a8adfe74569914822934b436909f615a07d0b0d`.

The ten-path candidate delta was restored from Git into the assigned workspace.
The reference decoder and regression tests were then repaired. Measurement
projection still includes every field consumed by the current evaluators; its
replay and lease-expiry tests execute with the focused suite. Initial root decoding
remains outside database serialization, with transactional final root rechecks.
ArtifactStore.retain and shared write fencing were already present in the base.

Both reported defects reproduced with the rejected decoder: the new collection
regressions each removed two artifacts where only the orphan should be removed.
`negative-control.json` binds that decoder's SHA-256 and the failed command output.
This control swaps only the decoder, not the whole checkout. The negative control
is an expected failed execution, not a successful audit or independent recurrence.
The fixed tests require the rooted parent and its child to survive, the orphan to
be removed, and stale record publication to roll back under a tombstone.

Duplicate-key preflight preserves key/value pairs and decoded escaped scalars
before typed exclusions. It covers multiple JSON structures in one output string.
Its bounded exhaustion retains raw references; unchanged unescaping terminates.
Docker inspection operands and stdout use the same complete command validation.
Unknown options and ambiguous or incomplete option values keep retention edges.

Final focused command:
`uv run pytest tests/test_reference_kinds.py tests/test_maintenance.py tests/test_measurements.py --runxfail -q`
returned 132 passed (command evidence `bfad76`). `validation.json` records final
required checks (Ruff passed; pytest 678 passed / 34 skipped; diff check passed)
and SHA-256 hashes of tested Python files and command logs.
`intermediate-validation.json` preserves an earlier failed full suite: the added
preflight initially repeated unchanged unescaping and retained a BuildKit identity.
That compatibility regression was repaired before final validation. These are
worker checks, not independent approvals or actual release canaries.

Inspection was scoped to the restored delta, shared store fencing, ArtifactStore
contract, metric evaluators and INV-RESOURCE-001 / INV-RELEASE-001. This is not a
full repository or reference-repository audit. No external runtime records were
queried or modified. No production inventory, missing-reference recovery,
PostgreSQL responsiveness measurement, policy binding, independent review or
actual Codex/Docker release canary was performed. Service integrations skipped
by the suite remain unverified. Historical production receipts and the reported
96.3% reduction remain supplied evidence rather than fresh measurements here.

Collection must remain paused. Release still requires graph recovery, successful
independent command inspections and approvals, fresh incumbent and candidate
integration suites, and actual successful exact-candidate canaries. Nothing was
pushed, merged or deployed; local fixture collection authorizes no production
artifact deletion.
