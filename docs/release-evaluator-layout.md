# Incumbent evaluator source layout

The release runner previously loaded candidate code but ran incumbent tests in
an incumbent checkout. File-relative fixtures copied that checkout's old src
into temporary policy repositories, so strict policy provenance checks compared
old source with candidate-loaded source and rejected valid fixture construction.

INV-RELEASE-001: retain incumbent test/config/history bytes in an ephemeral native
checkout, overlay only candidate src, and expose its tests and src through
PYTHONPATH. Neither reviewed checkout is modified. Strict current_policy checks
remain unchanged, including rejection of an actually changed policy definition.

This is an evaluator implementation change. Historical rejected releases must
remain rejected. Deployment requires review of this controller change and a fresh
qualification through the release workflow; passing targeted tests alone is not
release approval.

Validation: Ruff passed; full Windows suite 550 passed / 33 skipped. The original
incumbent native-routing/threshold collection/review tests ran against maintenance
candidate 7cc2bd326c41d0790d5742217e16078f716a7de6 in the corrected evaluator:
39 passed, including the previously failing 32 cases. The layout regression checks
unaltered test bytes, candidate import/file agreement, original checkout preservation
and temporary-directory cleanup.
