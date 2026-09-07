"""Docker-host supervision, wake-on-message and release recovery without an LLM."""
import argparse
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from codex_harness.adapters.bus import RedisBus
from codex_harness.adapters.commands import run_process
from codex_harness.adapters.deployment import ReleaseRunner
from codex_harness.bootstrap import build, build_executor, redis_url
from codex_harness.domain.model import envelope, utcnow

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {"conductor": "conductor", "lead:research": "research-lead",
           "lead:improvement": "improvement-lead", "worker:implementation": "implementation-worker",
           "worker:github": "github-worker", "worker:geeknews": "geeknews-worker"}
release_thread = None


def schedule_research(service, hours=6):
    slot = int(time.time() // (hours * 3600))
    with service.store.transaction() as tx:
        for source in ("github", "geeknews"):
            key = f"research:{source}:{slot}"
            if tx.get("schedule", key):
                continue
            message = envelope("task.assign", "lead:research", "worker:" + source, "research",
                               {"source": source}, key)
            tx.put("outbox", message["message_id"], {"message": message, "sent": False})
            tx.put("schedule", key, {"id": key, "at": utcnow()})


def deploy_queued(service, executor):
    with service.store.transaction() as tx:
        queue = [r for r in tx.scan("release_queue") if r["status"] == "queued"]
    if not queue:
        return
    runner = ReleaseRunner(service, executor.git, executor.artifacts,
                           str(Path(os.environ["USERPROFILE"]) / ".codex/auth.json"))
    for row in queue[:1]:
        try:
            result = runner.run(row["id"])
        except Exception as exc:
            result = {"status": "failed", "reason": str(exc)}
        with service.store.transaction() as tx:
            tx.put("release_queue", row["id"], {**row, "status": result["status"], "result": result})
        print(json.dumps({"release": row["id"], "result": result}), flush=True)


def tick(research=False, releases=False):
    global release_thread
    service = build()
    bus = RedisBus(redis_url())
    if research:
        schedule_research(service)
    service.flush_outbox(bus)
    now = datetime.now(timezone.utc)
    with service.store.transaction() as tx:
        tasks = tx.scan("tasks") + tx.scan("decisions_pending")
        active = tx.get("deployment", "active")
        image = tx.get("images", active["release_id"]) if active else None
    desired = image["image"] if image else "codex-harness:bootstrap"
    status = run_process(["docker", "compose", "ps", "--all", "--format", "json"], cwd=str(ROOT), timeout=20)
    if status.returncode:
        raise RuntimeError(status.stderr)
    rows = [json.loads(line) for line in status.stdout.splitlines() if line.startswith("{")]
    services = {row["Service"]: row for row in rows}
    for agent, name in TARGETS.items():
        agent_tasks = [row for row in tasks if row.get("agent", row.get("actor")) == agent]
        busy = any(row["status"] == "running" and datetime.fromisoformat(row["lease_until"]) > now
                   for row in agent_tasks)
        ready = any(row["status"] in {"queued", "pending", "retry"}
                    or (row["status"] == "running" and datetime.fromisoformat(row["lease_until"]) <= now)
                    for row in agent_tasks)
        key = bus.stream(agent)
        groups = bus.client.xinfo_groups(key) if bus.client.exists(key) else []
        backlog = (sum(g.get("pending", 0) + (g.get("lag") or 0) for g in groups)
                   if groups else bus.client.xlen(key))
        row = services.get(name, {})
        running = row.get("State") == "running"
        replace = running and row.get("Image") != desired and not busy
        if (not running and (backlog or ready)) or replace:
            result = run_process(["docker", "compose", "--profile", "agents", "--profile", "workers",
                                  "up", "-d", "--no-build", name], cwd=str(ROOT), timeout=60,
                                 env={**os.environ, "HARNESS_AGENT_IMAGE": desired})
            if result.returncode:
                raise RuntimeError(result.stderr)
            print(json.dumps({"woken": agent, "queued": backlog, "durable_tasks": ready,
                              "image": desired}), flush=True)
            if replace:
                break
    if releases and (release_thread is None or not release_thread.is_alive()):
        release_thread = threading.Thread(target=deploy_queued, args=(service, build_executor(service)), daemon=True)
        release_thread.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--research", action="store_true")
    parser.add_argument("--releases", action="store_true")
    args = parser.parse_args()
    while True:
        try:
            tick(args.research, args.releases)
        except Exception as exc:
            print(json.dumps({"supervisor_error": str(exc), "at": utcnow()}), flush=True)
        if args.once:
            if release_thread:
                release_thread.join()
            break
        time.sleep(5)
