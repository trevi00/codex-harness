# Bootstrap verification — 2026-09-07

- `python scripts/check.py --integration`: ruff passed; **22 tests passed**.
- Real PostgreSQL: concurrent incident transactions create one hook/outbox record, state survives reconnect, stale checkpoints rejected.
- Real Redis Streams: an incident committed before consumer crash is redelivered without double counting; lead notification reaches conductor.
- Real pgvector: injected test vectors stored and searched with model identity filtering. No production embedding quality claim.
- Tree-sitter: code/contract-reference relationships queried; failed parsing preserves the previous index.
- `harness demo`: scripted fixture produces a reviewed/canary-checked active executable-alias hook.
- `harness run-command -- codex.ps1 --version`: prepared `codex.cmd --version`, exit 0, `codex-cli 0.153.4`.
- `harness canary --live` on Windows host: real Codex CLI read input, wrote output, returned validated JSON; passed (9 JSONL events).
- `docker compose exec -T conductor harness canary`: container CLI startup passed, version 0.153.4. Container model authentication was not configured/tested.
- `uv run python scripts/smoke_bus.py`: two incident messages handled by improvement-lead; exactly one required hook; conductor received it as `awaiting_handler`.
- Stopped conductor, published a fixture message, ran `scripts/supervise.py --once`: conductor restarted and consumed the message.
- Latest local code index at verification: 151 nodes / 127 edges. Reindex after source changes.
- Running: postgres, redis, conductor, research-lead, improvement-lead. Measured aggregate idle container memory ~155 MiB (excludes Docker/WSL overhead and live Codex work).

These results establish the bootstrap behavior only. Automated GitHub PR reviews, candidate deployment,
full runtime session rotation, source-wide knowledge retrieval and ongoing research remain in docs/status.md.


## Output-schema candidate canary attempts — 2026-09-07

Actual installed CLI invocations, distinct from transport fixtures. Returned records count only if validated=true.

