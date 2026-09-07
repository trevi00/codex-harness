from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RuntimePolicy:
    context_checkpoint_fraction: float = 0.70
    idle_seconds: int = 3600
    max_active_executions: int = 2
    max_attempts: int = 3
    max_reworks: int = 2
    task_seconds: int = 900
    decision_seconds: int = 300
    task_lease_seconds: int = 600
    research_interval_hours: int = 6
    recurrence_threshold: int = 2
    artifact_retention_days: int = 7
    stream_retention_entries: int = 1000

    def snapshot(self) -> dict:
        return asdict(self)


POLICY = RuntimePolicy()
