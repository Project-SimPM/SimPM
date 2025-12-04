Project modeling concepts in SimPM
==================================

SimPM models project management systems using discrete-event simulation.

Key building blocks
-------------------

* **Environment** (:class:`simpm.des.Environment`):
  the simulation world and event scheduler.
* **Entities** (:class:`simpm.des.Entity`):
  things that move through the system (e.g., work packages, tasks).
* **Resources** (:class:`simpm.des.Resource` and variants):
  crews, equipment, or other limited capacities.
* **Distributions** (:mod:`simpm.dist`):
  probabilistic durations and quantities
  (e.g., :func:`simpm.dist.norm`, :func:`simpm.dist.triang`).

Basic workflow
--------------

1. Define the environment and random seeds.
2. Declare resources with capacities (crews, machines).
3. Define processes/activities that:
   * Request resources
   * Wait for durations drawn from distributions
   * Release resources
4. Run the environment for a specified horizon.
5. Analyze logs and statistics (queue lengths, utilization, total duration).

Where to go next
----------------

* :doc:`../getting-started` for your first minimal run.
* :doc:`../tutorials/hello-simpm` for a full project example.
* :doc:`../tutorials/schedule-risk` for Monte Carlo schedule risk.
