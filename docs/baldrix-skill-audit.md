# Passive skill telemetry audit

Source: trevi00/baldrix at b9586c59c062457a45018e41c2e753934b5ca6c9,
`scripts/cli/skill_telemetry_audit.py`, `scripts/lib/thin_skill_advisor.py`,
`scripts/lib/telemetry_read.py`, the prompt skill-match producer, and
`scripts/tests/test_skill_telemetry_audit.py`.

The read-only command reports per-content-version match counts, score min/median/max,
thin-match rates, dominant dimensions, overall dimension counts, and false-positive
candidates. The live adviser and report share one domain predicate. Raising
`--min-samples` affects this report only, never prompt-time policy. Candidates are
signals for investigation, not verified error labels or permission to edit metadata.

Example from the repository with the harness environment configured:

```powershell
uv run python scripts/skill_telemetry_audit.py --project-id YOUR-PROJECT-UUID --json --since 7d
uv run python scripts/skill_telemetry_audit.py --github-repo owner/repo --min-samples 5
```

Use the UUID committed in `.harness/tech-stack.yaml` when present. The GitHub slug
selects the legacy configured identity only; it is not an alias for UUID history.
The CLI reads PostgreSQL and does not invoke an LLM, run project commands, initialize
schemas, write observations, modify skills or activate hooks. Empty history exits 0;
invalid arguments exit 2; unavailable storage exits 1 without exposing backend secrets.

Adaptations and limitations:

- Runtime records, not Claude JSONL files, are authoritative. History is bounded to
  the latest 4000 retained observations per project. `--since` filters that window,
  not an unbounded archive. Historical JSONL import is still separate pending work.
- Skills are grouped by full path plus content ref. The same filename in different
  directories and changed content versions do not collapse into one group. JSON
  therefore uses a skill-record list instead of a filename-keyed mapping.
- New observations retain scoring dimensions and transaction-time UTC timestamps.
  Original observations are never backfilled with invented dates or dimensions.
  As upstream does, time filters include unknown timestamps, with an explicit count.
  UTC offsets are honored; naive legacy timestamps are interpreted as UTC, avoiding
  the source's host-local `mktime` interpretation of a `Z` suffix.
- Dimensional counts are occurrences, not weighted score contributions. Tie ordering
  follows first observed category, as in the source Counter. Unknown categories remain
  visible; absent older dimension data does not become zero-confidence evidence.
- Scores are total scores including stage boost, exactly as the pinned upstream
  prompt producer writes `top5` after adding +3. Both upstream and this harness use
  base scores for full-body admission. Thin-history classification is therefore not
  a classifier of all pointer-only matches: base=1 plus boost=3 is recorded as 4,
  non-thin, despite being a pointer. The fixed historical ceiling of 2 is the shared
  source predicate, not a dynamically derived routing threshold. The source's
  `score<=2, never full-body` reason is a one-way implication under current defaults.
- Invalid Boolean/negative scores are skipped explicitly. The original audit accepted
  Boolean scores accidentally; the original prompt adviser excluded them.
- New diagnostic fields do not change replay identity. Retrying an old observation
  does not add a sample, replace its first timestamp, or enrich it retroactively.
- Global transaction locking and permanent replay-ledger retention remain existing debt.
  Even this read-only report takes the existing global transaction lock while copying
  the project document; aggregation occurs after releasing it. JSON is compact ASCII-
  escaped output rather than the upstream indented Unicode formatting; values agree.
  This command is a passive audit, not threshold calibration or full Baldrix migration.
