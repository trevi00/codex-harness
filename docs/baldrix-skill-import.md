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
The current snapshot covers every committed prefix; previous source artifacts remain
available. Projection never rewrites the input file or drops raw evidence.

Parsing is bounded to an 8-MiB snapshot and 64-KiB lines. Larger archives require explicit
segmentation with unique IDs; no automatic truncation is accepted. Only LF-terminated
lines advance the cursor (CRLF is supported). An unterminated final line remains pending,
even if it happens to parse as JSON, until a later snapshot completes it. Malformed,
oversized, non-finite, unrepresentable Unicode/NUL and excessively nested JSON records
are counted and skipped in projection, with up to 20 issue examples per invocation.
Projected scores must be non-negative 32-bit signed integers; larger values stay in
the raw archive and are counted as invalid entries rather than overflowing median
calculations. This is an explicit import boundary, not a claim about an upstream cap.
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

Imported records live in `legacy_skill_imports`, scoped by project plus source ID. Their
identity is explicitly `legacy-name:*` / `legacy-version-unknown:*`. The audit can inspect
them via `--legacy-source`; ordinary live history and live advisory statistics are not
modified or evicted. There is no automatic assertion that an old name refers to the
current skill bytes. Binding historical names to verified source/content versions needs
a separate evidence-backed mapping contract. `--dry-run` parses only, writes nothing,
and does not validate an existing database cursor. Actual import uses the existing global
PostgreSQL transaction lock; source artifact writes happen before the transaction and
may leave a retained artifact when a conflicting prefix is rejected.

This does not import the user's original logs automatically. It does not implement the
remaining calibration proposal/holdout/approval pipeline, all other Baldrix telemetry,
full Baldrix adoption, or OMC/Ouroboros migration. Registry and metrics sources already
identify the next requirement: preserve body sizes and never tune locked invariants.
