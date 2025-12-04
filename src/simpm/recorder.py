"""Recording utilities for SimPM runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from queue import Queue
from typing import Any, Iterable, Protocol


def _to_records(table: Any) -> list[dict[str, Any]]:
    """Safely convert a pandas-like table to a list of dicts."""

    if table is None:
        return []
    try:
        if hasattr(table, "to_dict"):
            return table.to_dict(orient="records")  # type: ignore[arg-type]
        if isinstance(table, Iterable):
            return list(table)  # type: ignore[arg-type]
    except Exception:
        pass
    return []


def _to_list(array: Any) -> list[Any]:
    """Safely convert numpy-like arrays to plain Python lists."""

    if array is None:
        return []
    try:
        if hasattr(array, "tolist"):
            return array.tolist()
        if isinstance(array, Iterable) and not isinstance(array, (str, bytes)):
            return list(array)
    except Exception:
        pass
    return []


class SimulationObserver(Protocol):
    """Interface for receiving simulation events."""

    def on_run_started(self, env):
        ...

    def on_run_finished(self, env):
        ...

    def on_entity_created(self, entity):
        ...

    def on_resource_created(self, resource):
        ...

    def on_activity_started(
        self,
        entity,
        activity_name: str,
        activity_id: int,
        start_time: float,
        duration_info: dict[str, Any] | None = None,
    ):
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
class RunRecorder(SimulationObserver):
    """Collect structured data for a single simulation run."""

    collect_logs: bool = True
    env_name: str | None = None
    run_id: int | None = None
    start_time: float | None = None
    end_time: float | None = None
    entities: dict[int, dict[str, Any]] = field(default_factory=dict)
    resources: dict[int, dict[str, Any]] = field(default_factory=dict)
    logs: list[dict[str, Any]] = field(default_factory=list)

    def bootstrap_from_env(self, env):
        """Capture any entities or resources that existed before observers were registered."""
        for entity in env.entities:
            if entity.id not in self.entities:
                self.on_entity_created(entity)
        for res in env.resources:
            if res.id not in self.resources:
                self.on_resource_created(res)

    def on_run_started(self, env):
        self.env_name = env.name
        self.run_id = env.run_number
        self.start_time = env.now
        self.bootstrap_from_env(env)

    def on_run_finished(self, env):
        self.end_time = env.now
        # capture entity and resource log data that are only available after the run
        for entity in env.entities:
            self._populate_entity_logs(entity)

        for res in env.resources:
            self._populate_resource_logs(res)

    def on_entity_created(self, entity):
        self.entities[entity.id] = {
            "id": entity.id,
            "name": entity.name,
            "type": entity.__class__.__name__,
            "activities": [],
            "logs": [],
            "attributes": dict(getattr(entity, "_attributes", {})),
            "schedule_log": [],
            "status_log": [],
            "waiting_log": [],
            "waiting_time": [],
        }

    def on_resource_created(self, resource):
        self.resources[resource.id] = {
            "id": resource.id,
            "name": resource.name,
            "type": resource.__class__.__name__,
            "capacity": getattr(resource.container, "capacity", None),
            "initial_level": getattr(resource.container, "_init", None),
            "usage": [],
            "logs": [],
            "queue_log": [],
            "status_log": [],
            "waiting_time": [],
            "stats": {},
        }

    def on_activity_started(
        self,
        entity,
        activity_name: str,
        activity_id: int,
        start_time: float,
        duration_info: dict[str, Any] | None = None,
    ):
        entity_data = self.entities.setdefault(
            entity.id,
            {
                "id": entity.id,
                "name": entity.name,
                "type": entity.__class__.__name__,
                "activities": [],
                "logs": [],
                "attributes": dict(getattr(entity, "_attributes", {})),
            },
        )
        entity_data["activities"].append(
            {
                "activity_id": activity_id,
                "activity_name": activity_name,
                "start": start_time,
                "end": None,
                "duration_info": duration_info,
                "sampled_duration": duration_info.get("sampled_duration") if duration_info else None,
            }
        )

    def on_activity_finished(self, entity, activity_name: str, activity_id: int, end_time: float):
        entity_data = self.entities.get(entity.id)
        if not entity_data:
            return
        for activity in reversed(entity_data["activities"]):
            if activity["activity_id"] == activity_id and activity["end"] is None:
                activity["end"] = end_time
                activity["duration"] = end_time - activity["start"]
                break
        # refresh schedule/status/waiting logs so dashboards can display data during long runs
        self._populate_entity_logs(entity)

    def on_resource_acquired(self, entity, resource, amount: int, time: float):
        resource_data = self.resources.get(resource.id)
        if resource_data is None:
            self.on_resource_created(resource)
            resource_data = self.resources[resource.id]
        resource_data["usage"].append(
            {
                "time": time,
                "delta": amount,
                "entity_id": entity.id,
                "action": "acquired",
            }
        )
        self._populate_resource_logs(resource)
        self._populate_entity_logs(entity)

    def on_resource_released(self, entity, resource, amount: int, time: float):
        resource_data = self.resources.get(resource.id)
        if resource_data is None:
            self.on_resource_created(resource)
            resource_data = self.resources[resource.id]
        resource_data["usage"].append(
            {
                "time": time,
                "delta": -amount,
                "entity_id": entity.id,
                "action": "released",
            }
        )
        self._populate_resource_logs(resource)
        self._populate_entity_logs(entity)

    def on_log_event(self, event: dict[str, Any]):
        if not self.collect_logs:
            return
        self.logs.append(event)
        source_type = event.get("source_type")
        source_id = event.get("source_id")
        if source_type == "entity" and source_id in self.entities:
            self.entities[source_id]["logs"].append(event)
        elif source_type == "activity":
            entity_id = event.get("metadata", {}).get("entity_id")
            if entity_id and entity_id in self.entities:
                self.entities[entity_id]["logs"].append(event)
        elif source_type == "resource" and source_id in self.resources:
            self.resources[source_id]["logs"].append(event)

    def _populate_entity_logs(self, entity):
        ent_data = self.entities.get(entity.id)
        if not ent_data:
            return
        try:
            ent_data["schedule_log"] = _to_records(entity.schedule())
            ent_data["status_log"] = _to_records(entity.status_log())
            ent_data["waiting_log"] = _to_records(entity.waiting_log())
            ent_data["waiting_time"] = _to_list(entity.waiting_time())
        except Exception:
            # best effort capture; don't break finalization if a log is unavailable
            return

    def _populate_resource_logs(self, resource):
        res_data = self.resources.get(resource.id)
        if not res_data:
            return
        try:
            res_data["queue_log"] = _to_records(resource.queue_log())
            res_data["status_log"] = _to_records(resource.status_log())
            res_data["waiting_time"] = _to_list(resource.waiting_time())
            res_data["stats"] = {
                "average_queue_length": resource.average_queue_length(),
                "average_utilization": resource.average_utilization(),
                "average_idleness": resource.average_idleness(),
                "average_level": resource.average_level(),
                "total_time_idle": resource.total_time_idle(),
                "total_time_in_use": resource.total_time_in_use(),
            }
        except Exception:
            return

    @property
    def run_data(self) -> dict[str, Any]:
        return {
            "environment": {
                "name": self.env_name,
                "run_id": self.run_id,
                "time": {"start": self.start_time, "end": self.end_time},
            },
            "entities": list(self.entities.values()),
            "resources": list(self.resources.values()),
            "logs": self.logs,
        }


class StreamingRunRecorder(RunRecorder):
    """A recorder that also streams events through a queue for live dashboards."""

    def __init__(self, collect_logs: bool = True, event_queue: Queue | None = None):
        super().__init__(collect_logs=collect_logs)
        self.event_queue: Queue = event_queue or Queue()

    def _enqueue(self, event_type: str, payload: dict[str, Any]):
        self.event_queue.put({"event": event_type, **payload})

    def on_run_started(self, env):
        super().on_run_started(env)
        self._enqueue("run_started", {"env_name": self.env_name, "run_id": self.run_id, "time": env.now})

    def on_run_finished(self, env):
        super().on_run_finished(env)
        self._enqueue("run_finished", {"time": env.now})
        # send full snapshots so live dashboards receive queue/status logs captured at
        # the end of the run
        for entity in self.entities.values():
            self._enqueue("entity_snapshot", {"entity": entity})
        for resource in self.resources.values():
            self._enqueue("resource_snapshot", {"resource": resource})

    def on_entity_created(self, entity):
        super().on_entity_created(entity)
        self._enqueue("entity_created", {"entity": self.entities[entity.id]})

    def on_resource_created(self, resource):
        super().on_resource_created(resource)
        self._enqueue("resource_created", {"resource": self.resources[resource.id]})

    def on_activity_started(
        self,
        entity,
        activity_name: str,
        activity_id: int,
        start_time: float,
        duration_info: dict[str, Any] | None = None,
    ):
        super().on_activity_started(entity, activity_name, activity_id, start_time, duration_info)
        self._enqueue(
            "activity_started",
            {
                "entity_id": entity.id,
                "activity": {
                    "activity_id": activity_id,
                    "activity_name": activity_name,
                    "start": start_time,
                    "end": None,
                    "duration_info": duration_info,
                    "sampled_duration": duration_info.get("sampled_duration") if duration_info else None,
                },
            },
        )

    def on_activity_finished(self, entity, activity_name: str, activity_id: int, end_time: float):
        super().on_activity_finished(entity, activity_name, activity_id, end_time)
        # send an updated snapshot so live dashboards can show schedule/status logs mid-run
        self._enqueue("entity_snapshot", {"entity": self.entities.get(entity.id, {})})
        self._enqueue(
            "activity_finished",
            {
                "entity_id": entity.id,
                "activity_id": activity_id,
                "end_time": end_time,
            },
        )

    def on_resource_acquired(self, entity, resource, amount: int, time: float):
        super().on_resource_acquired(entity, resource, amount, time)
        self._enqueue("resource_snapshot", {"resource": self.resources.get(resource.id, {})})
        self._enqueue(
            "resource_acquired",
            {"entity_id": entity.id, "resource_id": resource.id, "amount": amount, "time": time},
        )

    def on_resource_released(self, entity, resource, amount: int, time: float):
        super().on_resource_released(entity, resource, amount, time)
        self._enqueue("resource_snapshot", {"resource": self.resources.get(resource.id, {})})
        self._enqueue(
            "resource_released",
            {"entity_id": entity.id, "resource_id": resource.id, "amount": amount, "time": time},
        )

    def on_log_event(self, event: dict[str, Any]):
        super().on_log_event(event)
        if self.collect_logs:
            self._enqueue("log", {"payload": event})
