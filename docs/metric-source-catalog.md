# Metric sources and applicability backlog

Status: source discovery and implementation requirements, 2026-09-07. This is an extensible catalog,
not a claim to have read all international standards or finished auditing any upstream harness.
Use conductor-evaluation.md and research-standard.md for evidence and adoption gates.

## Source families

| Source | Kind and candidate application | Evidence scope / remaining work |
|---|---|---|
| [Google SRE](https://sre.google/workbook/implementing-slos/) | Reliability practice: SLIs/SLOs, error budgets, recovery and canaries | Official chapters checked; map measurements to our actual task/deployment populations. |
| [DORA](https://dora.dev/guides/dora-metrics/) | Delivery research: change lead time, deployment frequency, failed deployment recovery time, change fail rate, deployment rework rate | Official current five-metric guide checked; define committed/deployed/recovered events and unplanned work classification. Not an agent productivity leaderboard. |
| [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) | International product-quality model; structure quality requirement coverage | Public abstract checked only. Full clauses not accessed; do not claim complete conformance or invent clause IDs. |
| [ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html) | International architecture-description standard; viewpoints and architecture model relationships | Public official abstract located; full-clause analysis pending. It does not prescribe a universal architecture score. |
| [arc42](https://docs.arc42.org/section-10/) | Architecture documentation framework; measurable quality scenarios and ADR traceability | Official quality/decision sections checked; derive executable harness-specific scenarios. |
| [NIST AI RMF](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/) | Voluntary AI risk-management framework: govern/map/measure/manage | Official core checked; map applicable risks and evidence, not a blanket checklist. Track revisions. |
| [ISO/IEC 23894:2023](https://www.iso.org/standard/77304.html) | International AI risk-management guidance | Official abstract located; full clauses unavailable in this review. Assess overlap with AI RMF. |
| [ISO/IEC 42001:2023](https://www.iso.org/standard/42001) | International AI management-system standard | Official overview located; organizational processes must not be mislabeled runtime numerical metrics. Full clauses not reviewed. |
| [NIST SSDF](https://csrc.nist.gov/projects/ssdf) | Secure-development guidance; integrity, verification and vulnerability response | Official project page checked; pin selected final publication, distinguish drafts and map actual release controls. |
| [SLSA](https://slsa.dev/spec/v1.2/) | Supply-chain specification; source/build provenance and artifact identity | Versioned official specification opened; detailed requirements mapping pending. Do not claim a SLSA level from a Git hash alone. |
| [OWASP GenAI risks](https://genai.owasp.org/llm-top-10/) | Security guidance; tool authority, untrusted content, sensitive data and resource abuse | Official risk index checked; derive reproducible adversarial cases relevant to our agents, not generic compliance claims. |
| [OpenTelemetry GenAI conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) | Telemetry vocabulary; interoperable operation/token/tool observations | Official entry redirects/moves; resolve and pin actual conventions and their stability before implementation. Not an SLO target source. |

Inventory additional applicable references discovered through these sources, record cross-references,
and consolidate overlapping criteria. For each source/criterion record adopt/adapt/defer/not-applicable
with a reason, provenance, owner, evidence gaps and re-review trigger. An inaccessible standard remains
incomplete; neither purchase nor access-control circumvention is implied by this task.

## Harness-derived and new metrics

The following are **our proposed definitions**, not assertions that an international source mandates them.
Each needs a versioned formula, observation implementation, comparison method and tests before activation.

| Candidate | Operational definition to validate |
|---|---|
| Handoff continuity | Handoffs that resume the same logical task and satisfy checkpoint obligations / eligible completed handoff trials; unresolved trials reported separately. |
| Mandatory context preservation | Required obligations preserved with valid source bindings / obligations required at composition/handoff; stale or missing evidence is a failure, not a smaller denominator. |
| Graph evidence fidelity | Checked claims with valid commit-bound source edges / sampled claims under a declared sampling plan; report inventory and semantic coverage separately. |
| Message side-effect integrity | Duplicate logical side effects per unique operation ID and stale-writer acceptance count; redelivery volume reported independently. |
| Verified recurrence repair | Eligible same-cause/scope incident groups reaching a verified active hook / groups requiring one, plus time-to-activation and post-activation recurrence. |
| Automation effectiveness | Comparable tasks completed with verified acceptance and recorded human interventions; do not equate absence of chat messages with zero intervention. |
| Resource-normalized benefit | Verified comparable task outcomes against token, time and memory observations; report quality/regression and resource changes together. |
| Review defect detection | Known injected defects rejected / applicable injected defects, alongside false rejections of known-good candidates; use isolated fixtures and separate from production outcomes. |
| Evidence-to-adoption latency | Time from source audit readiness to verified deployment, with research, queue, review and canary stages separately observable. |

Inspect the user's harness + guardian as related components, baldrix separately, and oh-my-hermes /
ouroboros using pinned manifests in reference-audit-status.md. For each borrowed metric trace its actual
collector, denominator, storage, evaluator, consumers and tests. A README claim is not a working metric.

The user clarified that `khaness` was a mistaken name for `https://github.com/trevi00/baldrix.git`.
Resolve that name to the existing `trevi00/baldrix` audit and its pinned source identity in
reference-audit-status.md. Do not create another repository audit or double-count its metrics.
This identity correction does not change the audit's semantic coverage or verification status.

## Integration and metric lifecycle

Extend the current conductor evaluator with a source-to-criterion registry and applicability coverage.
Classify origin as international standard, official practice/framework, upstream implementation or
harness-defined. Distinguish observed, proposed, enforced and retired metrics on the dashboard.

Run collection in scripts/adapters, with bounded query/sampling cost and retention. Prefer existing
events over extra model calls. Measure collector overhead and cardinality before broadening telemetry.
Every added metric must explain which decision it changes; record deferral for expensive redundant ones.
Keep critical correctness gates separate from trends and prioritization. No new metric may silently
weaken the incumbent release evaluator or allow a candidate to approve itself.
