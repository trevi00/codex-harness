import json
import os
from importlib.resources import files

from codex_harness.adapters.store import PostgresStore
from codex_harness.application.service import Harness
from codex_harness.domain.model import Agent, Organization


def organization() -> Organization:
    data = json.loads(files("codex_harness.resources").joinpath("organization.json").read_text())
    org = Organization({a["id"]: Agent(**a) for a in data["agents"]})
    org.validate()
    return org


def database_url() -> str:
    value = os.environ.get("HARNESS_DATABASE_URL")
    if not value:
        from pathlib import Path

        env_file = Path.cwd() / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("HARNESS_DATABASE_URL="):
                    value = line.partition("=")[2]
    if not value:
        raise RuntimeError("Run scripts/setup.py or set HARNESS_DATABASE_URL")
    return value


def build() -> Harness:
    return Harness(PostgresStore(database_url()), organization())


def redis_url() -> str:
    return os.environ.get("HARNESS_REDIS_URL", "redis://127.0.0.1:56379/0")