```json
[
  {
    "kind": "AdaptationProposal",
    "revision": "992db51ee1778b993c7fa873d4196ae0eacfaa49",
    "tree": "da1faf7cf52e5dc2838584585e21a108c2465337",
    "schema_sha256": "cdae3d779a70cf5a0d54d72ea6ccd45482b84d875281df2f5cbbc4ed79ac2caa",
    "cli_version": {
      "passed": true,
      "version": "codex-cli 0.153.4",
      "exit_code": 0
    },
    "argv": [
      "/usr/local/bin/codex",
      "exec",
      "--json",
      "--ephemeral",
      "--skip-git-repo-check",
      "--color",
      "never",
      "--output-schema",
      "/tmp/codex-harness-uy5gpxn6/response.schema.json",
      "--output-last-message",
      "/tmp/codex-harness-uy5gpxn6/response.json",
      "-C",
      "/runtime/workspaces/6fa5ed1d-f453-44b8-af16-cc154a9862ef",
      "-"
    ],
    "exit_code": 1,
    "stdout": "{\"type\":\"thread.started\",\"thread_id\":\"01a07b9f-7562-7d22-8fd3-8646e91660b8\"}\n{\"type\":\"turn.started\"}\n{\"type\":\"error\",\"message\":\"{\\n  \\\"type\\\": \\\"error\\\",\\n  \\\"error\\\": {\\n    \\\"type\\\": \\\"invalid_request_error\\\",\\n    \\\"code\\\": \\\"invalid_json_schema\\\",\\n    \\\"message\\\": \\\"Invalid schema for response_format 'codex_output_schema': In context=('properties', 'tests_not_run', 'items'), 'additionalProperties' is required to be supplied and to be false.\\\",\\n    \\\"param\\\": \\\"text.format.schema\\\"\\n  },\\n  \\\"status\\\": 400\\n}\"}\n{\"type\":\"turn.failed\",\"error\":{\"message\":\"{\\n  \\\"type\\\": \\\"error\\\",\\n  \\\"error\\\": {\\n    \\\"type\\\": \\\"invalid_request_error\\\",\\n    \\\"code\\\": \\\"invalid_json_schema\\\",\\n    \\\"message\\\": \\\"Invalid schema for response_format 'codex_output_schema': In context=('properties', 'tests_not_run', 'items'), 'additionalProperties' is required to be supplied and to be false.\\\",\\n    \\\"param\\\": \\\"text.format.schema\\\"\\n  },\\n  \\\"status\\\": 400\\n}\"}}\n",
    "stderr": "",
    "validated": false,
    "error": "Codex execution failed (exit=1): "
  },
  {
    "kind": "IndependentReview",
    "revision": "992db51ee1778b993c7fa873d4196ae0eacfaa49",
    "tree": "da1faf7cf52e5dc2838584585e21a108c2465337",
    "schema_sha256": "16fdd1a8a779e81a59991b468f0a7216843e4531ab018968e9a095acbab777ad",
    "cli_version": {
      "passed": true,
      "version": "codex-cli 0.153.4",
      "exit_code": 0
    },
    "argv": [
      "/usr/local/bin/codex",
      "exec",
      "--json",
      "--ephemeral",
      "--skip-git-repo-check",
      "--color",
      "never",
      "--output-schema",
      "/tmp/codex-harness-wpmltrgk/response.schema.json",
      "--output-last-message",
      "/tmp/codex-harness-wpmltrgk/response.json",
      "-C",
      "/runtime/workspaces/6fa5ed1d-f453-44b8-af16-cc154a9862ef",
      "-"
    ],
    "exit_code": 1,
    "stdout": "{\"type\":\"thread.started\",\"thread_id\":\"01a07b9f-8a93-7671-bb59-6898f6247fd8\"}\n{\"type\":\"turn.started\"}\n{\"type\":\"error\",\"message\":\"{\\n  \\\"type\\\": \\\"error\\\",\\n  \\\"error\\\": {\\n    \\\"type\\\": \\\"invalid_request_error\\\",\\n    \\\"code\\\": \\\"invalid_json_schema\\\",\\n    \\\"message\\\": \\\"Invalid schema for response_format 'codex_output_schema': In context=('properties', 'tests_not_run', 'items'), 'additionalProperties' is required to be supplied and to be false.\\\",\\n    \\\"param\\\": \\\"text.format.schema\\\"\\n  },\\n  \\\"status\\\": 400\\n}\"}\n{\"type\":\"turn.failed\",\"error\":{\"message\":\"{\\n  \\\"type\\\": \\\"error\\\",\\n  \\\"error\\\": {\\n    \\\"type\\\": \\\"invalid_request_error\\\",\\n    \\\"code\\\": \\\"invalid_json_schema\\\",\\n    \\\"message\\\": \\\"Invalid schema for response_format 'codex_output_schema': In context=('properties', 'tests_not_run', 'items'), 'additionalProperties' is required to be supplied and to be false.\\\",\\n    \\\"param\\\": \\\"text.format.schema\\\"\\n  },\\n  \\\"status\\\": 400\\n}\"}}\n",
    "stderr": "",
    "validated": false,
    "error": "Codex execution failed (exit=1): "
  }
]
```

## Recurrence implementation handoff — 2026-09-07

Status: implementation available for independent review; **not eligible for promotion**.
Baseline `09c1d58298b22337125f29842382d2aef960c7d2` was clean on entry.
Implementation candidate `49abb5faee959c282eb99547110cf2e0e17ceda2`, tree
`fb3f02ec730445b4afd1e6e39257aa2ed42165d9`. The subsequent documentation-only
commit records this candidate; release reviews must bind the exact proposed release commit/tree,
not reuse approvals from this source candidate or the earlier canary revision.

Authorized plan artifact: `sha256:6e3ba20f46e427dd0887103306103e024776f10bfcd90113a3ece901e69e5863`;
planning execution: `sha256:5506ce90dda64f876c40564a162656a81ef87683cf94299a8440dc64aa523a7f`.
Recovery commit `cd4765c46aba3d69eb2ba07f957b410860a9a902` was inspected as evidence,
not adopted wholesale: its different hook ID and object-closure changes are outside this narrow fix.
Only assigned paths were changed. No push, merge, deployment, activation or runtime approval occurred.

