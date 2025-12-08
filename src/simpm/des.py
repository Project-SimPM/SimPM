"""Discrete Event Simulation primitives for project-management style models.

This module wraps :mod:`simpy` with opinionated helpers for creating entities,
resources, and environments that can be logged and observed while a simulation
is running. The docstrings are intentionally verbose so that API documentation
generated from them provides ready-to-use guidance and code snippets.
"""
from __future__ import annotations
from typing import Any, TYPE_CHECKING, Callable, List, Union
from bisect import insort_left
from pandas import DataFrame
from numpy import array, append, divide, nansum, zeros_like
import simpy
from simpy.events import Event
from .dashboard import run_post_dashboard
import sys

if TYPE_CHECKING:  # pragma: no cover - type hinting only
    from simpm.recorder import SimulationObserver

from simpm.dist import distribution
from simpm._utils import _swap_dict_keys_values


def _describe_duration(duration: Any) -> dict[str, Any]:
    """Normalize a duration input and capture the sampled value.

    Parameters
    ----------
    duration : float | int | distribution | None
        Either a fixed numeric duration, a :class:`simpm.dist.distribution`
        instance (any subclass with a ``sample`` method), or ``None`` when the
        caller does not yet know the duration.

    Returns
    -------
    dict[str, Any]
        A dictionary describing the duration with keys:

        ``type``
            ``"fixed"`` for numeric durations, ``"unknown"`` for ``None``, or
            the distribution class name for stochastic durations.
        ``parameters``
            Raw parameters of the distribution or the fixed value provided by
            the caller.
        ``sampled_duration``
            The positive sample used for the current activity. When a
            distribution is provided, the helper draws until a non-negative
            value is produced.
    """

    def _sample_positive(dist: distribution) -> float:
        sampled = -1
        while sampled < 0:
            sampled = dist.sample()
        return sampled

    if isinstance(duration, distribution):
        sampled_duration = _sample_positive(duration)
        return {
            "type": getattr(duration, "dist_type", type(duration).__name__),
            "parameters": getattr(duration, "params", None),
            "sampled_duration": sampled_duration,
        }

    return {
        "type": "fixed" if duration is not None else "unknown",
        "parameters": duration,
        "sampled_duration": duration,
    }


class Preempted(Exception):
    """Raised when an interruptible activity is preempted by a resource.

    The exception captures who caused the interruption and for how long the
    entity had been using the resource, allowing callers to log or react to the
    preemption in higher-level processes.
    """

    def __init__(self, by, resource, usage_since, message: str = "Activity preempted"):
        super().__init__(message, by, resource, usage_since)
        self.by = by
        self.resource = resource
        self.usage_since = usage_since


