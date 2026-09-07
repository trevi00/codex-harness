# Baldrix skill ranking and body/pointer routing

Pinned source: trevi00/baldrix b9586c59c062457a45018e41c2e753934b5ca6c9.
Source symbols are in scripts/lib/skill_score.py, frontmatter.py, frontmatter_norm.py,
skill_token_budget.py and handlers/prompt/skill_match.py. Source ownership and explicit
user migration authorization are recorded with the existing pipeline provenance.
The domain functions were extracted from the pinned AST with docstrings/comments
removed; score_skill replaces host reads with supplied cache values and validates
min_score. The adapter owns Git reads and frontmatter parsing. No new dependencies.

Intent-before-keyword concept dedup, ASCII boundaries, Korean >=3-syllable stems,
longest-first keyword overlap checks, seven high-frequency intents, contiguous path
segments/basename stems and per-file pattern scores retain the original algorithm.
The high-frequency vocabulary is the upstream pinned corpus default, not a newly
measured vocabulary for our still-incomplete skill corpus. Path mentions remain text
signals; only pattern contents require committed evidence. At most 64 mentioned files
are inspected, each regular Git file <=1 MiB with a 3000-character prefix. Absolute,
parent-traversal, symlink, untracked and large-file reads never reach host contents.

Actual Executor passes its objective into project_context. Annotated eligible skills
are scored, with pipeline +3 recorded separately. Full-body eligibility uses base score
>=3, top three, shared 4000 characters and 3000 per body. Decision-tree/Gotchas reduction
and explicit truncation markers retain original intent. Post-allocation per-body fitting
also bounds oversized sections (the original post-cap path could leave a large section).
Up to eight weak/pipeline-only pointers enter the context with immutable body handles.
Additional pointers and unmatched eligible records stay in the external manifest with
explicit tier labels. Budget-dropped strong matches become pointers, instead of silently
vanishing. Full source body hashes survive all reductions. The final Executor compiler
still enforces the independent UTF-8 byte budget and recovery reserve.

Compatibility: existing explicit project skills without frontmatter remain in their
previous unranked compiler path, labeled legacy, and are not counted in the annotated
4000-character pool. This preserves earlier project routing; new Baldrix metadata skills
use the ranked path. The outer compiler remains the hard total prompt bound. Direct
project_context calls without an objective remain snapshot/introspection calls; actual
Executor calls always supply an objective. Duplicate/malformed metadata fails explicitly;
flat string fields follow upstream conventions, not full nested YAML. Existing project
stack filtering remains authoritative. Full prompt identity and pattern references live
in the manifest, invalidating session recovery when objective/evidence changes.

This component covers score calculation and body/pointer tiers, not every renderer or
consumer. Cross-skill requires recommendations, phase guidance, Codex tool hints, sensor
reminders, thin-skill historical advisories, runtime threshold tuning/calibration, all
skill assets and the rest of Baldrix remain open before OMC and Ouroboros. No full source
migration or production activation claim follows from component acceptance.