Historical artifacts were read from `/runtime/artifacts/<hash>.txt` and SHA-256 verified:

- `sha256:397eaeeaef6e4483009240704d77710f8e49de381ce791b8e0de0fff697ce338`,
  task `32c0a1a0-ddde-49a7-ab76-7f2dbfaa22d8`.
- `sha256:9f2775205b7ee225d0045550c82fdef8ee267ca0e571aefececc004427c582fa`,
  task `0f326328-d5ce-4539-801e-c430e73304a0`.

Both contain HTTP 400 `invalid_json_schema` at `properties.version` requiring `type`.
Original outbound request bytes and failing audit stages remain unverified.
Baseline-schema replay in `test_baseline_reconstruction_and_semantic_preservation` is a
reconstruction, not an exact original request. It reproduces five affected definitions.
Removing only newly added constant types recovers the exact baseline parsed schema, including
required fields, references, open object semantics, and additionalProperties restrictions.
All 21 constant nodes now have explicit integer or string types.

The shared adapter preflight runs before AppServer sends `turn/start` and before CodexRuntime
starts a process. It checks JSON Schema structure and missing explicit types on schema constants,
including nested definitions and combinators, but skips data in examples/annotations.
It does not mutate schemas or attempt comprehensive provider compatibility validation.
Failures include an actionable path and SHA-256 of sorted compact JSON (ASCII escaping enabled);
non-JSON inputs cannot have this JSON-content hash. No incident is automatically inferred from
prompt text. Existing execution-failure reporting is exercised; the confirmed version cause and
`codex-harness/research-audit/output-schema` scope remain unchanged under INV-RECURRENCE-001.
Other untyped constants have a separate diagnostic cause.

