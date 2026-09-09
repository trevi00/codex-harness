# Incumbent evaluator source layout

The release runner previously loaded candidate code but ran incumbent tests in
an incumbent checkout. File-relative fixtures copied that checkout's old src
into temporary policy repositories, so strict policy provenance checks compared
old source with candidate-loaded source and rejected valid fixture construction.

INV-RELEASE-001: retain incumbent test/config/history bytes in an ephemeral native
checkout, overlay only candidate src, and expose its tests and src through
PYTHONPATH. Neither reviewed checkout is modified. Strict current_policy checks
remain unchanged, including rejection of an actually changed policy definition.

This is an evaluator implementation change. Historical rejected releases must
remain rejected. Deployment requires review of this controller change and a fresh
qualification through the release workflow; passing targeted tests alone is not
release approval.

Operator-reported validation (receipts not supplied for Windows): Ruff passed;
full Windows suite 550 passed / 33 skipped. The original
incumbent native-routing/threshold collection/review tests ran against maintenance
candidate 7cc2bd326c41d0790d5742217e16078f716a7de6 in the corrected evaluator:
39 passed, including the previously failing 32 cases. The layout regression checks
unaltered test bytes, candidate import/file agreement, original checkout preservation
and temporary-directory cleanup.


## Combined candidate and qualification boundary

Task `e33e0d91-93c7-41e1-8af4-3704ae4cebff` started with a clean native checkout
at `0548efaf1bc8833c750c80b242de03b5a73d7799`. Fast-forward integration preserved
maintenance commit `7cc2bd326c41d0790d5742217e16078f716a7de6` and tree
`e07f5b3d889452c2e15932a11afcb46f77dd6d5d`. Local fetch of
`/repository refs/heads/fix/release-evaluator-layout` verified commit
`f4389250349ffbda00984cdfe6b43a5594152de4` and tree
`34e1f01ed6c036bc76e3903f70cb50f1504c4b49`; its change was cherry-picked.
No original checkout was edited. Additional regressions execute fixture pytest
through `ReleaseRunner._run`, preserve incumbent configuration and history, and
verify cleanup after body and source-copy failures. Mock installation and early
termination in that regression are not real release checks or canaries.

The planning file `/repository/.review-layout-evidence.json` was hash-verified as
`37ff19bb4297ba403cd5af0f7e28fcfd3c1272f37aff97965f60cce1f081a956`.
Its reported 32 failures / 7 passes before correction and 39 passes afterward
are planning evidence, not this worker's executions or historical release approval.
Final worker receipts are content-addressed under `.git/qualification/` in the
assigned workspace. Each records command argv, exit, commit/tree, diff digest,
environment and output hash. Reviewers must retain these files before workspace
collection. The final commit is the commit containing this runbook; receipts bind
its exact identity without a self-referential documentation amendment.

## Operator-owned controller activation and recovery

INV-RELEASE-001 / INV-RECOVERY-001: a candidate cannot update an already imported
controller. Controller activation, publishing and promotion require separate
operator authorization. Do not run the normal release supervisor for qualification
until its publication and promotion behavior is explicitly authorized.

The repository launch definition is `scripts/start_supervisor.ps1`: it resolves
`uv.exe`, then launches `uv run --project <checkout> python
<checkout>/scripts/supervise.py --research --releases` with that checkout as cwd.
It writes `.runtime/supervisor.pid`, `.runtime/supervisor.log` and
`.runtime/supervisor.err`; optional startup registration is
`HKCU:\Software\Microsoft\Windows\CurrentVersion\Run/CodexHarnessSupervisor`.
This identifies the checked-in definition, not the actual host process. The host
PID, checkout, interpreter, imported module and startup registration remain unknown
until the operator captures them. Supplied deployed revision
`38962239f49d88bb97b2dcdbcbd88f63a32dbbec` is context, not a loaded-source receipt.

1. Before activation, retain the actual supervisor process command line and parent,
   executable path, working directory, startup registration, launch script bytes,
   Git commit/tree/status, lockfile, environment configuration and interpreter
   version. Keep secrets in protected operator storage, not public logs. Retain the
   previous checkout and its complete environment; do not overwrite either.
   On Windows inspect `Get-CimInstance Win32_Process` filtered to `supervise.py`
   and the retained PID, plus `Get-ItemProperty` for the startup registration.
