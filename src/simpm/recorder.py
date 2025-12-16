"""Backward-compatible stubs for deprecated recorder classes.

SimPM used to require attaching recorder objects to environments in order to
gather metrics. The dashboard now reads directly from the environment logs, so
these recorders exist solely to avoid breaking older code. They capture a final
snapshot after a run finishes and expose the same public attributes as the
legacy implementations.
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

    The class keeps the historical ``run_data`` attribute while avoiding the
    overhead of tracking every intermediate event. Register it as an observer
    on an environment to populate ``run_data`` automatically when the
    simulation finishes.
    """

    collect_logs: bool = True
    run_data: dict[str, Any] = field(default_factory=dict)
    _env: Any | None = None

    def on_run_started(self, env, run_id=None, start_time=None):
        """Store the environment reference when a run begins."""

        self._env = env

    def on_run_finished(self, env, run_id=None, start_time=None, end_time=None, duration=None):
        """Collect a final dashboard snapshot when the run ends."""

        self._env = env
        self.run_data = collect_run_data(env).as_dict()

    # Remaining callbacks are retained for API compatibility.
    def on_entity_created(self, entity):  # pragma: no cover - noop
        """Retained for compatibility; no per-entity tracking is performed."""
        return None

    def on_resource_created(self, resource):  # pragma: no cover - noop
        """Retained for compatibility; no per-resource tracking is performed."""
        return None

    def on_activity_started(self, entity, activity_name: str, activity_id: int, start_time: float, duration_info: dict[str, Any] | None = None):  # pragma: no cover - noop
        """Retained for compatibility; activity state is not mirrored."""
        return None

    def on_activity_finished(self, entity, activity_name: str, activity_id: int, end_time: float):  # pragma: no cover - noop
        """Retained for compatibility; activity state is not mirrored."""
        return None

    def on_resource_acquired(self, entity, resource, amount: int, time: float):  # pragma: no cover - noop
        """Retained for compatibility; resource usage is not mirrored."""
        return None

    def on_resource_released(self, entity, resource, amount: int, time: float):  # pragma: no cover - noop
        """Retained for compatibility; resource usage is not mirrored."""
        return None

    def on_log_event(self, event: dict[str, Any]):  # pragma: no cover - noop
        """Retained for compatibility; log events are ignored."""
        return None


class StreamingRunRecorder(RunRecorder):  # pragma: no cover - compatibility shim
    """Legacy streaming recorder that publishes a final snapshot only.

    The original class streamed events to an external listener. The simplified
    version only pushes a single ``run_finished`` event containing the final
    snapshot, which is often sufficient for tests or small utilities expecting
    the legacy shape.
    """

    def __init__(self, collect_logs: bool = True, event_queue: Queue | None = None):
        super().__init__(collect_logs=collect_logs)
        self.event_queue: Queue = event_queue or Queue()

    def on_run_finished(self, env, run_id=None, start_time=None, end_time=None, duration=None):
        """Forward the final snapshot through the event queue."""

        super().on_run_finished(env, run_id=run_id, start_time=start_time, end_time=end_time, duration=duration)
        self.event_queue.put({"event": "run_finished", "run_data": self.run_data})
