from __future__ import annotations

import time

from codex_harness.domain.model import envelope, utcnow
from codex_harness.domain.policy import POLICY


def schedule_research(service, now: float | None = None) -> int:
    slot = int((time.time() if now is None else now) // (POLICY.research_interval_hours * 3600))
    created = 0
    with service.store.transaction() as tx:
        for source in ("github", "geeknews"):
            key = f"research:{source}:{slot}"
            if tx.get("schedule", key):
                continue
            message = envelope("task.assign", "lead:research", "worker:" + source, "research",
                               {"source": source}, key)
            service.org.authorize(message)
            tx.put("outbox", message["message_id"], {"message": message, "sent": False})
            tx.put("schedule", key, {"id": key, "at": utcnow()})
            created += 1
    return created
