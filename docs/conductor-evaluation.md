# Conductor evaluation requirements

Status: implementation specification, not deployed metric enforcement. The current VERDICT uses
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
