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
policy code plus the organization resource (20 fixed files).
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

Unit tests substitute model execution, while using actual Git checkouts and content
artifacts. They cover ordered completion, rejected/blocked lead decisions, wrong
receipt identity, mid-execution record/policy changes and stale generations. Actual
CLI/model and PostgreSQL evidence is distinguished in validation receipts.
