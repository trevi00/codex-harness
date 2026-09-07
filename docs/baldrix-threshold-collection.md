# Git-bound threshold proposal collection

`scripts/propose_skill_threshold.py --github-repo owner/project --harness-repo PATH`
loads the current native threshold definition from a selected harness Git commit
(`--revision`, default HEAD), compares ten fixed policy/calculation/collection source files
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
The archived report states that the target is a score-margin statistic, not admission
quality or task success. All archived evidence must serialize as finite JSON before
any artifact or run write. The pinned sources include timestamp parsing, history
window constants, canonical/digest helpers, and collection/CLI logic. They are not a
whole-process attestation; external libraries and unrelated policy paths are excluded.

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

Verification at runtime revision `c5159d9f56c89ba9f74fa2dbf3a200bb19922eba`:

- Ruff passed. Windows PostgreSQL/Redis suite: 455 passed, 7 skipped;
  `sha256:b7f0d2d4a66e82818651b3bfce8e8cd03dbdb52c23e95303b5b98c2d7ba95aa2`.
- Linux PostgreSQL/Redis suite: 462 passed, no skips;
  `sha256:7276af89768c4a7561abff3c0c4bb892eeadfbf64bc236f293f0a8c528e4effb`.
- Actual Codex CLI file canary passed; all 92 source/config/lock files matched the
  immutable image:
  `sha256:14ef1803a5953295cdae5ded218c24d29d6eeb4a900fa3deca4c0a895793761d`.
- Actual proposal CLI subprocesses against PostgreSQL verified eight concurrent
  identical deliveries converge, plus empty-admission blockers and import provenance.
  Exact corpus/policy artifacts matched and scoped source histories stayed unchanged:
  `sha256:16b6f6890ce3ca240774c19652d1ba909b42374808d899a03a5349f3264d8be8`.
  All these observations were synthetic isolated fixtures, not task-success evidence.

Initial actual Claude review ACCEPT:
`sha256:226f060e424bfb9d76949094d05966a10492687922c14632e01e7f4663dbe749`.
Follow-up extends source binding, makes metric limitations visible in evidence and
rejects nonfinite evidence metadata. The source proposer retains its last rejected
candidate when neither candidate passes; the corpus and calculation basis permit
replay, but the other rejected candidate's report is not individually archived yet.
Unknown timestamps remain in training and can count toward that sample floor; their
count is explicit. These source semantics must not be read as native success proof.
