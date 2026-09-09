# Evaluator migration, receipt proof and evidence admission

This integration combines migration implementation 58cd95d with verified printed
receipt copies 244566f. The proposed evaluator is c9eb4c7, derived from the unchanged
445fbc8 source base. Its five expected-set changes are confined to three existing
test functions. The host independently ran that entire proposed suite against
87b1b3: 711 passed, 40 skipped. This is local validation, not migration approval.
Evidence: `sha256:dc7512784429160b1cdc0af47eb10f0954bd38c1ae98fe5a1197d697cc5cd340`.

Normal host qualification of 87b1b3 preserved three incumbent failures (742 passed,
six skipped), while the candidate suite passed 829 tests with six skips. Actual
Codex start and file-task canaries passed for that candidate. Combined suite receipt:
`sha256:fb3dc1eeaf93dd4022b4fc678bcbc2863b0616096b2d8870caced6f8981648ea`.
These results neither qualify this changed controller nor authorize a new baseline.
Fresh explicit migration reviews and exact-final-controller qualification remain.

Three missing review citations were recovered from their exact original bytes:
two scratch receipts still present in the conductor container, and Git-preserved
negative-control output matching the original command-output hash. Recovery:
`sha256:4ac75627df32646d63be9c29101619594e104121b7ad1ad1540c87ac8cf11e7e`.
No historical verdict or test outcome was changed.

Accepted source reviews now verify cited artifact existence and complete content
integrity in the shared store before an approval or downstream review is created.
A local temporary FileArtifacts handle alone cannot pass. Review guidance separates
local command/output digests from published artifact references. The state-transition
regression proves that an unpublished receipt creates no approval or outbox; exact
publication permits the ordinary retry. Other tests cover corruption, rejection,
and typed image identities. This is an admission check, not a claim that all legacy
transcripts have been normalized or that every historical dependency is resolved.

The full production inventory is still running on 87b1b3. Its snapshot has known
unresolved identifiers and predates these recoveries. GC remains paused, and global
automatic release dispatch is temporarily held for the explicit policy transition.
Research, workers and monitoring remain active. Upstream audit scope is unchanged.

Final local integration validation: 833 passed, 42 skipped in 282.02 seconds;
uv run ruff check . passed. These are local results, not deployment approval.
