# Native threshold definition and shared resolution

Source pin: Baldrix `b9586c59c062457a45018e41c2e753934b5ca6c9`.
Inspected complete `scripts/lib/threshold_policy.py`, `scripts/cli/threshold_override.py`
and `scripts/tests/test_threshold_tuning.py`, plus repository-wide call-site search.
The only native consumer of this source resolver is
`scripts/handlers/prompt/skill_match.py:61-62`. Breaker `resolve_thresholds` is a
different subsystem and is not covered here. Source tests were read, not executed
in this increment; prior reference proposer replay receipts cover earlier arithmetic.

Source resolution reads a tiny numeric YAML mapping from Claude home. Unknown names
fall back to the supplied default. Apply rechecks locked names, returns no-op before
token checks, compares direction against the registry default, and requires a
name-only readiness file for risky changes. It writes YAML non-atomically, attempts
to consume the readiness file, and appends best-effort JSONL history. Readiness does
not bind a particular value, corpus, Git revision or deployment; numeric coercion
also admits non-finite floats. These are implementation limitations, not native
authorization requirements. The operator CLI is explicitly separate from the agent.

The native adaptation stores `resources/threshold-policy.json` in Git and packages
it with the candidate image. `runtime_thresholds.effective_policy` is shared by
actual skill routing and the Git-bound proposal collector. The router captures one
resolved definition per call and records its values and text hash in routing evidence.
The collector includes both resolver source and definition in its source binding
(22 fixed files). Defaults are the existing ranking constants; the shipped override
mapping is empty. A candidate commit may change the mapping, and the existing image
release/rollback machinery determines which definition is deployed.

Only the currently implemented native consumer is configurable. Four other source
registry entries remain declared but cannot silently pretend to affect nonexistent
native consumers. Malformed, duplicate-key, non-finite, boolean, locked and unsupported
definitions fail explicitly. Unlike the source's silent fallback, an invalid packaged
definition must be fixed before candidate verification succeeds. No separate mutable
host override or ready-file/token bypass is introduced. Numeric finite values are
preserved without an invented range constraint; task-outcome assessment remains needed
to justify any particular value.

Subprocess tests copy the package into isolated Git repositories, commit overrides of
2 and 4, and prove that the actual router changes full-body admission while collection
archives the same effective value. Tests do not substitute the resolver or router.
Default routing tests cover unchanged behavior. This is live-consumer plumbing, not
automatic application: approved investigation-to-implementation dispatch, native
performance evidence, migration of the operator apply experience/history, remaining
consumers and source adoption rollout remain required.
