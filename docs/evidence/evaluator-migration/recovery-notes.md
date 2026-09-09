# Recovery validation notes

The assignment resumed from progress artifact
`sha256:545939cae49d930259ad786e692d7bd6df21b91eb117782915290066b6b34e64`.
HEAD remains the preserved candidate `87b1b36244e4371f53318b8d813ea8d42a2372a8`;
implementation changes are in this workspace for capture and independent review.
The evaluator migration remains proposed and unapproved.

Recovery added an executor-derived successful command inspection requirement,
rejected stale migration source bases before automatic rebase, and checked release
identity before recording a migration review. Tests exercise command evidence
including model spoofing, missing inspection, stale source base, and existing
approval/manifest/evaluator rejection and positive controls.

The first recovery `uv run pytest` invocation returned exit 1: 821 passed,
36 skipped, one failure at
`tests/test_native_routing_replay.py::test_explicit_new_round_recovers_missing_evidence_without_rewriting_old_run`.
At line 101 the CLI returned 2 instead of 0, with stderr
`{"error": "Invalid or stale proposal input"}`. This paragraph is a transcription
of the command result, not a complete raw log. The unchanged test module then
passed separately (9 passed). Cause is unconfirmed. No test was skipped, edited,
whitelisted or relabeled to resolve that result.

Final `uv run pytest -ra` returned exit 0: 828 passed, 36 skipped, in 124.21s.
The full output is `recovery-pytest.log`. `uv run ruff check .` returned exit 0;
its output is `recovery-ruff.log`. Migration-focused tests passed (29 tests).
Actual isolated `python -I` bootstrap negative controls rejected the wrong
controller revision and dirty checkout before imports/runtime access; exact
argv and errors are in `recovery-bootstrap.json`.

`recovery-environment.json` preserves the exact failed `docker version` probe.
Docker is absent. No actual start/file canary or full isolated-service qualification
was performed, and no independent approval was created. Local test fixtures are
not reviews or canaries. Publication, deployment and runtime approval records were
not changed. GC must remain paused pending complete host traversal and writer
convergence; neither production graph closure nor upstream completeness is claimed.

Historical legacy/proposed evaluator logs and the old decoder negative control
remain unchanged. Final-source evaluator reruns are stored separately under
`recovery-evaluators/`, with argv, exit status, source hashes and output hashes.
These runs are local diagnostics with service integration disabled, not authorized
release checks. The versioned resource independently reconstructs five expected-set
changes in exactly three test functions from the pinned Git objects; no incumbent
test is rewritten in this working tree.
