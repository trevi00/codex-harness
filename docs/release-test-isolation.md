# Release integration service isolation

Release qualification previously pointed integration tests at the production
PostgreSQL DSN. Separate schemas still share advisory locks: maintenance tests
could contend with live agents, and the final batch measurement exceeded its
one-second contract (1.243 seconds). The rejected release remains immutable.

The host release adapter now starts disposable PostgreSQL and Redis containers,
with randomly allocated loopback-only ports, resource limits, and ephemeral
storage. Both incumbent and candidate suites receive these service endpoints.
The candidate interpreter migrates the disposable database before testing.
Container image identities, setup commands, and cleanup results are retained as
an artifact. Cleanup runs on success and exceptions; incomplete cleanup fails
qualification. Production credentials are not passed as test endpoints.

Each complete pytest process has a 900-second wall-clock budget. The maintenance
batch assertion remains strictly below one second. An isolated real PostgreSQL
run passed all five maintenance integration tests with a maximum batch of
0.562235 seconds; this is evidence for that run, not a latency guarantee.
The real Docker lifecycle test verifies PostgreSQL migration, Redis connectivity,
exception propagation, container removal, and the cleanup receipt.

Deployment still requires independent lead and conductor reviews, complete
incumbent and candidate suites, and actual Codex startup/file-task canaries.
The running host controller must load the reviewed deployment adapter and its
new service adapter before qualifying this candidate. Do not reset a rejected
release or substitute operator test results for release checks. After promotion,
restore the normal supervisor and artifact collection once runtime writers have
converged on the reviewed image.
