# Git-bound threshold proposal collection

`scripts/propose_skill_threshold.py --github-repo owner/project --harness-repo PATH`
loads the current native threshold definition from a selected harness Git commit
(`--revision`, default HEAD), compares five fixed policy/calculation source files
with the running package's on-disk source, and records calculated proposals.
All inspected Git files must be regular files. Text comparison normalizes newlines;
each exact normalized source and its hash is archived. No repository code is executed
to load values: the value comes from the imported native constant and the adapter
checks agreement between the router's imported value and its domain definition.
Uncommitted files in the inspected repository do not override the selected commit.
A selected commit whose relevant source differs from the running package is refused.

This is source provenance for the current constant-based policy, not a new override
mechanism. It assumes the ordinary unmodified Python process and its installed source
files; it is not attestation against runtime monkeypatching or hostile package mutation.
The application accepts a trusted policy-provider port. The provided CLI uses the Git
adapter; callers that inject another provider must establish equivalent provenance.

The application snapshots up to 4000 observations, computes outside the database lock,
archives policy sources, exact corpus, source import reference and proposals, then
transactionally records `threshold_proposal_runs` and `threshold_proposals` keyed by
evidence. Concurrent identical calls converge on the same persisted run. Source
histories, deployment pointers and decision queues are unchanged. These records have
status `calculated`, not approved; all have `activation_ready: false` and require native
task-success and release review. Historical imports carry an additional unknown-version
blocker. Empty proposed admission on either temporal partition is explicitly blocked
even if the source reference metric accepts. Source numerical semantics are preserved.

The replay report now exposes per-partition event, admitted-entry and admitted-event
counts for old and proposed thresholds, plus the optimistic empty-admission limitation.
The target score still uses holdout while the guard uses the complete corpus.

Source pin and upstream proposer/policy traces are in `baldrix-threshold-proposals.md`.
The source ready-file side effect is adapted into immutable, project-scoped runtime
calculation records. This does not complete active staging: integration with leased
lead/conductor reviews, current-policy revalidation before apply, shared override
resolution, native admission/task-success verification, release promotion and rollback
remains pending. A historical Git basis may be recorded for inspection, but cannot
authorize applying against a changed current policy.

Tests exercise actual Git reads, regular-file restrictions, source mismatch refusal,
concurrent idempotent collection, unchanged history, explicit empty-admission blocking,
legacy import-to-replay-to-proposal lineage and CLI error containment. Unit collection
tests use MemoryStore; actual PostgreSQL subprocess evidence is recorded separately.
