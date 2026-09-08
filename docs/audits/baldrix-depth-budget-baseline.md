# Baldrix agent-depth and budget baseline

Pin: `b9586c59c062457a45018e41c2e753934b5ca6c9`. This is a scoped source review,
not full hook-system analysis, adoption approval or proof of live native hook execution.
Four files were read fully: agent_depth.py, agent_depth_guard.py, budget.py and their
test_budget_and_depth.py. Settings and search results were inspected only for this connection.

The original, unchanged test module passed **15 tests** in a networkless, read-only
Docker source mount, with temporary scratch only and no host credentials.

Concrete gaps: the depth helper reads ORCH_DEPTH but neither writes nor propagates an
increment; the configured guard relies on that value and passes malformed/absent inputs.
No production depth-increment writer was established by the repository search. An
inherited environment value alone is not recursive-depth enforcement.

Budget accounting measures characters, is advisory, and uses read-modify-write. Atomic
replacement is not a concurrency proof. Sanitized session identifiers can collide.
Event emission failure is swallowed before the emitted flag is persisted; retry can be
suppressed. Existing tests do not cover that delivery failure, collisions or concurrency.

Direct copying is deferred. A Codex adaptation needs trusted task-parent relationships,
fenced accounting and delivery acknowledgement. Dependencies, installation, live events,
license constraints, independent review and destination/release mapping remain open.

Immutable source blobs, exact test argv/result, reference search and open questions:
sha256:c3408b9b15ac5ae190eec5dfb4fd054fb8861636198f5bfddbaf4e9c00dce2af
