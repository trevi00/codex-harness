# Hermes partial source inspection

Pinned source: `https://github.com/witt3rd/oh-my-hermes` at `2a98d38b43010a438b316fb48dbe68a3c8ee8fed`.

Seven of 120 tracked files were read: pyproject.toml, plugin registration, three hooks, evidence_tool.py, and the Ralph skill. State, role, configuration dependencies and test semantics still require tracing; this is not a completed semantic audit.

Original plugin tests ran in a read-only, networkless Docker container: **194 passed, 7 skipped**. The skipped tests require an installed live Hermes agent. Test receipt: `sha256:686be37df17579cb7b82df9bc8c96117f2bd8276d14218a77bdc1850060c7730`. Partial findings: `sha256:2e8269c71869a88548b39df9e6f1ac2ca21d9dc15349d407533168301f75e26b`.

Ralph specifies bounded invocations, persistent feedback, command evidence and separate verifier/architect reviews at the skill level. Runtime enforcement remains unverified. Its three-strike circuit breaker does not implement the user's two-recurrence mandatory-hook policy. The evidence adapter produces exit statuses using shell-free argv execution, but does not itself provide isolation or bind candidate commit, image and immutable evidence; these require harness adapters and gates.

Remaining: 113 paths unread in this pass, dependency/caller tracing, live integration, independent review and adoption validation. No source-derived behavior is approved for adoption by this note.
