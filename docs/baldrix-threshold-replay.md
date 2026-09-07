# Baldrix threshold reference replay

Source: Baldrix `b9586c59c062457a45018e41c2e753934b5ca6c9`,
`scripts/lib/calibration/threshold_metrics.py` and numeric threshold evaluation
in `scripts/lib/no_degradation_gate.py`. This migrates their diagnostic calculation;
threshold registry, proposal generation, activation and rollback remain separate work.

`scripts/replay_skill_threshold.py --project-id UUID --old-value 3 --proposed-value 4
--holdout-boundary 2026-02-01T00:00:00Z` reads PostgreSQL observations and writes an
immutable artifact containing the exact bounded corpus, its digest, options and report.
Use `--legacy-source SEGMENT` to read an isolated historical import instead.
The command does not modify runtime records or Git policy.

The source target metric counts scores strictly above the threshold among scores
at or above it. An empty eligible set yields 1.0. The guard sums raw character
lengths for the highest three eligible recorded matches and checks a 4000 character
budget. A positive target delta on holdout and nonnegative guard delta on the whole
corpus pass the reference calculation. Each temporal partition requires ten events
by default. Missing all body sizes yields a non-finite guard and rejection.

This calculation is not approval to change native routing: total scores differ from
base-score admission, raw sizes omit per-body reduction and the final UTF-8 context
compiler, and only recorded top matches are available. Partially missing sizes are
skipped by the source guard; report coverage must be inspected even when it accepts.
The replay remains advisory until the remaining proposal and release controls exist.

Adaptations: timestamps are parsed as timezone-aware instants rather than compared
lexicographically; source `ts` is mapped to native `at`, and unknown dates remain in
the trailing partition. Minimum sample counts must be positive. Boolean/nonfinite
scores and boolean sizes are excluded. New native observations preserve Unicode
body character counts before rendering or truncation. Missing historical sizes are
not invented. Size enrichment does not change observation identity or overwrite a
previously recorded event on retry (INV-SKILL-HISTORY-001).

Tests cover numerical rejection and acceptance, missing sizes, temporal boundaries,
immutable replay evidence, no database mutation, producer sizing before truncation,
and propagation through Executor into persisted observations. Executor unit tests
use a substituted runtime and are not actual Codex CLI canary evidence.

Validation at runtime revision `2c7e3586919d1f933968ca18e44b71e907331e49`:

- Ruff passed. Windows PostgreSQL/Redis suite: 441 passed, 7 skipped;
  `sha256:0fd2fa56ab1af4a918ecb7a0dff7361d1f2ee5fbc267c7976da0a309075211e5`.
- Linux PostgreSQL/Redis suite: 448 passed, no skips;
  `sha256:f85a3e4cc73da253afc9682d4f06ca138f097fbe289856d45f55f75f42233fbb`.
- Actual Codex CLI file canary passed with all 88 source/config/lock files matched
  to the immutable image; binding and result:
  `sha256:65e2e55c8554f361eb09fdd96e8cf60e3e0eee28cc62d5734b92911d020f646f`.
- Actual PostgreSQL CLI accepted the sized synthetic corpus, rejected its unsized
  counterpart, preserved exact replay artifacts and left both scoped histories
  unchanged. A seeded 500-corpus comparison executed both original metric functions
  (1,000 comparisons) with equal results on finite ordinary inputs:
  `sha256:d983764c569715c74833d19e54b73168bc7cf5b5fc1aa118cc476d8d4e776fde`.

Next source trace: `scripts/lib/calibration/threshold_registry.py` declares five
entries; only `skill_match.FULL_BODY_MIN_SCORE` has metric/guard wiring upstream.
Its twelve locked invariant names must remain excluded from tuning. The proposer
in `scripts/lib/calibration/threshold_proposer.py` uses a 70/30 temporal partition,
minimum ten events per partition, improvement greater than 0.02 and a single step
in either allowed direction. It chooses among candidates accepted by the holdout
gate and emits a separate ready flag. These source files were read, but their
registry/proposer behavior is not yet migrated or tested here. Their activation
caller and validators still require complete tracing before implementation.

Claude review of that revision accepted the component:
`sha256:72c71aea4a965226737ad0f24abb7a9fad8096aece70e83cde33f819bb7d820a`.
Follow-up adds the guard's usable/skipped/partially-sized event counts and makes
downward-threshold undercount bias explicit. The suggested oversized-body failure
was checked against `adapters/project_skills.py`: the caller already rejects skill
inputs above 1 MiB UTF-8 before routing, so its body character count cannot exceed
the observation bound. Unchecked lease ownership still fails closed intentionally.
The diagnostic read currently uses the shared transactional lock; lock-free reads
remain future infrastructure work. Malformed runtime documents fail with a structured
unavailable error rather than being silently interpreted as empty evidence.
