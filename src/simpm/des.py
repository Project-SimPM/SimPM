"""Discrete Event Simulation primitives for project-management style models.

This module wraps :mod:`simpy` with opinionated helpers for creating entities,
resources, and environments that can be logged and observed while a simulation
is running. The docstrings are intentionally verbose so that API documentation
generated from them provides ready-to-use guidance and code snippets.
"""
from __future__ import annotations
from typing import Any, TYPE_CHECKING

from bisect import insort_left
from pandas import DataFrame
from numpy import array, append, nansum
import simpy
from simpy.events import Event

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

    Examples
    --------
    >>> from simpm.dist import normal
    >>> _describe_duration(5)
    {'type': 'fixed', 'parameters': 5, 'sampled_duration': 5}
    >>> desc = _describe_duration(normal(10, 2))
    >>> desc['sampled_duration'] >= 0
    True
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

    Examples
    --------
    Create an entity and annotate it with custom attributes::

        customer = Entity(env, "customer")
        customer["tier"] = "gold"
        yield env.process(customer._activity("check-in", 2))
    """

    def __init__(self, env: Environment, name: str, print_actions: bool = False, log: bool = True):
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
        self.act_dic = {}
        self.print_actions: bool = print_actions
        self.log: bool = log
        self.using_resources = {}  # a dictionary showing all the resources an entity is using
        self._current_process: simpy.events.Process | None = None
        self._current_interruptible: str | None = None
        self._current_timeout: Event | None = None

        # ***logs
        self._schedule_log = array([[0, 0, 0]])  # act_id,act_start_time,act_finish_time
        self._status_codes = {"wait for": 1, "get": 2, "start": 3, "finish": 4, "put": 5, "add": 6}
        self._status_log = array([[0, 0, 0]])  # time,entity_status_code,actid/resid
        self._waiting_log = array([[0, 0, 0, 0]])  # resource_id,start_waiting,end_waiting,amount waiting for
        self.pending_requests = []  # the simpy requests made by an entity but not granted yet

        if print_actions:
            print(name + "(" + str(self.id) + ") is created, sim_time:", env.now)

        self.env._notify_observers("on_entity_created", entity=self)

    def __str__(self) -> str:
        """Return ``"<name> (<id>)"`` for quick debugging output."""
        return f"{self.name} ({self.id})"
    
    def __repr__(self) -> str:
        """Detailed representation including environment and flags."""
        return f"Entity({self.env},{self.name}, print_actions={self.print_actions}, log={self.log})"
    
    def __getitem__(self, key: str) -> Any:
        """Return an attribute value stored on the entity.

        Raises
        ------
        KeyError
            If the attribute has not been set.
        """
        return self._attributes[key]

    def __setitem__(self, key: str, value: Any):
        """Attach an attribute to the entity.

        Type checking ensures the key is a string so downstream consumers (e.g.,
        serialization to DataFrames) behave predictably.
        """
        if not isinstance(key, str):
            raise TypeError("Attribute keys must be strings")
        self._attributes[key] = value

    def __delitem__(self, key):
        """Delete an attribute from the entity."""
        del self._attributes[key]

    def __contains__(self, key):
        """Return ``True`` when an attribute exists on the entity."""
        return key in self._attributes

    def _activity(self, name, duration):
        """Run a non-interruptible activity for the given duration.

        Parameters
        ----------
        name : str
            Human-friendly activity name (used in logs and observer callbacks).
        duration : float | int | distribution
            Fixed duration or distribution to sample from.

        Yields
        ------
        simpy.events.Timeout
            The timeout representing the activity's run.
        """
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
            self._status_log = append(self._status_log, [[self.env.now, self._status_codes["start"], self.act_dic[name]]], axis=0)

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
            self._status_log = append(self._status_log, [[self.env.now, self._status_codes["finish"], self.act_dic[name]]], axis=0)

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

    def _interruptive_activity(self, name, duration):
        """Run an activity that can be interrupted by preemptive resources.

        Parameters
        ----------
        name : str
            Activity label used for logging and observer callbacks.
        duration : float | int | distribution
            Target runtime or distribution to sample from.

        Notes
        -----
        The coroutine catches :class:`simpy.Interrupt` and :class:`Preempted`
        exceptions to gracefully stop when a preemptive resource evicts the
        entity. Use this helper when coordinating with
        :class:`PreemptiveResource`.
        """
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
            self._status_log = append(self._status_log, [[self.env.now, self._status_codes["start"], self.act_dic[name]]], axis=0)

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

    def _on_preempted(self, resource, cause: Preempted):
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

        Returns:
        --------
        dict: A dictionary containing all attributes of the entity.
        """
        return self._attributes

    @attributes.setter
    def attributes(self, value: dict[str, Any]) -> None:
        """
        Set the dictionary of all attributes of the entity.

        Parameters:
        -----------
        value: dict
            A dictionary containing all attributes to be set for the entity.

        Returns:
        --------
        None

        Raises:
        -------
        TypeError: If the value is not a dictionary.
        """
        if not isinstance(value, dict):
            raise TypeError("Attribute values must be stored in a dictionary.")

        self._attributes = value

    def do(self, name, dur):
        """
        Defines the activity that the entity is doing.

        Parameters
        ----------
        name : string
            Name of the activity
        duration : float , int, or distribution
            The duration of that activity

        Returns
        -------
        Environment.process
            the process for the activity
        """
        try:
            return self.env.process(self._activity(name, dur))
        except:
            print("simpm: error in  duration of activity", name)

    def interruptive_do(self, name, dur):
        try:
            self._current_process = self.env.process(self._interruptive_activity(name, dur))
            return self._current_process
        except:
            print("simpm: error in  duration of activity", name)

    def get(self, res, amount=1, priority=1, preempt: bool = False):
        """
        Entity requests to get a resource using this method.

        Parameters
        ----------
        res : simpm.resource
            the resource to be captured by the entity
        amount :  int
            The number of resouces to be captured
        priority : int
            The priority of the request for getting the resource
        preempt : bool
            Preemptive resources are not yet implemented

        Returns
        -------
        simpm.environment.process
            The process for the request
        """
        try:
            if isinstance(amount, distribution):
                a = -1
                while a < 0:
                    a = amount.sample()
                amount = int(a)
            if isinstance(res, PreemptiveResource):
                if amount > 1:
                    print("Warning: amount of preemptive resource is always 1")
                return self.env.process(res.get(self, amount, priority, preempt))
            if isinstance(res, PriorityResource):
                return self.env.process(res.get(self, amount, priority))
            if isinstance(res, Resource):
                return self.env.process(res.get(self, amount))
        except:
            print("simpm: error in get")

    def add(self, res, amount=1):
        """
        Entity increases the number of resources using this method.

        Parameters
        ----------
        res : simpm.resource
            the resource to be added by the entity
        amount :  int
            The number of resouces to be added

        Returns
        -------
        simpm.environment.process
            The process for adding resources
        """
        if isinstance(amount, distribution):
            a = -1
            while a < 0:
                a = amount.sample()  # ?can this amount be float!
            amount = int(a)
        return self.env.process(res.add(self, amount))

    def put(self, res, amount=1, request=None):
        """
        Entity puts back the resources using this method.

        Parameters
        ----------
        res : simpm.resource
            the resource to be added by the entity
        amount :  int
            The number of resouces to be put back

        Returns
        -------
        simpm.environment.process
            The process for putting back the resources
        """
        if isinstance(amount, distribution):
            a = -1
            while a < 0:
                a = amount.sample()
            amount = int(a)
        if type(res) == PreemptiveResource:
            if amount > 1:
                amount = 1
                print("Warning: amount of preemptive resource is always 1")
            return res.put(self, request)
        return self.env.process(res.put(self, amount))

    def is_pending(self, res, amount: int = 1):
        """

        Parameters:
        -----------
        res : resource
            Resource for which the eneity is waiting for.
        amount: int
            Number of resources that the entity is waiting for.
            If the number of entities is not specified, waiting for any number of resources is ok

        Returns
        --------
        True if entity is waiting for the resource, and False if the entity is not waiting for the resource
        """

        for r in res.request_list:
            if r.entity == self and r.amount == amount:
                return True
        return False

    def not_pending(self, res, amount: int = 1):
        """

        Parameters:
        -----------
        res : resource
            Resource for which the eneity is waiting for.
        amount: int
            Number of resources that the entity is waiting for.
            If the number of entities is not specified, waiting for any number of resources is ok

        Returns
        --------
        Flase if the entitiy is not waiting for the resource, and True if the entity is not waiting for the resource
        """
        return not self.is_pending(res, amount)

    def cancel(self, res, amount: int = 1):
        """
        cancels a resource request if it is pending, and put it back if it is already granted.

        Parameters
        -----------
        res : resource
            Resource for which the eneity is waiting for.
        amount: int
            Number of resources that the entity is waiting for.
            If the number of entities is not specified, waiting for any number of resources is ok


        """

        for r in res.request_list:
            if r.entity == self and r.amount == amount:
                res.cancel(r)
                return

        self.put(res, amount)  # a problem may occur of someone adds to the resouce meanwhile we are canceling

    def schedule(self):
        """

        Returns
        -------
        pandas.DataFrame
            The schedule of each entity.
            The columns are activity name, and start time and finish time of that activity
        """
        df = DataFrame(data=self._schedule_log[1:, :], columns=["activity", "start_time", "finish_time"])
        df["activity"] = df["activity"].map(_swap_dict_keys_values(self.act_dic))
        return df

    def waiting_log(self):
        """

        Returns
        -------
        pandas.DataFrame
            The time the entity started waiting and the time it finished waiting.
            The columns show the resource name for which the entity is waiting for, time when waiting is started,
            time when waiting is finished, and the number of resources the entity is waiting for
        """
        df = DataFrame(data=self._waiting_log[1:, :], columns=["resource", "start_waiting", "end_waiting", "resource_amount"])
        df["resource"] = df["resource"].map(self.env.resource_names)
        df["waiting_duration"] = df["end_waiting"] - df["start_waiting"]
        return df

    def waiting_time(self):
        """

        Returns
        -------
        numpy.array
            The waiting durations of the entity each time it waited for a resource
        """
        a = self.waiting_log()
        a = a["end_waiting"] - a["start_waiting"]
        return a.values

    def status_log(self):
        """

        Returns
        -------
        pandas.DataFrame
            shows any change in the status of an entity, the change can be either
            waiting for a resourcing, getting a resources, putting a resource back, or adding to a resouce,
            or it can be starting or finishing an activity
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

    def __init__(self, env, name, capacity, init, print_actions=False, log=True):
        """Create a basic resource container and register it with the environment.

        Parameters
        ----------
        env : Environment
            Environment that owns the resource.
        name : str
            Human-readable name used in logs and summaries.
        capacity : int
            Maximum capacity for the resource's :class:`simpy.Container`.
        init : int
            Initial level of the container and idle count.
        print_actions : bool, optional
            When ``True``, echo acquisitions and releases to stdout.
        log : bool, optional
            When ``True``, capture queue and status history for later
            aggregation.
        """
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
        self.request_list = []
        self.attr = {}  # attributes for resoruces

        # logs
        self._status_log = array([[0, 0, 0, 0]])  # time,in-use,idle,queue-length
        self._queue_log = array([[0, 0, 0, 0]])  # entityid,startTime,endTime,amount

        self.env._notify_observers("on_resource_created", resource=self)

    def queue_log(self):
        """

        Returns
        -------
        pandas.DataFrame
            All entities waiting for the resource, their start waiting time and
            finish waiting time are stored in this DataFrame
        """
        df = DataFrame(data=self._queue_log[1:, :], columns=["entity", "start_time", "finish_time", "resource_amount"])
        df["entity"] = df["entity"].map(self.env.entity_names)
        df["waiting_duration"] = df["finish_time"] - df["start_time"]
        return df

    def status_log(self):
        """

        Returns
        -------
        pandas.DataFrame
            Any changes in the status of the resource and the time of the change is presented
            in this DataFrame. The recorded statuses are number of in-use resources ,
            number of idle resources, and number of entities waiting for the resource.
        """
        df = DataFrame(data=self._status_log[1:, :], columns=["time", "in_use", "idle", "queue_length"])
        return df

    def waiting_time(self):
        """

        Returns
        -------
        numpy.array
            The waiting durations for a resource
        """
        a = self.queue_log()
        a = a["finish_time"] - a["start_time"]
        return a.values

    ####*****************plotting is still under construction*************
    # def plot_utilization(self):
    #     l=self.status_log()
    #     y=l["in_use"].values/(l["in_use"].values+l["idle"].values)
    #     x=l["time"].values
    #     plt.plot(x,y*100)
    #     plt.show()

    # def plot_idleness(self):
    #     l=self.status_log()
    #     l["idleness%"]=l["idle"].values/(l["in_use"].values+l["idle"].values)*100
    #     l.plot(x="time",y="idleness%")
    #     plt.show()

    # def plot_queue_length(self):

    #     l=self.status_log()
    #     l.plot(x="time",y="queue_length")
    #     plt.show()

    def average_utilization(self):
        """

        Returns
        -------
        int
            The average utilization for the resource
        """
        l = self.status_log()
        t1 = l["time"].values[:-1]
        t2 = l["time"].values[1:]
        y = l["in_use"].values / (l["in_use"].values + l["idle"].values)
        y_dur = y[:-1]
        d = t2 - t1
        r = nansum(d * y_dur) / l["time"].values[-1]
        return r

    def average_idleness(self):
        """
        Returns
        -------
        int
            The average idleness for the resource
        """
        return 1 - self.average_utilization()

    def total_time_idle(self):
        """
        Returns
        -------
        int
            The total idle time of the resource
        """
        l = self.status_log()
        t1 = l["time"].values[:-1]
        t2 = l["time"].values[1:]
        this_level = l["idle"].values
        this_level = this_level[:-1]
        d = t2 - t1
        r = nansum(d * this_level)
        return r

    def total_time_in_use(self):
        """
        Returns
        -------
        int
            The total idle time of the resource
        """
        l = self.status_log()
        t1 = l["time"].values[:-1]
        t2 = l["time"].values[1:]
        this_level = l["in_use"].values
        this_level = this_level[:-1]
        d = t2 - t1
        r = nansum(d * this_level)
        return r

    def average_level(self):
        """
        Returns
        -------
        int
            The average level for the resource
        """
        l = self.status_log()
        return self.total_time_idle() / l["time"].values[-1]

    def _request(self, entity, amount):
        """
        Calculate needed logs when an entity requests the resource.

        Parameters
        ----------
        entity : simpm.entity
            The entity requesting the resource
        amount : int
            The number of requested resouces
        """
        self.queue_length += 1
        if self.print_actions or entity.print_actions:
            print(entity.name + "(" + str(entity.id) + ")" + " requested", str(amount), self.name + "(s)" + "(" + str(self.id) + ")" + ", sim_time:", self.env.now)
        if self.log:
            self._status_log = append(self._status_log, [[self.env.now, self.in_use, self.idle, self.queue_length]], axis=0)
        if entity.log:
            entity._status_log = append(entity._status_log, [[self.env.now, entity._status_codes["wait for"], self.id]], axis=0)

    def _get(self, entity, amount):
        """
        Calculate needed logs when an entity got the resource.

        Parameters
        ----------
        entity : simpm.entity
            The entity getting the resource
        amount : int
            The number of taken resouces
        """
        self.queue_length -= 1
        self.in_use += amount
        self.idle -= amount
        if self.print_actions or entity.print_actions:
            print(entity.name + "(" + str(entity.id) + ")" + " got " + str(amount), self.name + "(s)" + "(" + str(self.id) + ")" + ", sim_time:", self.env.now)
        if self.log:
            self._status_log = append(self._status_log, [[self.env.now, self.in_use, self.idle, self.queue_length]], axis=0)

        if entity.log:
            entity._status_log = append(entity._status_log, [[self.env.now, entity._status_codes["get"], self.id]], axis=0)
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

    def _add(self, entity, amount):
        """
        Calculate needed logs when an entity add to the resource.

        Parameters
        ----------
        entity : simpm.entity
            The entity adding the resource
        amount : int
            The number of added resouces
        """
        if self.print_actions or entity.print_actions:
            print(entity.name + "(" + str(entity.id) + ")" + " added " + str(amount), self.name + "(s)" + "(" + str(self.id) + ")" + ", sim_time:", self.env.now)
        if self.log:
            self._status_log = append(self._status_log, [[self.env.now, self.in_use, self.idle, self.queue_length]], axis=0)

        if entity.log:
            entity._status_log = append(entity._status_log, [[entity._status_codes["add"], self.id, self.env.now]], axis=0)

    def _put(self, entity, amount):
        """
        Calculate needed logs when an entity add to the resource.

        Parameters
        ----------
        res : simpm.entity
            The entity putting the resource back
        amount : int
            The number of resouces being put back
        """
        if self not in entity.using_resources:
            raise Warning(entity.name, "did not got ", self.name, "to put it back")
        if self in entity.using_resources and entity.using_resources[self] < amount:
            raise Warning(entity.name, "did not got this many of", self.name, "to put it back")

        entity.using_resources[self] = entity.using_resources[self] - amount

        self.in_use -= amount
        self.idle += amount

        if self.print_actions or entity.print_actions:
            print(entity.name + "(" + str(entity.id) + ")" + " put back " + str(amount), self.name + "(s)" + "(" + str(self.id) + ")" + ", sim_time:", self.env.now)

        if self.log:
            self._status_log = append(self._status_log, [[self.env.now, self.in_use, self.idle, self.queue_length]], axis=0)

        if entity.log:
            entity._status_log = append(entity._status_log, [[entity._status_codes["put"], self.id, self.env.now]], axis=0)

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

    def level(self):
        """

        Returns
        -------
        int
            The number of resources that are currently available
        """
        return self.container.level

    def idle(self):
        """

        Returns
        -------
        int
            The number of resources that are currently available

        """
        return self.level()

    def in_use(self):
        """

        Returns
        -------
        int
            The number of resources that are currently in-use

        """
        return self.in_use

    def capacity(self):
        """

        Returns
        -------
        int
            The maximum capacity for the resource
        """
        return self.container.capacity

    def average_queue_length(self):
        """
        Returns
        -------
        float
            The average  queue length for a resource
        """
        return sum(self.waiting_time()) / (self.env.now)


class Request:
    """
    A class defining the a priority request for capturing the resources.
    This class allows to keep all the requests in a sorted list of requests.
    """

    def __init__(self, entity, amount):
        self.time = entity.env.now
        self.entity = entity
        self.amount = amount
        self.flag = simpy.Container(entity.env, init=0)  # show if the resource is obtained when flag truns 1

    def __eq__(self, other_request):
        return self.priority == other_request.priority and self.time == other_request.time and self.amount == other_request.amount


class Resource(GeneralResource):
    def __init__(self, env, name, init=1, capacity=1000, print_actions=False, log=True):
        """
        Defines a resource for which a priority queue is implemented.

        Parameters
        ----------
        env:simpm.environment
            The environment for the entity
        name : string
            Name of the resource
        capacity: int
            Maximum capacity for the resource, defualt value is 1000.
        init: int
            Initial number of resources, defualt value is 1.
        print_actions : bool
            If equal to True, the changes in the resource will be printed in console.
            defualt value is False
        log: bool
            If equals True, various statistics will be collected for the resource.
            defualt value is True.
        """
        super().__init__(env, name, capacity, init, print_actions, log)

        # self.resource=simpy.PriorityResource(env,1) #shoule be deleted

    def get(self, entity, amount):
        """
        A method for getting the resource.

        Parameters
        ----------
        entity : simpm.entity
            The entity adding the resource
        amount : int
            The number of resouces to be added
        priority : int
            lower values for this input show higher priority
        """
        super()._request(entity, amount)
        pr = Request(entity, amount)
        entity.pending_requests.append(pr)  # append priority request to the eneity
        self.request_list.append(pr)
        yield self.env.timeout(0)  # ? why do we need this?
        yield entity.env.process(self._check_all_requests())
        yield pr.flag.get(1)  # flag shows that the resource is granted

    def _check_all_requests(self):
        """
        Check to see if any rquest for the resource can be granted.
        """
        while len(self.request_list) > 0 and self.request_list[0].amount <= self.container.level:
            r = self.request_list.pop(0)  # remove the first element from the list
            simpy_request = self.container.get(r.amount)
            yield simpy_request
            r.entity.pending_requests.remove(r)
            r.flag.put(1)
            super()._get(r.entity, r.amount)
            if self.log:
                self._queue_log = append(self._queue_log, [[r.entity.id, r.time, self.env.now, r.amount]], axis=0)
            if r.entity.log:
                r.entity._waiting_log = append(r.entity._waiting_log, [[self.id, r.time, self.env.now, r.amount]], axis=0)

    def cancel(self, priority_request):
        if priority_request in self.request_list:
            self.request_list.remove(priority_request)
        else:
            print("warning: the request can not be cancled as it is not in the request list")

    def add(self, entity, amount):
        """
        A method for adding the resource by the entity.

        Parameters
        ----------
        entity : simpm.entity
            The entity adding the resource
        amount : int
            The number of resouces to be added
        """
        yield self.container.put(amount)
        super()._add(entity, amount)
        return entity.env.process(self._check_all_requests())

    def put(self, entity, amount):
        """
        A method for putting back the resource by the entity.

        Parameters
        ----------
        entity : simpm.entity
            The entity adding the resource
        amount : int
            The number of resouces to be added
        """
        yield self.container.put(amount)
        super()._put(entity, amount)
        return entity.env.process(self._check_all_requests())


class PriorityRequest:
    """
    A class defining the a priority request for capturing the resources.
    This class allows to keep all the requests in a sorted list of requests.
    """

    def __init__(self, entity, amount, priority):
        self.time = entity.env.now
        self.entity = entity
        self.amount = amount
        self.priority = priority
        self.flag = simpy.Container(entity.env, init=0)  # show if the resource is obtained

    def __gt__(self, other_request):
        """
        Decides if a resource request has a higher priority than antothe resource request
        Lower priority values show higher priority!
        If the priority of two requests is equal and are made at the same time,
        the request with lower number of needed resources will have a higher priority.
        """
        if self.priority == other_request.priority:
            if self.time == other_request.time:
                return self.amount < other_request.amount
            else:
                return self.time < other_request.time
        return self.priority < other_request.priority

    def __eq__(self, other_request):
        if type(other_request) != type(self):
            return False
        return self.priority == other_request.priority and self.time == other_request.time and self.amount == other_request.amount

    def __ge__(self, other_request):
        return self > other_request or self == other_request


class PreemptiveRequest:
    """Request type used for preemptive resources."""

    def __init__(self, entity, amount, priority, preempt, env):
        self.time = env.now
        self.entity = entity
        self.amount = amount
        self.priority = priority
        self.preempt = preempt
        self.flag = simpy.Container(env, init=0)
        self.usage_since = None
        self.key = (self.priority, self.time, not self.preempt)

    def __lt__(self, other_request):
        return self.key < other_request.key


class PriorityResource(GeneralResource):
    def __init__(self, env, name, init=1, capacity=1000, print_actions=False, log=True):
        """
        Defines a resource for which a priority queue is implemented.

        Parameters
        ----------
        env:simpm.environment
            The environment for the entity
        name : string
            Name of the resource
        capacity: int
            Maximum capacity for the resource, defualt value is 1000.
        init: int
            Initial number of resources, defualt value is 1.
        print_actions : bool
            If equal to True, the changes in the resource will be printed in console.
            defualt value is False
        log: bool
            If equals True, various statistics will be collected for the resource.
            defualt value is True.
        """
        super().__init__(env, name, capacity, init, print_actions, log)
        self.request_list = []
        # self.resource=simpy.PriorityResource(env,1) #shoule be deleted

    def get(self, entity, amount, priority=1):
        """
        A method for getting the resource.

        Parameters
        ----------
        entity : simpm.entity
            The entity adding the resource
        amount : int
            The number of resouces to be added
        priority : int
            lower values for this input show higher priority
        """
        super()._request(entity, amount)
        pr = PriorityRequest(entity, amount, priority)
        entity.pending_requests.append(pr)  # append priority request to the eneity
        insort_left(self.request_list, pr)
        yield self.env.timeout(0)  # ? why do we need this?
        yield entity.env.process(self._check_all_requests())
        yield pr.flag.get(1)  # flag shows that the resource is granted

    def _check_all_requests(self):
        """
        Check to see if any rquest for the resource can be granted.
        """
        while len(self.request_list) > 0 and self.request_list[-1].amount <= self.container.level:
            r = self.request_list.pop()
            yield self.container.get(r.amount)
            r.entity.pending_requests.remove(r)
            r.flag.put(1)
            super()._get(r.entity, r.amount)
            if self.log:
                self._queue_log = append(self._queue_log, [[r.entity.id, r.time, self.env.now, r.amount]], axis=0)
            if r.entity.log:
                r.entity._waiting_log = append(r.entity._waiting_log, [[self.id, r.time, self.env.now, r.amount]], axis=0)

    def cancel(self, priority_request):
        # ***the followig code did not work***
        # if priority_request in self.request_list:
        # self.request_list.remove(priority_request)
        # remove does not work since it uses equal defined in the priority resource class
        for i in range(len(self.request_list)):
            pr = self.request_list[i]
            if pr.entity == priority_request.entity and pr.amount == priority_request.amount:
                del self.request_list[i]
                return

        print("warning: the priority request can not be cancled as it is not in the request list")

    def add(self, entity, amount):
        """
        A method for adding the resource by the entity.

        Parameters
        ----------
        entity : simpm.entity
            The entity adding the resource
        amount : int
            The number of resouces to be added
        """
        yield self.container.put(amount)
        super()._add(entity, amount)
        return entity.env.process(self._check_all_requests())

    def put(self, entity, amount):
        """
        A method for putting back the resource by the entity.

        Parameters
        ----------
        entity : simpm.entity
            The entity adding the resource
        amount : int
            The number of resouces to be added
        """
        yield self.container.put(amount)
        super()._put(entity, amount)
        return entity.env.process(self._check_all_requests())


class PreemptiveResource(GeneralResource):
    """Resource with priority-based preemption (capacity is assumed to be 1)."""

    def __init__(self, env, name, print_actions=False, log=True):
        super().__init__(env, name, 1, 1, print_actions, log)
        self._users: list[PreemptiveRequest] = []
        self._queue: list[PreemptiveRequest] = []

    def level(self):  # type: ignore[override]
        return self.idle

    def idle(self):  # type: ignore[override]
        return self.idle

    def get(self, entity, amount=1, priority: int = 1, preempt: bool = False):
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

    def put(self, entity, request=None):
        active_request = None
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

    def _select_victim(self, new_request: PreemptiveRequest):
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


"""
*****************************************
*****Environment Class*******************
*****************************************
"""


class Environment(simpy.Environment):
    """Simulation environment with observer hooks and logging helpers.

    The environment owns all entities and resources, and exposes lifecycle
    callbacks so observers can react to changes without patching core logic.
    """

    def __init__(self, name: str = "Environment"):
        """Create a new simulation environment.

        Parameters
        ----------
        name : str, optional
            Human-readable label used in dashboards and logs.
        """
        super().__init__()
        self.name = name
        self.last_entity_id = 0
        self.entities: list[Entity] = []
        self.entity_names: dict[int, str] = {}
        self.last_res_id = 0
        self.resources: list[Resource] = []
        self.resource_names = {}
        self.run_number = 0
        self.finishedTime = []
        self._observers: list[SimulationObserver] = []

    def register_observer(self, observer: SimulationObserver):
        """Register a new simulation observer."""
        self._observers.append(observer)

    def _notify_observers(self, method_name: str, **kwargs):
        for observer in self._observers:
            if hasattr(observer, method_name):
                getattr(observer, method_name)(**kwargs)

    def log_event(self, source_type: str, source_id: Any, message: str, time: float | None = None, metadata: dict | None = None):
        """Send a structured log event to observers.

        Parameters
        ----------
        source_type : str
            Category of the emitter (e.g., ``"activity"`` or ``"resource"``).
        source_id : Any
            Identifier scoped to ``source_type``.
        message : str
            Human-readable description of the event.
        time : float, optional
            Simulation time associated with the log. Defaults to ``env.now``.
        metadata : dict, optional
            Free-form payload for dashboards or reporters.
        """
        event_time = time if time is not None else self.now
        self._notify_observers(
            "on_log_event",
            event={
                "time": event_time,
                "source_type": source_type,
                "source_id": source_id,
                "message": message,
                "metadata": metadata or {},
            },
        )

    def create_entities(self, name, total_number, print_actions=False, log=True):
        """Create and register multiple :class:`Entity` instances at ``env.now``.

        Parameters
        ----------
        name : str
            Base name for the entities; the environment appends numeric ids.
        total_number : int
            How many entities to create.
        print_actions : bool, optional
            Echo lifecycle events to stdout for all created entities.
        log : bool, optional
            Enable per-entity logging (schedule, waits, status changes).

        Returns
        -------
        list[Entity]
            The created entity objects.
        """
        Entities = []
        for i in range(total_number):
            Entities.append(Entity(self, name, print_actions, log))
        return Entities

    def run(self, *args, **kwargs):
        """Run the simulation while notifying registered observers."""
        self.run_number += 1
        self._notify_observers("on_run_started", env=self)
        print("Run started")
        result = super().run(*args, **kwargs)
        print(f"Run finished at sim time {self.now}")
        self._notify_observers("on_run_finished", env=self)
        return result