class Entity:
    """Dictionary-like item that moves through a :class:`Environment`.

    Entities are the actors in a simulation. They hold arbitrary attributes,
    start and finish activities, wait on resources, and emit lifecycle events
    that can be observed or logged.
    """

    def __init__(self, env: "Environment", name: str, print_actions: bool = False, log: bool = True):
        """Create a new entity and register it with the environment.

        Parameters
        ----------
        env : Environment
            Simulation environment that will host the entity.
        name : str
            Human-readable base name (an id suffix is added automatically).
        print_actions : bool, optional
            When ``True``, echo major lifecycle events to stdout.
        log : bool, optional
            When ``True``, capture schedule, status, and wait-time logs for
            later analysis.
        """
        self._attributes: dict[str, Any] = {}
        self.env = env
        self.name = name
        env.last_entity_id += 1
        self.id = self.env.last_entity_id  # pylint: disable=invalid-name
        env.entity_names[self.id] = self.name + "(" + str(self.id) + ")"
        env.entities.append(self)
        self.last_act_id: int = 0
        self.act_dic: dict[str, int] = {}
        self.print_actions: bool = print_actions
        self.log: bool = log
        self.using_resources: dict["GeneralResource", int] = {}  # resources currently held
        self._current_process: simpy.events.Process | None = None
        self._current_interruptible: str | None = None
        self._current_timeout: Event | None = None

        # logs
        # act_id, act_start_time, act_finish_time
        self._schedule_log = array([[0, 0, 0]])
        # status codes for compact logging
        self._status_codes = {"wait for": 1, "get": 2, "start": 3, "finish": 4, "put": 5, "add": 6}
        # time, entity_status_code, actid/resid
        self._status_log = array([[0, 0, 0]])
        # resource_id, start_waiting, end_waiting, amount waiting for
        self._waiting_log = array([[0, 0, 0, 0]])
        # simpy request handles that are not yet granted
        self.pending_requests: list[Any] = []

        if print_actions:
            print(name + "(" + str(self.id) + ") is created, sim_time:", env.now)

        self.env._notify_observers("on_entity_created", entity=self)

    def __str__(self) -> str:
        """Return ``"<name> (<id>)"`` for quick debugging output."""
        return f"{self.name} ({self.id})"

    def __repr__(self) -> str:
        """Detailed representation including environment and flags."""
        return f"Entity({self.env}, {self.name}, print_actions={self.print_actions}, log={self.log})"

    def __getitem__(self, key: str) -> Any:
        """Return an attribute value stored on the entity."""
        return self._attributes[key]

    def __setitem__(self, key: str, value: Any):
        """Attach an attribute to the entity."""
        if not isinstance(key, str):
            raise TypeError("Attribute keys must be strings")
        self._attributes[key] = value

    def __delitem__(self, key):
        """Delete an attribute from the entity."""
        del self._attributes[key]

    def __contains__(self, key):
        """Return ``True`` when an attribute exists on the entity."""
        return key in self._attributes

    def _activity(self, name: str, duration: Any):
        """Run a non-interruptible activity for the given duration."""
        duration_info = _describe_duration(duration)
        duration_value = duration_info["sampled_duration"]
        if self.print_actions:
            print(self.name + "(" + str(self.id) + ") started", name, ", sim_time:", self.env.now)

        if name not in self.act_dic:
            self.last_act_id += 1
            self.act_dic[name] = self.last_act_id
        if self.log:
            self._schedule_log = append(
                self._schedule_log,
                [[self.act_dic[name], self.env.now, self.env.now + duration_value]],
                axis=0,
            )
            self._status_log = append(
                self._status_log,
                [[self.env.now, self._status_codes["start"], self.act_dic[name]]],
                axis=0,
            )

        self.env._notify_observers(
            "on_activity_started",
            entity=self,
            activity_name=name,
            activity_id=self.act_dic[name],
            start_time=self.env.now,
            duration_info=duration_info,
        )

        if self.log:
            self.env.log_event(
                source_type="activity",
                source_id=self.act_dic[name],
                message=f"Activity {name} started",
                metadata={
                    "entity_id": self.id,
                    "activity_name": name,
                    "duration": duration_info,
                },
            )

        yield self.env.timeout(duration_value)

        if self.print_actions:
            print(self.name + "(" + str(self.id) + ") finished", name, ", sim_time:", self.env.now)
        if self.log:
            self._status_log = append(
                self._status_log,
                [[self.env.now, self._status_codes["finish"], self.act_dic[name]]],
                axis=0,
            )

        self.env._notify_observers(
            "on_activity_finished",
            entity=self,
            activity_name=name,
            activity_id=self.act_dic[name],
            end_time=self.env.now,
        )

        if self.log:
            self.env.log_event(
                source_type="activity",
                source_id=self.act_dic[name],
                message=f"Activity {name} finished",
                metadata={"entity_id": self.id, "activity_name": name},
            )

    def _interruptive_activity(self, name: str, duration: Any):
        """Run an activity that can be interrupted by preemptive resources."""
        duration_info = _describe_duration(duration)
        duration_value = duration_info["sampled_duration"]
        if self.print_actions:
            print(self.name + "(" + str(self.id) + ") started", name, ", sim_time:", self.env.now)

        if name not in self.act_dic:
            self.last_act_id += 1
            self.act_dic[name] = self.last_act_id
        if self.log:
            self._schedule_log = append(
                self._schedule_log,
                [[self.act_dic[name], self.env.now, self.env.now + duration_value]],
                axis=0,
            )
            self._status_log = append(
                self._status_log,
                [[self.env.now, self._status_codes["start"], self.act_dic[name]]],
                axis=0,
            )

        self.env._notify_observers(
            "on_activity_started",
            entity=self,
            activity_name=name,
            activity_id=self.act_dic[name],
            start_time=self.env.now,
            duration_info=duration_info,
        )

        if self.log:
            self.env.log_event(
                source_type="activity",
                source_id=self.act_dic[name],
                message=f"Activity {name} started",
                metadata={
                    "entity_id": self.id,
                    "activity_name": name,
                    "duration": duration_info,
                },
            )

        done_in = duration_value
        self._current_interruptible = name
        try:
            while done_in:
                try:
                    start = self.env.now
                    self._current_timeout = self.env.timeout(done_in)
                    yield self._current_timeout
                    done_in = 0
                except simpy.Interrupt as interrupt:
                    done_in -= self.env.now - start
                    if isinstance(interrupt.cause, Preempted):
                        return
                except Preempted:
                    done_in -= self.env.now - start
                    return
        finally:
            self._current_timeout = None
            self._current_interruptible = None
            self._current_process = None

    def _on_preempted(self, resource: "PreemptiveResource", cause: Preempted):
        """Propagate a preemption into the current interruptible activity."""

        if self._current_process is not None and not self._current_process.triggered:
            self._current_process.interrupt(cause)

        activity_name = self._current_interruptible

        if activity_name is None:
            if self.print_actions:
                print(
                    f"{self.name}({self.id}) was preempted but no activity was recorded as running, sim_time: {self.env.now}"
                )
            return

        if self.print_actions:
            print(self.name + "(" + str(self.id) + ") finished", activity_name, ", sim_time:", self.env.now)
        if self.log:
            self._status_log = append(
                self._status_log,
                [[self.env.now, self._status_codes["finish"], self.act_dic[activity_name]]],
                axis=0,
            )

        self.env._notify_observers(
            "on_activity_finished",
            entity=self,
            activity_name=activity_name,
            activity_id=self.act_dic[activity_name],
            end_time=self.env.now,
        )

        if self.log:
            self.env.log_event(
                source_type="activity",
                source_id=self.act_dic[activity_name],
                message=f"Activity {activity_name} finished",
                metadata={"entity_id": self.id, "activity_name": activity_name},
            )

    @property
    def attributes(self) -> dict[str, Any]:
        """
        Get the dictionary of all attributes of the entity.
        """
        return self._attributes

    @attributes.setter
    def attributes(self, value: dict[str, Any]) -> None:
        """
        Set the dictionary of all attributes of the entity.
        """
        if not isinstance(value, dict):
            raise TypeError("Attribute values must be stored in a dictionary.")
        self._attributes = value

    def do(self, name: str, dur: Any):
        """
        Defines the activity that the entity is doing.

        Parameters
        ----------
        name : str
            Name of the activity
        dur : float | int | distribution
            The duration of that activity
        """
        try:
            return self.env.process(self._activity(name, dur))
        except Exception:
            print("simpm: error in duration of activity", name)

    def interruptive_do(self, name: str, dur: Any):
        """Start an interruptible activity."""
        try:
            self._current_process = self.env.process(self._interruptive_activity(name, dur))
            return self._current_process
        except Exception:
            print("simpm: error in duration of interruptible activity", name)

    def get(
        self,
        res: "GeneralResource | PriorityResource | PreemptiveResource",
        amount: int = 1,
        priority: int = 1,
        preempt: bool = False,
    ):
        """
        Entity requests to get a resource using this method.
        """
        try:
            if isinstance(amount, distribution):
                a = -1.0
                while a < 0:
                    a = amount.sample()
                amount = int(a)
            if isinstance(res, PreemptiveResource):
                if amount > 1:
                    print("Warning: amount of preemptive resource is always 1")
                    amount = 1
                return self.env.process(res.get(self, amount, priority, preempt))
            if isinstance(res, PriorityResource):
                return self.env.process(res.get(self, amount, priority))
            if isinstance(res, Resource):
                return self.env.process(res.get(self, amount))
        except Exception:
            print("simpm: error in get")

    def add(self, res: "GeneralResource", amount: int = 1):
        """
        Entity increases the number of resources using this method.
        """
        if isinstance(amount, distribution):
            a = -1.0
            while a < 0:
                a = amount.sample()
            amount = int(a)
        return self.env.process(res.add(self, amount))

    def put(self, res: "GeneralResource | PreemptiveResource", amount: int = 1, request=None):
        """
        Entity puts back the resources using this method.
        """
        if isinstance(amount, distribution):
            a = -1.0
            while a < 0:
                a = amount.sample()
            amount = int(a)
        if isinstance(res, PreemptiveResource):
            if amount > 1:
                amount = 1
                print("Warning: amount of preemptive resource is always 1")
            return res.put(self, request)
        return self.env.process(res.put(self, amount))

    def is_pending(self, res: "GeneralResource", amount: int = 1) -> bool:
        """
        Check if the entity is waiting for a resource request.
        """
        for r in res.request_list:
            if r.entity == self and r.amount == amount:
                return True
        return False

    def not_pending(self, res: "GeneralResource", amount: int = 1) -> bool:
        """Convenience inverse of :meth:`is_pending`."""
        return not self.is_pending(res, amount)

    def cancel(self, res: "GeneralResource", amount: int = 1):
        """
        Cancels a resource request if it is pending, and puts it back if it is already granted.
        """
        for r in res.request_list:
            if r.entity == self and r.amount == amount:
                res.cancel(r)
                return

        # If not found in the queue, assume we already got it and must put it back.
        self.put(res, amount)

    def schedule(self) -> DataFrame:
        """
        Return a DataFrame with activity name and start/finish times.
        """
        df = DataFrame(data=self._schedule_log[1:, :], columns=["activity", "start_time", "finish_time"])
        df["activity"] = df["activity"].map(_swap_dict_keys_values(self.act_dic))
        return df

    def waiting_log(self) -> DataFrame:
        """
        Return a DataFrame with waiting episodes for resources.
        """
        df = DataFrame(data=self._waiting_log[1:, :], columns=["resource", "start_waiting", "end_waiting", "resource_amount"])
        df["resource"] = df["resource"].map(self.env.resource_names)
        df["waiting_duration"] = df["end_waiting"] - df["start_waiting"]
        return df

    def waiting_time(self):
        """
        Return the waiting durations of the entity each time it waited for a resource.
        """
        a = self.waiting_log()
        a = a["end_waiting"] - a["start_waiting"]
        return a.values

    def status_log(self) -> DataFrame:
        """
        Return a DataFrame with status changes (wait, get, start, finish, put, add).
        """
        df = DataFrame(data=self._status_log[1:, :], columns=["time", "status", "actid/resid"])
        df["status"] = df["status"].map(_swap_dict_keys_values(self._status_codes))
        return df


