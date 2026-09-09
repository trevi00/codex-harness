# Consolidated reference and execution-budget correction

This candidate preserves the occurrence-provenance implementation and its original
limited coverage from candidate `64070b115893172f634197ca442df9da8990bce4`.
It addresses the independent rejection of `6da57c81856d058a36f67a14d464b74b443390ef`.
No historical rejection, cancelled task, incomplete scan, or skipped integration
test is reclassified as success.

The source reviewer reproduced a mismatched nested delimiter that hid duplicate
keys. A deterministic enumeration of all 1,364 delimiter strings of length one
through five also found 446 missing-reference outcomes in the narrower rework
`b42e0955e3ecf12e54fd4190b6b310a16f44a544`. The consolidated classifier validates
completed outer JSON objects and retains references in recognized unclosed ones.
Every enumerated ambiguous reference remains visible in the corrected version.
The former clipped-output expectation was strengthened: an unfinished JSON object
cannot establish unique keys, even if an early image field looks complete.

Actual existing-blob retention and tombstone fencing still inspect original bytes,
independently of semantic classification or occurrence projection. Occurrence
attestations remain exact, reviewed source data; arbitrary copied summaries remain
unresolved rather than receiving a global digest exemption.

The runtime additionally grants at most 300 seconds for observed tool waits across
one turn. Only matching thread/turn tool events receive that shared allowance.
Repeated starts and new tools do not reset it; idle time and foreign/unattributed
events receive none. The hard bound is the original turn budget plus that allowance.
Protocol regressions verify completion after a slow tool, no idle allowance, shared
credit, and timeout for a hung tool. Independent review still owns source and focused
negative-control inspection; the host ReleaseRunner owns full integration suites.

Three isolated historical test inputs were recovered from their exact completed
commands through non-executing AST string evaluation and matching SHA-256 values.
Recovery receipt: `sha256:2c6f7dee81dc657f345ddb28dfa9cc05c51becd86eb0ff3493aa2064fde8c4de`.
These recoveries do not change the original failed test outcomes. Repeated-character
test identifiers were not materialized as counterfeit artifacts.

Known reconciliation is not a complete production graph traversal. Collection
must stay paused until the final candidate passes that separate host check and all
artifact writers converge. Independent lead/conductor reviews and fresh actual
incumbent/candidate integration plus CLI canaries remain mandatory for release.
Unreviewed upstream migration scope is unchanged.

The later independent rejection of b42e095 also identified malformed prefixes
that disabled key tracking. Object frames now track observed keys even after a
malformed prefix, while empty source braces do not capture unrelated receipts.
Ten new raw/enveloped cases include an early closing brace. Diagnostic image
field fragments no longer establish OCI semantics merely from a nearby context
key; complete receipt decoding remains available. The provenance candidate
64070b1 itself passed both independent reviews; that acceptance is not an approval
of this combined candidate or a claim that its seven unresolved parents closed.
