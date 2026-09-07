# Bootstrap contracts — authoritative definitions

| ID | Contract |
|---|---|
| INV-MESSAGE-001 | Agent messages are six-W JSON. A message ID cannot identify two payloads. DB commit precedes ACK; transport is at-least-once. |
| INV-RECURRENCE-001 | An occurrence ID identifies one independent incident. Two distinct occurrences with confirmed root-cause ID and scope require a hook. Fuzzy text similarity alone does not establish identity. |
| INV-CONTEXT-001 | Required role, goal, acceptance and policy are never silently truncated. Budget overflow rejects composition. UTF-8 byte count is explicitly a conservative estimate, not measured Codex tokens. |
| INV-RELEASE-001 | Hook activation requires author's team lead review, conductor review and a passing canary bound to the exact spec hash and revision. |
| INV-SESSION-001 | Checkpoint generation fences stale session checkpoint writers. 70% triggers handoff at a safe point. Busy executions do not hibernate. |

Comments reference these IDs and explain local reasons; they do not copy alternative policy definitions.
Organization SSOT: `src/codex_harness/resources/organization.json`.
Wire schema SSOT: `src/codex_harness/resources/message.schema.json`.

The bootstrap's caller identities are trusted local process inputs. Schema validation is not authentication.
Redis and PostgreSQL are exposed only on localhost. Host/container authentication and signed authority receipts
must precede use with untrusted producers or unrestricted autonomous agents.

The fixture canary verifies one declarative executable-alias hook and CLI startup. `harness canary --live`
separately verifies a real CLI file task. Neither is a candidate deployment/PR integration test.
