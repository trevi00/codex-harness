import os
import time

from codex_harness.adapters.artifacts import FileArtifacts
from codex_harness.adapters.maintenance import ArtifactMaintenance
from codex_harness.adapters.store import MemoryStore
from codex_harness.application.scheduling import schedule_research
from codex_harness.application.service import Harness
from codex_harness.bootstrap import organization


def test_old_orphans_are_collected_but_transitive_evidence_and_recent_files_survive(tmp_path):
    artifacts = FileArtifacts(str(tmp_path / "artifacts"))
    store = MemoryStore()
    child = artifacts.put("evidence", "fixture")["ref"]
    parent = artifacts.put(child, "fixture")["ref"]
    orphan = artifacts.put("orphan", "fixture")["ref"]
    for path in artifacts.root.glob("*.txt"):
        old = time.time() - 14 * 86400
        os.utime(path, (old, old))
    recent = artifacts.put("recent", "fixture")["ref"]
    with store.transaction() as tx:
        tx.put("arbitrary-new-bucket", "root", {"reference": parent})
    maintenance = ArtifactMaintenance(store, artifacts)
    assert maintenance.collect()["files"] == 1
    assert artifacts.read(orphan) == "orphan"
    assert maintenance.collect(apply=True)["files"] == 1
    assert not (artifacts.root / (orphan[7:] + ".txt")).exists()
    assert all((artifacts.root / (ref[7:] + ".txt")).exists() for ref in (child, parent, recent))


def test_research_schedule_deduplicates_each_interval():
    service = Harness(MemoryStore(), organization())
    assert schedule_research(service, now=0) == 2
    assert schedule_research(service, now=1) == 0
    assert schedule_research(service, now=6 * 3600) == 2
