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

## Current enforcement boundary

These repository instructions govern current work. The deployed research adapter currently pins and
fetches a README; it does **not yet enforce this full evidence contract in code**. Strengthening the
automated gate is required work, not a completed capability. Existing reference notes remain explicitly
limited-scope until replaced by reviewed coverage records.
