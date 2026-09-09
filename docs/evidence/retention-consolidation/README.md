# Retention and review retry consolidation

Task: `a56a0afd-03ec-4c23-bdb7-511bdf812073`.
Base: `e68d5e157465b4b03193ee3feeb3a776473b8d40`.
Restored candidate: `34da547aa6d8fc162ac9890cc5cd40d6a3d138b3`.

Inputs:

- Assignment: `sha256:aa04edcf1bb07255e4de91d19fe86d596d258c4970d9ff40234aeb478593eb94`.
- Finding: `sha256:a70e91eebdfdff896cf4eed8f559fd737c2bb796fc7233dd7360726a0bcedcd5`.
- Supplied patch: `sha256:0d2ecc73cebec4be644633a022fc7f03cbf083316af200d08c3aff91875d276a`.
- Prior rejected review: `sha256:f83af829cfbdef93c0bc5f75901d453dedf9c0211450910115cf27536dc7098b`
  (carried from the finding; not independently accepted or re-reviewed).

The patch was read with the bounded artifact reader and its exact bytes verified
against the supplied SHA-256. JSON indexing rejected this text artifact as
`Artifact is not valid JSON`; raw paging succeeded. Initial Git application failed
with `error: corrupt patch at line 462`: the artifact lacks its terminal newline.
Appending a newline to the in-memory application input succeeded. Original bytes
were not modified. An initial control command using system Python failed with
`ModuleNotFoundError: No module named 'codex_harness'`; rerunning through `uv run`
used the project environment successfully.

All previous candidate changes are preserved, including original runner bytes,
AST parsing/tests, compact measurement replay, root decoding outside database
serialization, strict Docker inspection, fixture cleanup and historical failures.
The historical evidence directories are unchanged from the prior candidate.
`validation.json` records preservation and hashes of current implementation,
tests, evidence and logs. `controls.py` executes Git-pinned rejected decoders in
memory; the resulting controls reproduce duplicate keys, unknown Docker inspection
options, truncated duplicate keys and the literal Python runner issue. These are
local negative controls, not independent recurrence, accepted audits or reviews.

Retention now unions semantic dependencies with existing conservatively extracted
handles for runtime roots, transitive artifact bodies, uncommitted bodies and final
transactional root checks. Artifact and record tombstone fencing use that same
conservative extraction. Missing metadata classification remains separate. ASCII
escapes are decoded conservatively; ambiguous prefixes/suffixes cannot remove an
existing blob. A file-index cache is never mixed into decoded measurement results.
This intentionally permits over-retention. The supplied patch was further adapted
to sample the existing file index under the publication lock alongside generation;
otherwise a completed publication between indexing and generation could be missed.
Dry-run and apply regression fixtures cover that race without production deletion.

Source review retries use decision generation in their native Git checkout path.
The test deliberately dirties the first checkout, verifies failure and preservation,
then verifies that the next generation receives a clean independent checkout.
This simulated reviewer is a unit fixture, not a successful independent source review.
Reviewers MUST keep the checkout clean and write logs, scripts and all other scratch
evidence to system temporary directories OUTSIDE the source checkout. Preserve
failed checkouts. Required command inspection must succeed; bubblewrap namespace
creation denial is inspection-blocked, not acceptance. Do not change sandbox
permissions, host sysctls or container privileges to bypass inspection failure.

Qualification is incomplete. Full pytest skips service integrations unless enabled;
`environment.json` records the environment without connection secrets.
`postgres-readonly.json` records only a read-only connectivity/control observation,
not contention or production throughput qualification. Existing root-lock tests,
measurement replay and cache tests validate local behavior; no fresh PostgreSQL
contention/performance integration suite or production reduction percentage is
claimed. No local PostgreSQL/Docker server executable is available. No production
artifact files or runtime records were modified.

Collection must stay paused. Before resumption or promotion require a full current
production dry run, verified host/container writer convergence, independent lead
and conductor source reviews with successful inspection, fresh incumbent AND
candidate integration suites, and actual successful exact-candidate CLI canaries
(INV-RESOURCE-001, INV-RELEASE-001). This work does not complete those gates.
Supplied deployment truth is `6fec51db27e23ac73ea7984a93bee2cd1572ec28`;
repository base is `e68d5e157465b4b03193ee3feeb3a776473b8d40`. This candidate is
not deployed. Nothing was pushed, merged or promoted. Historical rejections and
the entire unreviewed migration scope remain outstanding; neither this bounded
change nor historical inventories establish a full repository/migration audit.
