# Skill history review follow-up

The initial Claude review rejected revision
`bac4ccb7dee9f68507a44bb056d0fbbf0345483d` (artifact
`sha256:7d2230e859c2eecf492015e98a7a767820d17dc70cafc7befbad76db05fc7a41`).
This is an open review, not approval or deployment evidence.

## Findings checked against implementation

- Accounting: `ContextItem` fields four and five are `revision` and `priority`,
  not body digest and token count. `compile_context` measures the rendered UTF-8
  bytes after annotation, and `ContextPacket.seal` hashes the final rendering.
  Executor's `before_counts` is captured after compilation, so that comparison
  does not compare annotated bodies to their previous unannotated sizes.
  A direct boundary regression test is still needed for the new wrapper.
- Concurrent writes: `PostgresStore.transaction` acquires advisory transaction
  lock 734219 before reading state; distinct events are serialized as well as
  duplicate events. The integration test now checks twelve distinct concurrent
  events after eight duplicate deliveries, including exact retained IDs.
  This global bootstrap lock limits throughput; per-project locking remains a
  later measured optimization, not a missing correctness lock today.
- Replay context: the fingerprint intentionally identifies a compiled selection,
  not every surrounding prompt version. `context_ref` in the ledger is the first
  observation's evidence; subsequent execution contexts remain separate immutable
  artifacts. Replay with a changed selection is rejected. Missing evidence refs
  and malformed observation entries now fail with a contract error before writes.

## Regression fixed and remaining work at 85b785f

Executor no longer evaluates the Git repository identity when there is no routed
manifest. This restores the no-profile execution path exercised by the existing
recovery and cleanup tests; it does not substitute a fake identity for a real project.

Project identity based only on a local path remains insufficient across hosts and
container checkouts. The upstream best-effort advisory behavior, port boundaries,
artifact handle construction, and direct annotation budget coverage remain open.
The full migration and review must not be declared complete from these fixes.

## Subsequent implementation at 1cac973

Recovery now ignores the drifting advisory assessment hash, including when reading
checkpoints from the preceding draft. All authoritative binding fields still match
exactly. The real project-context/Executor regression exercises three weak samples,
a full-body advisory, another task changing the history, and preservation of both
checkpoint and progress on retry. Changing the objective still rejects old recovery.
The compiler boundary test now covers an unannotated item fitting exactly and its
annotated replacement being omitted atomically; final byte counts and seal differ.

Project init writes a portable UUID into Git-owned YAML. Existing profiles can use
the configured GitHub slug; absent either identity, history reports unavailable.
This UUID is a Git definition, not a tenant authorization boundary. Deliberately
copying it to a fork shares history, and intentionally changing it starts a new scope.
`GitWorkspace.remote` here is the configured `HARNESS_GITHUB_REPO` owner/repo slug,
not an origin URL read from the checkout. The validator should still reject dot-only
path segments; that follow-up remains open. A syntactically valid owner/repo string
cannot be distinguished from a relative path without its configuration contract.

Optional preparation and recording failures now expose a bounded unavailable status.
Ownership failures, including failure before the ownership check, propagate. More
detailed operational diagnostics for permanently malformed history data remain open.
Source refs/revisions describe original skill provenance (Git commit, not body hash);
derived advice points to its immutable assessment, and the final packet hash covers
delivered bytes. Knowledge-index revisions use a different hash contract. Unifying
derived-item provenance conventions remains a possible follow-up, not evidence that
the packet seal fails.

Validation of 1cac973 (not a full migration or deployment):

- Windows: 401 passed, 7 skipped;
  `sha256:98f29859636ee255fe61307bb10d3e59c5bd9ef0259a4b68f630a2e6cf2b485f`.
- Linux: 408 passed, no skips;
  `sha256:902c3f8de416407c22ca8ffbab2ffb8d51134bb6e5d849a002dd817009ade252`.
- Immutable image matched 80 Git source/config/lock files; actual CLI canary passed;
  `sha256:2f04a0b0ea19049f45bf3e34d28a68f08e082cd288610415bc2977fecb6f37a6`.
- Four actual isolated Executor/AppServer calls produced no advisory for the first
  three weak matches and an advisory for the fourth full match, with four observations;
  `sha256:c1aba548f72a9a89be219c67dd3c73c4d125ccf56aa71420804d01aaac6beb20`.
- Claude review remains REJECT;
  `sha256:11b920b4ee4042405dffe58550f6bcd9d2c8b51a07229ab64cf9f1a453843366`.
  A follow-up with complete project producer/initialization sources was requested.
