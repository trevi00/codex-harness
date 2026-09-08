# Baldrix path reconciliation

This observational ledger reconciles every tracked path at
`b9586c59c062457a45018e41c2e753934b5ca6c9` against its Git tree, retained
document claims, automatic research records and explicit scoped source reads.
It does not approve adoption or deployment. Contract: INV-MIGRATION-001.

Initial snapshot: 1,648 paths; 28 with exact document mentions; 293 automatic
unreviewed **records**; four newly attested full source reads. Mentions and
automatic records are not semantic completion. Zero path-level deployment
attestations does not mean previously deployed components are absent.

Follow-up snapshot (2026-09-08): 15 explicit full-read attestations, including six
budget-chain dependencies and five SDD comparison sources; 300 automatic unreviewed
records. The complete inventory remains 1,648 paths. This count is newly reconciled
path evidence, not a claim that only 15 files were ever read historically.
Snapshot: `sha256:216b39210e6737c240a4a8cb3e0a742c1ac36df391c8ff5a5b15c6289ea389a2`.
See baldrix-budget-chain.md for ten executed characterization probes and
baldrix-sdd-gap.md for the distinction between migrated recommendations and SDD execution.

Run with this branch on PYTHONPATH and the normal harness database configuration:

```text
python scripts/baldrix_ledger.py --root <harness-root> --source <pinned-bare-repository> --reviews <scoped-reviews.json>
```

The script verifies the full Git tree and source bytes, retains claim documents,
writes `.runtime/baldrix-path-ledger.json` and `.csv`, and stores immutable snapshot
references plus a latest pointer in PostgreSQL. Git owns the tool and definitions;
PostgreSQL owns observations. Review manifests contain path, revision, object_id,
source_ref, analysis_ref and scope. Keep these fields factual; nested review data
is evidence input, never an approval authority.

Validation: Ruff passed; full local suite 553 passed, 34 skipped. These skipped
tests are not production qualification. Independent Claude review accepted the
observational tool (input `sha256:932da7a01d4362acbf1fd95b354c6e14ef0ed72e65767cc8cdcbb3007d9e56c0`,
output `sha256:12156ec3aacdd62588b48bc8725448ed2b289da834b2bdd28d67edc78a1d19b2`).
This does not certify the whole upstream integration or a release.

Review follow-up: the original test archive underwent Git line-ending conversion.
Rerunning with core.autocrlf=false verified all four mounted source files against
the pinned blobs before execution: 15 passed in an isolated read-only container.
Receipt: `sha256:d1c6ac75aa4b43922fa7e12c6c88bb09953dcf338440e3a2a275a82007811514`.
The refreshed scoped analysis is linked from baldrix-depth-budget-baseline.md.

Remaining limitations: analysis_ref content is retained but nested claims and
references are not automatically qualified; document matching is conservative;
automatic counts count records, not distinct paths; active deployment metadata is
component context only. The ledger does not certify source license compatibility,
full dependency/caller coverage, live hook registration, or destination mapping.

Continue through atomic_json, paths, telemetry and budget callers, then actual
failure-delivery/concurrency/depth propagation tests before adapting these hooks.
The independent review additionally observed that the budget emitter returns True
even after delivery fails; do not use that return value as delivery acknowledgement.
Init, skill selection, reverse reading, agents/debate and the other reference
repositories remain in scope and require their own source and integration evidence.
