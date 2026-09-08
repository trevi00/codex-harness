# Budget accounting and emission dependency review

Source pin: `b9586c59c062457a45018e41c2e753934b5ca6c9`.
Six additional files were read completely: `scripts/lib/atomic_json.py`,
`scripts/lib/paths.py`, `scripts/lib/telemetry_log.py`,
`scripts/lib/event_taxonomy.py`, `scripts/lib/event_store.py`, and
`scripts/handlers/post_tool/agent_outcome_audit.py`.
The outcome hook's other validator, breaker and ledger dependencies remain outside
this transitive review. Search-derived caller discovery is not exhaustive dynamic resolution.

The source chain is Agent PostToolUse -> outcome main -> record budget -> atomic
JSON write -> check cap -> taxonomy emit -> raw event emit -> event store.
Raw emit imports a module-level `append` that does not exist. The existing
`EventStore.append` also has a different signature and needs a session-bound instance.
An import/name substitution alone cannot repair this contract.

Ten isolated characterization probes completed successfully, including a normal
accumulation/delivery control. **Passing here means the reported defects reproduced,
not that they were fixed.** Observed defects include:

- Missing event-store function is swallowed, yet the budget marks emission complete.
  A direct hook subprocess with stdin JSON confirms persisted usage and no budget event.
- Injected delivery failure returns True and suppresses the next retry.
- Injected atomic-write failure returns an increment that was never persisted.
- Two synchronized writers lose one increment; emitter bookkeeping can separately
  overwrite usage recorded between its read and write.
- Distinct session IDs `a/b` and `ab` share accounting.
- An in-process environment change redirects the dynamic path helper but not budget's
  imported constant. Separate hook processes with environment set before import mitigate
  this isolation hazard; this is not evidence of production path misdirection.

Fault injection is explicit in the probe source. The upstream files were not modified;
mounted source bytes were compared to pinned Git blobs. Network was disabled, source and
root mounts were read-only, credentials absent and scratch bounded. Run from the harness
root using its Python environment:

```text
python <audit-checkout>/docs/audits/probes/run_baldrix_budget_probe.py
```

The runner expects the existing pinned bare source under `.runtime/audit-sources`.
It retains its own source, the probe, bound upstream sources and actual execution output.
Final ten-probe receipt:
`sha256:d20091114dcf1a471ef21c2d7d33ca807cbec8bc79e44841f3a659358cda0177`.
Refreshed source/caller analysis:
`sha256:657d4cefaef1d5ab7a59e1512bf35d9651a3f6ed1eeb08511398f341ec3b7eaf`.
Independent Claude review accepted the earlier eight-probe scoped analysis and identified
the separate emitter race and missing main-path test; both now have reproductions.
Review output: `sha256:6305f4547c6e904a80a6b89830e4b32e65db78f408fef6fd835ec7924af2e458`.
That review does not certify the later probes or approve a production adaptation.

Adaptation proposal: keep raw usage units explicit, bind accounting to task/session
generation and unique execution receipts, commit usage plus event intent atomically in
PostgreSQL, and acknowledge delivery only after successful transport. The current
`PostgresStore.transaction` and `Harness.flush_outbox` are available primitives;
this review does not implement budget integration or prove an exactly-once transport.
The outbox currently publishes inside the global transaction, so bounded transport
behavior must be considered before reusing it for high-volume metering.

Native CLI registration/canary, full settings and install path, all other outcome
branches, license/adoption decisions, and destination/release mapping remain open.
