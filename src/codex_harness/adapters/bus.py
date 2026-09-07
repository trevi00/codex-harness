import json

from redis import Redis
from redis.exceptions import ResponseError

from codex_harness.adapters.contracts import validate_message
from codex_harness.domain.model import canonical


class RedisBus:
    def __init__(self, url: str, namespace: str = "codex-harness"):
        self.client = Redis.from_url(url, decode_responses=True, socket_timeout=10)
        self.namespace = namespace

    def stream(self, agent: str) -> str:
        return f"{self.namespace}:agent:{agent}"

    def publish(self, message: dict) -> str:
        validate_message(message)
        return self.client.xadd(self.stream(message["who"]["recipient"]), {"body": canonical(message)})

    def ensure_group(self, agent: str) -> None:
        try:
            self.client.xgroup_create(self.stream(agent), "workers", id="0", mkstream=True)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    def receive(self, agent: str, consumer: str, idle_ms: int = 60000) -> tuple | None:
        self.ensure_group(agent)
        # Recover messages left unacknowledged by a dead consumer before new delivery.
        reclaimed = self.client.xautoclaim(self.stream(agent), "workers", consumer,
                                         idle_ms, start_id="0-0", count=1)
        if reclaimed[1]:
            return reclaimed[1][0]
        rows = self.client.xreadgroup("workers", consumer, {self.stream(agent): ">"},
                                     count=1, block=1000)
        return rows[0][1][0] if rows else None

    def ack(self, agent: str, entry_id: str) -> None:
        self.client.xack(self.stream(agent), "workers", entry_id)

    def dead_letter(self, agent: str, entry_id: str, fields: dict, reason: str) -> None:
        self.client.xadd(f"{self.namespace}:dead-letter", {
            "source": self.stream(agent), "entry_id": entry_id,
            "body": fields.get("body", ""), "reason": reason,
        })
        self.ack(agent, entry_id)

    @staticmethod
    def decode(fields: dict) -> dict:
        return validate_message(json.loads(fields["body"]))
