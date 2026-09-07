# Baldrix reverse progress migration

Scope: `scripts/lib/reverse_prd_checkpoint.py`, its original tests, and the checkpoint
protocol in `commands/harness-reverse-prd.md`, pinned at
`b9586c59c062457a45018e41c2e753934b5ca6c9`. This candidate is the durable progress
component of the full migration in migration-sequence.json. It does not implement the
extractor registry, reverse PRD generation, legacy checkpoint import or automatic agent
workflow invocation yet. Those remain required; this component is not a replacement
for the entire reverse feature.

The original command instructs an agent to call the checkpoint module. It is not evidence
that a runtime hook automatically invokes it. Original checkpoint tests invoke it directly.
The source's dirty/unknown handling, overwrite and non-atomic writes are explicitly adapted.

## INV-REVERSE-001

- Stages remain 1-A, 1-B, 1-C, 2 with pending/partial/complete status.
- Git observation is read-only. Unknown, dirty, changing HEAD and a nested non-root path
  do not become an unchanged-source result. Observation is a point-in-time probe, not a
  lock over a mutable worktree; future extraction must read pinned objects.
- PostgreSQL owns runtime progress. A request identity makes exact retries idempotent;
  a generation compare-and-set prevents lost updates. Every successful write retains
  a history snapshot. The existing Store transaction supplies serialization.
- Later stages require completed predecessors and revalidated artifact bytes.
  Complete records need existing immutable artifacts. This proves storage integrity,
  not semantic quality, code correctness or adoption approval.
- Completed stages cannot be overwritten. A source change requires explicit rebaseline
  at 1-A; old history is retained. Same-source document correction and legacy import
  remain to be designed as explicit superseding events.
- Failures propagate to callers; DB failure must not become an empty or clean checkpoint.
- This initial component uses an operator script; workflow actor/lease integration remains
  required before autonomous activation. No production adoption or activation is claimed.

## Usage in this candidate

From a configured harness checkout with its PostgreSQL connection:

`python scripts/reverse_progress.py PROJECT SOURCE_ROOT`

Recording requires `--stage`, `--generation`, `--request-id`; `--status complete` also
requires one or more `--artifact sha256:...` handles in the harness artifact store.
Do not use synthetic test evidence to certify a real reverse workflow.

## Verification evidence

- Original four-module baseline: 33 passed, receipt
  `sha256:b2be22a6334bda46fb6cbc2747a53cf681879714bf9ff8f912ef6e4ebda7f1ac`.
- Claude source review: `sha256:95496b088f24aa1185b79f39d4fd8bf990380247b64e13cc025753a774c0595c`.
- Candidate component tests: 7 passed (stage order, evidence loss, source drift,
  rebaseline/history, request conflict, concurrent CAS, actual Git dirty/unknown probes).
- Full Windows suite: 290 passed, 30 skipped (service tests disabled in that run),
  `sha256:d9ce533a9a4bac2d8762dc738b8ba2f1fb1de40880b953d71bc1159a3bf62958`.
- Separately enabled service suite: 24 passed,
  `sha256:708bf5cadab7d13146983e5e0dc81b5ccb162782241bccf2980a554f308e7807`.
- Actual PostgreSQL concurrent-write/reload probe in isolated schema, synthetic source
  and artifact (not production adoption):
  `sha256:9bf42586aa74dc702ef51d7ab06c58a17c874b519692e573f00315ec0a0ddf64`.

Claude candidate review, full workflow integration, source adoption approvals and
exact-candidate Codex CLI canary are still required before promotion.

## Claude candidate review and corrections

Claude reviewed candidate 704ab1d and rejected it on four concrete findings, retained at
`sha256:5d1922d30ed878aa21c3918b01b10f38b43d8549c6da5ab71a64990aa26c4ffa`:

- A: resolve the tree from the captured commit, not HEAD a second time (ABA race).
- B: validate artifact sidecar object shape, matching reference and UTF-8 byte count;
  missing or malformed sidecars fail explicitly. Source/time remain unauthenticated
  descriptive metadata, never approval provenance.
- C: add an automated real PostgreSQL concurrency/replay/rebaseline/history test;
  remove the MemoryStore-specific JSON object-order assertion.
- D: test actual artifact content modification, not only deletion.

All four have corresponding code/tests in the follow-up candidate. Exact retries must
reuse the original request payload including expected_generation. The previous receipts
above apply to earlier candidates; follow-up review and test receipts are recorded in PR #14.
