Project modeling concepts in SimPM
==================================

SimPM models project-management and construction systems using
discrete-event simulation (DES). This page connects the basic DES ideas
from :doc:`des-background` to the concrete modeling blocks in SimPM.

.. contents:: On this page
   :local:

Key building blocks
-------------------

SimPM exposes the usual DES concepts as Python objects:

* **Environment** (:class:`simpm.des.Environment`) – the simulation world
  and event scheduler. It keeps the current simulation time (``env.now``)
  and manages all active processes.

* **Entities** (:class:`simpm.des.Entity`) – things that move through the
  system. In project-management, entities can represent:

  * trucks in an earthmoving operation,
  * tasks or work packages in a schedule,
  * crews, modules, or other units of work.

* **Resources** (:class:`simpm.des.Resource` and variants) – limited
  capacities that entities compete for:

  * crews, cranes, loaders, trucks, excavators,
  * storage yards or other constrained capacities,
  * priority or preemptive resources when some users have higher priority.

* **Distributions** (:mod:`simpm.dist`) – probabilistic durations and quantities
  (e.g., :func:`simpm.dist.norm()`, :func:`simpm.dist.triang()`,
  :func:`simpm.dist.expon()`). You can pass these distribution objects directly
  to :meth:`simpm.des.Entity.do`, and SimPM will sample a duration internally
  each time the activity runs.


Why SimPM for project management?
---------------------------------

SimPM uses a process-based DES style: you write Python generator
functions that ``yield`` operations such as waiting for a duration or
requesting a resource, and the environment manages time and events.

This is similar in spirit to libraries like SimPy, but SimPM adds
features aimed directly at project and construction models:

* **Project-focused entities** – :class:`simpm.des.Entity` carries user-defined arbitrary
  attributes (e.g. WBS code, activity type, planned duration) so you can
  attach project metadata to simulated work items.
* **Crew and equipment resources** – :class:`simpm.des.Resource`,
  :class:`simpm.des.PriorityResource`, and :class:`simpm.des.PreemptiveResource`
  capture limited crews, shared equipment pools, and prioritized work.
* **Schedule-oriented distributions** – :mod:`simpm.dist` provides common
  distributions (beta, triangular, trapezoidal, normal, exponential,
  uniform, empirical) for three-point and PERT-style estimates.
* **Built-in logging and dashboards** – simulations can log queue lengths,
  utilization, and activity timings to structured tables; :func:`simpm.run`
  can start a Plotly Dash dashboard (``"post"``) with minimal setup.
* **Central logging configuration** – :mod:`simpm.log_cfg` simplifies
  managing console and file logs in larger experiments.

These features are intended to make it straightforward to go from a
project plan to a simulation model and then study completion times,
risks, and bottlenecks.

Entities and their attributes
-----------------------------

Each entity instance has:

* a **name** and **id**,
* a reference to the **environment** it belongs to,
* a dictionary-like attribute store (via ``entity["key"]`` or
  :py:attr:`entity.attributes <simpm.des.Entity.attributes>`) for arbitrary
  user-defined metadata.

Example attributes:

* creation time (when the entity entered the system),
* due date or deadline,
* priority class,
* batch size or load size.

You usually create entities using
:meth:`simpm.des.Environment.create_entities`, which can also enable
logging:

.. code-block:: python

   import simpm.des as des

   env = des.Environment("Example")
   trucks = env.create_entities("truck", 10, log=True)

You can attach attributes with normal dictionary syntax and read them
later in your process logic:

.. code-block:: python

   import simpm.des as des

   env = des.Environment("Attr example")
   truck = env.create_entities("truck", 1, log=True)[0]
   crew = des.Resource(env, "crew", init=1, capacity=1, log=True)

   truck["wbs"] = "A-123"
   truck["load_size"] = 40

   def haul(entity, crew_res):
       # Access the attributes inside your process
       yield entity.get(crew_res, 1)
       yield entity.do("loading", 5 + entity["load_size"] / 10)
       yield entity.put(crew_res, 1)

   env.process(haul(truck, crew))

