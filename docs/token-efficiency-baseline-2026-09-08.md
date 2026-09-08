# Token efficiency baseline

At 11:16 KST on 2026-09-08, the production snapshot recorded 65 queued tasks,
19 pending decisions, one running task and one running decision. Cumulative task
successes were 292; decision successes were 242. Inspection-blocked decisions
numbered 16. These are storage counts, not a measured production failure rate.
The deployed revision remained `51a3ba02e8231562660d1e4ea524e4d8b28e824c`;
model routing in draft PR 14 was not deployed. Monitoring returned HTTP 200.
The conductor and improvement lead exited with status `idle_exit` and exit code
zero; GitHub worker and research lead were running, with healthy PostgreSQL/Redis.
Snapshot details: `sha256:ca9ebb9854196719b7dcd33fc4649ecacef3c2d0b301b9199ee797f35530291a`.

A read-only script sampled the latest 30 distinct retained execution receipts
with completion times. All 30 were research-lead diagnoses. Four candidate
receipts were excluded as missing or exceeding the script's 20 MiB read limit.
Reported cumulative counters across this sample were 4,590,343 input tokens,
3,792,640 cached input tokens and 39,938 output tokens. Stored completed-command
outputs totaled 1,026,780 characters; one execution had a command output longer
than 32,000 characters. Evidence:
`sha256:00cfd6e428e941ac2eea495bada50b06782bd6fc67ff1ca200e67d86ca10b5d0`.

Cached input is included in the reported input counters; these numbers are not
billed cost. The sample excludes absent receipts and is not all attempts or an
unbiased throughput study. Stored command output need not equal text delivered
to the model. No before/after token-saving percentage is established.

The immediate optimization is an exact-reference, bounded artifact-reader path
for model inspection: select a JSON pointer or page/search a known artifact instead
of recursively searching the store. Immutable source content remains intact.
This caps the reader's serialized response, not arbitrary Codex tool outputs.
Diagnosis coalescing, queue fairness and namespace-error classification still need
separate implementation and verification.