Lifecycle contract: [official Codex hooks documentation](https://learn.chatgpt.com/docs/hooks),
opened 2026-09-07, specifies SessionStart matching source and emitting
`hookSpecificOutput.additionalContext` as developer context. Installed `codex-cli 0.153.4`
startup passed. Static inspection of its bundled executable found serialized lifecycle fields
`session_id`, `cwd`, `hook_event_name`, `source`, and SessionStart/additionalContext identifiers.
This is contract/static evidence, not proof of native lifecycle execution. No native production
hook was installed or activated. Manifest reproduction is explicitly a constructed SessionStart
reminder fixture; historical provider failures are reproduced separately at the schema boundary.
Native fixtures cover startup/resume/clear/compact, malformed JSON values, wrong events and prompt-only
incident text. The reminder cannot inspect or repair outbound schemas.

Validation commands on the final implementation content:

- `uv run ruff check .`: exit 0, `All checks passed!`.
- `uv run pytest`: exit 0; 293 collected, **269 passed, 24 skipped**, 17.98 seconds.
  Integration services were not exercised by the skipped tests.
- Earlier targeted `uv run pytest tests/test_output_schema.py tests/test_native_hooks.py
  tests/test_executor_research.py tests/test_research_audits.py --capture=sys -q`:
  exit 0, 122 passed, 17.59 seconds.
- `git diff --check`: exit 0.

Tests exercise actual schema builders through mocked AppServer send / CLI process boundaries,
all referenced definitions, partition output, malformed schemas, unchanged reference/union schemas,
record parsing, rejection before transport, and failure preventing audit success. They are transport
fixtures, not provider acceptance. NativeHooks discovery, inactive exclusion, two independent incidents
with duplicate redelivery, stale approvals, authorization, activation failure and rollback exclusion
reuse incumbent use cases. The full suite also covers context overflow, stale writes and release failures.

Actual CLI canary records above bind the earlier candidate `992db51ee1778b993c7fa873d4196ae0eacfaa49`
and its tree. Both provider calls failed with a **different** HTTP 400: the pre-existing open
`SubsystemAnalysis.tests_not_run.items` object needs `additionalProperties: false` for this provider.
No returned records were available to validate; production recovery is unverified. The subsequent
partition-builder extraction changes no output schema bytes, but does not transfer a canary or approval
binding to the new candidate. A successful exact-release canary remains outstanding. Closing that object
would tighten accepted research records and requires a separately assessed semantic change; this patch
preserves the assigned research semantics. No canary failure is silently removed from evidence.
The canary prompt requested synthetic records without tools, source analysis, approvals or deployment.
Temporary schema filenames in argv have expired; immutable candidate sources and the hashes below
reconstruct the submitted schemas. Stdout/stderr are preserved verbatim as JSON strings above.

INV-RELEASE-001 still requires successful command inspection, independent lead then conductor review,
exact revision/tree and spec binding, passing incumbent release checks, and actual successful canaries.
No independent review was attempted or accepted here. If future inspection fails with bubblewrap namespace
creation denied, retain command evidence and report inspection-blocked; do not infer or alter host settings.
Hook rollback removes only the lifecycle component. Reverting the schema and adapter changes requires
release rollback; retain research evidence and approval bindings throughout.

Native spec digest: `80b386885f56e0b15c4ab34dbfa75a71859b2b6c966af5e8e03eef42ef479b95`; script SHA-256: `4630179b05ca0e255fbf95b21bc4af310d1bc655ded9547ff35e61928147f4ee`.

Research output schema SHA-256 values (domain canonical JSON, ensure_ascii=False):

```json
{
  "SourceIdentity": "e68c3f15e400e3b7540c37657ca90a2e225b5438b80ee6f18c20423478061130",
  "InventoryEntry": "1309e69245573406f22db8558b4aadf5a6893cee4f8b90caa0d3642647c9ea04",
  "PathDisposition": "e342a9ffa36c16cc10dd50fee14c6ddf116392d2b01c1656b8304caf4a18e9ae",
  "SubsystemAnalysis": "9a4a01f1dfdfe7f7236537cf84e721d2d4ba963ba8a13672e4dd4ce06f9dd689",
  "ExecutionReceipt": "2532f7020b7381f67e1475447bcf882599a618ebe7d613b1761f8562f8ccbe45",
  "PartitionCheckpoint": "53dff8bf629ce615cbd0ece53e61b4351ef6cc3c1af7c01f355df1074790d8bc",
  "AdaptationProposal": "cdae3d779a70cf5a0d54d72ea6ccd45482b84d875281df2f5cbbc4ed79ac2caa",
  "IndependentReview": "16fdd1a8a779e81a59991b468f0a7216843e4531ab018968e9a095acbab777ad",
  "partition": "b5bec56ca6ce86c42f2b28b60910e00dd717bc2743287d454eef1d0661ece110"
}
```

## Rework of rejected 444c8c82 — 2026-09-07

The preceding candidate narrative and failed canaries are historical evidence, not this
candidate's verification. This rework restores its typed constants, adapter preflight,
standalone SessionStart hook and regressions. It additionally projects a closed
`tests_not_run.items` object (required string fields `test`, `reason`, `follow_up`) in
both research output builders. This addresses the actual second provider rejection,
including unused definitions. The resource schema retains historical open-object
semantics; persisted evidence and extra historical metadata are not rewritten.
New generated entries cannot include arbitrary extra fields. This is an adapter output
constraint, consistent with the fields required by SubsystemAnalysis validation.

Source contracts checked against official documentation on 2026-09-07:
https://learn.chatgpt.com/docs/hooks and
https://developers.openai.com/api/docs/guides/structured-outputs .
The native hook remains a reminder: it cannot inspect outbound schemas. Its fixture
reproductions are constructed lifecycle inputs, not historical native event captures.
Schema boundary tests reconstruct the historical missing-type defect and open-object
rejection; neither fixture alone proves provider recovery or installed hook execution.

Run `uv run ruff check .`, `uv run pytest`, and `git diff --check` before committing.
Then run `uv run python scripts/verify_output_schema.py` on the clean candidate.
The script preserves exact argv, prompt, submitted schema, raw stdout/stderr, output,
validation outcome, CLI version and commit/tree in ignored workspace-local
`.runtime/schema-rework/<revision>/`. It never writes approvals or runtime records.
Do not commit later documentation and transfer the canary binding to that new revision.
The final task report supplies result counts and evidence hashes after execution.

Independent review, incumbent release-policy canaries, installed lifecycle execution,
production reliability benefit and service integration remain separate gates. A synthetic
provider record is not an actual independent review. Failed command inspection must be
reported inspection-blocked, retaining command evidence without changing host permissions.
Rollback removes the reminder and reverts output generation without changing stored records.

Current rework checks completed successfully: `uv run ruff check .` (exit 0),
`uv run pytest` (278 passed, 24 skipped, exit 0), `git diff --check` (exit 0).
A concurrent `--no-sync` run also passed 278 tests; it is not additional coverage.
The 24 integration skips leave service behavior unverified in this workspace.

## Assigned usage-limit containment — f3ff7591-e500-446d-9e2b-473f52bd2a02

Baseline: `c0954077dcce6008ddb66574248b6aa782a970a0`, initially clean.
Implementation candidate: `03b7ca3df130218bcc290504653c9fe9de8723fe`, tree
`9891bd65cebb8fd3ba5a7ac2be0d48a2220e2eb6`. The documentation commit containing
this section adds no implementation changes. The actual canary receipt described
below records its own exact final candidate revision/tree; approvals cannot be
transferred between revisions (INV-RELEASE-001). No push, merge or deployment.

Confirmed cause: `codex-provider-usage-limit-exceeded`; incident scope:
`worker:github/codex-turn`. Hash-verified the exact UTF-8 historical artifacts:

- `sha256:2b020dc9bfa2085c369c6b433d800dcc36ed4e4efdd8f49e405e163ebe06cc0c`
  — task `03de1041-2caf-4ffb-bf5f-e7b18cb5a9c0`, attempt 1.
- `sha256:3d8090132afcb28d3cfb26fbedeeb9233d103c7364625af1a01aa32d7c7739db`
  — task `2d2aa014-ba83-4001-b523-8b0e87ef80ac`, attempt 3.
- Associated diagnoses: `sha256:91a33020413af1f45037a9bb46a4037ebe422d043ba278ff87b9640e644213d6`
  and `sha256:ab5f1e66557a748f84541930e40de9292e37d4a27a89617a9fae6e33da41d170`.
- Assignment: `sha256:2417b466971c05b4f6f23923baaa018a7cbedc057ca1486e9e4044db033f7f24`;
  planning execution reference: `sha256:df4c83029ebe1298586d43903cd05a68288d78f49aa086fc5edd874d50f4ff99`.

The two receipts contain stringified provider errors with the exact code
`usageLimitExceeded`; reconstructed transport tests parse those fixture strings
only in tests. Production classification reads the structured `codexErrorInfo`
field of the current failed AppServer turn. Prompts, model answers, unrelated rate
limits, malformed codes and `invalid_json_schema` do not establish this cause.
Inspection-blocked takes precedence. Account identity, quota details, reset timezone
and quota recovery remain unverified. This work does not alter output schemas or
claim that the separate historical schema diagnosis has been resolved here.

`ExecutionFailure` carries runner evidence into application policy. `Workflow.fail`
with `retryable=False` persists terminal failure and attempt history, returning the
actual record. Task and decision writes check current owner, generation, status and
lease. Raw provider error, events, thread/turn, task/attempt, revision and immutable
execution reference are retained. The existing diagnostic route and six-W envelopes
remain in use. Duplicate assignment delivery and repeated polling cannot claim that
failed execution. A fresh authorized assignment is the recovery route after external
quota recovery; no attempts are reset and no account-wide block is inferred.

The standalone stdlib script is `harness_hooks/codex_usage_limit_guard.py`, exact
UTF-8 Git SHA-256 `7b4f09b09dd64453d5a0468cd84928bdff5bee99e8a1a03ca59354577886f8f4`.
Its assigned manifest is `harness_hooks/hook-ec928b6c78b06bb571eb45cb.json`.
SessionStart is only a reminder; deterministic containment belongs to the adapter
and application. Historical receipt fixtures deliberately produce no hook output:
they are not native lifecycle inputs. Native positive/negative inputs are separately
listed in `normal_case`. Existing NativeHooks proposal, canary, activation and rollback
mechanisms are reused without bypassing release approval.

Inspected `codex --version` (`codex-cli 0.153.4`), `codex app-server --help`, and
`codex app-server generate-json-schema --experimental --out .runtime/usage-limit/protocol`.
The installed schema exposes `usageLimitExceeded`, SessionStart and lifecycle completion
records. Generated schema SHA-256 values:

- `v2/TurnCompletedNotification.json`: `78af2a37391e8e669a4020cb58593e4d3e378756ced79d5fec72374fa69fb94b`.
- `v2/HookCompletedNotification.json`: `1f146d70303cea6e59752191179e36a273650d63a74d4f9338f9a399da6597d2`.
- `v2/HooksListResponse.json`: `891dd10ef7f78e59631fce05fff2becddb8004b3c0338dbbbd6b4f17ef1fa64f`.

The [official lifecycle contract](https://learn.chatgpt.com/docs/hooks), fetched
2026-09-07, documents SessionStart source matching and additional developer context.
Installed discovery/execution must still be verified; documentation alone is not a canary.

Validation: `uv run ruff check .` passed; `uv run pytest` passed with **323 passed,
25 skipped**; `git diff --check` passed. Observed-output summary (explicitly an excerpt,
not a full transcript): `.runtime/usage-limit/a8d9e65c0e34b2c54060319b0ce79a5ccaee2d9f1e7efccb7a4e46e09c431ae5.json`,
SHA-256 equal to its filename. Early incomplete dependency installation caused an
`idna.IDNAError` collection failure; a completed `uv` installation and subsequent
full run passed. An intermediate Ruff import-order error was corrected. Local tests
cover both historical reconstructions, malformed errors, duplicate delivery, distinct
tasks, prompt-only incident text, cleanup failure, generic retries, terminal attempt
history, stale writes, fresh authorization, context limits and native release failures.
The new PostgreSQL reconnect test and 24 existing service tests were skipped: durable
service behavior is not claimed verified by MemoryStore executor reconstruction.

Measured offline benefit: one provider submission for the confirmed failed execution,
then zero submissions across three additional polls and executor reconstruction;
terminal task identity remains unchanged on duplicate delivery. This is test evidence,
not a production observation. Production savings and quota recovery are unknown.

Actual installed lifecycle/canary execution uses the final Git bytes, CLI version,
existing AppServer hook discovery/trust mechanism, and a typed output schema whose
version has integer type and const=1. Its prompt asks only for developer-context
observation and prohibits tool use; it does not supply the reminder text. Raw events,
result or exception, exact revision/tree, schema hash, script hash, CLI version and
validation outcome are saved in `.runtime/usage-limit/canary.json` and an identical
content-addressed JSON file there. The final handoff supplies that immutable hash.
Read the receipt: this document does not predeclare a successful installed lifecycle.
A model answer or successful process exit without a matching lifecycle completion
record is insufficient. A provider rejection is a failed execution, not an accepted
canary. No automatic quota-failed retry is authorized or performed.

Release acceptance remains blocked pending successful actual canary evidence,
independent lead and conductor command inspections/reviews, and incumbent release
checks bound to the final revision. No independent review is claimed in this worker
implementation report. Bubblewrap namespace denial, if observed, is inspection-blocked;
retain the command evidence without changing permissions or asserting a host cause.
Hook rollback withdraws the lifecycle component using the existing mechanism. Adapter
and application rollback requires release rollback; preserve persisted failures and
immutable evidence. Nothing in this report authorizes quota purchases, account changes,
activation, push, merge or deployment.
