# Exact occurrence implementation and unresolved scope

This is a candidate implementation, not release approval or a completed historical
reconciliation. Previous candidate `6da57c81856d058a36f67a14d464b74b443390ef`
is preserved, including its complete evidence directory, classifier changes and
regressions. The cherry-pick applied cleanly but could not commit because the
workspace has no committer identity; its changes remain staged for review. No
identity configuration was changed.

## Evidence and bounded inspection

Design artifact: sha256:f3a09a9be31f98be9b9f26867de31dc226c7a5b61773720e704823146df10100.
Input archive: sha256:efc0d90da04bb8f4f9caf8cc0887692e394ce04643a8c2e2e880862fdfb46eaa.
The design is Markdown: the reader's JSON index failed with `Artifact is not
valid JSON`; a bounded raw page succeeded. This was a reader-format failure,
not a provider schema failure. No source bytes were reconstructed or published.

`observations.json` covers exactly the eight parent artifacts and four identifiers
named by `reference-final-known-remaining.json` inside the input archive. Every
parent was SHA-256 verified and smaller than one megabyte. This is not another
58-parent scan, a complete graph traversal, or migration semantic review.
The deterministic `inspect_sources.py` takes an artifact directory, checkpoints
per parent, and prepares draft source annotations plus evidence. It does not
execute historical commands. Run with `PYTHONPATH=src uv run python
 docs/evidence/occurrence-provenance/inspect_sources.py /runtime/artifacts`.
Generated data must receive new independent source review; regeneration is never
an approval. Raw diagnostic extracts are isolated under `raw/` and are never
loaded as classification authority.

The reviewed-resource candidate contains 22 individually enumerated UTF-8 byte
ranges in decoded event strings. They bind three immutable completed command
items and exact output hashes:

| Origin parent prefix | Completed event | Command item | Occurrences |
| --- | --- | --- | --- |
| d4d820258190 | 175 | exec-79b2a53c-14b6-4f32-a434-5e9b99f10f05 | 6 |
| be0a89b15234 | 230 | exec-093a4347-f621-4b8d-a581-f7ef36771e84 | 8 |
| f83af829cfbd | 145 | exec-8226115b-69bc-4522-92cf-6f5ee16d6975 | 8 |

The complete origin refs, command/output SHA-256 hex, expression, event index and
raw-extract hashes are retained in observations. An origin event selector is
`/events/{origin_event}`; target scalars are either
`/events/{target_event}/params/item/aggregatedOutput` or
`/events/{target_event}/params/delta`. Start/end are half-open UTF-8 byte intervals
in that decoded scalar. `output_offset` binds the entire target scalar to the
completed output, and thread, turn and item must agree. Only the individually
listed intervals are masked. No other occurrence of an equal value inherits it.

The commands explicitly construct repeated-character tokens before the temporary
artifact-store experiments. The actual child/parent artifact addresses printed by
those experiments are outside every listed interval and remain dependencies.
Historical `child_exists: false` and `stale_publication_accepted: true` results in
the raw receipts remain failures; no command was rerun to replace them.

## Fail-closed implementation

`occurrence_provenance.py` loads only the packaged, Git-owned resource at process
startup. Runtime records, source sidecars and copied diagnostic summaries cannot
supply or approve annotations. Version is strictly integer 1. Unknown fields,
namespaces, duplicate keys, stale hashes, overlapping ranges, missing selectors,
failed origins, wrong streams and mismatched output copies reject projection.
The resource hash joins measurement cache identity. The process snapshot remains
fixed throughout a collection; changed annotations require fresh processes and
release qualification. Existing publication generation checks are unchanged.

This first version supports only `isolated-test-token` occurrences in completed
command outputs and their bound deltas. It intentionally does not support
arbitrary copied summaries, generic source-expression evaluation, or OCI runner
attestations. Origin artifacts remain mandatory dependencies, including self
edges; this may retain those receipts indefinitely. No raw artifact bytes change.
Both conservative existing-edge retention and tombstone fencing consume ORIGINAL
bytes independently of projection. A deliberately wrong projection still cannot
make a referenced existing child eligible for deletion.

## Explicit blockers

Only the d4d820258190 parent has all occurrences of its assigned identifier bound.
Seven parents still have unresolved selectors, individually recorded with
sanitized counterexamples in `observations.json`:

- 34387bcb5a12: printed runner code. Docker-looking source text is not authenticated
  by a mutable source label; command/source binding remains unproved.
- 52303f1f2231: a later `observed_dependencies` summary does not inherit proof from
  an equal OCI digest.
- 4fe2f35b9494 and eb56f9fd8f9b: copied pytest failure text is not one of the verified
  original commands.
- 7746a7d29035 and be0a89b15234: later diff or diagnostic output needs its own
  content/selector and origin mapping.
- f83af829cfbd: a separate later command emits equal-valued test tokens. The first
  command's verified output does not authorize exclusions from that command.

These are real counterexamples to digest-wide exemptions. They remain edges and
may defer collection. The design's narrow implementation is reviewable, but the
four-kind reconciliation is incomplete. No fabricated preimage or copied-summary
exception was introduced. Prior cancelled, killed and incomplete attempts remain
in the preserved reference-classification evidence. Unreviewed migration scope
has not changed.

## Qualification gates

Collection must remain paused. This workspace did not change production control
records and did not independently confirm their current pause value. A full
current host traversal, host supervisor/monitor/container writer convergence,
fresh incumbent and candidate integration qualification, two independent reviews
of exact code AND data, and actual exact-candidate CLI canaries remain mandatory
under INV-RELEASE-001. No deployment, push, merge or production canary was run.
Reviewers must keep scratch evidence outside the checkout; failed command
inspection is inspection-blocked, never approval. Local test commands and their
results are recorded in validation.json and the adjacent logs. PostgreSQL tests
that skip are not successful integration qualification.
