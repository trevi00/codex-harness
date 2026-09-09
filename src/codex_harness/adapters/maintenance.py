from __future__ import annotations

import hashlib
import json
import re
import time

from filelock import FileLock, Timeout

from codex_harness.adapters.occurrence_provenance import PROVENANCE
from codex_harness.adapters.reader_provenance import READER_PROVENANCE
from codex_harness.adapters.record_references import (
    artifact_references,
    potential_record_references,
    potential_references,
    record_references,
)
from codex_harness.domain.model import require, utcnow
from codex_harness.domain.policy import POLICY


class ArtifactMaintenance:
    """Collect only old, unreferenced content; retain transitive evidence dependencies."""

    def __init__(self, store, artifacts):
        self.store, self.artifacts = store, artifacts

    @staticmethod
    def _roots(tx):
        records = tx if isinstance(tx, list) else tx.records()
        return {reference for record in records
                for reference in record_references(record['bucket'], record['id'], record['body'])}

    def _mark(self, root, roots):
        marked, pending = set(roots), list(roots)
        cache = {}
        existing = self._existing(root)
        parents = {}
        while pending:
            reference = pending.pop()
            path = root / (reference[7:] + ".txt")
            # INV-RESOURCE-001: missing evidence can hide dependencies. Fail closed.
            require(not path.is_symlink() and path.resolve().parent == root,
                    "Artifact escaped store")
            require(path.exists(), f"Referenced artifact missing; collection deferred: {reference}"
                    f" from {parents.get(reference, 'runtime record')}")
            content = path.read_bytes()
            require(hashlib.sha256(content).hexdigest() == reference[7:],
                    "Referenced artifact corrupted")
            children = self._dependencies(path, content, cache, existing) - marked
            parents.update((child, reference) for child in children)
            marked.update(children)
            pending.extend(children)
        return marked

    @staticmethod
    def _existing(root):
        return {'sha256:' + path.stem for path in root.glob('*.txt')
                if re.fullmatch(r'[0-9a-f]{64}', path.stem)}

    @staticmethod
    def _live_roots(records, existing):
        return {reference for record in records
                for reference in potential_record_references(record['bucket'], record['id'], record['body'])} & existing

    @staticmethod
    def _dependencies(path, content, cache=None, existing=None):
        # INV-RESOURCE-001: classification may identify missing metadata, but
        # can never make an existing referenced blob eligible for deletion.
        potential = potential_references(content.decode('utf-8'))
        live = potential & existing if existing is not None else {
            ref for ref in potential if (path.parent / (ref[7:] + '.txt')).exists()}
        projected, reader_origins = READER_PROVENANCE.project(path, content)
        projected, origins = PROVENANCE.project('sha256:' + path.stem, projected)
        origins |= reader_origins
        metadata_path = path.with_suffix('.json')
        source = ''
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
            require(isinstance(metadata, dict) and metadata.get('ref') == 'sha256:' + path.stem
                    and metadata.get('bytes') == len(content), 'Artifact metadata mismatch')
            source = metadata.get('source', '')
            require(isinstance(source, str), 'Artifact source metadata invalid')
        snapshot_key = None
        if source == 'conductor-measurements.v1' and cache is not None:
            # Observed timestamps carry no references. Otherwise byte-identical
            # measurement snapshots share decoding; all other bytes remain keyed.
            normalized = re.sub(
                rb'("observed_at"\s*:\s*")[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})(")',
                rb'\1OBSERVED_TIME\2', content)
            snapshot_key = ('measurement', PROVENANCE.revision, hashlib.sha256(normalized).digest())
            if snapshot_key in cache:
                return set(cache[snapshot_key]) | live
        references = artifact_references(projected.decode('utf-8'), source=source, cache=cache) | origins
        if snapshot_key is not None:
            if len(cache) >= 2048:
                cache.pop(next(iter(cache)))
            cache[snapshot_key] = frozenset(references)
        return references | live

    def _generation(self):
        path = self.artifacts.root / 'generation'
        return path.read_text() if path.exists() else None

    def collect(self, apply: bool = False, days: int = POLICY.artifact_retention_days) -> dict:
        require(days >= 1, "Artifact grace period must be at least one day")
        root = self.artifacts.root.resolve()
        cutoff = time.time() - days * 86400
        started = time.monotonic()
        with self.store.transaction() as tx:
            if apply and (tx.get('maintenance_control', 'collection') or {}).get('status') == 'paused':
                return {'id': 'latest', 'at': utcnow(), 'applied': False, 'files': 0, 'bytes': 0,
                        'deferred_scope': 'scan', 'reason': 'collection_paused', 'deferred': 1, 'errors': []}
            records = tx.records()
        snapshot_seconds = time.monotonic() - started
        # INV-RESOURCE-001: decode detached rows without holding DB serialization.
        # Final deletion batches still recheck current roots transactionally.
        roots = self._roots(records)
        # INV-RESOURCE-001: sample only between complete publications. A writer
        # changes generation before writing its body; an unlocked sample can
        # mistake an in-flight publication for an unchanged filesystem snapshot.
        # Probe outside the DB transaction so heartbeats remain independent.
        try:
            with FileLock(str(root.parent / "artifacts.lock"), timeout=0):
                generation = self._generation()
                # INV-RESOURCE-001: bind the file index to the same publication
                # snapshot; an earlier index could miss a newly published edge.
                existing = self._existing(root)
        except Timeout:
            # Defer the scan itself; no artifact count is known at this point.
            result = {"id": "latest", "at": utcnow(), "applied": apply, "files": 0,
                      "bytes": 0, "retained_references": len(roots), "grace_days": days,
                      "deferred": 1, "deferred_scope": "scan",
                      "reason": "publication_in_progress", "errors": [],
                      "snapshot_seconds": snapshot_seconds, "max_batch_seconds": 0}
            if apply:
                with self.store.transaction() as tx:
                    tx.put("maintenance", "latest", result)
            return result
        roots.update(self._live_roots(records, existing))
        marked = self._mark(root, roots)
        candidates = []
        scan_cache = {}
        # INV-RESOURCE-001: even uncommitted parents retain their children.
        # Traverse outside DB serialization; publication invalidates this snapshot.
        for path in root.glob("*.txt"):
            if not re.fullmatch(r"[0-9a-f]{64}\.txt", path.name) or path.is_symlink():
                continue
            try:
                content = path.read_bytes()
                require(hashlib.sha256(content).hexdigest() == path.stem,
                        "Artifact corrupted")
                marked.update(self._dependencies(path, content, scan_cache, existing))
                if path.stat().st_mtime < cutoff:
                    candidates.append(path)
            except FileNotFoundError:
                continue
        for pin in root.glob('*.pin'):
            try:
                marked.update(self._mark(root, {pin.read_text()}))
            except FileNotFoundError:
                continue
        candidates = [p for p in candidates if 'sha256:' + p.stem not in marked]
        count, reclaimed, deferred, errors = 0, 0, 0, []
        batch_seconds = []
        for index, path in enumerate(candidates):
            started = time.monotonic()
            lock = FileLock(str(root.parent / "artifacts.lock"), timeout=0)
            try:
                with self.store.transaction() as tx:
                    if apply and (tx.get('maintenance_control', 'collection') or {}).get('status') == 'paused':
                        deferred += len(candidates) - index
                        break
                    records = tx.records()
                    current_roots = self._roots(records) | self._live_roots(records, existing)
                    if not current_roots <= marked:
                        deferred += len(candidates) - index
                        break
                    lock.acquire()
                    if self._generation() != generation:
                        deferred += len(candidates) - index
                        break
                    if path.is_symlink() or not path.exists():
                        continue
                    stat = path.stat()
                    if stat.st_mtime >= cutoff:
                        continue
                    if apply:
                        # Fence publications before deletion. Crash/rollback can
                        # conservatively retain a body, never permit a dangling commit.
                        path.with_suffix('.deleted').touch()
                        tx.put('artifact_tombstones', 'sha256:' + path.stem,
                               {'id': path.stem, 'at': utcnow()})
                lock.release()
                # INV-RESOURCE-001: slow unlink owns neither shared lock.
                if apply:
                    path.unlink()
                count += 1
                reclaimed += stat.st_size
                if apply:
                    path.with_suffix('.json').unlink(missing_ok=True)
            except Timeout:
                deferred += 1
            except OSError as exc:
                errors.append({'file': path.name, 'error': str(exc)})
            finally:
                lock.release()
                batch_seconds.append(time.monotonic() - started)
        result = {"id": "latest", "at": utcnow(), "applied": apply, "files": count,
                  "bytes": reclaimed, "retained_references": len(marked), "grace_days": days,
                  "deferred": deferred, "errors": errors, "snapshot_seconds": snapshot_seconds,
                  "max_batch_seconds": max(batch_seconds, default=0)}
        if apply:
            with self.store.transaction() as tx:
                tx.put("maintenance", "latest", result)
        return result