"""
*****************************************
*****Resource Class*******************
*****************************************
"""


class GeneralResource:
    """Common bookkeeping shared by all resource types.

    The class keeps track of queue lengths, idle capacity, and historical logs
    so higher-level resources only need to implement queuing semantics.
    """

    def __init__(self, env: "Environment", name: str, capacity: int, init: int, print_actions: bool = False, log: bool = True):
        """Create a basic resource container and register it with the environment."""
        self.name = name
        self.env = env
        self.log = log
        self.print_actions = print_actions
        env.last_res_id += 1
        self.id = env.last_res_id
        env.resource_names[self.id] = self.name + "(" + str(self.id) + ")"
        env.resources.append(self)
        self.in_use = 0
        self.idle = init
        self.container = simpy.Container(env, capacity, init)
        self.queue_length = 0  # number of entities waiting for a resource
        self.request_list: list[Any] = []
        self.attr: dict[str, Any] = {}  # attributes for resources

        # logs
        # time, in-use, idle, queue-length
        self._status_log = array([[0, 0, 0, 0]])
        # entityid, startTime, endTime, amount
        self._queue_log = array([[0, 0, 0, 0]])

        self.env._notify_observers("on_resource_created", resource=self)

    def queue_log(self) -> DataFrame:
        """
        Return a DataFrame of all waiting episodes at this resource.
        """
        df = DataFrame(data=self._queue_log[1:, :], columns=["entity", "start_time", "finish_time", "resource_amount"])
        df["entity"] = df["entity"].map(self.env.entity_names)
        df["waiting_duration"] = df["finish_time"] - df["start_time"]
        return df

    def status_log(self) -> DataFrame:
        """
        Return a DataFrame of resource status over time.
        """
        df = DataFrame(data=self._status_log[1:, :], columns=["time", "in_use", "idle", "queue_length"])
        return df

    def waiting_time(self):
        """
        Return waiting durations for this resource.
        """
        a = self.queue_log()
        a = a["finish_time"] - a["start_time"]
        return a.values

    def average_utilization(self):
        """
        Return the average utilization for the resource.
        """
        l = self.status_log()
        if len(l) <= 1:
            return 0.0

        t1 = l["time"].values[:-1]
        t2 = l["time"].values[1:]
        denom = l["in_use"].values + l["idle"].values
        y = divide(
            l["in_use"].values,
            denom,
            out=zeros_like(denom, dtype=float),
            where=denom != 0,
        )
        y_dur = y[:-1]
        d = t2 - t1
        r = nansum(d * y_dur) / l["time"].values[-1]
        return r

    def average_idleness(self):
        """
        Return the average idleness for the resource.
        """
        return 1.0 - self.average_utilization()

    def total_time_idle(self):
        """
        Return the total idle time of the resource.
        """
        l = self.status_log()
        if len(l) <= 1:
            return 0.0
        t1 = l["time"].values[:-1]
        t2 = l["time"].values[1:]
        this_level = l["idle"].values[:-1]
        d = t2 - t1
        r = nansum(d * this_level)
        return r

    def total_time_in_use(self):
        """
        Return the total in-use time of the resource.
        """
        l = self.status_log()
        if len(l) <= 1:
            return 0.0
        t1 = l["time"].values[:-1]
        t2 = l["time"].values[1:]
        this_level = l["in_use"].values[:-1]
        d = t2 - t1
        r = nansum(d * this_level)
        return r

    def average_level(self):
        """
        Return the average level for the resource.
        """
        l = self.status_log()
        if len(l) <= 1:
            return 0.0
        return self.total_time_idle() / l["time"].values[-1]

    def _request(self, entity: Entity, amount: int):
        """
        Calculate needed logs when an entity requests the resource.
        """
        self.queue_length += 1
        if self.print_actions or entity.print_actions:
            print(
                entity.name
                + "("
                + str(entity.id)
                + ")"
                + " requested"
                + " "
                + str(amount)
                + " "
                + self.name
                + "(s)"
                + "("
                + str(self.id)
                + ")"
                + ", sim_time:",
                self.env.now,
            )
        if self.log:
            self._status_log = append(self._status_log, [[self.env.now, self.in_use, self.idle, self.queue_length]], axis=0)
        if entity.log:
            entity._status_log = append(
                entity._status_log,
                [[self.env.now, entity._status_codes["wait for"], self.id]],
                axis=0,
            )

    def _get(self, entity: Entity, amount: int):
        """
        Calculate needed logs when an entity obtained the resource.
        """
        self.queue_length -= 1
        self.in_use += amount
        self.idle -= amount
        if self.print_actions or entity.print_actions:
            print(
                entity.name
                + "("
                + str(entity.id)
                + ")"
                + " got "
                + str(amount)
                + " "
                + self.name
                + "(s)"
                + "("
                + str(self.id)
                + ")"
                + ", sim_time:",
                self.env.now,
            )
        if self.log:
            self._status_log = append(self._status_log, [[self.env.now, self.in_use, self.idle, self.queue_length]], axis=0)

        if entity.log:
            entity._status_log = append(
                entity._status_log,
                [[self.env.now, entity._status_codes["get"], self.id]],
                axis=0,
            )
        entity.using_resources[self] = amount

        self.env._notify_observers(
            "on_resource_acquired",
            entity=entity,
            resource=self,
            amount=amount,
            time=self.env.now,
        )

        if self.log:
            self.env.log_event(
                source_type="resource",
                source_id=self.id,
                message=f"Resource {self.name} acquired",
                metadata={"entity_id": entity.id, "amount": amount},
            )

    def _add(self, entity: Entity, amount: int):
        """
        Calculate needed logs when an entity adds to the resource.
        """
        if self.print_actions or entity.print_actions:
            print(
                entity.name
                + "("
                + str(entity.id)
                + ")"
                + " added "
                + str(amount)
                + " "
                + self.name
                + "(s)"
                + "("
                + str(self.id)
                + ")"
                + ", sim_time:",
                self.env.now,
            )
        if self.log:
            self._status_log = append(self._status_log, [[self.env.now, self.in_use, self.idle, self.queue_length]], axis=0)

        if entity.log:
            entity._status_log = append(
                entity._status_log,
                [[entity._status_codes["add"], self.id, self.env.now]],
                axis=0,
            )

    def _put(self, entity: Entity, amount: int):
        """
        Calculate needed logs when an entity puts back the resource.
        """
        if self not in entity.using_resources:
            raise Warning(entity.name, "did not get ", self.name, "to put it back")
        if self in entity.using_resources and entity.using_resources[self] < amount:
            raise Warning(entity.name, "did not get this many of", self.name, "to put it back")

        entity.using_resources[self] = entity.using_resources[self] - amount

        self.in_use -= amount
        self.idle += amount

        if self.print_actions or entity.print_actions:
            print(
                entity.name
                + "("
                + str(entity.id)
                + ")"
                + " put back "
                + str(amount)
                + " "
                + self.name
                + "(s)"
                + "("
                + str(self.id)
                + ")"
                + ", sim_time:",
                self.env.now,
            )

        if self.log:
            self._status_log = append(self._status_log, [[self.env.now, self.in_use, self.idle, self.queue_length]], axis=0)

        if entity.log:
            entity._status_log = append(
                entity._status_log,
                [[entity._status_codes["put"], self.id, self.env.now]],
                axis=0,
            )

        self.env._notify_observers(
            "on_resource_released",
            entity=entity,
            resource=self,
            amount=amount,
            time=self.env.now,
        )

        if self.log:
            self.env.log_event(
                source_type="resource",
                source_id=self.id,
                message=f"Resource {self.name} released",
                metadata={"entity_id": entity.id, "amount": amount},
            )

    # Convenience accessors (kept for backwards compatibility)
    def level(self) -> int:
        """
        Return the number of resources that are currently available.
        """
        return self.container.level

    def idle_level(self) -> int:
        """
        Alias for :meth:`level` (available capacity).
        """
        return self.level()

    def in_use_level(self) -> int:
        """
        Return the number of resources that are currently in use.
        """
        return self.in_use

    def capacity(self) -> int:
        """
        Return the maximum capacity for the resource.
        """
        return self.container.capacity

    def average_queue_length(self):
        """
        Return the average queue length for this resource.
        """
        return sum(self.waiting_time()) / (self.env.now if self.env.now > 0 else 1.0)


