"""Utilities to read simulation results directly from environment logs.

The helpers in this module avoid any additional observer/recorder layers and
derive dashboard-friendly structures from the logs that SimPM already
maintains when ``log=True`` is set on entities and resources.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from simpm._utils import _swap_dict_keys_values


def _safe_records(getter: Callable[[], Any]) -> list[dict[str, Any]]:
    try:
        table = getter()
        if hasattr(table, "to_dict"):
            return table.to_dict(orient="records")  # type: ignore[arg-type]
        if isinstance(table, list):
            return table
    except Exception:
        return []
    return []


def _safe_array(getter: Callable[[], Any]) -> list[Any]:
    try:
        values = getter()
        if hasattr(values, "tolist"):
            return list(values.tolist())
        if isinstance(values, list):
            return values
        if values is None:
            return []
        if hasattr(values, "__iter__") and not isinstance(values, (str, bytes)):
            return list(values)
    except Exception:
        return []
    return []


def _entity_snapshot(entity) -> dict[str, Any]:
    name_map = _swap_dict_keys_values(getattr(entity, "act_dic", {}))
    activities = []
    for raw in getattr(entity, "_schedule_log", [])[1:]:
        try:
            act_id, start, end = raw
        except Exception:
            continue
        act_name = name_map.get(act_id, act_id)
        activity = {
            "activity_id": int(act_id),
            "activity_name": act_name,
            "start": float(start),
            "end": float(end),
        }
        if end is not None:
            activity["duration"] = float(end) - float(start)
        activities.append(activity)

    waiting_time = _safe_array(entity.waiting_time)
    total_active = sum(act.get("duration", 0) for act in activities)
    total_waiting = sum(waiting_time)

    return {
        "id": entity.id,
        "name": entity.name,
        "type": entity.__class__.__name__,
        "activities": activities,
        "schedule_log": _safe_records(entity.schedule),
        "status_log": _safe_records(entity.status_log),
        "waiting_log": _safe_records(entity.waiting_log),
        "waiting_time": waiting_time,
        "total_active_time": total_active,
        "total_waiting_time": total_waiting,
    }


def _resource_stats(resource) -> dict[str, Any]:
    try:
        return {
            "average_queue_length": resource.average_queue_length(),
            "average_utilization": resource.average_utilization(),
            "average_idleness": resource.average_idleness(),
            "average_level": resource.average_level(),
            "total_time_idle": resource.total_time_idle(),
            "total_time_in_use": resource.total_time_in_use(),
        }
    except Exception:
        return {}


def _resource_snapshot(resource) -> dict[str, Any]:
    return {
        "id": resource.id,
        "name": resource.name,
        "type": resource.__class__.__name__,
        "capacity": getattr(resource.container, "capacity", None),
        "initial_level": getattr(resource.container, "_init", None),
        "queue_log": _safe_records(resource.queue_log),
        "status_log": _safe_records(resource.status_log),
        "waiting_time": _safe_array(resource.waiting_time),
        "stats": _resource_stats(resource),
    }


@dataclass
class RunSnapshot:
    """Lightweight snapshot of an environment for dashboards/tests."""

    environment: dict[str, Any]
    entities: list[dict[str, Any]]
    resources: list[dict[str, Any]]
    logs: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "environment": self.environment,
            "entities": self.entities,
            "resources": self.resources,
            "logs": self.logs,
        }


def collect_run_data(env) -> RunSnapshot:
    """Create a dashboard-ready snapshot directly from environment logs."""

    entities = [_entity_snapshot(entity) for entity in getattr(env, "entities", [])]
    resources = [_resource_snapshot(res) for res in getattr(env, "resources", [])]
    environment = {
        "name": getattr(env, "name", "Environment"),
        "run_id": getattr(env, "run_number", None),
        "time": {"start": None, "end": getattr(env, "now", None)},
    }

    return RunSnapshot(environment=environment, entities=entities, resources=resources, logs=[])
