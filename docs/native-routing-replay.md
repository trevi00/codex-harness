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
