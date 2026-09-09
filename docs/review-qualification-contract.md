# Review and host qualification boundary

Independent reviewers inspect source, contracts, evidence integrity, and rollback
compatibility. Their acceptance permits host qualification. It does not mark
tests passed, verify a release, or permit promotion without subsequent checks.

Reviewer containers intentionally lack the host Docker interface. Requiring a
reviewer to activate the host controller or execute the post-approval canary
before approving creates a circular dependency. Available host receipts remain
reviewable evidence and must bind exact source, image, and policy identities.
Missing required source inspection or corrupt evidence remains a blocker.

The executor places this boundary in mandatory context for read-only candidate
reviews. Large diffs may be externalized, but this instruction survives context
budgeting and session rotation. The release state machine and canary gates are
unchanged. A regression exercises a large diff, two sessions, a blocked verdict,
and absence of release or queue side effects.

Observed incident: candidate bfef3a243e4ecb410753597f5d56a1dcc0fa82f6
initially reached `blocked` after Docker exited 127 in the review container.
Exact-candidate host qualification subsequently passed 576 incumbent tests,
606 candidate tests, and real CLI startup/file-task canaries. This fixed prompt
boundary prevents treating that container capability gap as a circular
precondition; it does not suppress substantive review findings.