class Request:
    """
    A class defining a request for capturing the resources.
    This class allows keeping all the requests in a list.
    """

    def __init__(self, entity: Entity, amount: int):
        self.time = entity.env.now
        self.entity = entity
        self.amount = amount
        # show if the resource is obtained when flag turns 1
        self.flag = simpy.Container(entity.env, init=0)

    def __eq__(self, other_request):
        return (
            isinstance(other_request, Request)
            and self.time == other_request.time
            and self.amount == other_request.amount
            and self.entity == other_request.entity
        )


class Resource(GeneralResource):
    def __init__(self, env: "Environment", name: str, init: int = 1, capacity: int = 1000, print_actions: bool = False, log: bool = True):
        """
        Defines a resource for which a FIFO queue is implemented.
        """
        super().__init__(env, name, capacity, init, print_actions, log)

    def get(self, entity: Entity, amount: int):
        """
        A method for getting the resource.
        """
        super()._request(entity, amount)
        pr = Request(entity, amount)
        entity.pending_requests.append(pr)  # append request to the entity
        self.request_list.append(pr)
        yield self.env.timeout(0)  # allow other events to be scheduled
        yield entity.env.process(self._check_all_requests())
        # flag shows that the resource is granted
        yield pr.flag.get(1)

    def _check_all_requests(self):
        """
        Check to see if any request for the resource can be granted.
        """
        while len(self.request_list) > 0 and self.request_list[0].amount <= self.container.level:
            r = self.request_list.pop(0)  # remove the first element from the list
            simpy_request = self.container.get(r.amount)
            yield simpy_request
            r.entity.pending_requests.remove(r)
            r.flag.put(1)
            super()._get(r.entity, r.amount)
            if self.log:
                self._queue_log = append(
                    self._queue_log,
                    [[r.entity.id, r.time, self.env.now, r.amount]],
                    axis=0,
                )
            if r.entity.log:
                r.entity._waiting_log = append(
                    r.entity._waiting_log,
                    [[self.id, r.time, self.env.now, r.amount]],
                    axis=0,
                )

    def cancel(self, priority_request: Request):
        if priority_request in self.request_list:
            self.request_list.remove(priority_request)
        else:
            print("warning: the request cannot be cancelled as it is not in the request list")

    def add(self, entity: Entity, amount: int):
        """
        A method for adding the resource by the entity.
        """
        yield self.container.put(amount)
        super()._add(entity, amount)
        return entity.env.process(self._check_all_requests())

    def put(self, entity: Entity, amount: int):
        """
        A method for putting back the resource by the entity.
        """
        yield self.container.put(amount)
        super()._put(entity, amount)
        return entity.env.process(self._check_all_requests())


