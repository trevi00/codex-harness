import os
import time

import pytest

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


def age(artifacts, *refs):
    for ref in refs:
        path = artifacts.root / (ref[7:] + '.txt')
        old = time.time() - 14 * 86400
        os.utime(path, (old, old))


@pytest.mark.parametrize('encoding', ['plain', 'ascii', 'spec', 'suffix'])
def test_existing_evidence_survives_even_if_semantic_classification_fails(tmp_path, monkeypatch, encoding):
    import json

    from codex_harness.adapters import maintenance

    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    child = artifacts.put('valuable evidence', 'test')['ref']
    value = {'plain': child, 'ascii': child.replace('sha256:', r'\u0073ha256:'),
             'spec': 'spec-' + child, 'suffix': child + 'a'}[encoding]
    parent = artifacts.put(json.dumps({'candidate': {}, 'image': value}), 'test')['ref']
    orphan = artifacts.put('unreferenced', 'test')['ref']
    age(artifacts, child, parent, orphan)
    with store.transaction() as tx:
        tx.put('root', 'metadata-shaped', {'candidate': {}, 'image': parent})
    # Fault injection checks the independent safety boundary, not a classifier copy.
    monkeypatch.setattr(maintenance, 'artifact_references', lambda *a, **kw: set())
    monkeypatch.setattr(maintenance, 'record_references', lambda *a, **kw: set())
    result = ArtifactMaintenance(store, artifacts).collect(apply=True)
    assert result['files'] == 1
    assert artifacts.read(child) == 'valuable evidence'
    assert artifacts.read(parent)
    assert not (artifacts.root / (orphan[7:] + '.txt')).exists()


@pytest.mark.parametrize('apply', [False, True])
def test_file_index_includes_publication_before_generation_sample(tmp_path, monkeypatch, apply):
    import json

    from codex_harness.adapters import maintenance

    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    collector = ArtifactMaintenance(store, artifacts)
    generation = collector._generation
    published = []

    def sample():
        if not published:
            # Simulate a completed publication immediately before the initial
            # generation sample. _put runs under the collector's file lock.
            child = artifacts._put('late evidence', 'test')['ref']
            parent = artifacts._put(json.dumps({'candidate': {}, 'image': child}), 'test')['ref']
            age(artifacts, child)
            published.extend([child, parent])
        return generation()

    monkeypatch.setattr(collector, '_generation', sample)
    monkeypatch.setattr(maintenance, 'artifact_references', lambda *a, **kw: set())
    monkeypatch.setattr(maintenance, 'record_references', lambda *a, **kw: set())
    result = collector.collect(apply=apply)
    assert result['files'] == 0
    assert artifacts.read(published[0]) == 'late evidence'


def test_tombstone_fences_ignore_metadata_exclusions_and_ascii_escapes(tmp_path):
    import json

    from codex_harness.domain.model import ContractError

    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    child = artifacts.put('collected orphan', 'test')['ref']
    age(artifacts, child)
    assert ArtifactMaintenance(store, artifacts).collect(apply=True)['files'] == 1
    for reference in (child, child.replace('sha256:', r'\u0073ha256:')):
        body = {'candidate': {}, 'image': reference}
        with pytest.raises(ContractError, match='collected'):
            artifacts.put(json.dumps(body), 'test')
        with pytest.raises(ContractError, match='collected'):
            with store.transaction() as tx:
                tx.put('root', 'late-metadata', body)


def test_metric_decoder_cache_never_caches_the_live_file_index(tmp_path):
    import json

    artifacts = FileArtifacts(str(tmp_path / 'artifacts'))
    child = artifacts.put('valuable evidence', 'test')['ref']
    parent = artifacts.put(json.dumps({'candidate': {}, 'image': child}), 'conductor-measurements.v1')['ref']
    path = artifacts.root / (parent[7:] + '.txt')
    cache = {}
    assert ArtifactMaintenance._dependencies(path, path.read_bytes(), cache, set()) == set()
    assert ArtifactMaintenance._dependencies(path, path.read_bytes(), cache, {child}) == {child}