The *life-cycle* of each entity is described by a **process** – a
Python generator that yields operations such as requesting resources,
waiting for durations, or adding output to an inventory.

Resources, queues, and priorities
---------------------------------

Resources represent capacities that can be shared across entities.
SimPM provides:

* :class:`simpm.des.Resource` – basic capacity with FIFO queueing.
* :class:`simpm.des.PriorityResource` – entities can request with a
  priority value; higher-priority requests jump ahead in the queue.
* :class:`simpm.des.PreemptiveResource` – high-priority users can
  interrupt lower-priority holders (preemption).
* :class:`simpm.des.GeneralResource` – a generic resource wrapper used
  internally in some cases.

The typical pattern in an entity process is:

.. code-block:: python

   def task(entity, crew):
       # Request 1 unit of crew capacity
       yield entity.get(crew, 1)
       # Perform the work
       yield entity.do("work", 10)
       # Release the crew
       yield entity.put(crew, 1)

Whenever capacity is not immediately available, the entity waits in the
resource queue. SimPM can log:

* how long entities waited (waiting time),
* how many entities were in the queue (queue length),
* how busy the resource was (utilization).

Processes and the environment
-----------------------------

In SimPM, processes are plain Python generator functions that describe
what happens to an entity over time:

* **`yield entity.do("name", duration)`** – wait for a given duration
  ``duration`` can be a number (deterministic) or a :mod:`simpm.dist`
  distribution object; in the latter case SimPM samples a fresh duration
  internally.
* **`yield entity.get(resource, amount, priority=...)`** – request
  capacity from a resource; the process is suspended until the request
  is granted.
* **`yield entity.put(resource, amount)`** – release capacity back to
  the resource.
* **`yield entity.add(resource, amount)`** – add output (e.g., cubic
  meters of excavated material) to an inventory-like resource.

You attach processes to the environment with :meth:`env.process` and
run the simulation with either :meth:`env.run` or :func:`simpm.run`
(which can also start a dashboard):

.. code-block:: python

   import simpm
   import simpm.des as des

   env = des.Environment("Small example")
   crew = des.Resource(env, "Crew", init=1, capacity=1, log=True)
   job = env.create_entities("job", 1, log=True)[0]

   def job_process(entity, crew_res):
       yield entity.get(crew_res, 1)
       yield entity.do("work", 8)
       yield entity.put(crew_res, 1)

   env.process(job_process(job, crew))
   simpm.run(env, dashboard=False)

Logging and performance measures
--------------------------------

A key feature of SimPM is built-in logging for entities and resources
when ``log=True`` is set.

Typical project-management measures include:

* **Resource utilization** – fraction of time a crew or machine is busy.
* **Queue length** – how many entities were waiting over time.
* **Waiting time** – how long each entity spent waiting for resources.
* **Throughput / production** – how much volume or how many jobs were
  completed in a given time.
* **Completion time** – when a project or process finishes.

Examples of log accessors:

* ``resource.status_log()`` – time-stamped changes in resource
  allocation and queue length.
* ``resource.waiting_time()`` – per-request waiting times.
* ``resource.average_utilization()`` – average utilization over the
  run.
* ``entity.schedule()`` – the activity-level schedule of a single
  entity (start/finish times for each named activity).

These are used extensively in the tutorials:* :doc:`../tutorials/index` – overview of available tutorials.


Basic workflow
--------------

A typical modeling workflow in SimPM is:

1. Define the environment and random seeds.
2. Declare resources with capacities (crews, machines, inventories).
3. Define entity types and their processes (life-cycles).
4. Attach processes to the environment using ``env.process(...)``.
5. Run the environment using :func:`simpm.run` or :meth:`env.run`.
6. Analyze logs and statistics (queue lengths, utilization, waiting
   times, total duration, production).

