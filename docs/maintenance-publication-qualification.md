# Maintenance publication snapshot qualification

Candidate builds on f6d63130ec2685ca22da5e3e718d9cbf8ae9f6ab.

INV-RESOURCE-001: sample the filesystem generation under the publication lock,
outside database serialization. If a publisher owns the lock, defer the scan
without waiting; `deferred_scope=scan` distinguishes this from counted files.
File traversal remains outside database serialization. Existing generation checks,
tombstones and record reference validation remain required.

Previously supplied operator observations from 2026-09-08 (not independent receipts from this assignment):
- New concurrent-publication regression fails against f6d6313 and passes here.
- Actual Linux maintenance tests: 21 passed with --runxfail, including symlinks.
- Actual disposable PostgreSQL: 5 passed. Incumbent traversal caused 10-second
  claim/heartbeat timeouts; candidate operations took approximately 5-9 ms.
  1,000 records / 100 deletions: maximum deletion transaction 0.032 seconds.
- Linux full suite in an isolated native Git repository: 574 passed, 32 skipped.
- Ruff passed.
- Windows full suite: 566 passed, 34 skipped, one failure due to symlink privilege.
- Initial Linux runner failures were caused by Windows worktree Git paths and a
  global GIT_DIR contaminating fixture repositories. Native temporary Git checkout
  fixes the runner, without excluding tests.

These checks are not an independent review, actual CLI release canary or deployed
release. Re-run qualification for the final reviewed revision before promotion.
The five PostgreSQL tests require HARNESS_INTEGRATION=1 and an isolated database;
never point them at a production database.


## Worker qualification, task 846f4834-19a4-4774-97eb-e72dd69167f7

Reuse was verified from local `/repository`: candidate
`6b7093b2105b349b8361f39a680abea16c01abb4`, tree
`9e568d7be3a15a197c84884777edc00f73205694`, descendant of
`0548efaf1bc8833c750c80b242de03b5a73d7799`. The assigned native Git workspace
started clean. The external repository's unrelated working changes were not edited.
The imported 14-file delta is preserved; this assignment changes only this document
and `tests/test_maintenance.py`. Production implementation bytes are unchanged.

The strengthened test covers preview and apply, checking `publication_in_progress`,
`deferred_scope=scan`, zero removals, readable child and database write availability
before releasing the publisher. Apply persists the result; preview does not.
The identical test bytes fail on baseline f6d63130ec2685ca22da5e3e718d9cbf8ae9f6ab
in both cases because generation is sampled during publication. Import-path and
baseline checkout identity were separately verified. This is an expected negative
control, not a successful test execution, independent recurrence, or production canary.

The test changes are committed as `5ebce26890e5c08ee4dd457a6e2d2fd52f009d68`. Receipts below were executed on
6b7093b plus exactly that test diff (SHA-256
`090be91da4b416c53d01429cb0d94ad8d1f094f8b988dfc3fe5536281571369d`).
The baseline receipt's outer revision describes the invoking workspace; the identity
and import receipts establish the actual baseline code loaded. No global GIT_DIR or
GIT_WORK_TREE was set. Documentation commits do not change these tested code bytes.

Independent worker command results: Ruff exit 0; full suite exit 0, 575 passed /
32 skipped; maintenance --runxfail exit 0, 22 passed; dedicated real PostgreSQL
exit 0, 5 passed / 0 skipped; baseline negative control exit 1, 2 failed /
20 deselected. The full-suite skips are 25 service integrations, 5 PostgreSQL
maintenance cases, 1 skill-history integration and 1 usage-limit integration.
The five maintenance PostgreSQL cases were then executed separately; the other
27 integrations remain unexecuted here. These are worker qualification receipts,
not independent release approvals.

PostgreSQL 15.19 was downloaded and extracted locally, then initialized as the
existing unprivileged nobody user. The newly created UTF-8 database used only
`host=127.0.0.1 port=55439 user=qualification dbname=qualification`; the inherited
runtime connection was never used by the integration command. Preview/apply
incumbent lock timeouts were 10.02–10.03 seconds. Candidate claim/heartbeat times
were 0.038–0.051 seconds. For 1,000 documents and 100 old artifacts, snapshot took
0.037 seconds and maximum batch 0.100 seconds. These are bounded local measurements,
not deployment-scale latency guarantees. PostgreSQL was stopped after testing;
`pg_ctl status` returned 3 (no server running).

## Implementation inspection coverage

All 14 changed paths were read, including complete maintenance tests and PostgreSQL
fixture implementations. This is a worker inspection of the candidate delta, not a
claim that the entire repository or an upstream reference repository was analyzed.

| Paths | Behavior traced and evidence |
|---|---|
| adapters/maintenance.py | Roots snapshot, nonblocking generation probe, traversal outside DB serialization, final root/generation checks, tombstone-before-unlink, failure/defer persistence; direct CLI cleanup caller inspected. |
| adapters/artifacts.py | put and retain share publication lock; generation changes precede bodies/pins; deleted identities cannot be reused; durable pins conservatively survive crashes. |
| adapters/record_references.py, adapters/store.py | Shared bucket/ID/body-key/body-value semantics; only artifact_tombstones excluded; both stores reject references before writes, under transaction serialization. |
| application/rlm.py, ports.py | analyze wraps recursive provider work and result publication in retain; port declares ContextManager; CLI RLM caller and external-context tests traced. |
| tests/test_maintenance.py | All retention, generation, publication, rollback, corruption, symlink, concurrent collector, slow-unlink, store rejection and RLM cases inspected and executed. |
| tests/test_maintenance_postgres.py | Disposable-schema fixture; baseline source loaded by exact Git ID; claim/heartbeat lock observation in both modes; scale thresholds inspected and executed on real PostgreSQL. |
| docs/artifact-record-fence-review.md, docs/maintenance-publication-qualification.md | Historical claims and remaining release gates read; historical measurements are not substituted for fresh receipts. |
| tests/artifact-record-fence-evidence.json, tests/artifact-record-fence-pytest.txt, tests/artifact-record-fence-regressions.txt, tests/artifact-record-fence-ruff.txt | Historical bindings/output read as supplied evidence; test presence or old receipts do not establish current execution. |

