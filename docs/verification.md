# Bootstrap verification — 2026-09-07

- `python scripts/check.py --integration`: ruff passed; **22 tests passed**.
- Real PostgreSQL: concurrent incident transactions create one hook/outbox record, state survives reconnect, stale checkpoints rejected.
- Real Redis Streams: an incident committed before consumer crash is redelivered without double counting; lead notification reaches conductor.
- Real pgvector: injected test vectors stored and searched with model identity filtering. No production embedding quality claim.
- Tree-sitter: code/contract-reference relationships queried; failed parsing preserves the previous index.
- `harness demo`: scripted fixture produces a reviewed/canary-checked active executable-alias hook.
- `harness run-command -- codex.ps1 --version`: prepared `codex.cmd --version`, exit 0, `codex-cli 0.153.4`.
- `harness canary --live` on Windows host: real Codex CLI read input, wrote output, returned validated JSON; passed (9 JSONL events).
- `docker compose exec -T conductor harness canary`: container CLI startup passed, version 0.153.4. Container model authentication was not configured/tested.
- `uv run python scripts/smoke_bus.py`: two incident messages handled by improvement-lead; exactly one required hook; conductor received it as `awaiting_handler`.
- Stopped conductor, published a fixture message, ran `scripts/supervise.py --once`: conductor restarted and consumed the message.
- Latest local code index at verification: 151 nodes / 127 edges. Reindex after source changes.
- Running: postgres, redis, conductor, research-lead, improvement-lead. Measured aggregate idle container memory ~155 MiB (excludes Docker/WSL overhead and live Codex work).

These results establish the bootstrap behavior only. Automated GitHub PR reviews, candidate deployment,
full runtime session rotation, source-wide knowledge retrieval and ongoing research remain in docs/status.md.
