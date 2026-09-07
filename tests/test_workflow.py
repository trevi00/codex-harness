from datetime import datetime, timedelta, timezone

import pytest

from codex_harness.adapters.store import MemoryStore
from codex_harness.application.releases import Releases
from codex_harness.application.workflow import Workflow
from codex_harness.bootstrap import organization
from codex_harness.domain.model import ContractError, envelope


def assignment(action="implement", agent="worker:implementation"):
    parent = organization().actor(agent).parent
    return envelope("task.assign", parent, agent, action, {"objective": "fixture"}, "test")


def test_duplicate_delivery_and_expired_executor_cannot_commit():
    workflow = Workflow(MemoryStore(), organization())
    message = assignment()
    assert workflow.submit(message) == workflow.submit(message)
    task = workflow.claim("worker:implementation", "first", lease_seconds=1)
    assert workflow.claim("worker:implementation", "second") is None
    later = datetime.now(timezone.utc) + timedelta(seconds=2)
    replacement = workflow.claim("worker:implementation", "second", now=later)
    with pytest.raises(ContractError, match="Stale"):
        workflow.complete(task, {"summary": "old writer"})
    workflow.complete(replacement, {"summary": "accepted writer"})
    with workflow.store.transaction() as tx:
        assert len(tx.scan("outbox")) == 1


def test_dependencies_cancellation_deadline_and_attempt_exhaustion():
    workflow = Workflow(MemoryStore(), organization())
    first, second = assignment(), assignment()
    second["when"]["after"] = [first["message_id"]]
    workflow.submit(first)
    workflow.submit(second)
    task = workflow.claim("worker:implementation", "one")
    assert task["id"] == first["message_id"]
    assert workflow.claim("worker:implementation", "two") is None
    workflow.cancel(task["id"], "conductor", "cancel fixture")
    with pytest.raises(ContractError):
        workflow.complete(task, {})
    assert workflow.claim("worker:implementation", "two") is None
    with workflow.store.transaction() as tx:
        assert tx.get("tasks", second["message_id"])["status"] == "cancelled"
    expired = assignment()
    expired["when"]["deadline"] = "2020-01-01T00:00:00+00:00"
    workflow.submit(expired)
    assert workflow.claim("worker:implementation", "two") is None
    retry = assignment()
    workflow.submit(retry)
    for _ in range(3):
        task = workflow.claim("worker:implementation", "two")
        workflow.fail(task, "fixture error")
    assert workflow.claim("worker:implementation", "two") is None
    with workflow.store.transaction() as tx:
        assert tx.get("tasks", retry["message_id"])["status"] == "failed"


def test_report_requires_proven_result_and_only_queues_one_review():
    workflow = Workflow(MemoryStore(), organization())
    workflow.submit(assignment())
    task = workflow.claim("worker:implementation", "first")
    workflow.complete(task, {"candidate": {"revision": "abc"}})
    with workflow.store.transaction() as tx:
        report = tx.scan("outbox")[0]["message"]
    assert workflow.handle(report) == workflow.handle(report)
    with workflow.store.transaction() as tx:
        decisions = tx.scan("decisions_pending")
    assert len(decisions) == 1 and decisions[0]["actor"] == "lead:improvement"
    report["message_id"] = "unproven"
    report["what"]["details"]["result"] = {"candidate": {"revision": "forged"}}
    with pytest.raises(ContractError, match="Unproven"):
        workflow.handle(report)


def reviewed_release(service, revision="a"):
    candidate = {"revision": revision, "base": "base", "tree": "tree", "author": "worker:implementation"}
    release = service.propose(candidate, {"checks": ["live_cli"], "revision": "base"})
    service.review(release["id"], "lead:improvement", revision, True, "sha256:lead")
    service.review(release["id"], "conductor", revision, True, "sha256:conductor")
    return release


def test_release_requires_current_policy_complete_checks_and_fenced_promotion():
    service = Releases(MemoryStore(), organization())
    release = reviewed_release(service)
    with pytest.raises(ContractError, match="Stale"):
        service.verify(release["id"], "a", "candidate-weakened-policy", {})
    with pytest.raises(ContractError, match="Missing"):
        service.verify(release["id"], "a", release["policy_hash"], {})
    service.verify(release["id"], "a", release["policy_hash"],
                   {"live_cli": {"passed": True, "evidence": "actual-fixture-execution"}})
    service.promote(release["id"], None)
    second = reviewed_release(service, "b")
    service.verify(second["id"], "b", second["policy_hash"],
                   {"live_cli": {"passed": True, "evidence": "actual-fixture-execution"}})
    with pytest.raises(ContractError, match="changed"):
        service.promote(second["id"], None)
    service.promote(second["id"], release["id"])
    assert service.rollback(second["id"], "regression")["release_id"] == release["id"]


def test_failed_canary_never_promotes():
    service = Releases(MemoryStore(), organization())
    release = reviewed_release(service)
    service.verify(release["id"], "a", release["policy_hash"],
                   {"live_cli": {"passed": False, "evidence": "failure-log"}})
    with pytest.raises(ContractError, match="not verified"):
        service.promote(release["id"], None)
