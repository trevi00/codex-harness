# Native routing comparison beside Baldrix reference metrics

Source basis remains Baldrix `b9586c59c062457a45018e41c2e753934b5ca6c9`:
`scripts/handlers/prompt/skill_match.py` admits on base score, while
`scripts/lib/calibration/threshold_metrics.py` evaluates recorded total scores and
raw body sizes. Earlier source execution evidence is retained in the threshold
replay/proposal/runtime-threshold documents. This increment adds a native adaptation;
the pinned historical arithmetic and its known deficiencies are not relabeled.

`domain/skill_admission.py` now owns full-body admission and budgeting for both live
routing and comparison. It ranks by total score/path, admits by base score, caps top
three and per-body size, then applies the same shared body budget reduction. Live
manifests identify this model, retain eligibility for every metadata-bearing skill,
and hash each emitted full body. Full inventory is used, rather than the five-entry
history projection; unmatched and legacy paths retain their distinct meaning.

`adapters/native_routing_replay.py` loads immutable manifests and eligible body
artifacts. It validates identity uniqueness, scores/boost consistency, eligibility,
model and budget compatibility. It first reconstructs the observed threshold and
requires exact emitted body hashes, count and truncation status to match the stored
baseline. Only then does it compare current and proposed thresholds using those
same complete inputs. Missing, corrupted, old-model or nonreproducible evidence is
reported unavailable rather than counted as a successful replay. Repeated manifest
reads are cached within one evaluation; repeated events remain distinct observations,
not proof of statistically independent samples.

Review follow-up: the first committed comparison is reused for an identical input
basis (project, full policy, corpus, source identity, sample floor and evaluator mode).
This prevents later artifact loss or restoration from silently creating duplicate
proposal runs. Concurrent collectors resolve to the first committed run. A new
policy/corpus basis is required for reevaluation; an explicit refresh API remains
future work. Reuse returns the retained historical result, not a fresh integrity
check of all transitive files. Review/execution must still obtain the required evidence.
Distinct manifests are archived once and event-indexed observations reference them.
Reports expose complete/partial/unavailable status and distinct-manifest counts;
incomplete evaluation adds a blocker. Body reads hash/decode once per bounded read.

The collection CLI supplies this evaluator to the application use case and archives
the result in the same immutable corpus document as the reference proposals. Embedded
callers without an evaluator explicitly record unavailability. This is an optional
comparison port, not an alternative source of approval. The source-binding list now
includes the shared selector and replay adapter (24 files); broader import closure
and project-input provenance remain pending.

Limits: replay freezes matching scores and eligible inventory from the captured
manifest. It does not rerun matching against new prompts, changed skills or pipeline
definitions. It measures full-body selection and character pressure; legacy bodies,
pointers, guidance, history advisories and final context compilation are excluded.
It is not a task-success metric or release check. Current-policy calculation and
old-manifest replay can coexist only if the recorded admission model/budgets reproduce.
All reports and calculated rows retain false activation flags and the mandatory
native-task-success/release blocker. Historical events without native manifests are
explicitly unavailable. Automatic implementation/apply and full migration remain open.

Tests route actual bodies before replay, including a boost-only relevance mismatch,
body reduction and budget omission. They compare actual emitted hashes, lower/higher
thresholds and empty selection; missing bodies, altered hashes, incompatible models,
duplicate identities and eligibility changes cannot count as successful replay. The
actual collection CLI test archives native comparisons alongside reference proposals.

Claude accepted runtime `55cebf9b7c09809a34de19bd65d22c77c167ea09`
(`sha256:4fe0db0a00ef579fe93e2f67147cd2c301d1be83edccc269cc3be2a9e1d94efc`).
Remaining findings: structured reasons must distinguish missing evidence, incompatible
models and baseline mismatches; an explicit reevaluation round is needed when the
first retained evaluation was unavailable (for example, a wrong artifact root).
Input identity includes manifest references through the corpus, but intentionally not
the host artifact-root path. Current immutability also preserves unavailable results.
Complete means reproduction coverage, not independent/diverse observations or quality.
The emitted hashes are from the selector before guidance/history wrapping and final
context composition. Upstream project/pipeline constructors remain outside the source
binding list and materially influence selection inputs. A budget-algorithm fingerprint
and bounded manifest read remain follow-up work; the model label must change with
incompatible selection semantics. These limits continue to prohibit activation claims.

Runtime verification at that revision: Ruff passed; Windows PostgreSQL/Redis had
503 passing tests and 7 skipped (`sha256:3de72b0b6879ee76bd631a9b7039d0dd6fdb158e32511116ca2fa820feeead03`);
Linux had 510 passing tests (`sha256:94b304af7904e3615798060012412e07dbe3c44245bad20fbff5c511307ad793`).
Actual Codex CLI canary passed after all 98 packaged source/config/lock files matched
the immutable image (`sha256:47e026d9c456326e6da2aacb55e90cd6dfdf7b010a9592b91b51279ec6658c8f`).
An actual Git project_context -> collection CLI -> PostgreSQL canary reproduced all
40 repeated synthetic observations (`sha256:96b5d869c9e528efac9c330bcaa3fa2bafd82f96506dfb2b5df549e786fdfe75`).
It used one distinct manifest, not 40 independent workloads; no model-quality or
production deployment claim follows from these checks.
