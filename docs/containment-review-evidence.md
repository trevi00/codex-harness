# Namespace inspection containment rework

This change restores the rejected candidate `e33ff99498fc629d0049e34ee7fc7cbc3db290d9`
onto workspace base `83c1414e5ee595bb5956a25ee3603fdd3ed85787`, preserving the newer
execution lease fencing, receipt chaining, context policy and hook rework handling.
The supplied review artifact was read and its SHA-256 verified:
`aff831f5afdc77aee3cb1c1299da70daf3e92353491b86461622d681c3735704`.

The AppServer adapter detects the exact namespace-denial text only in failed,
nonzero command completions for the current thread and turn during read-only
execution. Command IDs are deduplicated; model answers cannot override blockage.
EOF, receive failure and budget expiry retain the observed failure and events.
The executor persists the execution artifact and fenced session checkpoint,
then records terminal `inspection_blocked` without approval, retry, rework,
incident diagnosis, canary or promotion effects. Runtime graph projection includes
decision status, ownership and evidence; PostgreSQL remains authoritative.

The additional cleanup fix escalates an unresponsive subprocess from SIGTERM to
SIGKILL and waits for it to be reaped. If context-manager cleanup still raises an
ordinary exception after `run` returned an inspection-blocked result, the executor
adds its type and message as `cleanup_error` and proceeds with artifact/checkpoint
persistence. It does not swallow exceptions before a result exists, cleanup errors
following normal completion, or artifact/checkpoint/lease failures. Cleanup errors
remain observable, and detection does not repair or identify the historical host
cause. Failure to kill/reap a process can still leave a process alive even though
the review outcome is preserved.

The restored SessionStart hook is advisory. Its offline AppServer replay is not
native failure-hook coverage. No hook has been activated. Hook rollback removes
the reminder from future configurations; adapter containment requires a code-release
rollback. Existing review and release gates are unchanged.

Regression coverage in `tests/test_workflow.py` exercises the actual AppServer loop
and executor decision/persistence path for both review roles, three termination
modes (EOF, receive timeout, budget expiry), and five cleanup modes (normal,
injected timeout, OS error, stream error, and a real POSIX subprocess ignoring
SIGTERM). The local subprocess signals readiness after installing its handler;
only its wait timeout is shortened to 50 ms. Tests check SIGKILL reaping and closed
streams, durable command receipts, artifacts, session checkpoints, retained errors,
no repeated decision claim, and no downstream release/rework/incident effects.
Negative tests preserve propagation of errors without a blocked result.

These are local fixtures using MemoryStore, controlled subprocesses and a SQL
capture connection. They do not establish live Codex containment, PostgreSQL/Redis
integration, Windows process cleanup, GitHub review or production reliability.
The historical namespace-denial cause remains unconfirmed. Nothing was pushed,
merged or deployed; no files outside the assigned workspace were changed.

## Validation

`uv run ruff check .`: passed. `uv run pytest`: **125 passed, 22 skipped**
(Python 3.13.15). Skips require `HARNESS_INTEGRATION=1` and local services.
`git diff --check HEAD`: passed. The full suite includes recurrence deduplication,
stale writes, authorization, context overflow and failed promotion checks.

SHA-256 of principal implementation and regression files:

- `src/codex_harness/adapters/app_server.py`: `341b20fa81b51389e80fcae7d4064a2cfe4a922e987c5586bf789478970ae13a`
- `src/codex_harness/adapters/executor.py`: `a35558a8ced0995a021199f3e04157f6a51731a0adaf4cd87caefd4a473c736d`
- `tests/test_workflow.py`: `df0a67b105acf228fcadb5b3038f22020bf1e40ee297e3abaf97c0be1b3f5ef1`
- `harness_hooks/codex_namespace_guard.py`: `8629a78b8e6c00adb5c737435ba3314ad4bbdbf0b5717ff8d90c3693d4c41d48`
