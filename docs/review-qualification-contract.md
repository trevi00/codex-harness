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

## Rollback containment

The host monitor now compares the current and rollback target's exact Git source
for artifact publication, record-reference extraction, database writes, and RLM
retention. Once tombstones exist, differing or unavailable writer source blocks
automatic rollback and produces a retained evidence reference in health status.
This deliberately conservative check can reject compatible but changed writers;
such changes need a separately qualified recovery path.

Git inspection runs outside database serialization. The final tombstone check
and rollback are fenced by the artifact publication lock. The collector's
nonblocking lock acquisition avoids a lock-order deadlock. Any rollback attempt
pauses collection durably, and each deletion batch rechecks that pause. This also
prevents a collector that started earlier from deleting after a legacy rollback.
Collection is resumed only after reviewed writer convergence is verified.

The previous prequalification receipt recorded the active release's historical
evaluator hash (`3c5f47...`) under `incumbent_policy_hash`. This candidate's actual
base is `0548efaf1bc8833c750c80b242de03b5a73d7799`; its policy is exactly
`{"checks":["tests","cli_start","cli_file_task"],"revision":"0548efaf1bc8833c750c80b242de03b5a73d7799"}`,
with canonical SHA-256 `79f04f6245a9bdba0a7350dba13618598287b2d8e0ddb92c3b4ae051dda6dc27`.
Correction receipt: `sha256:92fe4fe03ce2e14715ae86469f62392b9bce2919399462f5e546c2821c5d9082`.
The old receipt and rejection are retained; fresh qualification must record this
candidate-base policy and its bytes explicitly.
