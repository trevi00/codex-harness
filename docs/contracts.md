# Contracts — authoritative definitions

| ID | Contract |
|---|---|
| INV-MESSAGE-001 | All messages are six-W JSON. IDs cannot identify two payloads. DB commit precedes ACK; delivery is at-least-once. Reports match durable completed executions. |
| INV-RECURRENCE-001 | Two independent occurrences with the same confirmed cause/scope require a hook. Redelivery is not recurrence. Active-hook recurrence requires a version update while preserving the previous verified version. |
| INV-CONTEXT-001 | Required role, goal, acceptance, policy and provenance are never silently truncated. UTF-8 bytes are a conservative composition budget, distinct from measured tokens. External evidence is bounded data. |
| INV-RELEASE-001 | Exact commit/tree and incumbent policy bind lead review, conductor review, incumbent tests and actual CLI canaries. Failed checks cannot promote. Changed commits require new approvals. |
| INV-SESSION-001 | Current context at 70% requests safe-point handoff. Checkpoint generation and execution lease fence stale writers. Busy agents do not hibernate; identity survives replacement. |
| INV-GRAPH-001 | Git owns definitions; PostgreSQL owns runtime facts. Graph/vectors are versioned derived views. Unchanged symbols retain IDs; stale evidence cannot enter commit-bound review. |
| INV-RECOVERY-001 | An external host controller restores the previous deployment without Codex. Images are pinned; rollback withdraws that release's hook. Destructive schema downgrade is outside this contract. |
| INV-RESOURCE-001 | Runtime limits have one definition in domain/policy.py. Collection retains pending messages, referenced artifacts and transitive evidence; only aged unreferenced artifacts are removed. |

Comments cite invariant IDs and explain non-obvious local reasons, without duplicating policy definitions.
Organization SSOT: `src/codex_harness/resources/organization.json`.
Wire schema SSOT: `src/codex_harness/resources/message.schema.json`.
Runtime policy SSOT: `src/codex_harness/domain/policy.py`.
The trusted local-process identity boundary is documented in status.md; validation is not authentication.

## Research enforcement stage

| ID | Contract |
|---|---|
| INV-RESEARCH-001 | Discovery and historical inventory never imply semantic review. Versioned imports preserve original reference records. Source verification reconciles every raw Git path and object against the pinned commit/tree, not just a manifest hash. |
| INV-RESEARCH-002 | Partition scope is immutable. Checkpoints require an authorized assigned task, current lease and task/partition generations; evidence history and continuation outbox writes commit atomically. Remaining work reconciles with recorded evidence. |
| INV-RESEARCH-003 | Model-authored receipt IDs are not runner evidence. Missing execution, binary inspection or unresolved subsystem work cannot establish completion. Record tests not run with reasons and follow-up. |
| INV-RESEARCH-004 | Both discovery feeds and legacy approvals lack adoption authority. Positive eligibility requires complete coverage and ordered independent reviews bound to source/evidence/proposal, deployed revision/policy and graph. Revalidate approval and immutable bytes before execution. Verified release activation enables dispatch; rollback pauses it without deleting evidence. |

Audit wire schema: `src/codex_harness/resources/research.schema.json`.
Dormant seed definitions: `src/codex_harness/resources/research-backlog.json`.
Remaining integration work is explicit in `docs/research-standard.md`; these invariant definitions
must not be read as evidence that pending execution or rollout integrations exist.

## Bounded conductor measurements

| ID | Contract |
|---|---|
| INV-METRIC-001 | Git versions metric populations and formulas; PostgreSQL retains observations bound to immutable inputs and repository revision. Retries retain failed attempt outcomes. Missing, invalid, stale, future or insufficient evidence is unknown. Undefined targets remain observational. Measurements never authorize promotion or replace independent reviews and actual CLI canaries. |

## Reverse workflow progress

| ID | Contract |
|---|---|
| INV-REVERSE-001 | Reverse-stage records bind source repository, commit, tree and retained artifacts. Unknown or dirty source cannot authorize continuation. Requests are idempotent and generation-fenced; complete predecessors are required; explicit rebaseline preserves prior history. Component integrity is not source-adoption, semantic-quality or deployment approval. See baldrix-reverse-progress.md for remaining integration scope. |

## Project context routing

| ID | Contract |
|---|---|
| INV-PROJECT-001 | Git-pinned project YAML controls eligible skill paths. Missing configuration permits common skills only; invalid profiles fail explicitly. Selected regular Git files receive immutable content references and pass through the bounded context compiler. Initialization never overwrites an existing project definition. See baldrix-project-routing.md for scope and outstanding full-migration work. |


## INV-PIPELINE-001

Pipeline output presence is a recommendation signal, not a workflow completion or
approval. Definitions and observed project paths are bound to Git revisions; bundled
upstream assets retain hashes and source provenance. Dirty/untracked outputs cannot
advance recommendations. Pipeline priority cannot include a stack-ineligible skill.
Full recommendation evidence lives in the project-skill manifest, whose digest also
invalidates recovery after definition/output changes. Gate commands are inert data.


## INV-SKILL-001

Prompt relevance and pipeline boosts are recorded separately. A pipeline-only match
cannot satisfy the full-body score threshold. Annotated skill content uses bounded
full-body/pointer tiers; complete bytes remain in immutable artifacts. Pattern evidence
comes only from regular files at the captured Git revision, never host paths or dirty
files. Prompt identity is part of the skill manifest and session recovery binding.

Cross-skill references are advisory one-hop links within the eligible inventory; they
cannot activate an excluded stack. Ambiguous/unavailable names remain explicit. Full
reference evidence survives advisory truncation via immutable handles, and non-skill
guidance never inflates selected/included/omitted skill counters.

## INV-SKILL-HISTORY-001

Skill-history observations are project/content-bound compiled selections, never success
attestations. Retry delivery cannot add samples, including after hot-window eviction.
Leased writes require current task ownership in the same transaction. A task excludes
its own observation from historical assessment. Advisory text and its full skill body
are included or omitted atomically; assessment provenance binds session recovery.
# INV-SKILL-IMPORT-001

Legacy skill telemetry imports bind exact raw bytes to a project/source segment and
advance only a validated append-only prefix. Replays do not add observations; changed
committed prefixes fail. Historical timestamps and unknown content versions are not
replaced with import time or current skill identity. Imported archives do not mutate
live history or become authority to activate skills, hooks, thresholds or releases.
