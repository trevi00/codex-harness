# Leased threshold assessments

`scripts/request_threshold_review.py PROPOSAL_ROW_ID --artifacts PATH` requests an
assessment of a previously calculated record. Use it with a matching deployed
threshold-review-capable controller; mixed controller versions are not supported.
Collection does not automatically submit requests. Request submission is an operator
entry point, with trusted application/storage ports as elsewhere in this harness.

The request validates immutable calculation evidence and identities, captures the
entire row digest, and queues a six-W decision for `lead:improvement`. Executor claims
the usual generation/owner/time-bounded lease. It compares the current Git-bound
policy to archived policy, creates a clean checkout at that revision, and runs a
separate read-only model assessment. Before completion it rechecks current policy,
checkout, artifact integrity, actor/task/input/revision identity and answer consistency.
Interrupted or inspection-blocked execution cannot approve. A changed lease, record
or policy prevents committing the result.

Completion and next-review queueing share one transaction. A lead acceptance queues
`conductor`; rejection/blockage does not. Conductor receives the lead's recorded
assessment but executes independently. Both acceptances yield `assessed` with
`activation_ready: false`; there is no outbox implementation dispatch, release creation,
policy override or deployment mutation. Acceptance means potential value for further
investigation, not authorization to implement or activate. Existing source-adoption
and release checks are not bypassed. The model still evaluates SRE, arc42, actual
versus reference behavior, uncertainty and alternative proposals.

The source registry/proposer/operator boundary remains documented in the preceding
threshold migration notes. Ordered leased assessment is the native replacement for
the human-facing part of source calibration review; implementation/apply authorization,
native performance evaluation and rollback remain separate unfinished work.

The source binding includes review, lease, Git, command, artifact, store and runtime
policy code plus the organization and threshold resources (24 fixed files; see
`baldrix-runtime-thresholds.md` and `native-routing-replay.md` for additions after initial verification).
Older calculated policy snapshots must be recollected before current-policy review.
Terminal requests are idempotent; retrying the request command does not start a new
review round. Changed evidence/policy creates a new calculation/request identity.
Transient execution errors use the existing bounded decision retry policy.
Exhausted decisions mark the request failed rather than leaving it awaiting review.
Terminal failure is not automatically re-queued; a new calculation basis creates a
new request. An explicit operator-controlled repeat-round API remains future work.

Each input bundle also binds the decision generation, so an older attempt's receipt
cannot satisfy a newly claimed execution. Inspection-blocked status comes from the
execution artifact, not a caller-declared flag; a blocked-and-interrupted execution
can record its blockage, while an ordinary interrupted execution cannot complete.
Evidence contains an artifact-root path for bounded reads, so moving that root changes
input/recovery identity and requires fresh execution.

The application also checks the lease's actor and aggregate against the stored
decision, verifies its request/actor-derived identity, requires membership in the
original calculated run, and rejects missing execution verdict fields.

Binding limitations: the enumerated source set does not include all sandbox/context
assembly code or external dependencies; it is not a whole-runtime attestation. The
immutable image canary separately compares all packaged source files. Current-policy
comparison is conservatively tied to the whole Git HEAD, so even an unrelated commit
requires recollection. The post-execution Git check is not atomic with the PostgreSQL
commit; the assessment records a captured basis and never activation authority.
Artifact reads currently occur inside request/input-validation transactions. These
performance and repeat-round limitations remain explicit follow-up work. Conductor
execution is separate but receives the lead assessment; it is not a blind review.

Unit tests substitute model execution, while using actual Git checkouts and content
artifacts. They cover ordered completion, rejected/blocked lead decisions, wrong
receipt identity, mid-execution record/policy changes and stale generations. Actual
CLI/model and PostgreSQL evidence is distinguished in validation receipts.

Validation at runtime revision `049397f2f5f8845b066bc3771c4efd3d00b59594`:
Windows 479 passed / 7 skipped (`sha256:943055235f7b6382e0d45f11621fa3c6750f055b9a350ee3aaf88daa02207c9a`);
Linux 486 passed (`sha256:7edf078d3944c641090071a7d30ae6789f6471f9c2e62ee6aaf5ccb858b71763`).
Actual CLI image canary passed (`sha256:d21b1c39228ff4f9d5315532e2c18963fef64aa46636565cf7c6a108f8b339e3`).
Two actual Codex calls accepted further investigation over a synthetic corpus with
MemoryStore (`sha256:a708a43978af6081edf1850d847ffc0cdce62e84c2869983d45b37043bf43fd3`).
The PostgreSQL test used substituted model execution and isolated bucket prefixes
(`sha256:b51dabe261e76a50f3fb9e47b92e0188515a5b0fddc9cff8f564492d8dd22872`).
Claude returned ACCEPT with follow-up findings
(`sha256:88cf69db4762cd4facd2d9a182442f9e1495dfd2fc9a6a73493ba74ef8e65dc7`).
These receipts describe that revision, not subsequent fixes.

Review follow-up: a post-commit exception cannot downgrade a succeeded decision;
exhaustion only fails the stage awaiting that exact decision. Threshold retries use
generation-specific review clones, preserving prior attempt files and preventing
stale attempts from sharing a checkout. Clone retention remains follow-up work.
The heartbeat finding is conditional: current decision execution is bounded at 300
seconds and the heartbeat lease is 600 seconds; it does not currently expire before
the configured model deadline. Lease duration configuration still deserves a shared
decision policy instead of the initial hard-coded 1200 seconds.
