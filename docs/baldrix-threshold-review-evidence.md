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
