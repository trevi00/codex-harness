# Spec-driven development migration boundary

Pinned Baldrix source: `b9586c59c062457a45018e41c2e753934b5ca6c9`.
Destination inspected: `0548efaf1bc8833c750c80b242de03b5a73d7799`.
This is a gap analysis, not full SDD migration or deployment approval.
Immutable path/blob mapping and analysis:
`sha256:33f7447858a8d20a08af2291109f6b2a17db2a2500fef233ba8269f57c92422f`.

Fully read for this comparison: `templates/dev-pipeline.md`,
`skills/_pipeline/stages.core.yaml`, `scripts/lib/pipeline_stage_picker.py`,
`scripts/lib/pipeline_overlay.py`, and `scripts/lib/pipeline_gate_runner.py`.

| Capability | Evidence and current boundary |
| --- | --- |
| Stage definitions and stack overlays | Ten original YAML assets exist in resources/baldrix_pipeline with provenance hashes. project_pipeline loads and verifies them. |
| Stage and skill recommendation | domain/pipeline and project context select stages from committed output observations; these are recommendations with verified_complete=false. |
| Requirements/PRD -> design -> implementation -> verification | dev-pipeline describes generator/evaluator pairs and the OpenAPI/acceptance chain. Declarative stage data is retained; this does not execute the chain. |
| Stage gate enforcement | Upstream pipeline_gate_runner is explicitly a non-blocking advisory attestation logger. Its name does not imply gate execution. The upstream picker advances on output existence. Our recommendation code likewise grants no completion authority. |
| Spec/codegen and contract verification | greenfield_spec_emit.py and spec_bundle_emit.py are identified, not yet read in this review. Their dependencies, callers, test generation and runtime contract checks remain unverified. |
| Acceptance criteria tied to actual tests | No complete SDD acceptance-to-execution-to-stage-approval mapping was established in this component. General release tests do not substitute for that mapping. |

The template calls for verification before advancing; the inspected picker alone cannot
enforce that promise. Other explicit workflows may drive evaluators, and must be traced
before making a repository-wide conclusion. The supposedly neutral core also retains
some Java-specific outputs; stack applicability requires validation, not blind copying.

The next migration unit must trace spec emitters, reverse extraction, parser/stack
consumers, acceptance-test generators, actual caller activation and source tests. Preserve
the distinction between advisory routing and authoritative workflow progression.

Required Codex adaptation after source review:

1. Git-owned, versioned specification and AC identifiers, with generated output provenance.
2. Six-W assignments referencing the exact spec, stage and prerequisite evidence.
3. PostgreSQL stage runs binding generation, candidate revision and actual evaluator receipts.
4. Dependency-graph invalidation of downstream approvals when an upstream spec changes.
5. Script-executed build/contract/AC checks, followed by independent review and actual CLI
   release canary. File presence, a model's success statement or an advisory log cannot pass a gate.

This gap is required migration scope. It cannot be closed by importing YAML or renaming
existing plan/implement/review phases to SDD stages.
