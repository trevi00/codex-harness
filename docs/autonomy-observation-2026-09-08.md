# Live autonomous operation observation

Observed 2026-09-08 09:10 KST. This is a point-in-time production read, not a long-term
SLO claim and not deployment evidence for the migration branch.

Docker showed all six agent services running; PostgreSQL and Redis were healthy.
Durable execution progress was fresh for a conductor review and a GitHub audit task.
Recent completions included implementation, improvement-lead review, source audit and
GeekNews discovery. Outbox had zero unsent entries. Research control was active.
The deployed revision was `51a3ba02e8231562660d1e4ea524e4d8b28e824c`, recorded at
08:30 KST. It differs from the unmerged migration candidate.

There were 66 queued tasks: 64 source-audit partitions, one discovery mapping and one
GitHub research task. There were 95 pending decisions: 92 research-lead diagnoses and
three improvement-lead reviews. Oldest observed queue entries dated to approximately
04:27 KST (tasks) and 00:28 KST (decisions). Configured global execution capacity is two;
this snapshot does not prove which scheduling/resource condition caused every wait.

Cumulative storage counts were 255 succeeded / 86 failed tasks and 173 succeeded /
62 failed decisions, plus blocked and other statuses. These include historical/test
records and are not a production failure rate. Recent blocked review reasons cite
bubblewrap namespace denial, unavailable Docker commands and missing dependencies.
The underlying host cause was not independently established by this observation;
records were retained without retries, deletion, approval bypass or privilege changes.

Local monitoring at http://127.0.0.1:8787 returned HTTP 200 and a fresh collector timestamp.
Evidence: `sha256:4e464df39c84f80ba5728ae5101ffd7de0c0fc47585c573cffed5f31f404ee86`
and `sha256:32056905b4a85f29a0aa85a3f619a9e56a755d39c5ea7b3bc85918ecb6d759e3`.
Autonomy is active with a backlog and unresolved inspection/review failures. Sustainable
throughput, bounded waiting and automatic recovery remain unproven.
