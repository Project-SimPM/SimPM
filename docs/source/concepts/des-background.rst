Background – Introduction to Discrete Event Simulation
======================================================

.. contents:: On this page
   :local:

What is simulation?
-------------------

Simulation is the imitation of the operation of a real-world process or system over time.
Instead of experimenting on the real system (which can be expensive, risky, or impossible),
we build a *simulation model* and experiment on that.

In project management and construction this lets us:

* Try “what if?” scenarios without touching the real project.
* Train people in a safe environment.
* Quantify risk and variability before committing to a plan.

Types of models
---------------

A few useful distinctions that often appear in textbooks:

* **Static vs. dynamic** – static models do not represent time explicitly (e.g., algebraic
  cost models); dynamic models evolve over time (e.g., a construction schedule).
* **Deterministic vs. stochastic** – deterministic models have no randomness; stochastic
  models include random variables (e.g., uncertain task durations).
* **Continuous vs. discrete-event** – continuous models update the system state at every
  instant of time (e.g., differential equations); discrete-event models only update when
  *events* occur (e.g., task start/finish, arrival/departure of a truck).

Why discrete-event simulation?
------------------------------

Many project and construction systems are naturally described as a sequence of *events*:

* A truck arrives, starts loading, finishes loading, starts hauling, dumps, returns.
* A crew starts an activity, waits for a crane, finishes, releases the crane.
* A new work package becomes ready once all its predecessors are complete.

We do not need to follow the system at every second. We only need to jump from one
important change to the next. This is exactly what **discrete-event simulation (DES)**
does.

Basic DES concepts
------------------

* **System** – the part of the real world we want to study (e.g., an earthmoving
  operation, a project network, a site with multiple cranes).
* **Entities** – items that move through the system (trucks, tasks, work packages,
  crews, messages, etc.).
* **Resources** – limited capacities that entities compete for (loaders, cranes,
  work crews, storage space).
* **State** – a snapshot of the system at a given simulation time (who is busy,
  who is waiting, how many trucks are in the queue, current project time, etc.).
* **Events** – instantaneous changes in the system state (arrival, start of service,
  end of service, breakdown, repair, task completion).
* **Clock** – the simulation time, which advances from event to event.

Event scheduling vs. process interaction
----------------------------------------

There are different ways to implement a DES engine:

* In **event-scheduling**, you explicitly insert and remove events from an event list.
* In **process-interaction**, you describe *processes* for each entity (e.g., the life
  cycle of a truck or a task) and the engine handles the event list for you.

SimPM uses a process-interaction style: you write generator functions for entities,
yielding operations like “wait for 10 minutes”, “request a resource”, “release a
resource”, etc. The engine takes care of time advancement and event ordering.

DES vs. continuous simulation
-----------------------------

Continuous simulation tracks the system at every instant (or at very small time steps),
which is natural for physical processes like fluid flow or detailed machine motion.

DES focuses on *logical* events:

* We do not model the exact motion of a truck along the road.
* We only care about when it starts and finishes hauling.

This makes DES:

* More efficient for project and operations problems.
* Easier to connect to project management concepts (activities, resources, queues).

From real system to simulation model
-----------------------------------

The usual steps are:

1. **Define the system boundary** – what is in scope and what is not.
2. **Identify entities and resources** – who moves, who serves, what capacities exist.
3. **Identify events and activities** – arrivals, services, breakdowns, repairs, etc.
4. **Specify logic** – how entities flow, who gets priority, what happens on failure.
5. **Specify randomness** – which times or quantities should be modeled as random
   variables (distributions).
6. **Choose performance measures** – utilization, queue length, waiting time,
   throughput, project completion time, cost, etc.

How SimPM fits in
-----------------

General-purpose discrete-event simulation (DES) libraries such as
`SimPy <https://simpy.readthedocs.io/>`_ are widely used to model
queues and process flows. SimPy is a well-known open-source Python
library for this purpose.

SimPM adopts the same idea of process-based DES — you describe how a
system evolves over time using Python code, while an environment
advances the simulation clock and processes events in order. It
focuses specifically on project and construction management:

* Simulation time is interpreted as project time.
* Entities typically represent activities, work packages, or work items.
* Resources represent crews, equipment, or other limited project capacities.
* Distributions and logging are tuned for completion time, risk, and
  resource-usage questions.

You do not need prior experience with SimPy or other DES tools to use
SimPM. You can treat it as a focused project-simulation toolkit built
on these well-established ideas.

Where to go next
----------------

* :doc:`project-modeling` for SimPM-specific modeling concepts.
* :doc:`../getting-started` for a minimal runnable example.
* :doc:`../tutorials/hello-simpm` for a full earthmoving project tutorial.
