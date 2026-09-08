from __future__ import annotations

import hashlib
import re
import time

from filelock import FileLock, Timeout

from codex_harness.adapters.record_references import record_references
from codex_harness.domain.model import require, utcnow
from codex_harness.domain.policy import POLICY


class ArtifactMaintenance:
    """Collect only old, unreferenced content; retain transitive evidence dependencies."""

    def __init__(self, store, artifacts):
        self.store, self.artifacts = store, artifacts

    @staticmethod
    def _roots(tx):
        return {reference for record in tx.records()
                for reference in record_references(record['bucket'], record['id'], record['body'])}

    def _mark(self, root, roots):
        marked, pending = set(roots), list(roots)
        while pending:
            reference = pending.pop()
            path = root / (reference[7:] + ".txt")
            # INV-RESOURCE-001: missing evidence can hide dependencies. Fail closed.
            require(not path.is_symlink() and path.resolve().parent == root,
                    "Artifact escaped store")
            require(path.exists(), "Referenced artifact missing; collection deferred")
            content = path.read_bytes()
            require(hashlib.sha256(content).hexdigest() == reference[7:],
                    "Referenced artifact corrupted")
            children = set(re.findall(r"sha256:[0-9a-f]{64}", content.decode("utf-8"))) - marked
            marked.update(children)
            pending.extend(children)
        return marked

    def _generation(self):
        path = self.artifacts.root / 'generation'
        return path.read_text() if path.exists() else None

    def collect(self, apply: bool = False, days: int = POLICY.artifact_retention_days) -> dict:
        require(days >= 1, "Artifact grace period must be at least one day")
        root = self.artifacts.root.resolve()
        cutoff = time.time() - days * 86400
        started = time.monotonic()
        with self.store.transaction() as tx:
            roots = self._roots(tx)
        snapshot_seconds = time.monotonic() - started
        generation = self._generation()
        marked = self._mark(root, roots)
        candidates = []
        # INV-RESOURCE-001: even uncommitted parents retain their children.
        # Traverse outside DB serialization; publication invalidates this snapshot.
        for path in root.glob("*.txt"):
            if not re.fullmatch(r"[0-9a-f]{64}\.txt", path.name) or path.is_symlink():
                continue
            try:
                content = path.read_bytes()
                require(hashlib.sha256(content).hexdigest() == path.stem,
                        "Artifact corrupted")
                marked.update(re.findall(r"sha256:[0-9a-f]{64}", content.decode('utf-8')))
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
                    if not self._roots(tx) <= marked:
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
