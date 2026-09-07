# Baldrix pipeline recommendation migration

Source: trevi00/baldrix b9586c59c062457a45018e41c2e753934b5ca6c9.
Candidate source: domain/pipeline.py, adapters/project_pipeline.py and the existing
project_context -> Executor path. Ten original YAML files are preserved byte-for-byte
under resources/baldrix_pipeline, including legacy variants and skill lifecycle data.
provenance.json maps each source to its SHA-256. The user explicitly authorized migration
of their repository; no top-level LICENSE was found at this pin. This candidate does not
establish a general third-party redistribution license or source-adoption approval.

The picker/parser/overlay source and prompt consumer were traced. Java, Flutter and
Rust overlays reproduce the legacy consumer fields. The original parser discards reuse
and other unknown keys; golden comparisons use the actual consumer key set, while raw
assets keep all original fields. Schema values are native lists/string scalars instead
of the upstream parser's flow-string versus block-list distinction; both accepted input
forms are normalized for output/skill selection. Duplicate IDs and invalid shapes fail
explicitly instead of silently disabling the pipeline.

Project .harness/stages.yaml overrides defaults, including with an empty stage list.
Every configured stack gets its own recommendation; JavaScript/TypeScript map to the
Node overlay. This extends the original single-language picker. Overlay metadata,
including source_finder/testgen settings, is retained as data; test generation and
source-finder execution are not implemented by this component. Node/Dart contain IDs
(api-design, verification) absent from core and their own overrides; the resulting
ID-only recommendations explicitly carry incomplete_definition=true. No missing stage
body or successful gate result is fabricated. Languages without an overlay/variant use
the original default stages.yaml; its Java-specific text remains visible as an upstream
limitation until stack-specific definitions are supplied.

Output observation preserves the original ANY-output, last-observed-stage, optional
skip, final-index cap, literal-path and nonempty-src heuristics. It uses regular files
from the captured Git tree and inferred nonempty directories rather than working-tree
existence. .harness search roots supplement original .claude locations for migration.
Empty directories, untracked files, symlinks and submodules cannot supply observations.
Patterns such as migrations/*.sql remain literal, exactly as in the original picker;
free-text outputs are not parsed into invented commands or assertions. No gate executes.

The manifest contains full definitions' artifact references, merged selected stage,
output observations, language and overlay metadata. Compact stage/phase summaries enter
the required Executor context. Matching filenames receive the original +3 pipeline
boost, applied to eligible context-item priority; stack filtering remains authoritative.
Full prompt relevance scoring, forced-match/pointer tiers, body rendering and native
skill activation remain pending. This is pipeline recommendation integration, not the
full Baldrix skill matcher. Recovery is bound to the updated manifest digest.

Upstream tests: a combined run had 27 passes/3 failures because test_pipeline_yaml
leaves SKILLS_DIR bound to a deleted temporary directory. Four isolated source modules
passed 38 tests (picker, YAML, parser equivalence, Java/Flutter/Rust golden comparisons).
Both failed and successful runs are retained in immutable baseline
sha256:3156317ca30dbd8d04194402f886eb1e990222d465578396cc647f0f5897a12b.

Remaining full-scope work includes all pipeline gate/status consumers, lifecycle stage
execution, complete ranking/rendering, all skill/agent assets and remaining Baldrix
subsystems, then all oh-my-codex and Ouroboros. Component tests and Claude review do not
mean the full repository migration is complete or deployed.
