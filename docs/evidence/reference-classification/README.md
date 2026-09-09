# Production reference classification rework

Base: `e68d5e157465b4b03193ee3feeb3a776473b8d40`.
Restored entire candidate: `fbde139d40b868fe55a4d7d2df43be44d79e140c`,
tree `e71f0c9ade6e7e7c63987a2e91b8e3ebec014a8e`.
Prior evidence directories are preserved without rewriting their historical results.

Inputs:
- Plan: `sha256:2bb99f844d2c6b9091341d7cd263129da156e5066da81dae5633487477753076`.
- Finding: `sha256:3d767cbe0c693434c8fc5d2e64ac92f9af00980bd0b4a585ae7948d9cf78c423`.
- Supplied patch: `sha256:9916177da6c65b74a3f70d50abdb999ad7617168224f4b8b00a45daef7b9bc25`.
  Initial `git apply` failed at line 117. Appending the absent final newline and
  applying with `--recount` succeeded. The patch was then adapted to fence ambiguity
  locally rather than retaining every unrelated digest in the log.
- Partial archive: `sha256:6c059ad1d8d8dec7f9ef22557b10a335a437376cdafe4893c43eb2448e11eaf5`.
  `archived-inventory.json` is its decoded base64 payload. It records 16,931 visits,
  44 missing identities, zero observed corrupt bodies and `complete: false`.

`negative-controls.json` records three regressions against the Git-pinned previous
classifier: many JSON openers, unmatched Python delimiters, and a duplicate object
following an independent native hook receipt. All fail the expected result on the
previous classifier and pass on the updated classifier. These are local controls,
not independent review or production canaries.

`inspect_archive.py` rechecks every observed parent using actual artifact bytes,
SHA-256 verification, sidecar validation and the collector dependency function.
`parent-inspection.json` records per-parent outcomes and bounded occurrence context.
This is classifier execution coverage of the archived observations, not semantic
review of every byte or a current production root snapshot. Source strings remain
descriptive metadata, not authenticated command provenance. Synthetic-looking
references remain mandatory unless exact source/command provenance establishes
otherwise; there is no new digest exemption or synthetic-input exclusion.

`environment.json` records a read-only PostgreSQL observation that collection is
paused. No runtime record, artifact, supervisor, collector or container was changed.
No production collection or deployment was attempted. Docker and local PostgreSQL
service binaries are unavailable in this worker environment.

Before promotion (INV-RELEASE-001), independent lead and conductor reviewers must
inspect the exact final candidate successfully. Reviewers must write scratch
artifacts outside their source checkout and preserve failed inspection commands;
namespace denial is inspection-blocked, never an accepted review. Fresh candidate
and incumbent integration qualification and actual successful CLI canaries are
required. Keep collection paused until a complete current production dry run
succeeds and host supervisor, monitor collector and container writers all converge
to the reviewed code. Historical failures and unreviewed migration scope remain
open. This worker does not claim release qualification or production graph closure.

## Validation and namespace inspection

- `uv run ruff check .`: passed (`ruff.log`).
- `uv run pytest`: 724 passed, 34 skipped in 167.08 seconds (`pytest.log`).
  Skips are not release qualification.
- `git diff --check -- src tests`: passed.
- `namespace-contexts.json`: bounded occurrence inspection of all 44 archived
  identities. Observed namespaces include native hook current/trusted hashes,
  OCI receipt and Docker argv identities, BuildKit layer/config/manifest identities,
  package download integrity hashes, and isolated historical test inputs.
- `synthetic-command-candidates.json`: six identities matched to exact completed
  command items, including full command text, item ID, output and output SHA-256.
  Three repeated-character handles are explicit source expressions; the other
  three occur in FileArtifacts instances inside TemporaryDirectory with MemoryStore.
  This establishes that particular command's isolated namespace, not an exemption
  for every occurrence of the same hash. References copied into later summaries
  still need provenance reconciliation. No historical command was re-executed and
  no missing preimage was manufactured. Earlier `child_exists: false` and
  `stale_publication_accepted: true` results remain failed negative controls.

A supplementary whole-file context-extraction command exited 137 (`Killed`) while
pytest and the archive scan were running. This was a failed inspection attempt,
not success; its cause was not established. A subsequent read-only mmap extraction
used bounded slices and succeeded, producing `namespace-contexts.json`. The main
archive dependency scan is separate from this supplementary command.

The first dependency scan was terminated without claiming completion; see
`interrupted-scan.json`. It loaded a pre-final implementation and lacked the
per-scan index/cache. The replacement scan uses final classifier bytes, the same
existing-blob index and bounded cache interface as collection, and checkpoints
each parent outcome. `parent-scan.log` retains progress and completion counts.
No source/command exemption was added based on these observations.

`namespace-dispositions.json` records the observed namespace of every archived
identity with its immutable parent and context. These are occurrence-level
findings, not a hash allowlist. The final source-search regression is covered by
`test_search_result_open_brace_does_not_capture_later_log_objects`: a source-search
line ending in an open brace cannot establish a JSON object-key scope unless an
actual JSON key prefix follows. The intermediate parent scan discovered this
case; its partial results are preserved in `intermediate-parent-inspection.json`
and `intermediate-parent-scan.log`. That scan was explicitly terminated for the
fix and restarted against the final classifier. Final validation is recorded in
`ruff-release-candidate.log` and `pytest-release-candidate.log`; earlier passing
runs apply only to their earlier candidate bytes.

## Recovery and exact tested bytes

The recovered final command completed with 725 passed, 34 skipped in 157.08
seconds and Ruff passed. The command completion is retained at
`sha256:b2cbbae4c4590f4fc39726907199095442079ac12f576a15fb04b6ae58e670d6`;
its logs are `pytest-release-candidate.log` and `ruff-release-candidate.log`.
No implementation changes were made after that run. `tested-source-manifest.json`
records SHA-256 identities of the tested source, tests, project configuration and
lockfile. `final-prior-preservation.json` refreshes the prior-candidate comparison:
42 of 45 prior changed paths are identical; only the classifier, its test module
and the appended semantics document differ. The earlier preservation snapshot is
retained as historical evidence.

Copied runner source and `observed_dependencies` diagnostics can still retain the
runner image identity as a potential reference. Its occurrence in the original
validated runner is source-scoped; that does not authorize exclusions in copied
logs or diagnostics. These unresolved copied occurrences and isolated historical
command references require provenance reconciliation, not a fixed-hash exemption.

The final single-process archive scan was killed by signal 9 after 53 parents.
`signal-killed-scan.json` preserves its `/proc` wait status; the underlying cause
is unknown. `signal-killed-parent-inspection.json` and
`signal-killed-parent-scan.log` preserve its checkpoint and progress. This is a
failed execution, not a successful complete scan. Remaining parents are inspected
one per fresh process using the same classifier, dependency function and
existing-blob index; each process starts with an empty cache.
`remaining-parent-commands.jsonl` records each exit status and output, and
`completed-parent-inspection.json` combines successful checkpointed inspections
with those separate remaining-parent inspections. These bounded runs do not
establish successful single-process production traversal or its memory envelope.
