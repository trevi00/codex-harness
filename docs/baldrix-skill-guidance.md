# Baldrix skill guidance and cross-reference migration

Source: trevi00/baldrix b9586c59c062457a45018e41c2e753934b5ca6c9,
scripts/lib/phase_detector.py and skill_match_render.py, traced through the prompt
handler's phase union, reference and guidance rendering calls. Original phase signals,
strict-design signals, phase prose and sensor reminders are preserved via AST extraction.

The project_context -> Executor path adds a provenance-bearing advisory item containing
objective/pipeline phases, guidance, strict-design intent, sensor reminders and tool
hints. Strict-design intent is a flag, not automatic debate invocation. Unlike the old
hook's early exit without matches, configured projects can receive guidance without
annotated matches. Original tool-trigger arrays are retained; Claude Glob/Grep/Read/Edit
names are replaced by available workspace search/reader/shell/patch actions. The renderer
executes no commands and grants no permission to bypass read-only tasks.

Requires references start from ranked matches including external pointers, and select
only already stack-eligible records. Resolution is one hop. Bare names prefer the origin
directory, then language, then common skills; common origins can use a unique eligible
skill in another stack. Explicit skill-root-relative paths and packaged SKILL.md names
are supported. Ambiguous, invalid and unavailable names remain explicit unresolved
evidence. Already matched targets are not duplicated; the first ranked origin owns a
shared target. References hold exact content refs/file handles and three keywords, never
target bodies or new eligibility grants.

Complete guidance is stored in an immutable artifact referenced by the skill manifest.
Inline advice has at most eight references and 6000 UTF-8 bytes; excess references and
unresolved entries remain behind its handle. Advice items are excluded from skill
selected/included/omitted counts. The final compiler still bounds the entire prompt.
Changed metadata/objectives change the manifest and existing session recovery binding.

A previous budget regression fixture contained question marks in place of the Korean
decision-tree heading after shell encoding. This change restores the real heading with
a UTF-8 patch. Prior records are retained; fresh Unicode-safe parity checks supersede
them for Korean behavior claims.

Remaining scope: historical thin-skill advisories and runtime event production, threshold
tuning/calibration, native skill/debate invocation, all remaining Baldrix assets and
subsystems, then all OMC and Ouroboros. Component review is not source-adoption approval,
deployment or repository-wide migration completion.
