# Current proposal update

The current proposed evaluator is `4055d2d0b2a21908abc803f243c97953d928d994`.
It retains the five conservative expected-set changes below and adds the explicit
successful-inspection field to three pre-existing review fixtures in
`tests/test_git_workspace.py`, `tests/test_model_routing.py` and `tests/test_workflow.py`. Their assertions
remain byte-for-byte unchanged. The manifest verifies exactly these four files,
the original sole parent, exact fixture replacements and unchanged assertion ASTs.
This closes the newly reproduced generic-review admission defect without allowing
missing inspection evidence. The previous c9eb4c7 proposal and original failures
remain historical evidence. No approval is inherited; final controller/policy-bound
reviews and full qualification must use the current manifest.

The historical implementation handoff below describes the earlier narrower
proposal. Its c9eb4c7 identity and one-file scope are superseded by the current
manifest; the isolated review/qualification procedure otherwise remains applicable.

# Retention evaluator migration proposal

This implementation preserves final candidate `87b1b36244e4371f53318b8d813ea8d42a2372a8`
and its historical evidence. The baseline remains **proposed**, with no migration
approvals or production qualification created by this assignment. Collection
must remain paused pending complete current-host traversal and writer convergence.
No production graph closure or upstream migration completion is claimed.

The design is `sha256:33362398b94e7f65932aea166e4f44a8ca8bba4ea21c415386a1418e7f6eeb33`.
The contract is `src/codex_harness/resources/evaluator-migration.v1.json`.
It pins original source base `445fbc8859e896b90e974ed69447ce58e3446251` and
proposed evaluator `c9eb4c7c5d82a94f772c50dd7bfb510c493bfb76`, both trees, both
file blobs and SHA-256 hashes, and all five changed expressions. The adapter
reconstructs that proof from Git bytes at proposal, review and qualification.
It checks that the evaluator has exactly the original base as its sole parent,
only `tests/test_reference_kinds.py` differs, and replacing the five expected
expressions yields exact source and AST equality. All test names, calls, other
assertions and other files remain unchanged. None of the incumbent tests is
edited in this implementation workspace; its existing tests came from `87b1b3`.

The three assertions previously treated ambiguous clipped output or declarations
in a separate record as sufficient proof to omit an artifact edge. The five
expected expressions now retain the ambiguous `IMAGE` edge. This matches
INV-RESOURCE-001's conservative retention and cross-record isolation. The full
legacy failure is a failure, not an expected-failure exception. Diagnostics and
all original historical logs remain under `docs/evidence/`.

The new migration review API does not reuse ordinary qualification-only reviews.
An operator proposes the complete policy first. The release ID hashes candidate
and policy; the policy binds source base, evaluator, manifest digest, mandatory
checks and controller revision. The controller must be the final combined
candidate, so both reviewers inspect it along with the retained implementation.
The reviewer prompt and output schema explicitly carry these bindings; an accepted
review must also return `migration_approved=true`. Failed inspection, quota or
schema execution remains a failure and does not produce approval. The same
bindings are rechecked at qualification, verification and promotion. Generic
releases retain their previous evaluator semantics.

## Operator handoff (not executed here)

Keep automatic release dispatch and collection paused. Do not edit an old release,
review, verdict, or live checkout. Preserve the complete prior environment and
failure receipts. Obtain an isolated native checkout of the final combined
candidate, with a separate frozen environment (`uv sync --frozen`). Retain exact
commit/tree, interpreter, lockfile, controller source and image receipts.

1. Capture the final candidate object through the normal Git capture workflow,
   with original `base=445fbc...`, final commit/tree, worker author and task identity.
   `candidate.json` below is that exact object; candidate-supplied policy metadata
   is ignored. Set `HARNESS_DATABASE_URL` explicitly for the authorized runtime.
   The original repository passed as `--repository` must still have HEAD at the
   original source base and contain the candidate and proposed evaluator objects.
2. Explicitly propose the migration and queue fresh lead review using the new
   controller's interpreter and source (this command writes a new proposal and
   decision, but never an approval):

   ```sh
   uv run --project /isolated/controller python /isolated/controller/scripts/propose_migration.py \
     --candidate-json /operator/candidate.json --repository /original/repository \
     --workspaces /isolated/review-workspaces
   ```

   Retain the printed release ID, complete policy and policy hash. Use the new
   executor for the queued independent `lead:improvement` and `conductor`
   decisions; the old executor has no migration-review schema. The normal
   `Executor.decide_one(actor)` and `Workflow.handle` handoff process applies.
   Do not manually call `Releases.review` with invented actor identities or copy
   prior generic verdicts. Successful command inspection and fresh execution
evidence are required. Both approvals bind the exact candidate and controller.
   Migration review completion leaves the queue at `awaiting_bootstrap`, never
   `queued`, so the old supervisor cannot accidentally start qualification.
3. After both reviews explicitly approve, use the reviewed clean checkout's
   interpreter with isolation enabled. The following entry point imports only
   that checkout's controller, checks durable candidate/policy/review bindings,
   verifies loaded controller source bytes and Git state, and then invokes the
   existing release use case with `remote=None` and `auto_merge=False`:

   ```sh
   /isolated/controller/.venv/bin/python -I /isolated/controller/scripts/qualify_migration.py \
     --controller FINAL_COMMIT --candidate FINAL_COMMIT --policy-hash POLICY_SHA256 \
     --release-id RELEASE_ID --repository /original/repository \
     --runtime /isolated/qualification --auth /operator/codex-auth.json
   ```

   On Windows use `.venv/Scripts/python.exe`. The runtime path receives complete
   command/output receipts, separate full evaluator/candidate suite evidence,
   isolated-service lifecycle logs, image identity and actual Codex start/file
   canaries. The original base remains authoritative for ancestry and eventual
   merge. Missing Docker/authentication, failed commands, stale bindings or any
   mandatory failed check cannot qualify. No expected-failure whitelist exists.
4. Retain the final qualification receipt and independently inspect all skips and
   service/canary results. Publication, merge and live activation remain separate
   operator actions through the normal release mechanism after authorization;
   this bootstrap never publishes or promotes. A changed candidate/controller or
   policy requires fresh proposal/reviews. Never rewrite old rejected verdicts.

Local fixture approvals in tests are not independent reviews. Local suites with
integration skips do not establish actual isolated-service qualification. Docker
is absent in this worker environment; no container start/file canary is claimed.