def test_late_metadata_shaped_root_defers_deletion_even_if_classifier_misses_it(tmp_path, monkeypatch):
    from codex_harness.adapters import maintenance

    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    child = artifacts.put('newly referenced evidence', 'test')['ref']
    age(artifacts, child)
    collector = ArtifactMaintenance(store, artifacts)
    mark = collector._mark

    def publish(root, roots):
        marked = mark(root, roots)
        with store.transaction() as tx:
            tx.put('root', 'late', {'candidate': {}, 'image': child})
        return marked

    monkeypatch.setattr(maintenance, 'record_references', lambda *a, **kw: set())
    monkeypatch.setattr(collector, '_mark', publish)
    result = collector.collect(apply=True)
    assert result['files'] == 0 and result['deferred'] > 0
    assert artifacts.read(child) == 'newly referenced evidence'


def test_new_transitive_root_after_mark_defers_all_deletion(tmp_path, monkeypatch):
    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    child = artifacts.put('old child', 'test')['ref']
    parent = artifacts.put(child, 'test')['ref']
    age(artifacts, child, parent)
    collector = ArtifactMaintenance(store, artifacts)
    mark = collector._mark

    def publish(root, roots):
        result = mark(root, roots)
        with store.transaction() as tx:
            tx.put('arbitrary', 'root', {'ref': parent})
            tx.put('outbox', 'pending', {'ref': child, 'sent': False})
        return result

    monkeypatch.setattr(collector, '_mark', publish)
    result = collector.collect(apply=True)
    assert result['files'] == 0 and result['deferred'] == 1
    assert artifacts.read(child) == 'old child'
    assert artifacts.read(parent) == child


def test_republication_renews_grace_before_deletion(tmp_path, monkeypatch):
    from pathlib import Path

    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    ref = artifacts.put('republished', 'test')['ref']
    age(artifacts, ref)
    glob = Path.glob

    def enumerate_then_publish(path, pattern):
        yield from glob(path, pattern)
        artifacts.put('republished', 'again')

    monkeypatch.setattr(Path, 'glob', enumerate_then_publish)
    assert ArtifactMaintenance(store, artifacts).collect(apply=True)['files'] == 0
    assert artifacts.read(ref) == 'republished'


def test_missing_or_corrupted_root_fails_closed(tmp_path):
    import pytest

    from codex_harness.domain.model import ContractError

    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    orphan = artifacts.put('orphan', 'test')['ref']
    root = artifacts.put('root', 'test')['ref']
    age(artifacts, orphan, root)
    with store.transaction() as tx:
        tx.put('roots', 'one', {'ref': root})
    path = artifacts.root / (root[7:] + '.txt')
    path.write_text('corruption')
    with pytest.raises(ContractError, match='corrupted'):
        ArtifactMaintenance(store, artifacts).collect(apply=True)
    path.unlink()
    with pytest.raises(ContractError, match='missing'):
        ArtifactMaintenance(store, artifacts).collect(apply=True)
    assert artifacts.read(orphan) == 'orphan'


def test_partial_metadata_failure_counts_removed_body(tmp_path, monkeypatch):
    from pathlib import Path

    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    ref = artifacts.put('orphan', 'test')['ref']
    age(artifacts, ref)
    unlink = Path.unlink

    def fail_metadata(path, *args, **kwargs):
        if path.suffix == '.json':
            raise OSError('injected metadata failure')
        return unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'unlink', fail_metadata)
    result = ArtifactMaintenance(store, artifacts).collect(apply=True)
    assert result['files'] == 1 and result['bytes'] == 6
    assert len(result['errors']) == 1
    with store.transaction() as tx:
        assert tx.get('maintenance', 'latest') == result