Contracts inspected: INV-RESOURCE-001, INV-RELEASE-001, INV-MESSAGE-001 and incumbent
contracts.md. Inner layers retain standard-library/port dependencies. No domain policy
was moved into scripts. Remaining risks include per-candidate root rescans, filesystem
failure retention, crash-orphaned pins, and permanent tombstone rollback compatibility.
No demonstrated production-code defect required repair during this qualification.

## Release handoff and recovery

Acceptance remains withheld. `adapters/executor.py` routes successful implementation
results to lead:improvement, then conductor; `application/releases.py` binds approvals
to candidate identity and policy. `adapters/deployment.py` requires reviewed status
before incumbent/candidate suites and Docker CLI startup/file-task canaries. It can
publish/promote after verification, so this worker did not invoke it without those
gates. No reviews were manufactured or inserted into PostgreSQL.

The Docker prerequisite probe exited 1: `docker executable: None`. This establishes
an unavailable executable in this workspace, not the host's cause, daemon health,
authentication state, or provider quota. Actual release canaries were NOT executed.
The operator must supply the incumbent release runner with Docker/daemon access and
runtime authentication. Do not change container privileges, sandbox permissions or
host sysctls to work around that prerequisite. Keep auto-merge disabled and no remote
publication for this assignment. After separate successful lead and conductor reviews
of the final captured commit/tree and incumbent policy hash, execute actual canaries
through the normal runner. Any implementation revision requires fresh approvals.

Runtime policy hash supplied in the assignment is
`5642c13028e0f71ecd25a866a2aa37b81f228dd1dc4d68f8db2c0f9d95f3b7a3`;
this is provenance, not a newly verified live runtime-policy binding. The incumbent
release policy also hashes its checks plus base revision; the dispatcher must bind
the final candidate under that policy before review. The recovery envelope below is
prepared for incumbent dispatch, not evidence of a persisted runtime assignment.

Prior rejection/blocker history remains retained through supplied artifact
`sha256:ac762e8b21165b098b95bba39cd8f7b7e70b2a5d96658d02cd0daeb16374edb4`
and prior references `sha256:798e430339b15ea50585e35d8755b588b2e2bb0aecffa6815d5455411240947e`,
`sha256:9bcce1e57d7019be4b76797852ce96c92653ec659caf88c26a08aa26cfe42b1b`.
The previously reported clone/checkout/test ordering failures are supplied historical
attempts, separate from this worker's successes; their raw commands were not available
in this workspace and are not reconstructed. No prior rejection was overwritten.

Local setup failures are retained separately: initial apt download exited 100 (package
index absent); extracted postgres initially lacked libxml2/ICU and could not start;
local package provisioning subsequently succeeded. Initial commit failed for missing
Git author identity; a command-local Harness identity was then used. A stop receipt
wrapper collided with concurrent Git index writing and failed (git write-tree exit
128); its raw shutdown log was retained and independent pg_ctl status confirmed stop.
The receipt wrapper now uses read-only rev-parse for tree identity. Those failures do
not invalidate completed test commands and are not successful reviews/canaries.

## Content-addressed command evidence

Each entry contains the exact argv, command exit, elapsed seconds, timestamp, invoking
revision/tree, test-diff hash and stdout/stderr combined as a JSON string. SHA-256 of
that UTF-8 string reproduces log_ref. Raw copies and receipt JSON also reside under
`.git/qualification/<digest>.log` and `<digest>.json` in this assigned workspace.
This Git-tracked appendix preserves their bytes for reviewers even without that local
cache; these references are not claims of upload into the runtime artifact store.

