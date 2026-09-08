# Threshold review evidence prerequisites

Calculation version 2 preserves the pinned Baldrix proposal choice, but now includes
every finite, direction-allowed candidate considered when a proposal is emitted.
Each alternative records the training score/gain, whether it passed hysteresis, and
its replay report when that gate was actually run. An alternative filtered by training
has a null report; this must not be confused with a failed holdout gate. The selected
proposal explicitly names the source rule: greatest holdout improvement, raise-first
ties, or the last rejected candidate if none accepted. When no candidate passes
training, the source still emits no proposal. The recorded corpus remains available.

Both accepted and rejected alternatives survive in the immutable collection artifact.
The calculation-version bump changes proposal identity so old incomplete reports are
not silently reused as the new evidence format. No selection or activation policy
is relaxed; calculated rows still require native task-success and release review.

Additional executable checks now cover the prior review findings:

- Accepted and rejected reference calculations both retain the unconditional release
  blocker and false activation flags. Unsized evidence produces a rejected row with
  no suggested value and its explicit rejection blocker.
- A literal CRLF blob created with `git hash-object --no-filters` matches the loaded
  source after the existing Git subprocess/text-read normalization.
- An appended historical segment retains its exact complete source snapshot even
  after the projected event window drops early rows. Every retained row's original
  line hash and timestamp can be reproduced from that source artifact. A second
  source ID has a separate archive and collection record.
- Tied accepted alternatives, multiple rejected alternatives and training-filtered
  alternatives have distinct, inspectable evidence.

These are prerequisites for the next leased-review connection, not that connection
itself. Author identity, authoritative review dispatch, lead/conductor decision binding,
current-policy checks before apply, native performance criteria, release and rollback
remain pending. Earlier source-audit and cross-version observation-dedup gaps remain
open. See `baldrix-threshold-collection.md` for the existing collection boundary.

At runtime revision `d91fbcca5276d826736e5af8af1b61c4e5ee7cd4`, unchanged upstream
proposal execution again matched 300 seeded corpora and all 177 emitted proposals:
`sha256:e5f7b14f81868c7072b4cd2e9b951f86c131e98ce2caedf300e4ad547691d957`.
Actual collection CLI/PostgreSQL checks passed, including concurrent idempotence and
preserved source history, with the expanded alternative evidence:
`sha256:62856ffec471761d1261b8b05bcf0058d85011a131870306229494db0b66e72c`.
These used isolated synthetic observations; they do not measure real task improvement.

Verification for that runtime revision:

- Ruff passed. Windows PostgreSQL/Redis: 461 passed, 7 skipped;
  `sha256:bb3b2a6cdace331c81691d61667c0b01c299e5cc67b150fc10393232f4eb634d`.
- Linux PostgreSQL/Redis: 468 passed, no skips;
  `sha256:7a63b12155c6cdab17b6b9034878596457c49162568e093062e9ff11fad45d52`.
- Actual Codex CLI canary, with all 92 packaged source/config/lock files matched
  to the immutable image:
  `sha256:a1ad61a51438440f80536c535735f4fc67f1dd5927e58c0650b8ffa3ddb1ed83`.
- Actual Claude complete supplied-source review ACCEPT:
  `sha256:2a1945c51ce0949ab7cc0b0696ecf870db5bba1b271d1a5a12a9900b0f003e93`.

Remaining review findings to carry into the leased-review implementation: include
import parser version/cursor/counts in the immutable evidence so re-projection does
not depend on a live import row; expose native/reference budget differences explicitly;
include the Git comparison and legacy parser implementation in a broader provenance
receipt; evaluate admitted-event coverage, not merely nonzero admitted-entry count;
and expose a run-level blocker summary for consumers. Reference constants must remain
pinned for historical replay; native policy equality is not a substitute for the
required native performance evaluation. Source text binding is not whole-process
attestation. An artifact may survive a failed DB write and be reused on retry; CLI
output/transport failure after commit must be reconciled by its idempotent run key.

The next substantive integration is an explicitly scoped, leased lead/conductor
review workflow over calculated records. It must distinguish permission to investigate
or implement a candidate from activation approval, bind decisions to immutable input,
and reuse incumbent release checks for any eventual change. Do not reclassify these
calculation records as approved or dispatch source-adoption work without its audit.
