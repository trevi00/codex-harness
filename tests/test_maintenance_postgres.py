"""Explicitly enabled, real PostgreSQL contention test; incumbent source is pinned."""
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from codex_harness.adapters.artifacts import FileArtifacts
from codex_harness.adapters.maintenance import ArtifactMaintenance
from codex_harness.adapters.store import PostgresStore
from codex_harness.application.workflow import Workflow
from codex_harness.bootstrap import database_url, organization
from codex_harness.domain.model import envelope

pytestmark = [pytest.mark.integration, pytest.mark.skipif(
    os.environ.get('HARNESS_INTEGRATION') != '1', reason='Set HARNESS_INTEGRATION=1')]
BASELINE = '0548efaf1bc8833c750c80b242de03b5a73d7799'


@pytest.fixture
def maintenance_store():
    dsn, schema = database_url(), 'maintenance_test_' + uuid4().hex
    with psycopg.connect(dsn) as conn:
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    store = PostgresStore(make_conninfo(dsn, options=f'-c search_path={schema}'))
    try:
        with psycopg.connect(store.dsn) as conn:
            conn.execute('CREATE TABLE documents (bucket text, id text, body jsonb, '
                         'PRIMARY KEY(bucket,id))')
        yield store
    finally:
        with psycopg.connect(dsn) as conn:
            conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


@pytest.mark.parametrize('apply', [False, True])
@pytest.mark.parametrize('incumbent', [True, False])
def test_slow_traversal_workflow_responsiveness(maintenance_store, tmp_path, monkeypatch,
                                             apply, incumbent):
    store = maintenance_store
    artifacts = FileArtifacts(str(tmp_path / 'artifacts'))
    ref = artifacts.put('root', 'fixture')['ref']
    workflow = Workflow(store, organization())
    for agent in ('worker:implementation', 'worker:github'):
        workflow.submit(envelope('task.assign', organization().actor(agent).parent,
                                 agent, 'implement' if agent.endswith('implementation') else 'research',
                                 {'objective': 'fixture'}, 'test'))
    running = workflow.claim('worker:implementation', 'heartbeat', lease_seconds=120)
    with store.transaction() as tx:
        tx.put('arbitrary', 'root', {'ref': ref})
    collector_type = ArtifactMaintenance
    if incumbent:
        source = subprocess.check_output(
            ['git', 'show', BASELINE + ':src/codex_harness/adapters/maintenance.py'], text=True)
        namespace = {}
        exec(compile(source, BASELINE + '/maintenance.py', 'exec'), namespace)
        collector_type = namespace['ArtifactMaintenance']
    entered, release = Event(), Event()
    read = Path.read_bytes

    def paused_read(path):
        if path.name == ref[7:] + '.txt':
            entered.set()
            assert release.wait(35), 'test did not release traversal'
        return read(path)

    monkeypatch.setattr(Path, 'read_bytes', paused_read)

    def invoke(operation):
        started = time.monotonic()
        try:
            value = operation()
            return {'seconds': time.monotonic() - started, 'status': 'ok', 'value': value}
        except psycopg.errors.LockNotAvailable as exc:
            return {'seconds': time.monotonic() - started, 'status': 'lock_timeout',
                    'error': str(exc), 'sqlstate': exc.sqlstate}

    with ThreadPoolExecutor(max_workers=3) as pool:
        collection = pool.submit(collector_type(store, artifacts).collect, apply)
        try:
            assert entered.wait(5)
            claim = pool.submit(invoke, lambda: workflow.claim('worker:github', 'claim'))
            heartbeat = pool.submit(invoke, lambda: workflow.heartbeat(running))
            # Inspect actual lock state while traversal is paused beyond 10 seconds.
            with psycopg.connect(store.dsn) as conn:
                locks = conn.execute("SELECT granted, mode FROM pg_locks WHERE locktype="
                                     "'advisory' AND objid=734219").fetchall()
            outcomes = [claim.result(timeout=15), heartbeat.result(timeout=15)]
            assert not release.wait(max(0, 10.5 - min(o['seconds'] for o in outcomes)))
            print({'incumbent': incumbent, 'apply': apply, 'locks': locks, 'outcomes': outcomes})
            if incumbent:
                assert all(o['status'] == 'lock_timeout' for o in outcomes)
                assert any(granted for granted, _ in locks)
            else:
                assert all(o['status'] == 'ok' and o['seconds'] < 5 for o in outcomes)
                assert outcomes[0]['value'] is not None
        finally:
            release.set()
        assert collection.result(timeout=10)['files'] == 0


def test_snapshot_and_final_batch_duration(maintenance_store, tmp_path):
    artifacts = FileArtifacts(str(tmp_path / 'artifacts'))
    with maintenance_store.transaction() as tx:
        for index in range(1000):
            tx.put('scale', str(index), {'body': 'x' * 1024})
    for index in range(100):
        ref = artifacts.put(str(index), 'scale')['ref']
        old = time.time() - 14 * 86400
        os.utime(artifacts.root / (ref[7:] + '.txt'), (old, old))
    result = ArtifactMaintenance(maintenance_store, artifacts).collect(apply=True)
    print({'scale_documents': 1000, 'scale_artifacts': 100, 'result': result})
    assert result['files'] == 100
    assert result['snapshot_seconds'] < 1
    assert result['max_batch_seconds'] < 1


def test_slow_root_decoding_does_not_hold_postgres_workflow_lock(maintenance_store, tmp_path):
    entered, release = Event(), Event()
    artifacts = FileArtifacts(str(tmp_path / 'artifacts'))
    workflow = Workflow(maintenance_store, organization())
    workflow.submit(envelope('task.assign', 'lead:improvement', 'worker:implementation',
                             'implement', {'objective': 'root decode responsiveness'}, 'test'))
    running = workflow.claim('worker:implementation', 'heartbeat', lease_seconds=120)

    class PausedRootDecoder(ArtifactMaintenance):
        def _roots(self, records):
            entered.set()
            assert release.wait(15)
            return super()._roots(records)

    with ThreadPoolExecutor(max_workers=2) as pool:
        collection = pool.submit(PausedRootDecoder(maintenance_store, artifacts).collect, False)
        try:
            assert entered.wait(5)
            heartbeat = pool.submit(workflow.heartbeat, running)
            heartbeat.result(timeout=5)
            assert not collection.done()
        finally:
            release.set()
        assert collection.result(timeout=10)['files'] == 0
