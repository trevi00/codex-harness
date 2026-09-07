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

Native routing currently reads `domain/skill_ranking.py:FULL_BODY_MIN_SCORE`
through `adapters/skill_routing.py`; the routed manifest records that effective
value under its routing policy. The future Git policy loader must supply the same
resolution to the live router and proposer. A separate YAML policy used only by
the proposer would not be authoritative and must not be presented as effective
runtime policy. Full-body admission uses base score while reference calibration
uses total score, so native replay and canary checks remain necessary before apply.

Final runtime verification at `53159fdd7044e42451e169fa7117faec07c9314d`:

- Ruff passed. Windows PostgreSQL/Redis: 450 passed, 7 skipped;
  `sha256:7f72a05f703c9b011b480efa239ac76ac676aedf80092c3bb377a5ac0b5e2e36`.
- Linux PostgreSQL/Redis: 457 passed, no skips;
  `sha256:4ab7ed15820af9d5fde6190654df2fc5e664e6c4b0605295290c401d1a08eb6a`.
- Actual Codex CLI canary passed with all 89 source/config/lock files matching the
  immutable image:
  `sha256:81b64cfa6c3e45bcb666c4dd41cbfed1f98b2532f590d3d7433630670999f7a0`.
- Original proposer parity (300 corpora, 177 proposals):
  `sha256:98d88f5bdae0c5d91bec0c86203b0d3aaa35df9040c6b353777f4286676d4222`.
- Actual optimized Python subprocess rejected locked overlap:
  `sha256:10b7e3da6c2cdb1e8fde42851c540b8fd0aa0ea68b16efd0e35161aa988e59d2`.
- Actual Claude follow-up ACCEPT:
  `sha256:7303b4fc01ae5aa88a5d289a40d8943f0383411560ed07f0da32f5d7c012f2f3`.

Pre-activation findings: the reference target returns 1.0 for zero admitted entries,
and the sized-event guard returns 1.0 when no body is selected. Thus raising above all
observed scores can be reference-accepted while selecting no skills. Native staging
must expose admission counts on both partitions and reject loss of useful admission
without independent task-success evidence. Preserve source replay semantics for
auditability; do not promote its numerical verdict as native improvement. Guard
deltas use the full corpus while target deltas use holdout only. The current report
limitations do not yet expose the empty-admission issue directly; add coverage and
its warning to the next report/staging increment.

Other review follow-ups: enforce registry name/qualified pairing, include the registry
check in a future CLI/build validator, use deterministic decimal steps before wiring
fractional entries, and cover unknown-date and lower-safe end-to-end cases. Current
source parity checks exact registry pairs and full pytest already exercises runtime
registry validation. The four unwired entries remain inert. Neither source parity
nor the baseline Codex CLI canary establishes task-success improvement from applying
any proposed threshold.
