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
lexicographically; unknown dates remain in the trailing partition. Boolean/nonfinite
scores and boolean sizes are excluded. New native observations preserve Unicode
body character counts before rendering or truncation. Missing historical sizes are
not invented. Size enrichment does not change observation identity or overwrite a
previously recorded event on retry (INV-SKILL-HISTORY-001).

Tests cover numerical rejection and acceptance, missing sizes, temporal boundaries,
immutable replay evidence, no database mutation, producer sizing before truncation,
and propagation through Executor into persisted observations. Executor unit tests
use a substituted runtime and are not actual Codex CLI canary evidence.
