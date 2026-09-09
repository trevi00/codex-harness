# Artifact reference classification

Runtime records and artifact bodies share `artifact_references`. Collection keeps
explicit evidence references, dictionary keys, record bucket names and record IDs.
Missing or corrupt evidence continues to defer collection (INV-RESOURCE-001).

Retention and tombstone fencing also use a conservative handle extractor with no
metadata exclusions. Existing referenced blobs remain roots and dependencies even
if semantic classification misses an edge. Initial snapshots and final deletion
batches both apply this rule. Classification only helps distinguish missing
metadata identities; it cannot authorize deleting an existing referenced blob.
The current file index is never cached inside a decoded measurement snapshot.
ASCII-escaped handles in diagnostic strings participate in retention and fencing.
This deliberately permits over-retention rather than evidence loss.

Duplicate object keys are detected lexically as well as through complete JSON
decoding. An unmatched prefix or truncated outer object cannot turn a duplicate
receipt into trusted image metadata. Regression coverage includes those variants,
classifier fault injection, and a metadata-shaped root published after marking.

Known receipt shapes distinguish OCI image identities, native hook identities and
HTTP download integrity checksums from artifact addresses. Unknown command flags,
duplicate JSON keys, malformed download URLs and unrecognized metadata retain
potential references conservatively. Clipped diagnostic output supports only
complete image scalar tokens with a recognized receipt context. The historical
OCI collection diagnostic has a narrowly scoped compatibility decoder.

Qualification tests cover nested receipts, explicit references beside metadata,
malformed input, escaped-input scanning cost and PostgreSQL contention. Test
presence does not establish execution; see the task-specific rework evidence.
Provider output frames are grouped by thread, turn and item identity. Reassembly
uses actual completed output when all deltas match it in order; gaps are covered
only by those completed bytes. Incomplete streams
must not fabricate a reference across a missing chunk. Complete JSON is decoded before
clipped diagnostic fragments. Complete Docker argv arrays, BuildKit progress,
native hook metadata, specification revisions and download tables have separate
identity semantics. Incomplete or unknown shapes remain conservative.

Pinned GitHub source artifacts belong to the upstream repository namespace. Their
code literals do not address the local evidence store. Collection validates the
sidecar's content identity and byte count before applying that classification;
unpinned or unknown sources retain normal reference traversal.

Per-scan task/decision caches use a digest of the complete record, not its mutable
ID. They hold at most 2,048 entries and do not survive a collection call. Changed
record bodies are re-evaluated. All artifact bytes still undergo integrity checks.
Otherwise byte-identical measurement snapshots may share decoding after replacing
only ISO observation timestamps, which cannot contain references. Every other byte
remains part of the cache key. Clipped metadata tokens may bind to complete typed
declarations within the same artifact, while explicit evidence fields remain edges.
Migration claim records distinguish retained evidence from unavailable handles.
Only that complete claim-record shape treats unavailable handles as findings rather
than dependencies; document and retained-evidence references remain mandatory.
This does not make an unavailable claim verified or change migration completeness.
Retained migration Markdown classifies only complete `Image:` declaration lines
as OCI identities, with that rule scoped to validated migration-document sources.
Concurrent collectors may defer an orphan: total removals plus remaining files
must conserve the original inventory, and a subsequent uncontended pass must
drain the remainder.

Operational recovery must copy original bytes and verify their recorded SHA-256.
Do not fabricate missing bodies or turn a failed historical result into a pass.
Classification tests do not establish production graph completeness. Collection
must remain paused until production traversal, independent review and release
qualification succeed; fixture contamination and unregistered evidence require
separate recovery.

PostgreSQL skill-history integration tests clean up their UUID-scoped history and
deduplication records in `finally`, including when assertions fail. Disposable
release services remain the primary isolation boundary. Historical fixture rows
may be quarantined only after exact fixture and ledger matching, with a reversible
backup and a transactional comparison before removal.

Measurement snapshots retain all fields read by the versioned metric evaluators,
including malformed inputs, attempt outcomes and lease timestamps. Prompts, result
logs and unrelated task metadata remain in their authoritative runtime records
and original evidence, rather than being copied into every five-second snapshot.
Each compact snapshot retains its own observation time, definitions and revision;
it can reproduce the calculation independently, including lease expiration.

## Rework of rejected candidate 5dc00f1

The prior duplicate-key check rejected JSON but allowed the same bytes to reach
image-fragment exclusion. A pair-preserving preflight now detects duplicate keys
before any typed exclusion and retains all potential references, including escaped
scalars. It handles headed, nested, multiline and escaped receipts, and retained
references cannot be canceled by another image declaration in the same artifact.
This implements INV-RESOURCE-001 conservative handling of ambiguous input.

Docker inspection operands and identity stdout now share one complete argv parser.
Unknown flags, missing option values, duplicate format options, invalid type values
and non-string arguments prevent identity exclusions. Recognized commands retain
the existing image-identity behavior.

The restored improvement also includes compact measurement snapshots, detached
initial root decoding, bounded content caches and isolated test-fixture cleanup.
No production collection or recovery operation was run for this rework. Collection
must remain paused pending graph recovery and release qualification. Independent
reviews, fresh incumbent/candidate integration suites and successful exact-candidate
CLI canaries remain required by INV-RELEASE-001. Earlier production comparisons and
recovery receipts supplied with the assignment were not independently reverified.

Worker command receipts and limitations: [reference-rework evidence](evidence/reference-rework/README.md).

## Retained Python runner

The validated artifact source kind `baldrix-budget-probe-runner` uses non-executing
Python AST parsing. Only single string tokens in recognized Docker argv image
positions are excluded. Dynamic option values are allowed in known value slots;
dynamic image operands, starred expansions, unknown options and invalid Python
retain potential edges. UTF-8 byte offsets locate operands without deleting
adjacent Unicode text. Concatenated literals remain conservative because comments
can occur within their AST spans. Remaining source is scanned directly, so
comments and explicit evidence equal to the image identity remain edges.
The original runner is retained byte-for-byte as an inert test fixture.

## Exact command-output occurrence provenance

The packaged `occurrence-provenance.v1.json` binds individual decoded UTF-8 output
intervals to immutable parent bytes, completed command/output hashes and stream
identity. Only the listed synthetic test-token intervals are projected. Original
bytes still drive live-edge retention and tombstone fencing; origins stay mandatory.
Annotations are fixed for the process and their hash participates in measurement
cache identity. Runtime metadata cannot supply them. Unknown or invalid bindings
fail closed. Equal identifiers in other occurrences and arbitrary copied summaries
remain dependencies. This bounded candidate leaves seven historical parents with
explicit blockers; see [occurrence evidence](evidence/occurrence-provenance/README.md).
It does not establish full production traversal or authorize resuming collection.
