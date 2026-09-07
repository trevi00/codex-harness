# Stage-one review handoff

Assignment: d7472a03-b522-4978-b890-19829badc9ca.
Base: bc867cf7f283650333afe7e451e045a307f15974.
Candidate is the commit containing this dossier, on the dedicated harness assignment branch.

Implemented: three Git-versioned definitions, deterministic typed evaluation, immutable input
snapshots and PostgreSQL observation persistence through existing ports, retained attempt history,
and monitor presentation with reasons and windows. Capacity uses the incumbent domain policy;
reliability targets remain undefined. See ../../conductor-evaluation.md for exact population rules.

Validation commands and complete output are retained in ruff.txt and pytest.txt. Unit coverage
includes retry denominator integrity, cancellation/expiry, empty population, minimum samples,
stale/future/invalid evidence, capacity over limit, snapshot reproducibility, monitoring collection,
and stale-write/authorization protection around attempt history. Existing full-suite checks cover
recurrence, context overflow and failed promotion gates. A PostgreSQL observation integration test
is added but is skipped unless HARNESS_INTEGRATION=1 enables service-backed tests.

No independent lead/conductor review was performed by this implementation worker. No actual
candidate CLI canary, PostgreSQL/Redis service integration, browser visual inspection, GitHub
production verification or deployment was performed. Unit fixtures and mocks are not production
verification. Independent review must successfully inspect commands; namespace denial means
inspection-blocked, not accepted, and does not identify or fix a host cause.

Scope/risks: legacy first-attempt history cannot be reconstructed. All task classes, including
synthetic tasks, share the initial reliability population. Capacity observes leases rather than
processes. Collection is tied to the host monitor cadence; retained snapshots grow with workload
and observation count. Sampling/retention budgets and later evaluation dimensions remain pending.
Rollback is additive: prior code ignores metric records and attempt history. Existing promotion,
incumbent review and actual canary requirements are unchanged. Nothing was pushed, merged or deployed.

Primary documentation fetched for scope verification is pinned by SHA-256 in sources.json.
This is limited documentation verification, not a fully analyzed reference repository or full
SRE/arc42/GraphRAG implementation.
