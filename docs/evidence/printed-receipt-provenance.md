# Printed receipt provenance

The read-only production dry run at candidate 87b1b3 stopped on parent
`sha256:26f4e92f18f03d9eb01b30077a902c3effd02dfbf16284ac940bd7210d00e8d9`.
Two completed commands printed original validation artifacts with 2,500- and
5,500-character clipping. Four image-identity occurrences were left ambiguous.

The new proof pins the parent and nine original sources in the Git-owned catalogue,
checks exact completed command hashes, reconstructs each entire observed output,
and verifies that the full originals do not use the same image value as a mandatory
artifact reference. Only those four output occurrences are projected. Every original
source remains a mandatory graph dependency; the unchanged raw parent still
participates in conservative retention and tombstone fencing.

Source/output/command corruption controls reject unbound copies. No repeated-value
heuristic, arbitrary source-name exemption, fabricated artifact or rewritten
historical outcome is introduced. Existing 30 copy proofs and 22 V1 bindings remain.
The catalogue now contains 34 copy intervals across nine parents.

Local full pytest: 798 passed, 42 skipped on Windows; Ruff passed. The skips are
not claimed executed. This is implementation evidence, not independent approval,
release qualification or complete production traversal. Other parents and the
separate evaluator migration remain unresolved. Collection stays paused.
