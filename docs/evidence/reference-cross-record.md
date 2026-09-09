# Cross-record reference isolation

The independently approved candidate 11d79cc lost an unresolved image-field
reference when another complete receipt declared an equal digest as an image.
Six new regressions cover both log orders and raw, JSON-wrapped and escaped logs.
All six fail against the unchanged 11d79cc source, imported from its own checkout.
The operator hold preserves the original reviews and release record in evidence
`sha256:da1b6f6fb2188e07067865042e68f955c10349eb52560d6a0ded6f4fbd0440b5`.

INV-RESOURCE-001 now keeps unresolved image and native-handler occurrences
regardless of equal-valued declarations elsewhere. Complete structured receipts
still receive local typing; reviewed exact occurrence proofs remain available.
Old clipped-token expectations are strengthened, not silently claimed compatible:
value equality is not occurrence provenance. This may conservatively expose more
historical copies. They remain collection blockers until independently proven.

The active deployment is unchanged. Collection remains paused. Prior acceptance,
local tests, and disposable canaries are not production traversal success.
Any incumbent test mismatch must be reported by normal release qualification;
this change introduces no evaluator exception or gate bypass.
