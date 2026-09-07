import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from codex_harness.adapters.bus import RedisBus
from codex_harness.adapters.knowledge import PostgresKnowledge
from codex_harness.adapters.store import PostgresStore
from codex_harness.application.service import Harness
from codex_harness.bootstrap import database_url, organization, redis_url
from codex_harness.domain.model import ContractError, digest, envelope

pytestmark = [pytest.mark.integration, pytest.mark.skipif(
    os.environ.get("HARNESS_INTEGRATION") != "1", reason="Set HARNESS_INTEGRATION=1 for local services")]


@pytest.fixture
def pgstore():
    dsn = database_url()
    schema = "test_" + uuid4().hex
    with psycopg.connect(dsn) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    store = PostgresStore(make_conninfo(dsn, options=f"-c search_path={schema},public"))
    store.migrate()
    yield store
    with psycopg.connect(dsn) as conn:
        conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.fixture
def bus():
    transport = RedisBus(redis_url(), "test-" + uuid4().hex)
    yield transport
    keys = list(transport.client.scan_iter(match=transport.namespace + ":*"))
    if keys:
        transport.client.delete(*keys)


def message(occurrence=None):
    return envelope("incident.report", "worker:implementation", "lead:improvement", "record_incident",
                    {"occurrence_id": occurrence or str(uuid4()), "root_cause": "cause",
                     "scope": "integration", "evidence_refs": ["test:evidence"]}, "integration")


def test_concurrent_second_strike_is_atomic(pgstore):
    service = Harness(pgstore, organization())
    messages = [message() for _ in range(8)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(service.record_incident, messages))
    assert sum(r["hook_created"] for r in results) == 1
    with pgstore.transaction() as tx:
        assert len(tx.scan("incidents")) == 8
        assert len(tx.scan("hooks")) == 1
        assert len(tx.scan("outbox")) == 1


def test_real_bus_crash_redelivery_and_outbox(pgstore, bus):
    service = Harness(pgstore, organization())
    msg = message()
    bus.publish(msg)
    entry_id, fields = bus.receive("lead:improvement", "crashed")
    assert service.record_incident(bus.decode(fields))["occurrences"] == 1
    # Simulate a crash after DB commit but before Redis ACK.
    recovered_id, fields = bus.receive("lead:improvement", "replacement", idle_ms=0)
    assert recovered_id == entry_id
    assert service.record_incident(bus.decode(fields))["occurrences"] == 1
    bus.ack("lead:improvement", recovered_id)
    service.record_incident(message())
    assert service.flush_outbox(bus) == 1
    assert service.flush_outbox(bus) == 0
    received_id, fields = bus.receive("conductor", "conductor-test")
    notification = bus.decode(fields)
    assert notification["type"] == "hook.required"
    assert notification["who"]["recipient"] == "conductor"
    bus.ack("conductor", received_id)


def test_canary_state_and_checkpoint_survive_reconnect(pgstore):
    service = Harness(pgstore, organization())
    service.record_incident(message())
    hook_id = service.record_incident(message())["hook_id"]
    spec = {"kind": "executable_alias", "platform": "windows", "match": "codex.ps1", "replacement": "codex.cmd"}
    service.propose(hook_id, "worker:implementation", spec, "abc")
    for actor in ("lead:improvement", "conductor"):
        service.review(hook_id, actor, "abc", digest(spec), True, "test:review")
    service.record_canary(hook_id, "abc", digest(spec), {"reproduction": True, "normal_case": True, "cli_start": True})
    service.activate(hook_id)
    service.checkpoint("worker:implementation", 0, {"next_action": "verify", "source_revision": "abc", "graph_snapshot": "123"})
    restarted = Harness(PostgresStore(pgstore.dsn), organization())
    assert restarted.prepare_command(["codex.ps1"], "windows") == ["codex.cmd"]
    with pytest.raises(ContractError, match="Stale session"):
        restarted.checkpoint("worker:implementation", 0, {"next_action": "old", "source_revision": "abc", "graph_snapshot": "123"})


def test_tree_sitter_graph_vector_and_failed_reindex(pgstore, tmp_path):
    source = tmp_path / "service.py"
    source.write_text("def recover():\n    # @invariant INV-RECOVERY-001\n    return 42\n", encoding="utf-8")
    knowledge = PostgresKnowledge(pgstore.dsn)
    report = knowledge.index_python(str(tmp_path))
    assert report["nodes"] == 3 and report["edges"] == 2
    hits = knowledge.query("recover", depth=1)
    assert {h["kind"] for h in hits} == {"file", "function_definition", "rule_reference"}
    symbol = next(h for h in hits if h["kind"] == "function_definition")
    knowledge.set_embedding(symbol["id"], [1.0, 0.0, 0.0], "test-fixture-v1")
    assert knowledge.vector_query([1.0, 0.0, 0.0], "test-fixture-v1")[0]["id"] == symbol["id"]
    assert knowledge.vector_query([1.0, 0.0, 0.0], "different-model") == []
    source.write_text("def broken(:", encoding="utf-8")
    with pytest.raises(ContractError, match="Parse failed"):
        knowledge.index_python(str(tmp_path))
    assert knowledge.query("recover")
