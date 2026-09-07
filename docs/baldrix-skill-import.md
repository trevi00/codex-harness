# Historical skill telemetry import

Source format: trevi00/baldrix at b9586c59c062457a45018e41c2e753934b5ca6c9,
`scripts/lib/telemetry_log.py`, `scripts/lib/telemetry_read.py`, and
`scripts/handlers/prompt/skill_match.py`. The original writer records UTC `ts`,
top-five name/score/dims/body_chars and other invocation metadata. It rotates a
1-MiB segment to `.jsonl.1`. It provides no globally unique event ID or skill-content
version. This import is a migration adapter for that format, not an upstream feature.

```powershell
uv run python scripts/import_skill_telemetry.py copied-skill-match.jsonl --project-id YOUR-UUID --source-id old-machine-segment-001 --dry-run
uv run python scripts/import_skill_telemetry.py copied-skill-match.jsonl --project-id YOUR-UUID --source-id old-machine-segment-001 --artifacts .runtime/artifacts
uv run python scripts/skill_telemetry_audit.py --project-id YOUR-UUID --legacy-source old-machine-segment-001 --json --since 7d
```

The caller explicitly selects a file and stable source ID. A source ID denotes one
append-only physical log segment, not a rotating pathname. Reuse it for a renamed
copy or a longer snapshot of that segment; choose a new ID after log rotation. An
already-consumed prefix that differs, or a shorter snapshot, is rejected. Source IDs
do not deduplicate across segments: original identical same-second records can be
distinct real invocations. Cross-segment deduplication cannot be inferred from hashes.

Exact raw bytes (including invalid UTF-8) are retained in an immutable base64 artifact.
Its canonical digest is verified against input before PostgreSQL writes. A transaction
stores the prefix hash, byte/line cursor, cumulative counters, last 4000 projected events
and source ref. Replays and concurrent identical deliveries make no cursor/data change.
Event IDs are segment/line identifiers inside the project scope, not globally unique IDs.
The current snapshot covers every committed prefix; previous source artifacts remain
available. Projection never rewrites the input file or drops raw evidence.
Identical snapshots reuse their content-addressed artifact. Growing snapshots currently
store a full base64 copy each time: importing every small append can cost quadratic total
archive bytes in segment length. Prefer importing completed copied segments. Incremental
chunk archives and retention are follow-up work; this CLI is not a continuous tailer.

Parsing is bounded to an 8-MiB snapshot and 64-KiB lines. Larger archives require explicit
segmentation with unique IDs; no automatic truncation is accepted. Only LF-terminated
lines advance the cursor (CRLF is supported). An unterminated final line remains pending,
even if it happens to parse as JSON, until a later snapshot completes it. Malformed,
oversized, non-finite, unrepresentable Unicode/NUL and excessively nested JSON records
are counted and skipped in projection, with up to 20 issue examples per invocation.
Projected scores must be non-negative 32-bit signed integers; larger values stay in
the raw archive and are counted as invalid entries rather than overflowing median
calculations. This is an explicit import boundary, not a claim about an upstream cap.
Names are capped at 512 UTF-8 bytes; at most 128 dimensions, each at most 512 bytes,
are projected per entry. Oversized entries are counted and remain in the raw archive.
The total original prefix remains bounded by the 8-MiB segment limit across appends.
The immutable source keeps every skipped byte. Valid empty top lists remain invocations;
wholly invalid top lists do not become empty successful observations. Partially valid
top lists retain valid entries and count invalid ones.

String timestamps are preserved verbatim. Missing/non-string timestamps become unknown;
the raw source retains the original value. Import time is separate state metadata, never
substituted for the historical event time. Unknown dates follow the passive audit's
documented time-filter behavior. Dimensions and valid body sizes are retained; no basic
score, skill version or omitted metadata is invented. Other source fields remain in the
raw artifact. Duplicate display names remain duplicate top entries as in upstream;
name collisions cannot be resolved retrospectively.
An initial snapshot with invalid lines and no valid skill events fails without claiming
a database cursor, so a wrong-category input can be corrected. Empty/blank or wholly
pending snapshots are allowed. CLI contract errors include their actionable reason.
Replies distinguish `source_ref` (the committed snapshot) from `input_ref` (the exact
file inspected this call); a pending-only change does not replace the committed ref.
State retains both `created_at` and last-advance `at`, separate from source event times.

Imported records live in `legacy_skill_imports`, scoped by project plus source ID. Their
identity is explicitly `legacy-name:*` / `legacy-version-unknown:*`. The audit can inspect
them via `--legacy-source`; ordinary live history and live advisory statistics are not
modified or evicted. There is no automatic assertion that an old name refers to the
current skill bytes. Binding historical names to verified source/content versions needs
a separate evidence-backed mapping contract. `--dry-run` parses only, writes nothing,
and does not validate an existing database cursor. Actual import uses the existing global
PostgreSQL transaction lock; source artifact writes happen before the transaction and
may leave a retained artifact when a conflicting prefix is rejected.
The CLI adapter persists the artifact before calling the application use case; direct
application callers must honor that port contract. The use case verifies the receipt's
digest, not filesystem availability. Audit echoes the stored ref; reading the artifact
through FileArtifacts performs its integrity check. If the parser version changes, the
old archive stays readable but cannot advance; use a new source ID (for example a parser
generation suffix) to re-import under the new projection. Do not aggregate both copies as
independent observations. Text reports explicitly identify legacy/unknown-version data.

This does not import the user's original logs automatically. It does not implement the
remaining calibration proposal/holdout/approval pipeline, all other Baldrix telemetry,
full Baldrix adoption, or OMC/Ouroboros migration. Registry and metrics sources already
identify the next requirement: preserve body sizes and never tune locked invariants.