class PriorityRequest:
    """
    A class defining a priority request for capturing the resources.
    This class allows keeping all the requests in a sorted list of requests.
    """

    def __init__(self, entity: Entity, amount: int, priority: int):
        self.time = entity.env.now
        self.entity = entity
        self.amount = amount
        self.priority = priority
        # show if the resource is obtained
        self.flag = simpy.Container(entity.env, init=0)

    def __gt__(self, other_request):
        """
        Decide if a resource request has a higher priority than another.
        Lower priority values show higher priority.
        """
        if self.priority == other_request.priority:
            if self.time == other_request.time:
                return self.amount < other_request.amount
            return self.time < other_request.time
        return self.priority < other_request.priority

    def __eq__(self, other_request):
        if type(other_request) != type(self):
            return False
        return (
            self.priority == other_request.priority
            and self.time == other_request.time
            and self.amount == other_request.amount
        )

    def __ge__(self, other_request):
        return self > other_request or self == other_request


class PreemptiveRequest:
    """Request type used for preemptive resources."""

    def __init__(self, entity: Entity, amount: int, priority: int, preempt: bool, env: "Environment"):
        self.time = env.now
        self.entity = entity
        self.amount = amount
        self.priority = priority
        self.preempt = preempt
        self.flag = simpy.Container(env, init=0)
        self.usage_since: float | None = None
        # ordering key: lower priority value = higher priority
        # for ties, earlier time wins; non-preemptive loses to preemptive
        self.key = (self.priority, self.time, not self.preempt)

    def __lt__(self, other_request: "PreemptiveRequest"):
        return self.key < other_request.key


