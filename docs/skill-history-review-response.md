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

## Regression fixed and remaining work

Executor no longer evaluates the Git repository identity when there is no routed
manifest. This restores the no-profile execution path exercised by the existing
recovery and cleanup tests; it does not substitute a fake identity for a real project.

Project identity based only on a local path remains insufficient across hosts and
container checkouts. The upstream best-effort advisory behavior, port boundaries,
artifact handle construction, and direct annotation budget coverage remain open.
The full migration and review must not be declared complete from these fixes.