2. Disable release dispatch at the operator launch boundary: remove `--releases`
   from the controlled restart and disable automatic startup of the old release
   supervisor. Drain any existing release thread before stopping the process.
   Record queue state and in-flight completion. A restart alone does not prove
   draining; do not kill an active release and assume it never published.
3. Prepare a separate native checkout of the independently reviewed controller
   commit with `uv sync --frozen`. Retain old environment and launch configuration.
   From the exact new interpreter and cwd, record `sys.executable`, `sys.version`,
   `codex_harness.adapters.deployment.__file__`, SHA-256 of that file, and Git
   commit/tree. Clear inherited import-path overrides only in this controlled
   launch environment. Verify the module lies in the selected checkout and its
   bytes equal the reviewed Git blob.
4. Restart under that exact interpreter/cwd with release dispatch disabled.
   Capture the new PID and command line. The startup process must emit the module
   identity after importing `scripts/supervise.py` (for example an operator-owned
   Python launcher imports via `runpy.run_path(..., run_name="controller_probe")`,
   records `ReleaseRunner`'s module identity, sets `sys.argv` to the recorded
   arguments, then uses `runpy.run_path(..., run_name="__main__")` in that same
   interpreter; the imported deployment module remains cached). A separate probe alone does not prove the daemon's loaded
   source. Retain startup logs and health evidence before enabling qualification.
5. If source identity, startup or health fails, stop release execution, stop the
   new controller after draining, restore the exact previous checkout/interpreter,
   environment and startup configuration, then restart the previous controller
   with release dispatch disabled. Record restored PID, imported source identity,
   database/Redis connectivity and CLI health. Escalate unresolved failures to the
   operator; do not change host sysctls, sandbox permissions or container privileges.
6. After successful activation and fresh independent lead then conductor reviews,
   run complete incumbent and candidate suites and real CLI start/file-task
   canaries on the capable host for the exact final commit/tree and incumbent
   policy. Retain image digest, controller identity, service versions, argv,
   output, exits and all skip reasons. A revision change invalidates qualification.

`ReleaseRunner._promote` calls `git.publish` whenever `git.remote` is configured,
even with `auto_merge=False`. `scripts/supervise.py` uses the default
`auto_merge=True`. For authorized qualification without publication, the operator
must construct the runner with an explicitly absent remote and `auto_merge=False`,
verify those values before invocation, and keep automatic release dispatch off.
An empty environment variable is insufficient: `build_executor` can load the remote
from `.env`. Never enter `_promote` with a configured remote before publication
authorization. Passing checks does not itself authorize merge or deployment.

## Fresh workflow handoff

This assignment is a fresh implementation identity. The normal executor captures
its final candidate, completes its leased task via `Workflow.complete`, and handles
the durable report via `Workflow.handle` to queue `review_lead`. Do not manually
complete a live lease or manufacture a lead/conductor identity. On successful lead
inspection the executor calls `Releases.propose(candidate, policy)` and records
that independent review; a successful conductor review queues release evaluation.
The policy uses incumbent base `0548efaf1bc8833c750c80b242de03b5a73d7799` and
checks `tests`, `cli_start`, `cli_file_task`. Capture the actual resulting release
ID and policy hash from PostgreSQL. Runtime creation and independent review are
pending until this handoff is consumed; a prepared identity is not a durable release.

Never modify rejected release
`fa495ed648605b2ba5d5ca6c2864610d1be75bddef0416908c0e904a996c7a27`.
`Releases.propose` returns an existing record for identical candidate/policy data;
use the newly captured candidate and assignment, never erase a rejection. Previous
Windows Ruff/550-pass/33-skip, maintenance22 and prior canary reports need original
receipts and skip explanations from the operator; they do not qualify this commit.
No host receipts or independent approvals were obtained by writing this runbook.

Failed command inspection is inspection-blocked, not an accepted review.
`usageLimitExceeded` is a nonretryable provider usage-limit execution failure:
retain the exact provider error, task/attempt/revision and immutable references;
external recovery requires a fresh authorized assignment. Do not infer account,
quota category or reset timezone. Schema failures are separate diagnoses: preserve
schema bytes/hash, offending path, revision and provider error; version fields
must retain integer type and const=1 even in nested definitions. Retry or redelivery
alone is not independent recurrence. None of these failures qualify as successful
reviews or canaries.