class PriorityResource(GeneralResource):
    def __init__(self, env: "Environment", name: str, init: int = 1, capacity: int = 1000, print_actions: bool = False, log: bool = True):
        """
        Defines a resource for which a priority queue is implemented.
        """
        super().__init__(env, name, capacity, init, print_actions, log)
        self.request_list: list[PriorityRequest] = []

    def get(self, entity: Entity, amount: int, priority: int = 1):
        """
        A method for getting the resource with priority.
        """
        super()._request(entity, amount)
        pr = PriorityRequest(entity, amount, priority)
        entity.pending_requests.append(pr)  # append priority request to the entity
        insort_left(self.request_list, pr)
        yield self.env.timeout(0)  # allow other events to be scheduled
        yield entity.env.process(self._check_all_requests())
        # flag shows that the resource is granted
        yield pr.flag.get(1)

    def _check_all_requests(self):
        """
        Check to see if any request for the resource can be granted.
        """
        while len(self.request_list) > 0 and self.request_list[-1].amount <= self.container.level:
            r = self.request_list.pop()
            yield self.container.get(r.amount)
            r.entity.pending_requests.remove(r)
            r.flag.put(1)
            super()._get(r.entity, r.amount)
            if self.log:
                self._queue_log = append(
                    self._queue_log,
                    [[r.entity.id, r.time, self.env.now, r.amount]],
                    axis=0,
                )
            if r.entity.log:
                r.entity._waiting_log = append(
                    r.entity._waiting_log,
                    [[self.id, r.time, self.env.now, r.amount]],
                    axis=0,
                )

    def cancel(self, priority_request: PriorityRequest):
        # remove does not work since it uses __eq__ defined in the PriorityRequest class
        for i in range(len(self.request_list)):
            pr = self.request_list[i]
            if pr.entity == priority_request.entity and pr.amount == priority_request.amount:
                del self.request_list[i]
                return

        print("warning: the priority request cannot be cancelled as it is not in the request list")

    def add(self, entity: Entity, amount: int):
        """
        A method for adding the resource by the entity.
        """
        yield self.container.put(amount)
        super()._add(entity, amount)
        return entity.env.process(self._check_all_requests())

    def put(self, entity: Entity, amount: int):
        """
        A method for putting back the resource by the entity.
        """
        yield self.container.put(amount)
        super()._put(entity, amount)
        return entity.env.process(self._check_all_requests())


