# Progressive model handoff

The user's revised procedure is a behavioral transfer workflow, not a model table:

1. Astra performs the scoped task and records the reference behavior and acceptance criteria.
2. Sol encodes that behavior in scripts, contracts and guardrails, then performs the same task.
3. After Sol's behavior is verified, its working procedure is packaged with guardrails for Terra.
4. Terra performs the task under those guardrails and must pass the same acceptance criteria.
5. Astra reviews the evidence at the boundaries and the final result.

Equivalent behavior means the same required outcomes and failure handling, not identical prose.
The first pilot is exact-reference artifact inspection: integrity verification, JSON field
selection, bounded serialized output and explicit continuation. Deterministic checks should
run as scripts rather than asking another model to repeat a mechanical check.

A transfer must be scoped to a versioned task contract and implementation revision. Its evidence
must retain input references, the Astra reference run, the Sol guardrail revision and execution,
the Terra guardrail revision and execution, and independent verification results. Successful
cases alone are insufficient: missing/tampered evidence, malformed inputs, budget overflow and
ambiguous results need explicit expected behavior. Cached and uncached input counters, output,
latency and successful completion should be compared under the same workload; model identity
alone is not evidence of efficiency or equivalence.

Changing the contract, relevant code, tools or model invalidates the affected transfer evidence.
An unqualified task starts at Astra. A failed Terra transfer returns to the qualified Sol stage;
an unqualified or failed Sol stage returns to Astra. Repeating a failure should repair and
version the guardrail, then rerun its checks, rather than silently retrying the same lower model.
These transitions must preserve the existing task lease, approval and release boundaries.

Implementation status: the artifact reader is the first guardrail pilot. Its real-model smoke
runs, when recorded, demonstrate only their narrow fixture. They do not certify an entire
model or authorize general downward routing. The existing static model selector does **not**
implement a qualification registry or enforce these promotion/fallback gates. Those runtime
gates and broader held-out evaluations remain required before autonomous model transfer is
treated as complete. The migration PR remains a draft and is not deployed by this pilot.

Validation on 2026-09-08: an actual Docker Codex CLI pilot ran the Astra reference,
then guarded Sol, then guarded Terra. Each stage extracted a fresh nonce from a
1,048,654-character artifact and rejected deliberately mismatched evidence. The driver
required the predecessor's passing receipt; Terra also required the same guardrail source
hashes and image as Sol. Sol and Terra each returned 299 characters for the projection and
60 for the rejection. These are reader output sizes, not measured token or cost savings.
The reader argv was generated inside the execution image and invoked from the canary cwd.
Ruff passed; the Windows/PostgreSQL/Redis suite reported 539 passed and 7 skipped.
Actual Claude CLI supplied-source review returned structured ACCEPT with residual findings;
it did not run the tests. Astra reviewed the retained execution and validation evidence.
Immutable bundle, including validation driver sources:
`sha256:718b9bc6b74b1b3fa78b9ce577644b74585c2af47ebda040550526e4fc4186d1`.

The live pilot covers one valid projection and one integrity failure per model; the wider
paging/malformed-input cases are deterministic tests. It is not a held-out task-family
qualification. Remaining reader limitations include whole-input memory use, possible index
page failure at tight budgets with long pointers, and raw file/tool access outside the reader
cap. The qualification registry and automatic escalation remain unimplemented.
