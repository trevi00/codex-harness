# Guardian source review

Repository: trevi00/harness-guardian. Commit: `8d13d3b4b26dcac9eca2a9e414966a1247ebf39d`.
Reviewer: root recovery session, 2026-09-07. This is a source review and isolated test result,
not independent conductor approval, a production rollout, or a full cross-repository conformance claim.

All 11 tracked files were read. The immutable inventory is
`sha256:d0ccfc9b562bae61cb9f808dc73437d42a949df0e7b95f407075098e6c6551fa`.
All four original smoke scripts exited 0 in an isolated Linux container with no network, read-only
reference mounts, no host credentials, dropped capabilities and a temporary writable directory.
Execution evidence (command, image digest and complete outputs):
`sha256:934ec2db66eb9cf6a231953aeec2fe92e226ab9a908b583424dd99982547118b`.
The restorer smoke also reads the separately pinned harness's paths.yaml and append_restore helper.

## File coverage and execution paths

| Path | Reviewed responsibility and trace |
|---|---|
| `.gitignore` | Excludes machine config, tokens and runtime state; these are outside tracked evidence. |
| `README.md` | Declares external guardian boundary, Windows scheduler installation and safe-mode handling. References sibling harness-design/HARNESS-SPEC.md, which was not available in this audit. |
| `issue_token.py` | CLI issue/revoke/status -> guardian mutation_token.json; token includes expiry and random bytes. No upstream dedicated token test found in the tracked test set. |
| `ledger_seal.py` | seal/verify -> persisted normalized ledger prefix and compacted sidecar hashes; results distinguish tamper, reseal required, unsealed and OK. Called by restorer mark and watchdog. |
| `notifier.py` | alert -> local append and optional webhook; errors are reported to stderr and do not propagate. Fixtures do not configure external delivery. |
| `restorer.py` | mark -> dirty check, execute harness smoke scripts, save known-good SHA, attempt seal; restore -> tracked assets from known-good excluding ledger, remove later additions, append audit event through harness helper. |
| `watchdog.py` | one-shot run -> notification relay and hook probe -> unattended binding -> grace/session/heartbeat/driver/circuit/progress/seal checks -> bounded incident recovery and safe mode -> atomic state replacement. |
| `tests/test_notify_relay_smoke.py` | Executed: delivery while unarmed, watermark deduplication, incremental notifications. |
| `tests/test_recovery_smoke.py` | Executed: seal-triggered restoration, removal of post-baseline files, ledger preservation, restore cap, safe mode, incident reset and missing-known-good failure. |
| `tests/test_restorer_smoke.py` | Executed: reject missing baseline, dirty tree and failed smoke; successful restore, ledger preservation and audit append. |
| `tests/test_watchdog_smoke.py` | Executed: armed/unarmed behavior, stale/missing heartbeat, escalation/reset and progress stall conditions. Linux execution does not verify Windows Task Scheduler/tasklist behavior. |

## Findings and adoption decisions

1. **Adapt: distinguish inactivity from corruption.** Current watchdog restoration requires a seal
   corruption signal. A liveness/progress failure alone does not restore source assets. Preserve this
   distinction in our supervisor: diagnose/continue a stalled task; never discard legitimate work merely
   because a model is quiet. Existing image rollback remains bound to deployment-health evidence.
2. **Adapt: bounded incident recovery.** Restore attempts are capped per incident and reset after healthy
   observation. Map this to durable incident IDs and recovery receipts rather than mutable file counters.
   Our task attempt budget must distinguish failed execution from resumable work and retain its reason.
3. **Adapt: evidence-preserving recovery.** The upstream excludes ledger/ from source restoration.
   Our equivalent is Git/image recovery with PostgreSQL facts and transitive evidence retained. The
   source rebase repair preserves failed attempts and the interrupted worker's actual patch.
4. **Keep our outbox semantics: notification watermark is insufficient.** alert catches webhook errors,
   yet relay advances the watermark. This proves a local attempt, not acknowledged external delivery.
   Define delivery success separately and retain retryable outbox entries. Do not copy this as reliable
   remote-delivery measurement. No webhook delivery was attempted in our tests.
5. **Validate before adopting: clock and missing-observation handling.** Heartbeat and circuit calculations
   accept negative ages from future timestamps. A missing driver marker and several corrupt/missing
   records are ignored; these are not proof of operational health. Our metric gate needs explicit unknown
   and clock-skew handling, backed by negative tests.
6. **Validate before adopting: seal authority and statuses.** The CLI maps UNSEALED to exit 0, while
   watchdog reacts only to TAMPER and suppresses seal exceptions. Do not interpret exit 0 as an intact
   seal without parsing the verdict. Normalization drops blank lines, so hashes prove the normalized
   record stream, not exact file bytes. New sidecars can cause a reseal-required result; provenance of
   compaction must be independently verified before accepting a replacement seal.
7. **Validate before adopting: concurrency and known-good binding.** Atomic file replacement alone
   does not serialize concurrent watchdog invocations; both use the same temporary filename. mark
   checks dirty state before tests but does not bind before/after tree identity across test execution.
   Use PostgreSQL fencing/CAS and exact candidate receipts in our implementation. These are static
   findings; concurrent-run and mutating-test reproductions remain to be added.
8. **Defer upstream expiring operator tokens.** This file-based authorization model is not the user's
   chosen unattended authorization policy. Retain role/lease/promotion authority checks; do not add
   periodic human approval merely because the reference does.

## Remaining verification

The external design document, actual machine config, OS write boundary, Windows scheduler/tasklist,
real webhook delivery, token tests and adversarial seal/concurrency cases are not verified here.
Smoke logs include expected fixture hook-probe failures for absent helper scripts; passing suite exit
codes do not establish a deployed native-hook chain. Full source-file coverage is recorded separately
from these remaining behavioral and external-contract gaps. Independent review is still required.