class PreemptiveResource(GeneralResource):
    """Resource with priority-based preemption (capacity is assumed to be 1)."""

    def __init__(self, env: "Environment", name: str, print_actions: bool = False, log: bool = True):
        super().__init__(env, name, 1, 1, print_actions, log)
        self._users: list[PreemptiveRequest] = []
        self._queue: list[PreemptiveRequest] = []

    def level(self) -> int:  # type: ignore[override]
        return self.idle

    def idle_level(self) -> int:  # type: ignore[override]
        return self.idle

    def get(self, entity: Entity, amount: int = 1, priority: int = 1, preempt: bool = False):
        if amount > 1:
            print("Warning: amount of preemptive resource is always 1")
            amount = 1

        super()._request(entity, amount)
        request = PreemptiveRequest(entity, amount, priority, preempt, env=self.env)

        if self.idle >= amount and not self._users:
            self._grant(request)
            yield request.flag.get(1)
            return

        if preempt:
            victim = self._select_victim(request)
            if victim is not None:
                self._preempt(victim, request)
                yield request.flag.get(1)
                return

        insort_left(self._queue, request)
        yield request.flag.get(1)

    def put(self, entity: Entity, request: PreemptiveRequest | None = None):
        active_request: PreemptiveRequest | None = None
        for r in self._users:
            if r.entity == entity:
                active_request = r
                break

        if active_request is None:
            return self.env.event().succeed()

        self._users.remove(active_request)
        super()._put(entity, active_request.amount)
        return self.env.process(self._check_queue())

    def _grant(self, request: PreemptiveRequest):
        if request in self._queue:
            self._queue.remove(request)
        self._users.append(request)
        request.usage_since = self.env.now
        request.flag.put(1)
        super()._get(request.entity, request.amount)
        if self.log:
            self._queue_log = append(
                self._queue_log,
                [[request.entity.id, request.time, self.env.now, request.amount]],
                axis=0,
            )
        if request.entity.log:
            request.entity._waiting_log = append(
                request.entity._waiting_log,
                [[self.id, request.time, self.env.now, request.amount]],
                axis=0,
            )

    def _check_queue(self):
        yield self.env.timeout(0)
        while self.idle > 0 and self._queue:
            next_request = self._queue.pop(0)
            self._grant(next_request)

    def _select_victim(self, new_request: PreemptiveRequest) -> PreemptiveRequest | None:
        if not self._users:
            return None
        current = self._users[0]
        if current.key > new_request.key:
            return current
        return None

    def _preempt(self, victim: PreemptiveRequest, new_request: PreemptiveRequest):
        if victim in self._users:
            self._users.remove(victim)
        super()._put(victim.entity, victim.amount)
        victim.entity._on_preempted(
            resource=self,
            cause=Preempted(by=new_request.entity, resource=self, usage_since=victim.usage_since),
        )
        insort_left(self._queue, new_request)
        self.env.process(self._check_queue())

