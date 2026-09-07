# Baldrix project profile and context routing

This component migrates `scripts/lib/tech_stack.py` and the eligibility portion of
`handlers/prompt/skill_match.py` at Baldrix b9586c59. It is not the entire matcher,
project onboarding pipeline, native skill installer or skill corpus migration.

## INV-PROJECT-001

Project definitions live in `.harness/tech-stack.yaml` and skill content in
`.harness/skills/`. The runtime reads both from the current task's Git revision.
Uncommitted edits do not silently change a resumed task. Selected bodies are retained
as immutable artifacts and passed through the incumbent context compiler as evidence;
budget overflow retains handles in the compiler's omitted list. This is context routing,
not a claim that Codex native skill activation or a PreToolUse hook was invoked.

Supported YAML includes the original stack/backend/frontend/mobile blocks and extensions,
or canonical `schema_version: '1'` plus a `stacks` list. These formats cannot be mixed.
A scalar-preserving YAML loader keeps versions such as 3.10 unchanged, rejects duplicate
keys, and does not instantiate application objects. Invalid profiles fail explicitly;
missing profiles permit common skills only, never an all-skills recursive fallback.

Eligibility preserves specific-to-general candidates and language-major variants. Only
immediate Markdown files in an eligible directory are selected; packaged child SKILL.md
files are also selected within common, explicit extension, or specific stack directories.
A language fallback directory does not recursively activate sibling frameworks.
Git symlinks/submodules cannot masquerade as selected profiles or skills.

## Initialize and inspect

From the configured harness Python environment:

```
python scripts/project_init.py PROJECT_ROOT --config profile.yaml
python scripts/project_init.py PROJECT_ROOT --from-claude
```

Both forms create a new `.harness/tech-stack.yaml` exclusively; an existing definition
is never overwritten. Commit it and the selected skill files in the target project.
The actual Executor `_run` loads the selection for its cwd and basis revision; its
context records a manifest reference and count. Deterministic stack discovery, original
pipeline stage selection/scoring, global skill installation and the rest of Baldrix
remain required subsequent work, not implicitly completed by this component.

## Source trace and validation scope

Source `load_tech_stack` yields candidates; `collect_skill_files` consumes them; the
original prompt handler then performs phase/pipeline scoring and rendering. Those
later stages are distinct. The original fallback scans every skill subtree when the
profile is absent; our explicit common-only behavior implements the user's requirement
that a project select only relevant skills. This behavior change is deliberate.

Automated checks cover legacy multi-stack input, scalar spelling, extension traversal,
invalid/duplicate YAML, packaged skill selection, non-overwriting init, committed-vs-dirty
configuration, Git symlink mode, and the actual Executor/compiler input with an instrumented
runtime. That runtime test is not an actual Codex invocation. Claude review and actual
candidate CLI canary are retained separately before any activation.

## Claude review corrections

Initial source review at 4fffd5c was conditionally accepted with required fixes:
`sha256:04d7a4560cf5d460ac7998630daf6213ff5ac9e144184dd4dd43d8a88f4e3cd6`.

The follow-up rejects unsupported explicit YAML tags, classifies excessive nesting,
adds selected/included/omitted counts and actionable manifest/body file handles, and
prioritizes selected skill content above the already-externalized raw task evidence.
Counts reserve their maximum encoded width before compilation and are finalized with
the shared packet seal, without increasing the context byte budget.

Explicit `--from-claude` import now retains fields such as database, ORM, cache and
per-stack annotations under canonical profile metadata. Blocks without language are
preserved as unmapped metadata rather than invented language selections. This follows
the actual `skills/_common/tech-stack-template.yaml` in Baldrix, which contains these
extra fields. The original legacy file remains untouched. Native canonical profiles
remain strict about unknown fields; use metadata for additional context.

Root resolution and skill-manifest-bound session recovery prevent subdirectory scope
mismatch and reuse of stale skills after a committed stack change or removal. Tests
also cover selected-skill symlink mode, CLI legacy import, metadata preservation,
expected CLI errors, and real-sized budget overflow. The standard no-profile path is
covered by existing Executor regressions and explicit profile-removal continuation.

Original tech-stack and scan-root tests were run unchanged in a read-only, networkless
container: 25 passed, receipt
`sha256:b4181f5fe5ba43f3bf39376c190657588076ed0a0f3f356aafbfb37bd5d65cf5`.
