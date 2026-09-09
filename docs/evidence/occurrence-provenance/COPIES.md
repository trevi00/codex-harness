# Completion of the seven historical copy parents

This additive candidate starts at `11d79cc69a9c5a29a8a3ee834741033882c55849`.
It preserves the original V1 annotations, malformed-JSON decoder, bounded tool-wait
coverage, original-byte retention and publication fencing. The earlier README
and observations remain historical evidence; `copy-completion.json` records the
new local result. All seven previously blocked parents now have their 25 remaining
occurrences bound. This is implementation evidence pending independent review,
not release approval or production traversal.

| Parent prefix | New ranges | Proof |
| --- | ---: | --- |
| 34387bcb5a12 | 7 | Complete runner-reader output, exact appended test function, completed diagnostic output |
| 52303f1f2231 | 1 | Diagnostic Git blob printed by completed command, linked to original diagnostic receipt |
| 4fe2f35b9494 | 1 | Exact added-file diff from candidate/base/tree and immutable pytest-log blob |
| eb56f9fd8f9b | 4 | Restored/appended/edited test source, tested-file manifest, failed pytest output and completed wrapper receipt |
| 7746a7d29035 | 2 | Exact added-file diff of a source-bound negative control |
| be0a89b15234 | 2 | Completed command printing that exact negative-control blob |
| f83af829cfbd | 8 | Exact separate literal-construction program, complete expected output and same-stream delta |

The original 22 V1 ranges remain separate and unchanged. The four identifier
values are represented as namespace plus hex in the new report and annotations.
No classification depends on the appearance of a repeated-character digest.
Synthetic values are traced to literal expressions in the original commands or
exact tested source. The image value is traced to the runner's parsed Docker
image operand. No synthetic artifact preimage is created.

## Inspectable provenance

`src/codex_harness/resources/occurrence-copies.v1.json` retains nine compressed
originals: the seven parents, the prefix diagnostic execution, and the original
runner. These are exact original bytes authenticated by SHA-256; raw copies are
isolated from the observation report. Required commit/tree/blob objects are
retained as their original Git bytes and authenticated by Git object SHA-1.
The catalogue pins source identities and revisions independently of supplied
resource metadata, preventing a changed receipt from authenticating itself.

The loader derives every annotation again from these originals and requires exact
equality with the packaged annotations. Each entry contains its immutable parent,
RFC 6901 scalar selector and SHA-256, half-open UTF-8 byte range, namespace,
mandatory origin dependencies, completed command item/selector and command/output
hashes, and relevant revision/tree/path/blob-content hashes. Git diff proofs also
bind the base and base tree, prove the file absent at the base, and reproduce its
entire added-file section from the candidate blob. Output deltas require matching
thread, turn, item and unique whole-delta membership in completed output.

The adapter parses archived source as data; it does not execute archived Python
or shell commands. `prepare_copies.py` invokes the adapter's proof derivation and
uses argument arrays for Git. To reproduce the bounded resource from originals:

```sh
uv run python docs/evidence/occurrence-provenance/prepare_copies.py /runtime/artifacts src/codex_harness/resources/occurrence-copies.v1.json
```

This reads only the nine named originals and selected Git paths. It checkpoints
progress; regeneration is never approval. The recovered `copy-draft.checkpoint.json`
is preserved as an earlier preparation checkpoint, not a completed execution.
The resource checkpoint records the successful 25-entry derivation.

## Independent safety and qualification

Only enumerated intervals are projected. Equal-valued unannotated references and
all origin artifacts remain mandatory. Original bytes still drive existing-child
retention and tombstone fencing even if projection is wrong. The composition
rejects overlap with V1; both resource hashes enter the process snapshot/cache
identity. Unknown schema/version, source changes, swapped revisions, forged Git
objects, corrupt selectors, duplicate ranges and stale parents fail closed.
Tests cover the exact original blocker selectors and raw byte positions, arbitrary
copied summaries, an equal-valued explicit handle, corruption and original-byte
retention/fencing. A PostgreSQL regression covers a deliberately incorrect copy
projection plus stale publication, but a skipped service test is not qualification.

Historical pytest failures, negative controls, failed inspections and cancelled
attempts remain unchanged. A completed wrapper with a failed child pytest process
is recorded as such; it is not a successful historical test run. New local check
results are in `copy-validation.json`. No provider review or actual CLI canary is
claimed by these tests.

Collection must remain paused. This workspace has neither inspected nor changed
production pause records. Before release, independently inspect exact code and
all data attestations, incorporate any pending review findings on the base,
qualify incumbent and candidate against integration services, run actual
exact-candidate CLI canaries, complete a current production traversal, and confirm
host supervisor/monitor collector/container writer convergence. Review scratch
belongs outside the checkout; failed command inspection is inspection-blocked,
never approval. No full archive scan, deployment, push, merge, or production
collection was performed. Unreviewed migration scope remains outstanding.