def test_grace_boundary_and_symlink_are_retained(tmp_path, monkeypatch):
    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    ref = artifacts.put('boundary', 'test')['ref']
    now = 2000000000
    path = artifacts.root / (ref[7:] + '.txt')
    os.utime(path, (now - 86400, now - 86400))
    external = tmp_path / 'external'
    external.write_text('outside')
    (artifacts.root / ('a' * 64 + '.txt')).symlink_to(external)
    monkeypatch.setattr('codex_harness.adapters.maintenance.time.time', lambda: now)
    assert ArtifactMaintenance(store, artifacts).collect(apply=True, days=1)['files'] == 0
    assert external.read_text() == 'outside'


def test_publisher_file_lock_does_not_block_database(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from filelock import FileLock

    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    ref = artifacts.put('orphan', 'test')['ref']
    age(artifacts, ref)
    entered, release = Event(), Event()

    def publisher():
        with FileLock(str(artifacts.root.parent / 'artifacts.lock')):
            entered.set()
            assert release.wait(5)
            with store.transaction() as tx:
                tx.put('callback', 'root', {'ref': ref})

    with ThreadPoolExecutor() as pool:
        future = pool.submit(publisher)
        try:
            assert entered.wait(2)
            result = ArtifactMaintenance(store, artifacts).collect(apply=True)
            assert result['files'] == 0 and result['deferred'] == 1
        finally:
            release.set()
        future.result(timeout=5)


def test_multiple_collectors_count_each_body_once(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    refs = [artifacts.put(str(i), 'test')['ref'] for i in range(20)]
    age(artifacts, *refs)
    with ThreadPoolExecutor() as pool:
        results = list(pool.map(lambda _: ArtifactMaintenance(store, artifacts).collect(apply=True),
                                range(2)))
    # Nonblocking publication locks may defer an orphan in both concurrent
    # scans. Count every actual removal once, then drain the retained remainder.
    remaining = len(list(artifacts.root.glob('*.txt')))
    assert sum(r['files'] for r in results) + remaining == 20
    drained = ArtifactMaintenance(store, artifacts).collect(apply=True)
    assert drained['files'] == remaining and drained['deferred'] == 0
    assert sum(r['files'] for r in results) + drained['files'] == 20
    assert not list(artifacts.root.glob('*.txt'))


def test_repeated_new_roots_conservatively_defer_each_run(tmp_path, monkeypatch):
    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    refs = [artifacts.put('old ' + str(i), 'test')['ref'] for i in range(3)]
    age(artifacts, *refs)
    collector = ArtifactMaintenance(store, artifacts)
    mark = collector._mark
    publications = iter(refs[:2])

    def publish(root, roots):
        marked = mark(root, roots)
        with store.transaction() as tx:
            tx.put('outbox', 'pending', {'ref': next(publications), 'sent': False})
        return marked

    monkeypatch.setattr(collector, '_mark', publish)
    for _ in range(2):
        result = collector.collect(apply=True)
        assert result['files'] == 0 and result['deferred'] > 0
    assert all(artifacts.read(ref).startswith('old ') for ref in refs)


def test_cycle_traversal_terminates_with_synthetic_digest_fixture(tmp_path, monkeypatch):
    # A real SHA-256 reference cycle needs infeasible fixed points. Stub ONLY the
    # digest for this graph test; corrupted-content tests exercise real hashes.
    from types import SimpleNamespace

    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    first, second = 'sha256:' + 'a' * 64, 'sha256:' + 'b' * 64
    (artifacts.root / (first[7:] + '.txt')).write_text(second)
    (artifacts.root / (second[7:] + '.txt')).write_text(first)
    hashes = {second.encode(): first[7:], first.encode(): second[7:]}
    monkeypatch.setattr('codex_harness.adapters.maintenance.hashlib.sha256',
                        lambda content: SimpleNamespace(hexdigest=lambda: hashes[content]))
    assert ArtifactMaintenance(store, artifacts)._mark(artifacts.root, {first}) == {first, second}


def test_recent_uncommitted_parent_retains_old_child(tmp_path):

    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    child = artifacts.put('old dependency', 'test')['ref']
    age(artifacts, child)
    parent = artifacts.put(child, 'publisher')['ref']
    ArtifactMaintenance(store, artifacts).collect(apply=True)
    with store.transaction() as tx:
        tx.put('outbox', 'pending', {'ref': parent, 'sent': False})
    # INV-RESOURCE-001: a freshly published parent must retain its dependency.
    assert artifacts.read(child) == 'old dependency'


def test_rlm_publication_after_deletion_retains_source(tmp_path):

    from codex_harness.application.rlm import RecursiveContext

    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    child = artifacts.put('old dependency', 'test')['ref']
    age(artifacts, child)

    class Runtime:
        def run(self, *args):
            # Deterministic interleaving: analyze has read the source, but has
            # not published its result. Collection wins during the provider call.
            assert ArtifactMaintenance(store, artifacts).collect(apply=True)['files'] == 0
            return {'answer': {'finding': 'fixture', 'sufficient': True}}

    result = RecursiveContext(artifacts, Runtime(), str(tmp_path)).analyze(child, 'inspect')
    with store.transaction() as tx:
        tx.put('outbox', 'pending', {'ref': result['artifact'], 'sent': False})
    assert artifacts.document(result['artifact'])['source'] == child
    # INV-RESOURCE-001: this is a real publication caller, not a fabricated review.
    assert artifacts.read(child) == 'old dependency'


def test_slow_unlink_releases_database_serialization(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from pathlib import Path
    from threading import Event

    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    ref = artifacts.put('orphan', 'test')['ref']
    age(artifacts, ref)
    entered, release = Event(), Event()
    unlink = Path.unlink

    def paused_unlink(path, *args, **kwargs):
        if path.name == ref[7:] + '.txt':
            entered.set()
            assert release.wait(5)
        return unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'unlink', paused_unlink)
    with ThreadPoolExecutor() as pool:
        collection = pool.submit(ArtifactMaintenance(store, artifacts).collect, True)
        try:
            assert entered.wait(2)
            # Inspect actual lock ownership without timing a competing thread.
            acquired = store.lock.acquire(blocking=False)
            if acquired:
                store.lock.release()
            assert acquired
        finally:
            release.set()
        assert collection.result(timeout=5)['files'] == 1


def test_collected_reference_cannot_be_published_directly_or_in_parent(tmp_path):
    import pytest

    from codex_harness.domain.model import ContractError

    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    ref = artifacts.put('retired', 'test')['ref']
    age(artifacts, ref)
    assert ArtifactMaintenance(store, artifacts).collect(apply=True)['files'] == 1
    with pytest.raises(ContractError, match='collected'):
        artifacts.put(ref, 'late parent')
    with pytest.raises(ContractError, match='collected'):
        artifacts.put('retired', 'resurrection')
    with pytest.raises(ContractError, match='collected'):
        with store.transaction() as tx:
            tx.put('outbox', 'late', {'ref': ref})
    with store.transaction() as tx:
        assert tx.get('outbox', 'late') is None


def test_publication_during_mark_defers_collection(tmp_path, monkeypatch):
    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    child = artifacts.put('child', 'test')['ref']
    age(artifacts, child)
    collector = ArtifactMaintenance(store, artifacts)
    original = collector._mark

    def publish(root, roots):
        marked = original(root, roots)
        artifacts.put(child, 'parent')
        return marked

    monkeypatch.setattr(collector, '_mark', publish)
    assert collector.collect(apply=True)['files'] == 0
    assert artifacts.read(child) == 'child'


def test_failed_unlink_preserves_fence_and_body(tmp_path, monkeypatch):
    from pathlib import Path

    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    ref = artifacts.put('orphan', 'test')['ref']
    age(artifacts, ref)
    original = Path.unlink

    def fail(path, *args, **kwargs):
        if path.suffix == '.txt':
            raise OSError('injected slow storage failure')
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'unlink', fail)
    result = ArtifactMaintenance(store, artifacts).collect(apply=True)
    assert result['files'] == 0 and len(result['errors']) == 1
    assert artifacts.read(ref) == 'orphan'
    with store.transaction() as tx:
        assert tx.get('artifact_tombstones', ref)


def reference_record(location, ref):
    if location == 'bucket':
        return 'prefix:' + ref, 'record', {}
    if location == 'id':
        return 'records', 'prefix:' + ref, {}
    if location == 'body_key':
        return 'records', 'record', {'nested': [{ref: 'value'}]}
    return 'records', 'record', {'nested': ['prefix:' + ref]}


def test_collected_references_in_all_record_fields_are_rejected(tmp_path):
    import pytest

    from codex_harness.domain.model import ContractError

    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    ref = artifacts.put('deleted record reference', 'test')['ref']
    age(artifacts, ref)
    collector = ArtifactMaintenance(store, artifacts)
    assert collector.collect(apply=True)['files'] == 1
    for location in ('bucket', 'id', 'body_key', 'body_value'):
        record = reference_record(location, ref)
        with pytest.raises(ContractError, match='Artifact reference was collected'):
            with store.transaction() as tx:
                tx.put('atomic', 'before-invalid-write', {})
                tx.put(*record)
        with store.transaction() as tx:
            assert tx.get(*record[:2]) is None
            assert tx.get('atomic', 'before-invalid-write') is None
        assert collector.collect(apply=True)['files'] == 0


def test_live_references_in_all_record_fields_retain_artifacts(tmp_path):
    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    refs = []
    for location in ('bucket', 'id', 'body_key', 'body_value'):
        ref = artifacts.put(location, 'test')['ref']
        refs.append(ref)
        bucket, key, body = reference_record(location, ref)
        with store.transaction() as tx:
            tx.put(bucket, key + location, body)
    age(artifacts, *refs)
    assert ArtifactMaintenance(store, artifacts).collect(apply=True)['files'] == 0
    assert all(artifacts.read(ref) for ref in refs)


def test_postgres_transaction_rejects_collected_record_fields_before_insert():
    import pytest

    from codex_harness.adapters.store import PostgresTransaction
    from codex_harness.domain.model import ContractError

    class TombstonedConnection:
        def execute(self, query, params):
            assert query.startswith('SELECT body')  # No INSERT may be issued.
            assert params == ('artifact_tombstones', ref)
            return self

        def fetchone(self):
            return ({'id': ref[7:]},)

    ref = 'sha256:' + 'a' * 64
    tx = PostgresTransaction(TombstonedConnection())
    for location in ('bucket', 'id', 'body_key', 'body_value'):
        with pytest.raises(ContractError, match='Artifact reference was collected'):
            tx.put(*reference_record(location, ref))


@pytest.mark.parametrize('apply', [False, True])
def test_generation_snapshot_waits_for_complete_publication_without_db_lock(tmp_path, apply):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    changed, release, sampled, roots_read = Event(), Event(), Event(), Event()

    class PausedArtifacts(FileArtifacts):
        pause = False

        def _changed(self):
            super()._changed()
            if self.pause:
                changed.set()
                assert release.wait(5)

    class ObservedMaintenance(ArtifactMaintenance):
        def _roots(self, tx):
            roots = super()._roots(tx)
            roots_read.set()
            return roots

        def _generation(self):
            sampled.set()
            return super()._generation()

    artifacts, store = PausedArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    child = artifacts.put('publication dependency', 'test')['ref']
    age(artifacts, child)
    artifacts.pause = True
    with ThreadPoolExecutor(max_workers=2) as pool:
        publisher = pool.submit(artifacts.put, child, 'parent')
        assert changed.wait(2)
        collector = pool.submit(ObservedMaintenance(store, artifacts).collect, apply)
        try:
            assert roots_read.wait(2)
            # A real publisher owns the file lock. Snapshot sampling must wait
            # without retaining DB serialization needed for claims/heartbeats.
            assert not sampled.wait(0.25)
            acquired = store.lock.acquire(blocking=False)
            if acquired:
                store.lock.release()
            assert acquired
            result = collector.result(timeout=2)
            assert not release.is_set() and not publisher.done()
            assert result['reason'] == 'publication_in_progress'
            assert result['deferred_scope'] == 'scan'
            assert result['deferred'] == 1 and result['files'] == 0
            assert result['applied'] is apply
            assert artifacts.read(child) == 'publication dependency'
            with store.transaction() as tx:
                tx.put('heartbeat', 'during-publication', {'alive': True})
                assert tx.get('maintenance', 'latest') == (result if apply else None)
        finally:
            release.set()
        parent = publisher.result(timeout=5)['ref']
        assert collector.result(timeout=5)['files'] == 0
    with store.transaction() as tx:
        tx.put('outbox', 'published-parent', {'ref': parent})
    assert artifacts.read(parent) == child
    assert artifacts.read(child) == 'publication dependency'


@pytest.mark.parametrize('kind', ['duplicate', 'unknown_inspect'])
def test_ambiguous_receipts_retain_children_and_reject_stale_publication(tmp_path, kind):
    import json

    from codex_harness.domain.model import ContractError

    artifacts, store = FileArtifacts(str(tmp_path / 'artifacts')), MemoryStore()
    child = artifacts.put('ambiguous receipt child', 'test')['ref']
    if kind == 'duplicate':
        body = {'stdout': '{"candidate":{},"image":"' + child + '","image":"unknown"}'}
    else:
        body = {'argv': ['docker', 'image', 'inspect', '--unknown', 'target',
                         '--format', '{{.Id}}'], 'stdout': child}
    parent_body = json.dumps(body)
    parent = artifacts.put(parent_body, 'test')['ref']
    orphan = artifacts.put('unreferenced control', 'test')['ref']
    age(artifacts, child, parent, orphan)
    with store.transaction() as tx:
        tx.put('roots', 'parent', {'ref': parent})
    result = ArtifactMaintenance(store, artifacts).collect(apply=True)
    assert result['files'] == 1 and result['errors'] == []
    assert artifacts.read(child) == 'ambiguous receipt child'
    assert artifacts.read(parent) == parent_body
    assert not (artifacts.root / (orphan[7:] + '.txt')).exists()
    # INV-RESOURCE-001: publication and collection use the same conservative edges.
    with store.transaction() as tx:
        tx.put('artifact_tombstones', child, {'ref': child})
    with pytest.raises(ContractError, match='Artifact reference was collected'):
        with store.transaction() as tx:
            tx.put('receipts', 'stale', body)
    with store.transaction() as tx:
        assert tx.get('receipts', 'stale') is None


def test_original_runner_traversal_uses_validated_metadata(tmp_path):
    import json
    from pathlib import Path

    from codex_harness.domain.model import ContractError

    artifacts, store = FileArtifacts(tmp_path / 'artifacts'), MemoryStore()
    body = (Path(__file__).parent / 'fixtures/reference_runner/original.txt').read_text()
    runner = artifacts.put(body, 'baldrix-budget-probe-runner')['ref']
    orphan = artifacts.put('unreferenced', 'fixture')['ref']
    age(artifacts, runner, orphan)
    with store.transaction() as tx:
        tx.put('evidence', 'runner', {'ref': runner})
    collector = ArtifactMaintenance(store, artifacts)
    result = collector.collect()
    assert result['files'] == 1 and not result['errors']
    metadata_path = artifacts.root / (runner[7:] + '.json')
    metadata = json.loads(metadata_path.read_text())
    metadata_path.write_text(json.dumps({**metadata, 'bytes': 0}))
    with pytest.raises(ContractError, match='Artifact metadata mismatch'):
        collector.collect()
    assert artifacts.read(orphan) == 'unreferenced'
