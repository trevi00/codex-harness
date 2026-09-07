# Codex harness implementation rules

- This is a new Codex harness. Reference repositories are not implementation roots.
- Domain and application depend only on the standard library and inner contracts.
- Scripts/CLI invoke use cases; do not duplicate domain policy in shell scripts.
- Inter-agent messages use the versioned six-W JSON schema in package resources.
- Git is authoritative for definitions; PostgreSQL is authoritative for runtime records.
- Cite contract IDs in comments where behavior is non-obvious. Contracts live in docs/contracts.md.
- Test recurrence deduplication, stale writes, authorization, context overflow, and promotion failures.
- Never report simulated review/canary as an actual Codex or GitHub production verification.
- Run `uv run ruff check .` and `uv run pytest` after code changes.
- Reference adoption follows `docs/research-standard.md`. README summaries are discovery only.
- Every reference review pins a commit, inventories every tracked path, traces implementations and
  callers against contracts/configuration/tests, and records coverage and unknowns. Inventory is
  not semantic review; an upstream test file is not evidence that the test was executed.
- Never mark a repository fully analyzed while files or subsystems remain unreviewed. Carry forward
  remaining work using immutable evidence references and bounded context, rather than skipping it.
