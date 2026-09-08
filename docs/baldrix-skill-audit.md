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
  Reports additionally expose available base-score min/median/max, boosted counts,
  and missing-base-score counts so operators can inspect this distinction directly.
  Pipeline boost dimensions retain `pipeline:<stage>` in observations; the original
  audit classifies that category as `unknown`, and this report preserves that behavior.
- Invalid Boolean/negative scores are skipped explicitly. The original audit accepted
  Boolean scores accidentally; the original prompt adviser excluded them.
- New dimension/time diagnostics do not change replay identity for the same selection.
  Replaying that selection does not add a sample, replace its first timestamp, or enrich
  it retroactively. Base score is an immutable scoring field (already recorded before
  this audit migration); changing or adding it to an existing observation conflicts.
  Changing the routing manifest identifies a new selection, even for the same task.
  Older imported records can omit base scores but cannot silently retrofit them later.
- Global transaction locking and permanent replay-ledger retention remain existing debt.
  Even this read-only report takes the existing global transaction lock while copying
  the project document; aggregation occurs after releasing it. JSON is single-line ASCII-
  escaped output rather than the upstream indented Unicode formatting; values agree.
  This command is a passive audit, not threshold calibration or full Baldrix migration.

Review follow-up: the live adviser and passive audit now share malformed-score and
identity guards; corrupt legacy entries do not discard healthy samples. The actual
producer-to-CLI project test, legacy slug selection, retained-window bound and exact
cutoff boundary are covered. Leased execution still fails closed when ownership cannot
be checked before an observation write. That includes a store connection failure before
the guard runs; this is the existing documented ownership tradeoff, not a promise that
all database outages are advisory. Unleased recording remains best-effort. Passive CLI
reads have no lease and return unavailable on storage errors. No ownership exception was
weakened in response to the review.

Input tightening is intentional: duration must be finite and positive (`0s` and negative
durations are rejected). Invalid non-object event envelopes are excluded and counted
under invalid entries instead of crashing as upstream does. `read_only` means no writes
to observations or definitions; a database read transaction still commits and may lock.
Empty valid-skill reports return an empty message, matching upstream's early return.
JSON structure differs as documented; mapped per-skill values and candidate reasons
were compared against upstream in 400 randomized cases, not asserted byte-identical.

## Candidate validation

Implementation revision: `7b9d9c814631185e3f571ed0fbfba40103943e43`.
These are component checks, not production release or full-repository adoption.

- Windows PostgreSQL/Redis suite: 421 passed, 7 skipped.
  `sha256:db6a1ba340e666d183a243d04a4a48e9341acd98fc8b473f265ba53163d10614`.
- Linux PostgreSQL/Redis suite: 428 passed, no skips.
  `sha256:7039d5a31a3fb3bd9224a3e59904ab89549c84cf49ba653cd3e66a843cd7027e`.
- Actual Codex CLI canary passed; 82 source/config/lock files matched the immutable
  image. `sha256:9a8f9e1dd5d5e8cd201aa2c8bf9d8456c2d770a00efb0fcc5aac6ac00cb5d83e`.
- Actual audit CLI subprocesses against PostgreSQL verified JSON/text, minimum samples,
  exclusion of an explicitly backdated isolated fixture record with `--since`, and no
  history/ledger changes during reads.
  `sha256:12cfb82877d443078b98873b5dc7cbc01d395f7d78adbfa4ea7880e7119da744`.
- Original upstream test script: all 9 passed in a temporary isolated source copy;
  400 seeded pure-function comparisons matched mapped statistics and candidate reasons.
  `sha256:8f81d4b26b363b89377d3b64bf27c29916854ceeecbe66923b7b5a32797e9f45`.
  The local runner is `.runtime/check_skill_audit_parity.py` in the parent development
  workspace; publishing a portable runner in Git remains a reproducibility follow-up.
- Claude complete-source review: ACCEPT.
  `sha256:7df8f1edb9052799b1156cd744f84e03e35caca9587a01676a02156421adca53`.
  Earlier rejected/conditional reviews are retained in immutable artifacts. Remaining
  non-blocking items include separate diagnosis of malformed legacy base scores,
  report-format polish, identity-length bounds and the portable verification runner.

Pending calibration work also requires body-size observations, proposal/holdout metrics,
locked-vs-tunable registries and guarded activation. Current transaction-time timestamps
must not be reused as an import API that invents dates for old events. Historical JSONL
import needs its own provenance-preserving, idempotent contract. Remaining Baldrix and
all OMC/Ouroboros remain in the migration sequence.