class Environment(simpy.Environment):
    """Simulation environment with observer hooks and logging helpers.

    The environment owns all entities and resources, and exposes lifecycle
    callbacks so observers can react to changes without patching core logic.
    """

    def __init__(self, name: str = "Environment"):
        """Create a new simulation environment."""
        super().__init__()
        self.name = name

        # Entity/resource bookkeeping
        self.last_entity_id = 0
        self.entities: list[Entity] = []
        self.entity_names: dict[int, str] = {}

        self.last_res_id = 0
        self.resources: list[Resource] = []
        self.resource_names: dict[int, str] = {}

        # Run-level bookkeeping
        self.run_number: int = 0               # how many times this env has been executed
        self.planned_runs: int | None = None   # optional hint (from num_runs)
        self.finishedTime: list[float] = []    # legacy list of end times
        self.run_history: list[dict[str, Any]] = []  # rich per-run metadata

        # Current run id (attached to log events)
        self.current_run_id: int | None = None

        # Environment-level event log (consumed by dashboard_data.collect_run_data)
        self.event_log: list[dict[str, Any]] = []

        # Registered observers (e.g. recorders / dashboard adapters)
        self._observers: list["SimulationObserver"] = []

    # ------------------------------------------------------------------
    # Observer helpers
    # ------------------------------------------------------------------
    def register_observer(self, observer: "SimulationObserver"):
        """Register a new simulation observer."""
        self._observers.append(observer)

    def _notify_observers(self, method_name: str, **kwargs):
        """Invoke a method on all observers if they implement it."""
        for observer in self._observers:
            if hasattr(observer, method_name):
                getattr(observer, method_name)(**kwargs)

    # ------------------------------------------------------------------
    # Structured environment-level logging
    # ------------------------------------------------------------------
    def log_event(
        self,
        source_type: str,
        source_id: Any,
        message: str,
        time: float | None = None,
        metadata: dict | None = None,
    ):
        """Send a structured log event to observers and store it on the env."""
        event_time = time if time is not None else self.now
        run_id = self.current_run_id

        meta = dict(metadata or {})
        if run_id is not None:
            meta.setdefault("run_id", run_id)

        event = {
            "time": event_time,
            "run_id": run_id,
            "source_type": source_type,
            "source_id": source_id,
            "message": message,
            "metadata": meta,
        }

        # Store on environment so dashboard_data can see it
        self.event_log.append(event)

        # Also forward to any observers (recorders, etc.)
        self._notify_observers("on_log_event", event=event)

    # ------------------------------------------------------------------
    # Entity creation
    # ------------------------------------------------------------------
    def create_entities(
        self,
        name: str,
        total_number: int,
        print_actions: bool = False,
        log: bool = True,
    ) -> list[Entity]:
        """Create and register multiple :class:`Entity` instances at ``env.now``."""
        entities: list[Entity] = []
        for _ in range(total_number):
            entities.append(Entity(self, name, print_actions, log))
        return entities

    # ------------------------------------------------------------------
    # Run with metadata (single environment, single event loop)
    # ------------------------------------------------------------------
    def run(self, *args, **kwargs):
        """Run the simulation once, with per-run metadata.

        This wraps :class:`simpy.Environment.run` and additionally:

        - increments :attr:`run_number` and sets ``current_run_id``,
        - stores a row in :attr:`run_history`,
        - notifies observers via ``on_run_started`` / ``on_run_finished``,
        - accepts a hint ``num_runs`` (planned total runs in the experiment),
        - logs a final event with ``simulation_time`` for the dashboard.
        """
        # Optional hint: planned total number of runs in the wider experiment
        num_runs_hint = kwargs.pop("num_runs", None)
        if num_runs_hint is not None:
            try:
                self.planned_runs = int(num_runs_hint)
            except Exception:
                self.planned_runs = None

        # One actual execution of the event loop
        self.run_number += 1
        run_id = self.run_number
        self.current_run_id = run_id

        start_time = self.now

        self._notify_observers(
            "on_run_started",
            env=self,
            run_id=run_id,
            start_time=start_time,
        )
        print(f"Run {run_id} started")

        # Delegate to SimPy
        result = super().run(*args, **kwargs)

        end_time = self.now
        duration = end_time - start_time
        print(f"Run {run_id} finished at sim time {end_time}")

        # Record run-level history
        self.finishedTime.append(end_time)
        self.run_history.append(
            {
                "run_id": run_id,
                "start_time": start_time,
                "end_time": end_time,
                "duration": duration,
            }
        )

        # Emit a structured log event with simulation_time for the dashboard
        self.log_event(
            source_type="environment",
            source_id="run",
            message="Run finished",
            metadata={
                "simulation_time": end_time,
                "duration": duration,
            },
        )

        self._notify_observers(
            "on_run_finished",
            env=self,
            run_id=run_id,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
        )

        return result