```json
[
  {
    "label": "identity",
    "receipt": {
      "argv": [
        "python",
        "-c",
        "import hashlib,json,subprocess; from pathlib import Path; g=lambda *a:subprocess.check_output([\"git\",*a],text=True).strip(); print(json.dumps({\"head\":g(\"rev-parse\",\"HEAD\"),\"tree\":g(\"rev-parse\",\"HEAD^{tree}\"),\"baseline\":g(\"-C\",\".git/qualification/baseline\",\"rev-parse\",\"HEAD\"),\"test_sha256\":hashlib.sha256(Path(\"tests/test_maintenance.py\").read_bytes()).hexdigest(),\"baseline_test_sha256\":hashlib.sha256(Path(\".git/qualification/baseline/tests/test_maintenance.py\").read_bytes()).hexdigest(),\"paths\":g(\"diff\",\"--name-only\",\"0548efaf\",\"HEAD\").splitlines()}))"
      ],
      "at": "2026-09-08T08:29:52.055664+00:00",
      "diff_sha256": "090be91da4b416c53d01429cb0d94ad8d1f094f8b988dfc3fe5536281571369d",
      "environment": {
        "GIT_DIR": null,
        "GIT_WORK_TREE": null,
        "HARNESS_DATABASE_URL": "[set; redacted]",
        "HARNESS_INTEGRATION": null
      },
      "exit_code": 0,
      "log_ref": "sha256:b41c391e6e1829ad0284d33aed44869105fa1a4593066642229f05a6b8498101",
      "revision": "6b7093b2105b349b8361f39a680abea16c01abb4",
      "seconds": 0.33215689299686346,
      "tree": "9e568d7be3a15a197c84884777edc00f73205694"
    },
    "stdout_stderr": "{\"head\": \"6b7093b2105b349b8361f39a680abea16c01abb4\", \"tree\": \"9e568d7be3a15a197c84884777edc00f73205694\", \"baseline\": \"f6d63130ec2685ca22da5e3e718d9cbf8ae9f6ab\", \"test_sha256\": \"b1a3b3869fbf677ad62c316fe511bc62f30b5ab398f296a89a3256d1d7843b65\", \"baseline_test_sha256\": \"b1a3b3869fbf677ad62c316fe511bc62f30b5ab398f296a89a3256d1d7843b65\", \"paths\": [\"docs/artifact-record-fence-review.md\", \"docs/maintenance-publication-qualification.md\", \"src/codex_harness/adapters/artifacts.py\", \"src/codex_harness/adapters/maintenance.py\", \"src/codex_harness/adapters/record_references.py\", \"src/codex_harness/adapters/store.py\", \"src/codex_harness/application/rlm.py\", \"src/codex_harness/ports.py\", \"tests/artifact-record-fence-evidence.json\", \"tests/artifact-record-fence-pytest.txt\", \"tests/artifact-record-fence-regressions.txt\", \"tests/artifact-record-fence-ruff.txt\", \"tests/test_maintenance.py\", \"tests/test_maintenance_postgres.py\"]}\n"
  },
  {
    "label": "ancestry",
    "receipt": {
      "argv": [
        "git",
        "merge-base",
        "--is-ancestor",
        "0548efaf1bc8833c750c80b242de03b5a73d7799",
        "6b7093b2105b349b8361f39a680abea16c01abb4"
      ],
      "at": "2026-09-08T08:30:53.279740+00:00",
      "diff_sha256": "090be91da4b416c53d01429cb0d94ad8d1f094f8b988dfc3fe5536281571369d",
      "environment": {
        "GIT_DIR": null,
        "GIT_WORK_TREE": null,
        "HARNESS_DATABASE_URL": "[set; redacted]",
        "HARNESS_INTEGRATION": null
      },
      "exit_code": 0,
      "log_ref": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "revision": "6b7093b2105b349b8361f39a680abea16c01abb4",
      "seconds": 0.054028775994083844,
      "tree": "9e568d7be3a15a197c84884777edc00f73205694"
    },
    "stdout_stderr": ""
  },
  {
    "label": "baseline-import",
    "receipt": {
      "argv": [
        "env",
        "PYTHONPATH=.git/qualification/baseline/src",
        ".venv/bin/python",
        "-c",
        "from codex_harness.adapters.maintenance import ArtifactMaintenance; import inspect; print(inspect.getfile(ArtifactMaintenance))"
      ],
      "at": "2026-09-08T08:29:53.636285+00:00",
      "diff_sha256": "090be91da4b416c53d01429cb0d94ad8d1f094f8b988dfc3fe5536281571369d",
      "environment": {
        "GIT_DIR": null,
        "GIT_WORK_TREE": null,
        "HARNESS_DATABASE_URL": "[set; redacted]",
        "HARNESS_INTEGRATION": null
      },
      "exit_code": 0,
      "log_ref": "sha256:d61a48d3328684f8be6197d1d78c4358d8768f4450dd5763b710ae0b3190fa5e",
      "revision": "6b7093b2105b349b8361f39a680abea16c01abb4",
      "seconds": 0.7773913220007671,
      "tree": "9e568d7be3a15a197c84884777edc00f73205694"
    },
    "stdout_stderr": "/runtime/workspaces/846f4834-19a4-4774-97eb-e72dd69167f7/.git/qualification/baseline/src/codex_harness/adapters/maintenance.py\n"
  },
  {
    "label": "ruff",
    "receipt": {
      "argv": [
        "uv",
        "run",
        "ruff",
        "check",
        "."
      ],
      "at": "2026-09-08T08:28:25.557568+00:00",
      "diff_sha256": "090be91da4b416c53d01429cb0d94ad8d1f094f8b988dfc3fe5536281571369d",
      "environment": {
        "GIT_DIR": null,
        "GIT_WORK_TREE": null,
        "HARNESS_DATABASE_URL": "[set; redacted]",
        "HARNESS_INTEGRATION": null
      },
      "exit_code": 0,
      "log_ref": "sha256:c2c755659ee879515866fc14d005e57916fcb89d1d1eeccf166545efca22ab20",
      "revision": "6b7093b2105b349b8361f39a680abea16c01abb4",
      "seconds": 129.14435521300766,
      "tree": "9e568d7be3a15a197c84884777edc00f73205694"
    },
    "stdout_stderr": "Using CPython 3.13.15 interpreter at: /usr/local/bin/python3\nCreating virtual environment at: .venv\n   Building codex-self-harness @ file:///runtime/workspaces/846f4834-19a4-4774-97eb-e72dd69167f7\n      Built codex-self-harness @ file:///runtime/workspaces/846f4834-19a4-4774-97eb-e72dd69167f7\nwarning: Failed to hardlink files; falling back to full copy. This may lead to degraded performance.\n         If the cache and target directories are on different filesystems, hardlinking may not be supported.\n         If this is intentional, set `export UV_LINK_MODE=copy` or use `--link-mode=copy` to suppress this warning.\nInstalled 55 packages in 2m 05s\nAll checks passed!\n"
  },
  {
    "label": "maintenance",
    "receipt": {
      "argv": [
        "uv",
        "run",
        "pytest",
        "tests/test_maintenance.py",
        "-q",
        "--runxfail"
      ],
      "at": "2026-09-08T08:28:46.983265+00:00",
      "diff_sha256": "090be91da4b416c53d01429cb0d94ad8d1f094f8b988dfc3fe5536281571369d",
      "environment": {
        "GIT_DIR": null,
        "GIT_WORK_TREE": null,
        "HARNESS_DATABASE_URL": "[set; redacted]",
        "HARNESS_INTEGRATION": null
      },
      "exit_code": 0,
      "log_ref": "sha256:4cbb4fedcab957f801bb3e4853b0a8f1c49fe267c174b57d39cf28580ae2b709",
      "revision": "6b7093b2105b349b8361f39a680abea16c01abb4",
      "seconds": 8.365994485997362,
      "tree": "9e568d7be3a15a197c84884777edc00f73205694"
    },
    "stdout_stderr": "......................                                                   [100%]\n22 passed in 4.34s\n"
  },
  {
    "label": "full-suite",
    "receipt": {
      "argv": [
        "uv",
        "run",
        "pytest"
      ],
      "at": "2026-09-08T08:30:00.417203+00:00",
      "diff_sha256": "090be91da4b416c53d01429cb0d94ad8d1f094f8b988dfc3fe5536281571369d",
      "environment": {
        "GIT_DIR": null,
        "GIT_WORK_TREE": null,
        "HARNESS_DATABASE_URL": "[set; redacted]",
        "HARNESS_INTEGRATION": null
      },
      "exit_code": 0,
      "log_ref": "sha256:a1ef88b8a805fac99fb6e2be3a22eae8a16beb94f86b136aea2096edb4ded4b5",
      "revision": "6b7093b2105b349b8361f39a680abea16c01abb4",
      "seconds": 83.04474563500844,
      "tree": "9e568d7be3a15a197c84884777edc00f73205694"
    },
    "stdout_stderr": "============================= test session starts ==============================\nplatform linux -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0\nrootdir: /runtime/workspaces/846f4834-19a4-4774-97eb-e72dd69167f7\nconfigfile: pyproject.toml\ntestpaths: tests\nplugins: anyio-4.15.1\ncollected 607 items\n\ntests/test_app_server.py ..................                              [  2%]\ntests/test_architecture.py ..                                            [  3%]\ntests/test_artifact_query.py ...........                                 [  5%]\ntests/test_bus.py ........                                               [  6%]\ntests/test_context_recovery.py ..                                        [  6%]\ntests/test_core.py .................                                     [  9%]\ntests/test_executor_research.py .......................                  [ 13%]\ntests/test_external_context.py ....                                      [ 14%]\ntests/test_git_workspace.py ....                                         [ 14%]\ntests/test_graph_topology.py .                                           [ 14%]\ntests/test_integration.py sssssssssssssssssssssssss                      [ 18%]\ntests/test_maintenance.py ......................                         [ 22%]\ntests/test_maintenance_postgres.py sssss                                 [ 23%]\ntests/test_measurements.py ...............                               [ 25%]\ntests/test_model_routing.py .................                            [ 28%]\ntests/test_monitoring.py ......                                          [ 29%]\ntests/test_namespace_guard.py ...............................            [ 34%]\ntests/test_native_hooks.py ...............                               [ 37%]\ntests/test_native_routing_replay.py .........                            [ 38%]\ntests/test_output_schema.py ......................................       [ 44%]\ntests/test_pipeline.py .................                                 [ 47%]\ntests/test_project_detection.py .....................                    [ 51%]\ntests/test_project_skills.py .......................                     [ 55%]\ntests/test_release_test_imports.py .                                     [ 55%]\ntests/test_research_audits.py .......................................... [ 62%]\n...........................                                              [ 66%]\ntests/test_reverse_progress.py ..............                            [ 68%]\ntests/test_runtime_projection.py .                                       [ 69%]\ntests/test_runtime_thresholds.py ..............                          [ 71%]\ntests/test_skill_audit.py ....................                           [ 74%]\ntests/test_skill_guidance.py ......                                      [ 75%]\ntests/test_skill_history.py ...s...                                      [ 76%]\ntests/test_skill_import.py ...............                               [ 79%]\ntests/test_skill_routing.py ......                                       [ 80%]\ntests/test_threshold_collection.py ..........                            [ 81%]\ntests/test_threshold_proposals.py .........                              [ 83%]\ntests/test_threshold_replay.py ......                                    [ 84%]\ntests/test_threshold_reviews.py ....................                     [ 87%]\ntests/test_usage_limit.py .........................s......               [ 92%]\ntests/test_workflow.py ...........................................       [100%]\n\n================== 575 passed, 32 skipped in 77.59s (0:01:17) ==================\n"
  },
  {
    "label": "baseline",
    "receipt": {
      "argv": [
        "env",
        "PYTHONPATH=.git/qualification/baseline/src",
        ".venv/bin/python",
        "-m",
        "pytest",
        ".git/qualification/baseline/tests/test_maintenance.py",
        "-q",
        "--runxfail",
        "-k",
        "generation_snapshot"
      ],
      "at": "2026-09-08T08:29:26.822837+00:00",
      "diff_sha256": "090be91da4b416c53d01429cb0d94ad8d1f094f8b988dfc3fe5536281571369d",
      "environment": {
        "GIT_DIR": null,
        "GIT_WORK_TREE": null,
        "HARNESS_DATABASE_URL": "[set; redacted]",
        "HARNESS_INTEGRATION": null
      },
      "exit_code": 1,
      "log_ref": "sha256:ef8b41347313ad1987505aef477ad1d5b6019b50e4f0987087268c583dd98bb8",
      "revision": "6b7093b2105b349b8361f39a680abea16c01abb4",
      "seconds": 10.585814810998272,
      "tree": "9e568d7be3a15a197c84884777edc00f73205694"
    },
    "stdout_stderr": "FF                                                                       [100%]\n=================================== FAILURES ===================================\n_ test_generation_snapshot_waits_for_complete_publication_without_db_lock[False] _\n\ntmp_path = PosixPath('/tmp/pytest-of-root/pytest-27/test_generation_snapshot_waits0')\napply = False\n\n    @pytest.mark.parametrize('apply', [False, True])\n    def test_generation_snapshot_waits_for_complete_publication_without_db_lock(tmp_path, apply):\n        from concurrent.futures import ThreadPoolExecutor\n        from threading import Event\n    \n        changed, release, sampled, roots_read = Event(), Event(), Event(), Event()\n    \n        class PausedArtifacts(FileArtifacts):\n            pause = False\n    \n            def _changed(self):\n                super()._changed()\n                if self.pause:\n                    changed.set()\n                    assert release.wait(5)\n    \n        class ObservedMaintenance(ArtifactMaintenance):\n            def _roots(self, tx):\n                roots = super()._roots(tx)\n                roots_read.set()\n                return roots\n    \n            def _generation(self):\n                sampled.set()\n                return super()._generation()\n    \n        artifacts, store = PausedArtifacts(str(tmp_path / 'artifacts')), MemoryStore()\n        child = artifacts.put('publication dependency', 'test')['ref']\n        age(artifacts, child)\n        artifacts.pause = True\n        with ThreadPoolExecutor(max_workers=2) as pool:\n            publisher = pool.submit(artifacts.put, child, 'parent')\n            assert changed.wait(2)\n            collector = pool.submit(ObservedMaintenance(store, artifacts).collect, apply)\n            try:\n                assert roots_read.wait(2)\n                # A real publisher owns the file lock. Snapshot sampling must wait\n                # without retaining DB serialization needed for claims/heartbeats.\n>               assert not sampled.wait(0.25)\nE               assert not True\nE                +  where True = wait(0.25)\nE                +    where wait = <threading.Event at 0x7c11ac90e3f0: set>.wait\n\n.git/qualification/baseline/tests/test_maintenance.py:453: AssertionError\n_ test_generation_snapshot_waits_for_complete_publication_without_db_lock[True] _\n\ntmp_path = PosixPath('/tmp/pytest-of-root/pytest-27/test_generation_snapshot_waits1')\napply = True\n\n    @pytest.mark.parametrize('apply', [False, True])\n    def test_generation_snapshot_waits_for_complete_publication_without_db_lock(tmp_path, apply):\n        from concurrent.futures import ThreadPoolExecutor\n        from threading import Event\n    \n        changed, release, sampled, roots_read = Event(), Event(), Event(), Event()\n    \n        class PausedArtifacts(FileArtifacts):\n            pause = False\n    \n            def _changed(self):\n                super()._changed()\n                if self.pause:\n                    changed.set()\n                    assert release.wait(5)\n    \n        class ObservedMaintenance(ArtifactMaintenance):\n            def _roots(self, tx):\n                roots = super()._roots(tx)\n                roots_read.set()\n                return roots\n    \n            def _generation(self):\n                sampled.set()\n                return super()._generation()\n    \n        artifacts, store = PausedArtifacts(str(tmp_path / 'artifacts')), MemoryStore()\n        child = artifacts.put('publication dependency', 'test')['ref']\n        age(artifacts, child)\n        artifacts.pause = True\n        with ThreadPoolExecutor(max_workers=2) as pool:\n            publisher = pool.submit(artifacts.put, child, 'parent')\n            assert changed.wait(2)\n            collector = pool.submit(ObservedMaintenance(store, artifacts).collect, apply)\n            try:\n                assert roots_read.wait(2)\n                # A real publisher owns the file lock. Snapshot sampling must wait\n                # without retaining DB serialization needed for claims/heartbeats.\n>               assert not sampled.wait(0.25)\nE               assert not True\nE                +  where True = wait(0.25)\nE                +    where wait = <threading.Event at 0x7c11ac506050: set>.wait\n\n.git/qualification/baseline/tests/test_maintenance.py:453: AssertionError\n=========================== short test summary info ============================\nFAILED .git/qualification/baseline/tests/test_maintenance.py::test_generation_snapshot_waits_for_complete_publication_without_db_lock[False]\nFAILED .git/qualification/baseline/tests/test_maintenance.py::test_generation_snapshot_waits_for_complete_publication_without_db_lock[True]\n2 failed, 20 deselected in 7.53s\n"
  },
  {
    "label": "postgres-init",
    "receipt": {
      "argv": [
        "env",
        "LD_LIBRARY_PATH=/runtime/workspaces/846f4834-19a4-4774-97eb-e72dd69167f7/.git/qualification/postgres/usr/lib/x86_64-linux-gnu",
        "runuser",
        "-u",
        "nobody",
        "--",
        ".git/qualification/postgres/usr/lib/postgresql/15/bin/initdb",
        "-D",
        ".git/qualification/pgdata",
        "-A",
        "trust",
        "-U",
        "qualification",
        "--no-locale"
      ],
      "at": "2026-09-08T08:29:32.860207+00:00",
      "diff_sha256": "090be91da4b416c53d01429cb0d94ad8d1f094f8b988dfc3fe5536281571369d",
      "environment": {
        "GIT_DIR": null,
        "GIT_WORK_TREE": null,
        "HARNESS_DATABASE_URL": "[set; redacted]",
        "HARNESS_INTEGRATION": null
      },
      "exit_code": 0,
      "log_ref": "sha256:3b51620d679e2d82def7e7be926270299bdd0e615234b8e8dff051a3c8cedeea",
      "revision": "6b7093b2105b349b8361f39a680abea16c01abb4",
      "seconds": 17.588619607005967,
      "tree": "9e568d7be3a15a197c84884777edc00f73205694"
    },
    "stdout_stderr": "The files belonging to this database system will be owned by user \"nobody\".\nThis user must also own the server process.\n\nThe database cluster will be initialized with locale \"C\".\nThe default database encoding has accordingly been set to \"SQL_ASCII\".\nThe default text search configuration will be set to \"english\".\n\nData page checksums are disabled.\n\nfixing permissions on existing directory .git/qualification/pgdata ... ok\ncreating subdirectories ... ok\nselecting dynamic shared memory implementation ... posix\nselecting default max_connections ... 100\nselecting default shared_buffers ... 128MB\nselecting default time zone ... Etc/UTC\ncreating configuration files ... ok\nrunning bootstrap script ... ok\nperforming post-bootstrap initialization ... ok\nsyncing data to disk ... ok\n\nSuccess. You can now start the database server using:\n\n    .git/qualification/postgres/usr/lib/postgresql/15/bin/pg_ctl -D .git/qualification/pgdata -l logfile start\n\n"
  },
  {
    "label": "postgres-start",
    "receipt": {
      "argv": [
        "env",
        "LD_LIBRARY_PATH=/runtime/workspaces/846f4834-19a4-4774-97eb-e72dd69167f7/.git/qualification/postgres/usr/lib/x86_64-linux-gnu",
        "runuser",
        "-u",
        "nobody",
        "--",
        ".git/qualification/postgres/usr/lib/postgresql/15/bin/pg_ctl",
        "-D",
        ".git/qualification/pgdata",
        "-l",
        ".git/qualification/pgdata/server.log",
        "-o",
        "-h 127.0.0.1 -p 55439 -k ''",
        "-w",
        "start"
      ],
      "at": "2026-09-08T08:30:10.761371+00:00",
      "diff_sha256": "090be91da4b416c53d01429cb0d94ad8d1f094f8b988dfc3fe5536281571369d",
      "environment": {
        "GIT_DIR": null,
        "GIT_WORK_TREE": null,
        "HARNESS_DATABASE_URL": "[set; redacted]",
        "HARNESS_INTEGRATION": null
      },
      "exit_code": 0,
      "log_ref": "sha256:66afd0411ccc09366e99fdd99b85f21899c8d2d064f5835126859618802153ad",
      "revision": "6b7093b2105b349b8361f39a680abea16c01abb4",
      "seconds": 0.5486223900079494,
      "tree": "9e568d7be3a15a197c84884777edc00f73205694"
    },
    "stdout_stderr": "waiting for server to start.... done\nserver started\n"
  },
  {
    "label": "postgres-create",
    "receipt": {
      "argv": [
        ".venv/bin/python",
        "-c",
        "import psycopg; c=psycopg.connect(\"host=127.0.0.1 port=55439 user=qualification dbname=postgres\",autocommit=True); c.execute(\"CREATE DATABASE qualification ENCODING 'UTF8' TEMPLATE template0\"); c.close()"
      ],
      "at": "2026-09-08T08:30:27.441227+00:00",
      "diff_sha256": "090be91da4b416c53d01429cb0d94ad8d1f094f8b988dfc3fe5536281571369d",
      "environment": {
        "GIT_DIR": null,
        "GIT_WORK_TREE": null,
        "HARNESS_DATABASE_URL": "[set; redacted]",
        "HARNESS_INTEGRATION": null
      },
      "exit_code": 0,
      "log_ref": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "revision": "6b7093b2105b349b8361f39a680abea16c01abb4",
      "seconds": 2.9237653460004367,
      "tree": "9e568d7be3a15a197c84884777edc00f73205694"
    },
    "stdout_stderr": ""
  },
  {
    "label": "postgres-identity",
    "receipt": {
      "argv": [
        "env",
        "HARNESS_DATABASE_URL=host=127.0.0.1 port=55439 user=qualification dbname=qualification",
        ".venv/bin/python",
        "-c",
        "import os,psycopg; c=psycopg.connect(os.environ[\"HARNESS_DATABASE_URL\"]); print(c.execute(\"SELECT version(), current_database(), current_user, inet_server_addr(), inet_server_port()\").fetchone()); c.close()"
      ],
      "at": "2026-09-08T08:31:25.197189+00:00",
      "diff_sha256": "090be91da4b416c53d01429cb0d94ad8d1f094f8b988dfc3fe5536281571369d",
      "environment": {
        "GIT_DIR": null,
        "GIT_WORK_TREE": null,
        "HARNESS_DATABASE_URL": "[set; redacted]",
        "HARNESS_INTEGRATION": null
      },
      "exit_code": 0,
      "log_ref": "sha256:d5eaad8385c4dc9e60d6342ae38ae22fcd66bd3e4e433da68c61a9bc2702f3c1",
      "revision": "6b7093b2105b349b8361f39a680abea16c01abb4",
      "seconds": 0.8313049650023459,
      "tree": "9e568d7be3a15a197c84884777edc00f73205694"
    },
    "stdout_stderr": "('PostgreSQL 15.19 (Debian 15.19-0+deb12u1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 12.2.0-14+deb12u1) 12.2.0, 64-bit', 'qualification', 'qualification', IPv4Address('127.0.0.1'), 55439)\n"
  },
  {
    "label": "postgres-suite",
    "receipt": {
      "argv": [
        "env",
        "HARNESS_INTEGRATION=1",
        "HARNESS_DATABASE_URL=host=127.0.0.1 port=55439 user=qualification dbname=qualification",
        "uv",
        "run",
        "pytest",
        "tests/test_maintenance_postgres.py",
        "-v",
        "-s"
      ],
      "at": "2026-09-08T08:31:32.581608+00:00",
      "diff_sha256": "090be91da4b416c53d01429cb0d94ad8d1f094f8b988dfc3fe5536281571369d",
      "environment": {
        "GIT_DIR": null,
        "GIT_WORK_TREE": null,
        "HARNESS_DATABASE_URL": "[set; redacted]",
        "HARNESS_INTEGRATION": null
      },
      "exit_code": 0,
      "log_ref": "sha256:582eb48c9fe742cab15aac1bcafb690c295fb467015bf639d2ab076efb4d7e1d",
      "revision": "6b7093b2105b349b8361f39a680abea16c01abb4",
      "seconds": 55.31586373700702,
      "tree": "9e568d7be3a15a197c84884777edc00f73205694"
    },
    "stdout_stderr": "============================= test session starts ==============================\nplatform linux -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0 -- /runtime/workspaces/846f4834-19a4-4774-97eb-e72dd69167f7/.venv/bin/python\ncachedir: .pytest_cache\nrootdir: /runtime/workspaces/846f4834-19a4-4774-97eb-e72dd69167f7\nconfigfile: pyproject.toml\nplugins: anyio-4.15.1\ncollecting ... collected 5 items\n\ntests/test_maintenance_postgres.py::test_slow_traversal_workflow_responsiveness[True-False] {'incumbent': True, 'apply': False, 'locks': [(False, 'ExclusiveLock'), (False, 'ExclusiveLock'), (True, 'ExclusiveLock')], 'outcomes': [{'seconds': 10.024586068000644, 'status': 'lock_timeout', 'error': 'canceling statement due to lock timeout', 'sqlstate': '55P03'}, {'seconds': 10.02443443100492, 'status': 'lock_timeout', 'error': 'canceling statement due to lock timeout', 'sqlstate': '55P03'}]}\nPASSED\ntests/test_maintenance_postgres.py::test_slow_traversal_workflow_responsiveness[True-True] {'incumbent': True, 'apply': True, 'locks': [(False, 'ExclusiveLock'), (True, 'ExclusiveLock')], 'outcomes': [{'seconds': 10.031822004995774, 'status': 'lock_timeout', 'error': 'canceling statement due to lock timeout', 'sqlstate': '55P03'}, {'seconds': 10.031782110003405, 'status': 'lock_timeout', 'error': 'canceling statement due to lock timeout', 'sqlstate': '55P03'}]}\nPASSED\ntests/test_maintenance_postgres.py::test_slow_traversal_workflow_responsiveness[False-False] {'incumbent': False, 'apply': False, 'locks': [(True, 'ExclusiveLock'), (False, 'ExclusiveLock')], 'outcomes': [{'seconds': 0.050370748998830095, 'status': 'ok', 'value': {'id': '06bd010f-c77c-45be-97f2-1dbbbadec9a7', 'agent': 'worker:github', 'error': None, 'result': None, 'status': 'running', 'attempt': 1, 'message': {'how': {'constraints': [], 'context_ref': None, 'result_schema': 'six-w.v1', 'acceptance_criteria': ['Preserve normal behavior']}, 'who': {'owner': 'worker:github', 'sender': 'lead:research', 'recipient': 'worker:github'}, 'why': {'objective': 'Improve harness reliability from verified evidence', 'evidence_refs': []}, 'type': 'task.assign', 'what': {'action': 'research', 'details': {'objective': 'fixture'}}, 'when': {'after': [], 'deadline': None, 'created_at': '2026-09-08T08:31:05.173146+00:00'}, 'where': {'revision': 'bootstrap', 'repository': 'codex-harness', 'environment': 'local', 'allowed_paths': []}, 'message_id': '06bd010f-c77c-45be-97f2-1dbbbadec9a7', 'causation_id': None, 'correlation_id': 'test', 'schema_version': '1.0'}, 'created_at': '2026-09-08T08:31:05.201953+00:00', 'generation': 1, 'input_hash': '1a7783188d674674b916751313cf9eae708f84e2a972d2521743bb21d6af79fe', 'lease_owner': 'claim', 'lease_until': '2026-09-08T08:41:05.317777+00:00'}}, {'seconds': 0.043258801990305074, 'status': 'ok', 'value': None}]}\nPASSED\ntests/test_maintenance_postgres.py::test_slow_traversal_workflow_responsiveness[False-True] {'incumbent': False, 'apply': True, 'locks': [(False, 'ExclusiveLock'), (True, 'ExclusiveLock')], 'outcomes': [{'seconds': 0.03829814100754447, 'status': 'ok', 'value': {'id': 'bf0b67df-e913-4e99-8f45-9a7061d9385e', 'agent': 'worker:github', 'error': None, 'result': None, 'status': 'running', 'attempt': 1, 'message': {'how': {'constraints': [], 'context_ref': None, 'result_schema': 'six-w.v1', 'acceptance_criteria': ['Preserve normal behavior']}, 'who': {'owner': 'worker:github', 'sender': 'lead:research', 'recipient': 'worker:github'}, 'why': {'objective': 'Improve harness reliability from verified evidence', 'evidence_refs': []}, 'type': 'task.assign', 'what': {'action': 'research', 'details': {'objective': 'fixture'}}, 'when': {'after': [], 'deadline': None, 'created_at': '2026-09-08T08:31:16.058913+00:00'}, 'where': {'revision': 'bootstrap', 'repository': 'codex-harness', 'environment': 'local', 'allowed_paths': []}, 'message_id': 'bf0b67df-e913-4e99-8f45-9a7061d9385e', 'causation_id': None, 'correlation_id': 'test', 'schema_version': '1.0'}, 'created_at': '2026-09-08T08:31:16.090577+00:00', 'generation': 1, 'input_hash': 'a22645ed49b6dd391a1678ebfa7feff5b66e7252bdd66d92224a784d3e7ee027', 'lease_owner': 'claim', 'lease_until': '2026-09-08T08:41:16.200738+00:00'}}, {'seconds': 0.04128490200673696, 'status': 'ok', 'value': None}]}\nPASSED\ntests/test_maintenance_postgres.py::test_snapshot_and_final_batch_duration {'scale_documents': 1000, 'scale_artifacts': 100, 'result': {'id': 'latest', 'at': '2026-09-08T08:31:32.386760+00:00', 'applied': True, 'files': 100, 'bytes': 190, 'retained_references': 0, 'grace_days': 7, 'deferred': 0, 'errors': [], 'snapshot_seconds': 0.036643844010541216, 'max_batch_seconds': 0.09986321900214534}}\nPASSED\n\n============================== 5 passed in 50.58s ==============================\n"
  },
  {
    "label": "postgres-stopped",
    "receipt": {
      "argv": [
        "env",
        "LD_LIBRARY_PATH=/runtime/workspaces/846f4834-19a4-4774-97eb-e72dd69167f7/.git/qualification/postgres/usr/lib/x86_64-linux-gnu",
        "runuser",
        "-u",
        "nobody",
        "--",
        ".git/qualification/postgres/usr/lib/postgresql/15/bin/pg_ctl",
        "-D",
        ".git/qualification/pgdata",
        "status"
      ],
      "at": "2026-09-08T08:32:17.141875+00:00",
      "diff_sha256": "090be91da4b416c53d01429cb0d94ad8d1f094f8b988dfc3fe5536281571369d",
      "environment": {
        "GIT_DIR": null,
        "GIT_WORK_TREE": null,
        "HARNESS_DATABASE_URL": "[set; redacted]",
        "HARNESS_INTEGRATION": null
      },
      "exit_code": 3,
      "log_ref": "sha256:e138ccb54fdb08283c6eb21159c53207bbbbf07077246e2804e18d22efe6e250",
      "revision": "6b7093b2105b349b8361f39a680abea16c01abb4",
      "seconds": 0.12249167299887631,
      "tree": "9e568d7be3a15a197c84884777edc00f73205694"
    },
    "stdout_stderr": "pg_ctl: no server running\n"
  },
  {
    "label": "evaluator-prerequisite",
    "receipt": {
      "argv": [
        "python",
        "-c",
        "import shutil,sys; print(\"docker executable:\",shutil.which(\"docker\")); sys.exit(0 if shutil.which(\"docker\") else 1)"
      ],
      "at": "2026-09-08T08:30:25.765634+00:00",
      "diff_sha256": "090be91da4b416c53d01429cb0d94ad8d1f094f8b988dfc3fe5536281571369d",
      "environment": {
        "GIT_DIR": null,
        "GIT_WORK_TREE": null,
        "HARNESS_DATABASE_URL": "[set; redacted]",
        "HARNESS_INTEGRATION": null
      },
      "exit_code": 1,
      "log_ref": "sha256:77201112177aa8681a239f5e87c821c442e418904886fc3781a7d5590547427c",
      "revision": "6b7093b2105b349b8361f39a680abea16c01abb4",
      "seconds": 0.029284593008924276,
      "tree": "9e568d7be3a15a197c84884777edc00f73205694"
    },
    "stdout_stderr": "docker executable: None\n"
  },
  {
    "label": "provision-download",
    "receipt": {
      "argv": [
        "apt-get",
        "download",
        "postgresql-15"
      ],
      "at": "2026-09-08T08:25:57.068646+00:00",
      "diff_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "environment": {
        "GIT_DIR": null,
        "GIT_WORK_TREE": null,
        "HARNESS_DATABASE_URL": "[set; redacted]",
        "HARNESS_INTEGRATION": null
      },
      "exit_code": 100,
      "log_ref": "sha256:781ee2130f94c3f9866506f7303788365a87cf043efaa97d7e80dc62e2ca5525",
      "revision": "6b7093b2105b349b8361f39a680abea16c01abb4",
      "seconds": 0.04076709400396794,
      "tree": "9e568d7be3a15a197c84884777edc00f73205694"
    },
    "stdout_stderr": "E: Unable to locate package postgresql-15\n"
  },
  {
    "label": "postgres-stop-partial-receipt",
    "log_ref": "sha256:e7b24f63c690806243625ca8cb53f81f1a71a030c6c34a3820e76021c6810564",
    "stdout_stderr": "waiting for server to shut down..... done\nserver stopped\n",
    "uncertainty": "wrapper failed after command; no complete command exit/timing receipt"
  }
]
```

