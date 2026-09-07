"""Wake configured stopped consumers on Redis backlog. Run on the Docker host.

This supervises message consumers, not yet long-running Codex sessions. Consumer
processes exit after 1h idle. No Docker socket is exposed to agent containers.
"""
import argparse
import json
import subprocess
import time
from pathlib import Path

from codex_harness.adapters.bus import RedisBus
from codex_harness.bootstrap import redis_url

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {"conductor": "conductor", "lead:research": "research-lead",
           "lead:improvement": "improvement-lead", "worker:implementation": "implementation-worker"}


def tick():
    bus = RedisBus(redis_url())
    for agent, service in TARGETS.items():
        key = bus.stream(agent)
        if not bus.client.exists(key):
            continue
        groups = bus.client.xinfo_groups(key)
        backlog = (sum(g.get("pending", 0) + (g.get("lag") or 0) for g in groups)
                   if groups else bus.client.xlen(key))
        if not backlog:
            continue
        result = subprocess.run(["docker", "compose", "ps", "--status", "running", "-q", service],
                                cwd=ROOT, capture_output=True, text=True, timeout=20, check=True)
        if not result.stdout.strip():
            subprocess.run(["docker", "compose", "--profile", "agents", "--profile", "workers",
                            "up", "-d", "--no-build", service], cwd=ROOT, check=True, timeout=60)
            print(json.dumps({"woken": agent, "queued": backlog}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    while True:
        tick()
        if args.once:
            break
        time.sleep(5)
