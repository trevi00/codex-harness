# Conductor evaluation requirements

Source expansion and harness-specific candidate metrics: [metric-source-catalog.md](metric-source-catalog.md).

Status: stage-one measurement candidate implemented below; not deployed metric enforcement. The current VERDICT uses
free-text SRE and arc42 assessments. Source audit work strengthens provenance but does not complete
the measurement and decision framework described here.

## Evidence and decision contract

Keep versioned metric definitions in Git; observations and decisions in PostgreSQL. GraphRAG is a
derived impact index bound to the source and harness revisions. Each structured metric result has:
metric ID and definition version, scope/population, formula/query version, unit, window start/end,
observed_at and freshness limit, numerator/denominator when meaningful, sample count and minimum,
baseline and candidate values, uncertainty, threshold and direction, immutable evidence references,
and status (pass/fail/unknown/not_applicable). Missing/stale/insufficient evidence is unknown, never
zero or pass. Not-applicable requires a scoped justification validated by the incumbent evaluator.

Counts must define retries, cancelled/expired work, duplicate deliveries, maintenance and synthetic
canaries explicitly. Keep raw failure attempts visible; do not silently improve reliability by
changing the denominator. Do not divide by zero or infer a production percentile from a single canary.

## Evaluation dimensions

| Dimension | Required measurements or executable criteria |
|---|---|
| Reliability | Logical task outcome and first-attempt success separately; completion latency by task class; queue age; stuck leases; message loss/duplicate side effects; SLI good/eligible events; SLO/error budget and burn rate only with defined windows and sufficient observations. |
| CLI and recovery | Actual CLI startup and file-task canaries bound to candidate commit/image; safe handoff at the existing 70% context policy; continuation correctness; hook failure and normal-case reproduction; rollback success and measured recovery duration. |
| Architecture | arc42 quality scenarios with stimulus, environment, affected component, expected response and measurable response criterion; hexagonal import boundaries, dependency cycles, ports/adapters, changed interfaces/schema compatibility, failure propagation and ADR tradeoffs. |
| SSOT and graph | Definition/runtime ownership; source and graph revision alignment; missing/dangling evidence; invalid graph edges/cycles according to relation-specific rules; change impact and uncovered affected contracts; stale generation/lease writes rejected. |
| Resources | CPU/memory usage and pressure; active model executions against existing limit 2; tokens and elapsed time per comparable successful task; idle shutdown after existing 3600-second policy excluding busy work; wake latency and artifact retention correctness. No cost estimate without known rates. |
| Self-improvement | Distinct confirmed incident recurrence; required-hook creation at threshold 2, time to verified activation, regression after activation; adoption benefit against a comparable baseline, defect/rework rate, rejected or rolled-back changes and remaining audit coverage. |

SRE provides reliability practices, and arc42 provides architecture documentation and quality
scenario structure. Neither is a universal certification score or a ready-made numeric cutoff.
Do not invent a 99.9% target or arbitrary percentile threshold and label it an international standard.
Existing user policies remain authoritative. Additional targets need explicit rationale, a measurement
plan and versioned policy review; initially collect baselines without declaring them satisfied.

## Staged decisions

Research/proposal approval authorizes bounded implementation or measurement work; it is not production
promotion. Its dossier must include benefit hypothesis, source audit binding, impacted contracts and
graph, measurable acceptance scenarios, evidence gaps and rollout/rollback plan. Unknown future
performance can justify an experiment, with a defined budget and completion criterion.

PR review checks the exact candidate against the incumbent policy and independent lead/conductor
reviews. Promotion requires all applicable mandatory gates plus actual tests/CLI canaries. Critical
contract violations, failed canaries, missing required evidence or unverifiable rollback block promotion
regardless of priority score. Noncritical comparative metrics inform priority and bounded experiments;
they must not deadlock all development merely because the system is new and has few samples.

Bind decisions to candidate commit/tree/image, policy hash, graph revision and evidence identities.
Do not permit the candidate to weaken its own evaluator or rewrite its baseline. Policy changes get
separate incumbent-policy review; revisions and stale evidence invalidate old approval. Persist why
each gate passed/failed and show it with its observation window on the local monitoring page.

