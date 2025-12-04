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
    name_map = getattr(entity, "act_dic", {})
    schedule_records = _safe_records(entity.schedule)
    schedule_log: list[dict[str, Any]] = []
    activities: list[dict[str, Any]] = []

    for rec in schedule_records:
        activity = dict(rec)
        act_name = activity.get("activity") or activity.get("activity_name")
        if act_name and "activity_id" not in activity:
            activity["activity_id"] = name_map.get(act_name)

        start = activity.get("start_time") or activity.get("start")
        end = activity.get("finish_time") or activity.get("end")
        if start is not None and end is not None:
            try:
                activity["duration"] = float(end) - float(start)
            except Exception:
                activity["duration"] = None

        schedule_log.append(activity)
        activities.append(
            {
                "activity_id": activity.get("activity_id"),
                "activity_name": act_name,
                "start": start,
                "end": end,
                "duration": activity.get("duration"),
                "duration_info": activity.get("duration_info"),
                "sampled_duration": activity.get("sampled_duration"),
            }
        )

    waiting_time = _safe_array(entity.waiting_time)
    total_active = sum(act.get("duration", 0) or 0 for act in activities)
    total_waiting = sum(waiting_time)

    return {
        "id": getattr(entity, "id", None),
        "name": getattr(entity, "name", None),
        "type": entity.__class__.__name__,
        "created_at": getattr(entity, "created_at", None),
        "completed_at": getattr(entity, "completed_at", None),
        "activities": activities,
        "schedule_log": schedule_log,
        "status_log": _safe_records(entity.status_log),
        "waiting_log": _safe_records(entity.waiting_log),
        "waiting_time": waiting_time,
        "logs": _safe_records(lambda: getattr(entity, "logs", [])),
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
        "waiting_log": _safe_records(getattr(resource, "waiting_log", resource.queue_log)),
        "waiting_time": _safe_array(resource.waiting_time),
        "stats": _resource_stats(resource),
        "logs": _safe_records(lambda: getattr(resource, "logs", [])),
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

    logs = _safe_records(lambda: getattr(env, "logs", []))

    return RunSnapshot(environment=environment, entities=entities, resources=resources, logs=logs)
