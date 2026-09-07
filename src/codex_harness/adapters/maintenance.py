from __future__ import annotations

import hashlib
import re
import time

from filelock import FileLock

from codex_harness.domain.model import canonical, require, utcnow
from codex_harness.domain.policy import POLICY


class ArtifactMaintenance:
    """Collect only old, unreferenced content; retain transitive evidence dependencies."""

    def __init__(self, store, artifacts):
        self.store, self.artifacts = store, artifacts

    def collect(self, apply: bool = False, days: int = POLICY.artifact_retention_days) -> dict:
        require(days >= 1, "Artifact grace period must be at least one day")
        root = self.artifacts.root.resolve()
        cutoff = time.time() - days * 86400
        with FileLock(str(root.parent / "artifacts.lock"), timeout=30):
            with self.store.transaction() as tx:
                marked = set(re.findall(r"sha256:[0-9a-f]{64}", canonical(tx.records())))
                pending = list(marked)
                while pending:
                    reference = pending.pop()
                    path = root / (reference[7:] + ".txt")
                    if not path.exists():
                        continue
                    require(not path.is_symlink() and path.resolve().parent == root, "Artifact escaped store")
                    content = path.read_bytes()
                    require(hashlib.sha256(content).hexdigest() == reference[7:], "Referenced artifact corrupted")
                    children = set(re.findall(r"sha256:[0-9a-f]{64}", content.decode("utf-8"))) - marked
                    marked.update(children)
                    pending.extend(children)
                candidates, reclaimed = [], 0
                for path in root.glob("*.txt"):
                    if not re.fullmatch(r"[0-9a-f]{64}\.txt", path.name) or path.is_symlink():
                        continue
                    require(path.resolve().parent == root, "Invalid cleanup target")
                    if "sha256:" + path.stem in marked or path.stat().st_mtime >= cutoff:
                        continue
                    candidates.append(path.name)
                    reclaimed += path.stat().st_size
                    if apply:
                        path.unlink()
                        path.with_suffix(".json").unlink(missing_ok=True)
                result = {"id": "latest", "at": utcnow(), "applied": apply, "files": len(candidates),
                          "bytes": reclaimed, "retained_references": len(marked), "grace_days": days}
                if apply:
                    tx.put("maintenance", "latest", result)
                return result