## Primary references

- Google SRE, [Implementing SLOs](https://sre.google/workbook/implementing-slos/).
- Google SRE, [Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/).
- arc42, [Quality Requirements](https://docs.arc42.org/section-10/).
- arc42, [Architecture Decisions](https://docs.arc42.org/section-9/).

Verify reference scope from primary sources during implementation. Retain their URLs and the fetched
content/version evidence in the dossier; do not treat this specification as upstream source code analysis.

## Stage one candidate implementation

Definitions are versioned dataclasses in `domain/measurements.py` (version/query version 1).
The host monitor calls the application `Measurements` use case through the existing `Store`
and `ArtifactStore` ports. Production uses PostgreSQL `documents` under `metric_observations`;
no schema migration is needed. Content-addressed snapshots retain inputs and exact definitions;
each observation includes their hash, collector repository HEAD, window, reason and evidence reference.
The monitor shows measurements with drill-down provenance. These observations have no release authority.
The deployed workload may differ from collector HEAD: HEAD identifies the measuring implementation,
not an assertion that every sampled task ran on that revision.

Population semantics:

- Reliability uses tasks created in the trailing 24-hour half-open interval `[start,end)`.
  First-attempt success divides successful first outcomes by resolved first outcomes, including
  failures, cancellations during attempt one and recorded lease expiry. Unstarted and unresolved
  attempts are outside that denominator. A lease expiry is recorded when the scheduler reclaims
  work, not inferred as an actual process failure by the monitor. Missing legacy first outcomes
  invalidate that metric rather than being reconstructed from a later success.
- Terminal logical success counts each task ID once and includes failed, cancelled and expired
  terminal tasks, including cancellation/expiry before execution. Queued/running/retry tasks are
  excluded until terminal. Retries share an ID; a separate rebase/rework assignment is a separate
  logical task. Duplicate input IDs invalidate the population. Delivery retries do not create IDs.
- All persisted task classes are included, including maintenance and synthetic assignments if
  submitted as tasks. There is no reliable synthetic discriminator in legacy records. Independent
  decision records and standalone CLI canaries are excluded from reliability; these ratios must
  not be represented as production-only reliability or a canary success rate.
- Capacity is an instantaneous count of running task AND decision records with leases strictly
  after observation time. Expired leases are excluded. It measures scheduler leases, not operating
  system process concurrency. Its sole target comes from `POLICY.max_active_executions` (currently 2).
- Freshness is 120 seconds; minimum samples is one (one snapshot for capacity). These are initial
  measurement configuration choices, not SRE-certified thresholds or statistical confidence.
  Zero reliability population is unknown; a complete empty capacity snapshot is a valid zero.
  Both reliability targets are undefined, so values retain status unknown with an observational
  reason. No baseline/candidate comparison is available in stage one.

Workflow outcome history is appended inside the existing authorized, lease-fenced transactions.
Failed attempt details survive later success. No historical errors are backfilled. Source snapshots
are written outside the DB transaction to preserve the artifact-maintenance lock order, then all
three observation records commit together. Artifact failure or DB failure yields unavailable monitor
collection; it cannot yield approval. An orphan artifact from a failed DB write is eligible for the
existing unreferenced-artifact collector. Referenced observations/evidence are retained; observation
compaction and long-term sampling/storage budgets are pending.

Primary documentation scope was verified on 2026-09-07. Fetched pages and SHA-256 manifests are in
`docs/evidence/measurement-stage-one/`. Google SRE supports explicit good/eligible-event SLIs and
stakeholder-defined SLOs, with alerting tied to defined error budgets. arc42 describes measurable
quality scenarios and architecture decision documentation. These inform the specification; this is
not a source repository adoption audit or full standards implementation.

Pending: approved SLOs/error budgets/burn rates, latency/queue/recovery and CLI measurements,
architecture scenarios and dependency analysis, GraphRAG impact and revision checks, CPU/memory,
tokens/cost/idle/wake telemetry, incident recurrence and self-improvement benefit comparisons.
Independent incumbent lead/conductor review, actual candidate CLI canaries and production validation
remain required. Rollback uses the existing release path; appended measurement/history fields are
additive and do not require destructive schema downgrade.
