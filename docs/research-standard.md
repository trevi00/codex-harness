# Reference analysis and adoption contract

This applies to the user's Claude harness repositories and every later open-source candidate.
Discovery feeds, README excerpts and Context7 answers identify work; they cannot authorize adoption.

## Sources of truth

Pin the repository URL, commit and tree. Inventory **every tracked path**, including hidden configuration,
CI, scripts, tests, generated files, dependency locks, submodules and runtime fixtures. Record a blob ID
and size for each path. Preserve binary/submodule/unsupported entries explicitly; do not silently omit
them. A moving branch or a checkout with unknown modifications is not commit-bound evidence.

Trace each subsystem from declared contract through entry point, call sites, state transitions,
storage authority, failure handling and tests. Documentation describes intended behavior; code and
effective configuration establish implemented behavior; recorded executions establish observed behavior.
Resolve contradictions explicitly. GraphRAG and summaries are derived indexes, never replacements for
these sources. Search hits and generated inventories do not establish semantic review coverage.

## Required review records

Each path has an explicit disposition: unreviewed, semantically reviewed, generated/duplicate with
justification and generator/original link, binary inspected with method, or unavailable/unsupported.
Subsystem records link the paths and symbols, declarations, tests, execution receipts and open questions.
Tests that were not run say **not run**, with a reason and the required follow-up. Isolate upstream code
before execution; do not run foreign installation scripts against the user's active harness or Chrome.

A repository-wide completion claim requires every path and subsystem to be accounted for, with no
unreviewed or unavailable scope. A narrower component finding must label its scope and remaining work;
it cannot inherit a repository-wide completion label. Large repositories use persisted work partitions,
bounded reads and session continuation until coverage is complete.

## Adoption decision

For each proposal record the immutable source and reviewed scope; concrete evidence paths/symbols;
the behavior and failure modes being adopted; license and dependency constraints; contradictions;
overlap with our existing implementation; adaptation to hexagonal boundaries, six-W messages,
PostgreSQL/Git SSOT and ontology/topology; and the reason to adopt, adapt, defer or reject.

The research lead independently checks these records. The conductor binds approval to the source
revision and our current revision, checking SRE/architecture criteria and graph impact. Missing or
changed evidence invalidates the approval. A declaration of completion from the proposing model alone
does not satisfy the gate. GitHub and GeekNews proposals follow the same standard.

Implementation then follows lead review, independent conductor review, exact-revision tests, actual
Codex CLI canary, promotion and rollback monitoring. An upstream feature is not considered incorporated
until that chain has passed. Preserve attribution and validation limitations in the resulting PR.

## Implemented lifecycle and verification boundary

Both feeds retain discovery-only records. The scheduler queues a primary-repository mapping task;
non-repository links with no justified mapping remain explicitly unmapped. Mapping is provisional,
never approval. Canonical GitHub URLs and exact commits are acquired into dedicated bare repositories.
No upstream checkout, hooks or installation scripts execute during acquisition. The object verifier
reconciles every raw path, mode, object ID and original byte envelope against the pinned tree.

Git-backed backlog seeds preserve historical `reference_audits`. Their imports do not claim review.
The scheduler queues acquisition in priority order, then bounded path and subsystem partitions.
Generation-specific schedule records deduplicate dispatch; a running predecessor prevents overlapping
continuations. Checkpoints preserve evidence history and reconcile all remaining work under task and
partition fencing. Context overflow uses immutable artifact handles and the existing executor handoff;
inspection planning and semantic analysis have separate evidence-bound session stages.

The configured runner creates execution receipts directly from process results. Immutable object
inspection uses bounded inert reads. Ordinary commands use PostgreSQL infrastructure requests tied to
the assigned source, task generation and lease; the host supervisor executes them in a separate Docker
container using the active deployment's immutable image. Source agents receive neither a Docker socket
nor host credentials. Only an ephemeral read-only source copy is mounted, with no network, dropped
capabilities, a read-only root, bounded scratch space, process/memory/CPU limits and an in-container
deadline. Runtime limits live in domain/policy.py. Output tails are bounded and their limit is recorded.
Rollback, changed deployment or stale task authority cancels result consumption while retaining evidence.

This is an explicit host execution backend, not a retry of a denied nested namespace with weaker
flags. The original bubblewrap adapter remains available for standalone inspection; denied isolation
still produces blocked evidence. Symlinks remain inert regular files; gitlinks, unsupported host paths
and missing upstream dependencies remain explicit gaps. Commands requiring source-tree writes can fail
in the read-only tree. No unavailable or failed execution establishes complete audit scope.

Subsystem `tests` records executed tests as JSON strings encoding exact argv arrays, matched to
successful command-execution receipts. Descriptive test names without execution belong verbatim in
`tests_not_run` with a reason and follow-up. Inert source listing/reading never establishes test
execution. Result consumption rechecks task authority, activation and deployment after completion.

Completed coverage and resolved partition questions permit adaptation proposals. Independent research
lead and conductor decisions use separate fenced leases and successful command inspection. Their
bindings include the source, coverage, referenced execution receipts, proposal, current deployed
revision/policy and Git-tree/organization graph identity. Model verdicts cannot create runner receipt
authority. Approval is revalidated at scheduling, workflow submission, claim and executor dispatch;
executor dispatch and eligibility also re-read original and transitive artifact bytes. Changed evidence,
review inspections, provenance, revision, graph or policy invalidates eligibility.

The Git `audit-lifecycle.json` definition identifies candidates supporting this lifecycle. Activation
occurs only through existing independently reviewed release promotion with passing incumbent tests,
CLI startup and actual CLI file-task checks. It does not bypass the release pipeline. Rollback pauses
audit scheduling and adoption dispatch while retaining runtime evidence and legacy records. Ordinary
incident work continues through its existing path. No deployment or activation was performed as part
of implementing this change.

Local fixture tests exercise the positive approval path and rollback. They are not independent Codex
reviews, actual upstream executions or production canaries. See `audit-lifecycle-review-evidence.md`
for this candidate's executed checks and unresolved verification work. Existing reference notes remain
limited-scope; no repository is newly designated fully analyzed or incorporated.
