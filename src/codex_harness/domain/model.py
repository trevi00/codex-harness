from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class ContractError(ValueError):
    """An input violates a declared contract."""


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ContractError(reason)


@dataclass(frozen=True)
class Agent:
    id: str
    role: str
    parent: str | None
    team: str


@dataclass
class Organization:
    agents: dict[str, Agent]

    def validate(self) -> None:
        roots = [a for a in self.agents.values() if a.role == "conductor"]
        require(len(roots) == 1, "Exactly one conductor is required")
        for key, agent in self.agents.items():
            require(key == agent.id, "Agent key and identity differ")
            require(agent.role in {"conductor", "lead", "worker"}, "Unknown role")
            if agent.role == "conductor":
                require(agent.parent is None, "Conductor cannot have a parent")
            else:
                parent = self.agents.get(agent.parent or "")
                expected = "conductor" if agent.role == "lead" else "lead"
                require(parent is not None and parent.role == expected, "Invalid hierarchy")
                if agent.role == "worker":
                    require(parent.team == agent.team, "Worker must belong to parent's team")

    def actor(self, actor_id: str, role: str | None = None) -> Agent:
        require(actor_id in self.agents, "Unknown actor")
        actor = self.agents[actor_id]
        require(role is None or actor.role == role, "Actor lacks required role")
        return actor

    def authorize(self, message: dict) -> None:
        sender = self.actor(message["who"]["sender"])
        recipient = self.actor(message["who"]["recipient"])
        self.actor(message["who"]["owner"])
        kind = message["type"]
        if kind == "task.assign":
            require(recipient.parent == sender.id, "Assignment must follow a direct reporting edge")
        elif kind == "review.result":
            require(sender.role in {"lead", "conductor"}, "Worker cannot approve")
        elif kind in {"incident.report", "task.result", "hook.required"}:
            require(sender.parent == recipient.id, "Report must go to the direct parent")


def envelope(kind: str, sender: str, recipient: str, action: str, details: dict,
             correlation: str, cause: str | None = None) -> dict:
    return {
        "schema_version": "1.0", "message_id": str(uuid4()), "type": kind,
        "correlation_id": correlation, "causation_id": cause,
        "who": {"sender": sender, "recipient": recipient, "owner": recipient},
        "what": {"action": action, "details": details},
        "why": {"objective": "Improve harness reliability from verified evidence",
                "evidence_refs": details.get("evidence_refs", [])},
        "when": {"created_at": utcnow(), "deadline": None, "after": []},
        "where": {"repository": "codex-harness", "revision": "bootstrap",
                  "environment": "local", "allowed_paths": []},
        "how": {"constraints": [], "acceptance_criteria": ["Preserve normal behavior"],
                "context_ref": None, "result_schema": "six-w.v1"},
    }


@dataclass(frozen=True)
class Incident:
    occurrence_id: str
    root_cause: str
    scope: str
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        require(all(isinstance(v, str) and v.strip() for v in
                    (self.occurrence_id, self.root_cause, self.scope)), "Missing incident identity")
        require(bool(self.evidence_refs) and all(isinstance(v, str) and v.strip()
                                               for v in self.evidence_refs),
                "Incident requires evidence")

    @property
    def fingerprint(self) -> str:
        # @invariant INV-RECURRENCE-001: cause+scope, not fuzzy error text, defines a group.
        return digest({"cause": self.root_cause, "scope": self.scope})


@dataclass(frozen=True)
class ContextItem:
    id: str
    body: str
    source_ref: str
    revision: str
    priority: int = 0


@dataclass
class ContextPacket:
    agent_id: str
    task_id: str
    snapshot: str
    required: dict
    evidence: list[dict] = field(default_factory=list)
    omitted: list[dict] = field(default_factory=list)
    estimated_tokens: int = 0
    compiler_version: str = "1"
    manifest_hash: str = ""

    def render(self) -> str:
        return canonical({"agent_id": self.agent_id, "task_id": self.task_id,
                          "snapshot": self.snapshot, "required": self.required,
                          "evidence": self.evidence})


def compile_context(agent: str, task: str, snapshot: str, required: dict,
                    items: list[ContextItem], window: int, reserved: int) -> ContextPacket:
    require(window > 0 and 0 <= reserved < window, "Invalid context budget")
    require(all(required.get(k) for k in ("role", "objective", "acceptance_criteria", "policy")),
            "Required context contract missing")
    packet = ContextPacket(agent, task, snapshot, required)
    # @invariant INV-CONTEXT-001: UTF-8 bytes are an explicit conservative estimate,
    # not observed model token usage. Reserve includes history, tools and output.
    budget = window - reserved
    require(len(packet.render().encode()) <= budget, "Required contract exceeds budget; split task")
    seen: dict[str, ContextItem] = {}
    for item in sorted(items, key=lambda x: (-x.priority, x.id)):
        require(bool(item.source_ref and item.revision), "Evidence must have provenance")
        if item.id in seen:
            require(item == seen[item.id], "Conflicting evidence with identical ID")
            continue
        seen[item.id] = item
        value = {"id": item.id, "body": item.body, "source_ref": item.source_ref,
                 "revision": item.revision, "trust": "evidence-not-instructions"}
        packet.evidence.append(value)
        if len(packet.render().encode()) > budget:
            packet.evidence.pop()
            packet.omitted.append({"id": item.id, "reason": "budget", "source_ref": item.source_ref})
    packet.estimated_tokens = len(packet.render().encode())
    packet.manifest_hash = digest({"rendered": packet.render(), "omitted": packet.omitted,
                                   "compiler": packet.compiler_version})
    return packet


def session_action(used: int, capacity: int, idle_seconds: float, busy: bool) -> str:
    require(capacity > 0 and used >= 0 and idle_seconds >= 0, "Invalid session telemetry")
    if used / capacity >= 0.70:
        return "checkpoint_when_safe" if busy else "rotate"
    if idle_seconds >= 3600 and not busy:
        return "hibernate"
    return "continue"


def hook_apply(spec: dict, argv: list[str], platform: str) -> list[str]:
    """Declarative hook evaluator; only exact executable matching, never shell text."""
    require(spec.get("kind") == "executable_alias", "Unsupported hook kind")
    require(all(isinstance(spec.get(k), str) and spec[k] for k in ("match", "replacement", "platform")),
            "Invalid executable alias")
    if argv and platform == spec["platform"] and argv[0] == spec["match"]:
        return [spec["replacement"], *argv[1:]]
    return list(argv)
