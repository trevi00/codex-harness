# Artifact collection publication rework

Assignment: `9fef2878-81e1-4110-b0c6-1b43835dfe44`.
Evidence: `sha256:c83761c32e6d0d9c736b97965788f9a88a7565c991b28dffa09dbcfca62ec72d`.
Base: `0548efaf1bc8833c750c80b242de03b5a73d7799`.
Recovered candidate: `460a453d04f63bbdaad1790d56a877408a183a5b`, verified tree
`6cfce6b60e2816e5493888673eb2b6701f0e27e1`.

The candidate's Store.put checked only canonical(body), whereas collection scanned
whole records. A deleted reference in a bucket or ID could therefore commit and
make subsequent collection fail closed. Both adapters now use record_references
for the bucket, ID, and body (including nested dictionary keys). Collection uses
the same extractor. Only the exact artifact_tombstones bucket is excluded, since
its references record deletion fences rather than live evidence. ArtifactStore
now declares the retain context manager used by RecursiveContext.

Recovered maintenance behavior includes durable pins during recursive context
analysis, publication generation checks, transitive retention, permanent deletion
markers and database tombstones, and unlink outside database serialization.
Regression tests retain the prior publication, interleaving, failure, and lock
availability cases. New tests check all record fields, atomic rollback, subsequent
collection, live retention, and PostgreSQL rejection before issuing an INSERT.
The PostgreSQL test uses a connection double, not a live database.

Validation: `uv run ruff check .` passed; `uv run pytest` completed with
573 passed and 27 skipped; `uv run pytest tests/test_maintenance.py --runxfail`
completed with 20 passed. `git diff --check` passed. Outputs are retained in
`tests/artifact-record-fence-*.txt`; source/output SHA-256 bindings are in
`tests/artifact-record-fence-evidence.json`. Skipped tests were not executed. Initial concurrent uv setup failed
for pytest while installing numpy (missing .venv/bin/numpy-config); this was a
local dependency setup failure, not a test result or provider failure.

Remaining qualification: full metadata rescans and per-candidate root rescans
remain, with deployment-scale latency unmeasured. Pins left by crashes retain
artifacts indefinitely. Permanent tombstones require qualified rollback; reverting
to code without fence enforcement is unsafe. Filesystem and transaction failures
can conservatively retain bodies. Arbitrary missing external references still
cause collection to defer. Incumbent runtime policy binding, live PostgreSQL
behavior, independent reviews, and actual successful release canaries remain
unverified. No push, merge, deployment, accepted review, or production verification
is claimed (INV-RELEASE-001).
