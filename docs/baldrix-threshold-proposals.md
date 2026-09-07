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

The identity also binds calculation version, reference-model identifier, body
budget, top-k, holdout fraction and hysteresis margin. Any algorithm change outside
these parameters must increment the calculation version. Ties preserve upstream's
raise-first candidate order; the source metric can rate raising and lowering equally
because it measures borderline admission, not task success.

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

Integration trace: native `application/research.py` queues lead/conductor reviews
with six-W envelopes and immutable bindings; `application/releases.py` binds
candidate revision and incumbent policy hash, requires ordered reviews and checks,
and compares the active deployment before promotion. Threshold staging must join
these existing review/release paths rather than treat the source token strings or
readiness file as standalone authorization. These native paths were inspected for
the integration design; threshold proposals are not connected to them yet.

At runtime revision `0b22fe9a941fe543048da1ba8589d33c2be04f80`, an isolated execution
of the unmodified upstream proposer compared 300 seeded corpora and 177 resulting
proposals. Registry fields and all locked names matched; proposal values, training
sizes and gate results matched with current values set to source defaults:
`sha256:c87fe0019ab3fde768d35c8c9480fa84171e9c767f58184ed0c4b034dcb4c860`.
Non-default current values are intentionally adapted and covered by native tests.

Initial actual Claude review ACCEPT:
`sha256:c72526f80c47b0be67772d965910d1f13c2e214a3814a1d466ddcc8d7f84581d`.
Follow-up binds calculation constants, moves metric validation into the registry
validator, normalizes corpus encoding failures and strengthens tests for ties,
hysteresis, lower-safe direction and malformed registry/input.
