"""Persist reproducible observations through inner storage and artifact ports."""
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from codex_harness.domain.measurements import (
    DEFINITIONS,
    definition_documents,
    evaluate,
    measurement_population,
)
from codex_harness.domain.model import canonical, digest, require
from codex_harness.ports import ArtifactStore, Store


class Measurements:
    def __init__(self, store: Store, artifacts: ArtifactStore):
        self.store, self.artifacts = store, artifacts

    def collect(self, repository_revision: str, now=None):
        require(bool(repository_revision), 'Measurement repository revision required')
        with self.store.transaction() as tx:
            tasks, decisions = tx.scan('tasks'), tx.scan('decisions_pending')
            now = now or datetime.now(timezone.utc)
        # INV-GRAPH-001: runtime snapshots live in PostgreSQL; bytes are immutable evidence.
        # INV-METRIC-001: retain every evaluator input, not repeated prompt/log payloads.
        # Each observation still has its own timestamp and independently replayable bytes.
        evidence = {'observed_at': now.isoformat(), 'tasks': measurement_population(tasks),
                    'decisions': measurement_population(decisions, decisions=True),
                    'input_schema': 'measurement-population.v1',
                    'repository_revision': repository_revision, 'definitions': definition_documents()}
        ref = self.artifacts.put(canonical(evidence), 'conductor-measurements.v1')['ref']
        results = []
        for definition in DEFINITIONS:
            result = asdict(evaluate(definition, evidence, now))
            result.update(definition=asdict(definition), definition_hash=digest(asdict(definition)),
                          repository_revision=repository_revision, evidence_refs=[ref],
                          observed_at=now.isoformat(),
                          window_start=(now - timedelta(seconds=definition.window_seconds)).isoformat(),
                          window_end=now.isoformat(), baseline_value=None, candidate_value=None,
                          uncertainty='No comparative baseline or production SLO inference',
                          promotion_approval=False)
            results.append(result)
        with self.store.transaction() as tx:
            for result in results:
                key = digest(result)
                tx.put('metric_observations', key, {'id': key, **result})
        return results
