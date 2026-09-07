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

The configured runner creates execution receipts directly from process results. It mounts only a
read-only source copy plus system executables in a networkless bubblewrap namespace, with temporary
scratch space. Symlinks and gitlinks are inert; this limitation is recorded in every receipt. The
container installs bubblewrap without adding privileges. Missing isolation, namespace denial and
command failure preserve command/output evidence and cannot support accepted independent reviews.
The environment revision fingerprints runner configuration and platform, not a reproducible dependency
image; upstream tests needing other dependencies must remain explicitly not run. Gitlinks still require
separate audits and cannot currently close parent path coverage. These limitations never count as
complete audit scope.

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
