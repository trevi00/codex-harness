"""Read-only monitoring projection; durable records retain their original meaning."""
from collections import Counter
from datetime import datetime, timezone
from typing import Protocol

from codex_harness.domain.policy import POLICY


class MonitoringFacts(Protocol):
    def read(self) -> dict: ...


def age_seconds(timestamp, now):
    try:
        return max(0, (now - datetime.fromisoformat(timestamp)).total_seconds())
    except (TypeError, ValueError):
        return None


class Monitoring:
    def __init__(self, facts: MonitoringFacts):
        self.facts = facts

    def snapshot(self, now=None):
        now = now or datetime.now(timezone.utc)
        facts = self.facts.read()
        health = facts.get('health') or {}
        age = age_seconds(health.get('checked_at'), now)
        facts['operating_status'] = (health.get('status', 'unknown')
                                     if age is not None and age <= 120 else 'unknown')
        facts['health_age_seconds'] = age
        facts['task_counts'] = dict(Counter(row['status'] for row in facts['tasks']))
        for agent in facts['agents']:
            owned = [row for row in facts['tasks'] + facts['decisions'] if row['agent'] == agent['id']]
            running = [row for row in owned if row['status'] == 'running'
                       and age_seconds(row.get('lease_until'), now) == 0
                       and row.get('lease_until') is not None]
            agent['execution_state'] = 'running' if running else 'waiting'
            agent['work'] = [row['id'] for row in running]
            agent['queued'] = sum(row['status'] in {'queued', 'pending', 'retry'} for row in owned)
            agent['expired_leases'] = sum(row['status'] == 'running' and row not in running for row in owned)
        facts['policy'] = POLICY.snapshot()
        facts['observed_at'] = now.isoformat()
        return facts
