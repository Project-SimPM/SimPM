"""Backward-compatible stubs for deprecated recorder classes.

The dashboard now reads logs directly from the simulation environment, so the
recorder classes are kept only to avoid breaking imports. They collect snapshots
at the end of a run without mirroring every event.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from queue import Queue
from typing import Any, Protocol

from simpm.dashboard_data import collect_run_data


class SimulationObserver(Protocol):  # pragma: no cover - compatibility shim
    def on_run_started(self, env):
        ...

    def on_run_finished(self, env):
        ...

    def on_entity_created(self, entity):
        ...

    def on_resource_created(self, resource):
        ...

    def on_activity_started(self, entity, activity_name: str, activity_id: int, start_time: float, duration_info: dict[str, Any] | None = None):
        ...

    def on_activity_finished(self, entity, activity_name: str, activity_id: int, end_time: float):
        ...

    def on_resource_acquired(self, entity, resource, amount: int, time: float):
        ...

    def on_resource_released(self, entity, resource, amount: int, time: float):
        ...

    def on_log_event(self, event: dict[str, Any]):
        ...


@dataclass
class RunRecorder:  # pragma: no cover - compatibility shim
    """Minimal recorder that snapshots run data after execution.

    The class maintains the previous public attributes but does not mirror
    per-event state. When registered as an observer, it simply stores the
    environment reference and builds ``run_data`` when the run finishes.
    """

    collect_logs: bool = True
    run_data: dict[str, Any] = field(default_factory=dict)
    _env: Any | None = None

    def on_run_started(self, env):
        self._env = env

    def on_run_finished(self, env):
        self._env = env
        self.run_data = collect_run_data(env).as_dict()

    # Remaining callbacks are retained for API compatibility.
    def on_entity_created(self, entity):  # pragma: no cover - noop
        return None

    def on_resource_created(self, resource):  # pragma: no cover - noop
        return None

    def on_activity_started(self, entity, activity_name: str, activity_id: int, start_time: float, duration_info: dict[str, Any] | None = None):  # pragma: no cover - noop
        return None

    def on_activity_finished(self, entity, activity_name: str, activity_id: int, end_time: float):  # pragma: no cover - noop
        return None

    def on_resource_acquired(self, entity, resource, amount: int, time: float):  # pragma: no cover - noop
        return None

    def on_resource_released(self, entity, resource, amount: int, time: float):  # pragma: no cover - noop
        return None

    def on_log_event(self, event: dict[str, Any]):  # pragma: no cover - noop
        return None


class StreamingRunRecorder(RunRecorder):  # pragma: no cover - compatibility shim
    """Legacy streaming recorder that publishes a final snapshot only."""

    def __init__(self, collect_logs: bool = True, event_queue: Queue | None = None):
        super().__init__(collect_logs=collect_logs)
        self.event_queue: Queue = event_queue or Queue()

    def on_run_finished(self, env):
        super().on_run_finished(env)
        self.event_queue.put({"event": "run_finished", "run_data": self.run_data})
