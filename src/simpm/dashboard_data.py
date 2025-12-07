"""Utilities to read simulation results directly from environment logs.

The helpers in this module avoid additional recorder layers and derive
dashboard-friendly structures from the logs that SimPM already maintains when
``log=True`` is set on entities and resources. They are safe to call in custom
post-processing scripts as well as inside the Streamlit dashboard runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pandas as pd

try:  # pragma: no cover - optional dependency at runtime
    import numpy as np

    _NUMERIC_TYPES = (np.integer, np.floating, np.bool_)
    _ARRAY_TYPES = (np.ndarray,)
except Exception:  # pragma: no cover - numpy not required for core logic
    _NUMERIC_TYPES = ()
    _ARRAY_TYPES = ()

from simpm._utils import _swap_dict_keys_values

_ENTITY_RESERVED_ATTRS = {
    "env",
    "name",
    "id",
    "last_act_id",
    "act_dic",
    "print_actions",
    "log",
    "using_resources",
    "pending_requests",
}

_RESOURCE_RESERVED_ATTRS = {
    "env",
    "name",
    "id",
    "container",
    "print_actions",
    "log",
}


def _safe_records(getter: Callable[[], Any]) -> list[dict[str, Any]]:
    """Invoke ``getter`` and coerce the result into a list of dictionaries.

    The function shields callers from failures when optional dependencies (such
    as pandas) are not present or when an object raises exceptions during
    conversion. Non-tabular objects result in an empty list.
    """
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
    """Invoke ``getter`` and coerce iterables into a plain Python list."""
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


def _to_jsonable(value: Any) -> Any:
    """Recursively coerce values into JSON-serializable objects.

    Parameters
    ----------
    value : Any
        Arbitrary object pulled from a simulation log.

    Returns
    -------
    Any
        A JSON-friendly structure comprised of dictionaries, lists, and
        primitives. Pandas and NumPy containers are converted to built-in
        Python equivalents.
    """

    if isinstance(value, dict):
        return {key: _to_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_jsonable(val) for val in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, pd.Timedelta):
        return value.isoformat()
    if _NUMERIC_TYPES and isinstance(value, _NUMERIC_TYPES):
        try:
            return value.item()
        except Exception:
            return int(value)
    if _ARRAY_TYPES and isinstance(value, _ARRAY_TYPES):
        return value.tolist()
    if hasattr(value, "tolist") and not isinstance(value, (str, bytes)):
        try:
            return value.tolist()
        except Exception:
            return value
    if hasattr(value, "to_dict"):
        try:
            return _to_jsonable(value.to_dict())
        except Exception:
            return str(value)
    if isinstance(value, pd.Interval):
        return str(value)
    return value


def _collect_attributes(obj: Any, reserved_keys: set[str], *, include_public: bool = True) -> dict[str, Any]:
    """Gather attribute dictionaries and optional public attributes for display."""

    base_attributes = getattr(obj, "attributes", None) or getattr(obj, "attr", None) or {}
    attributes: dict[str, Any] = {k: _to_jsonable(v) for k, v in base_attributes.items()}

    if include_public:
        for key, value in getattr(obj, "__dict__", {}).items():
            if key.startswith("_") or key in reserved_keys:
                continue
            if callable(value):
                continue
            attributes.setdefault(key, _to_jsonable(value))

    return attributes


def _entity_snapshot(entity) -> dict[str, Any]:
    """Build a serializable snapshot of an entity and its recorded activity."""
    name_map = dict(getattr(entity, "act_dic", {}))
    reverse_name_map = {val: key for key, val in name_map.items()}
    schedule_records = _safe_records(entity.schedule)
    schedule_log: list[dict[str, Any]] = []
    activities: list[dict[str, Any]] = []

    for rec in schedule_records:
        activity = dict(rec)
        act_name = activity.get("activity") or activity.get("activity_name")
        act_id = activity.get("activity_id")

        if act_id is None and act_name:
            act_id = name_map.get(act_name)
            if act_id is None:
                act_id = max(name_map.values(), default=0) + 1
                name_map[act_name] = act_id
                reverse_name_map[act_id] = act_name
        if act_name is None and act_id is not None:
            act_name = reverse_name_map.get(act_id) or f"Activity {act_id}"

        activity["activity_id"] = act_id
        activity["activity_name"] = act_name
        if "activity" not in activity:
            activity["activity"] = act_name

        start = activity.get("start_time")
        if start is None:
            start = activity.get("start")

        end = activity.get("finish_time")
        if end is None:
            end = activity.get("end")
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
    waiting_log = _safe_records(entity.waiting_log)
    for rec in waiting_log:
        if "waiting_duration" not in rec and {"start_waiting", "end_waiting"}.issubset(rec):
            try:
                rec["waiting_duration"] = float(rec.get("end_waiting", 0)) - float(rec.get("start_waiting", 0))
            except Exception:
                rec["waiting_duration"] = None
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
        "waiting_log": waiting_log,
        "waiting_time": waiting_time,
        "logs": _safe_records(lambda: getattr(entity, "logs", [])),
        "total_active_time": total_active,
        "total_waiting_time": total_waiting,
        "attributes": _collect_attributes(entity, _ENTITY_RESERVED_ATTRS, include_public=True),
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
    """Create a serializable view of a resource and its metrics."""

    queue_records = _safe_records(resource.queue_log)
    for rec in queue_records:
        if "waiting_duration" not in rec and {"start_time", "finish_time"}.issubset(rec):
            try:
                rec["waiting_duration"] = float(rec.get("finish_time", 0)) - float(rec.get("start_time", 0))
            except Exception:
                rec["waiting_duration"] = None

    return {
        "id": resource.id,
        "name": resource.name,
        "type": resource.__class__.__name__,
        "capacity": getattr(resource.container, "capacity", None),
        "initial_level": getattr(resource.container, "_init", None),
        "queue_log": queue_records,
        "status_log": _safe_records(resource.status_log),
        "waiting_time": _safe_array(resource.waiting_time),
        "stats": _resource_stats(resource),
        "logs": _safe_records(lambda: getattr(resource, "logs", [])),
        "attributes": _collect_attributes(resource, _RESOURCE_RESERVED_ATTRS, include_public=False),
    }


@dataclass
class RunSnapshot:
    """Lightweight snapshot of an environment for dashboards/tests.

    The snapshot groups environment metadata, entity state, resource state, and
    the raw event log into a single object that can be serialized or passed to
    :class:`simpm.dashboard.StreamlitDashboard`.
    """

    environment: dict[str, Any]
    entities: list[dict[str, Any]]
    resources: list[dict[str, Any]]
    logs: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        """Convert the snapshot into a JSON-friendly dictionary."""

        return _to_jsonable(
            {
                "environment": self.environment,
                "entities": self.entities,
                "resources": self.resources,
                "logs": self.logs,
            }
        )


def collect_run_data(env) -> RunSnapshot:
    """Create a dashboard-ready snapshot directly from environment logs.

    Parameters
    ----------
    env : simpm.des.Environment
        Simulation environment that has already executed.

    Returns
    -------
    RunSnapshot
        Structured view of entities, resources, and environment logs suitable
        for serializing to JSON or handing to the dashboard.

    Examples
    --------
    >>> snapshot = collect_run_data(env)
    >>> snapshot.environment['name']
    'Environment'
    >>> len(snapshot.entities)  # doctest: +SKIP
    3
    """

    entities = [_entity_snapshot(entity) for entity in getattr(env, "entities", [])]
    resources = [_resource_snapshot(res) for res in getattr(env, "resources", [])]
    environment = {
        "name": getattr(env, "name", "Environment"),
        "run_id": getattr(env, "run_number", None),
        "time": {"start": None, "end": getattr(env, "now", None)},
    }

    logs = _safe_records(lambda: getattr(env, "logs", []))

    return RunSnapshot(environment=environment, entities=entities, resources=resources, logs=logs)