## Prepared recovery assignment (six-w.v1)

```json
{
  "schema_version": "1.0",
  "message_id": "356feb01-5d98-4e7a-9acb-a3cfb092bc30",
  "type": "task.assign",
  "correlation_id": "qualification:846f4834-19a4-4774-97eb-e72dd69167f7",
  "causation_id": null,
  "who": {
    "sender": "lead:improvement",
    "recipient": "worker:implementation",
    "owner": "worker:implementation"
  },
  "what": {
    "action": "implement",
    "details": {
      "plan": {
        "objective": "Complete release qualification after operator provisions the incumbent release evaluator; preserve completed maintenance qualification and prior failures.",
        "allowed_paths": [
          "docs/maintenance-publication-qualification.md"
        ],
        "acceptance_criteria": [
          "Bind the final captured candidate commit/tree and incumbent policy hash; source revision 5ebce26890e5c08ee4dd457a6e2d2fd52f009d68 is provenance, not approval of a later documentation commit.",
          "Obtain separate successful command inspections and lead:improvement then conductor approvals through the incumbent workflow.",
          "Execute actual CLI startup/file-task canaries through the normal release evaluator after reviews; no push, merge or deployment.",
          "Keep failed attempts failed, retain immutable commands and results; external quota recovery requires a fresh authorized assignment if usageLimitExceeded occurs."
        ]
      },
      "recovery": {
        "owner": "worker:implementation",
        "external_prerequisite_owner": "operator",
        "failed_command": [
          "python",
          "-c",
          "import shutil,sys; print(\"docker executable:\",shutil.which(\"docker\")); sys.exit(0 if shutil.which(\"docker\") else 1)"
        ],
        "exit_code": 1,
        "failed_revision": "6b7093b2105b349b8361f39a680abea16c01abb4",
        "failed_diff_sha256": "090be91da4b416c53d01429cb0d94ad8d1f094f8b988dfc3fe5536281571369d",
        "evidence_ref": "sha256:77201112177aa8681a239f5e87c821c442e418904886fc3781a7d5590547427c",
        "prerequisite": "Incumbent release runner with Docker executable and usable daemon, runtime authentication, isolated integration services and durable ordered reviews. Do not alter sandbox permissions, container privileges or host sysctls.",
        "rerun_condition": "Operator verifies runner prerequisites; dispatcher binds final candidate and policy; successful independent lead then conductor reviews complete. Re-run prerequisite probe before normal evaluator canaries.",
        "status": "prepared-not-submitted"
      }
    }
  },
  "why": {
    "objective": "Improve harness reliability from verified evidence",
    "evidence_refs": [
      "sha256:77201112177aa8681a239f5e87c821c442e418904886fc3781a7d5590547427c"
    ]
  },
  "when": {
    "created_at": "2026-09-08T08:34:24.831135+00:00",
    "deadline": null,
    "after": []
  },
  "where": {
    "repository": "codex-harness",
    "revision": "5ebce26890e5c08ee4dd457a6e2d2fd52f009d68",
    "environment": "local",
    "allowed_paths": [
      "docs/maintenance-publication-qualification.md"
    ]
  },
  "how": {
    "constraints": [],
    "acceptance_criteria": [
      "Preserve normal behavior"
    ],
    "context_ref": null,
    "result_schema": "six-w.v1"
  }
}
```
