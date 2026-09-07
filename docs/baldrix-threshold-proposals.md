# Threshold proposal calculation

Pinned source: Baldrix `b9586c59c062457a45018e41c2e753934b5ca6c9`,
`scripts/lib/calibration/threshold_registry.py` and `threshold_proposer.py`.
The domain module preserves five registry records, all twelve locked names,
the sole wired reference metric pair, 70/30 temporal split, minimum sample floor,
0.02 training hysteresis, single-step candidates and holdout-gate ranking.
Unwired entries remain declared and inert, as upstream. Locked overlap fails at
runtime without relying on Python assertions or dynamic metric imports.

Adaptations: timestamps are normalized to UTC; unknown dates stay in training.
The caller supplies effective current values and a Git revision, rather than
implicitly proposing from the source registry default after a policy change.
Allowed direction is relative to that current value. Proposal identities bind
policy revision, current/proposed values, corpus digest, registry-entry digest,
minimum sample count and holdout boundary. Empty or invalid required policy
values fail explicitly. Pure-domain input validation does not prove that the
supplied revision exists or that its policy equals those values: the Git adapter
and staging application must establish that binding.

This increment provides calculation only. It does not emit the upstream ready
file, write PostgreSQL proposals, expose a CLI or activate policy. The existing
reference metric's limits remain: recorded top matches and raw body sizes are
not exact native-router replay. `reference_accepted` therefore never implies
`activation_ready`. Remaining migration includes authoritative Git policy loading,
immutable full-corpus artifacts, transactional staging, stale-basis rejection,
orchestrator review, actual CLI canary gates, activation and rollback. Do not
interpret this as completion of the upstream proposer/apply subsystem.

Existing follow-ups in `baldrix-threshold-replay.md`, including cross-version
observation identity and import integration coverage, remain open.
