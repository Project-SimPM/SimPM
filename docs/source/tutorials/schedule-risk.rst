02 – Schedule risk analysis with Monte Carlo
============================================

.. contents:: On this page
   :local:

Objective
---------

The objective here is to explore how SimPM performs Monte Carlo simulations to estimate project
schedule risk. This tutorial runs a
small CPM-style network hundreds of times and summarize completion
percentiles.

Scenario
--------

We will run a seven-activity project with shared resources and
precedence links:

* Tasks ``1`` and ``2`` depend on ``0``.
* Task ``3`` depends on ``1`` and ``2``.
* Task ``4`` depends on ``1``; task ``5`` depends on ``2``.
* Task ``6`` depends on ``3``, ``4``, and ``5``.

Each activity consumes a limited pool of priority-controlled resources
with uncertain durations drawn from :mod:`simpm.dist`.

Simulation code (batchable)
---------------------------

.. code-block:: python

   import numpy as np
   import simpm
   import simpm.des as des
   import simpm.dist as dist

   # Data mirrors example/test_cpm.py
   DURATIONS = [
       dist.triang(2, 3, 4),   # activity 0
       dist.triang(1, 3, 5),   # activity 1
       5,                      # activity 2 (deterministic)
       1,                      # activity 3
       dist.triang(3.5, 5, 6), # activity 4
       4,                      # activity 5
       dist.norm(2.5, 1),      # activity 6
   ]
   RESOURCES = [1, 3, 2, 3, 1, 2, 2]
   PRIORITIES = [1, 2, 1, 1, 3, 1, 1]

   def simulate_once(seed: int, dashboard: bool = False, log: bool = False) -> float:
       """Run one CPM-like schedule and return total duration."""
       np.random.seed(seed)
       env = des.Environment(f"Run {seed}")
       tasks = env.create_entities(
           "task", len(DURATIONS), print_actions=False, log=log
       )
       pool = des.PriorityResource(
           env, "totalres", init=4, print_actions=False, log=log
       )

       def run_task(i: int, prereq=None):
           if prereq is not None:
               yield prereq
           yield tasks[i].get(pool, RESOURCES[i], PRIORITIES[i])
           yield tasks[i].do(f"activity-{i}", DURATIONS[i])
           yield tasks[i].put(pool, RESOURCES[i])

       p0 = env.process(run_task(0))
       p1 = env.process(run_task(1, p0))
       p2 = env.process(run_task(2, p0))
       p3 = env.process(run_task(3, p1 & p2))
       p4 = env.process(run_task(4, p1))
       p5 = env.process(run_task(5, p2))
       p6 = env.process(run_task(6, p4 & p5 & p3))

       # Batch runs should avoid the dashboard to keep each trial lightweight
       simpm.run(env, dashboard=dashboard)
       return env.now

   # Run many trials for percentiles
   durations = [simulate_once(seed) for seed in range(200)]
   p50, p80, p95 = np.percentile(durations, [50, 80, 95])

   print(f"Median completion: {p50:.2f}h")
   print(f"P80 completion: {p80:.2f}h")
   print(f"P95 completion: {p95:.2f}h")

If you want to explore a single run interactively, you can turn the
dashboard on for an ad hoc simulation (``dashboard`` must be a boolean)::

   simulate_once(seed=123, dashboard=True, log=True)

Interpreting the results
------------------------

* **Spread** – A wide gap between P50 and P95 indicates meaningful risk.
* **Drivers** – Increase the variance of a single activity (e.g., change
  ``dist.norm(2.5, 1)`` to ``dist.norm(2.5, 2.5)`` for activity 6) and
  re-run to see how it shifts the distribution.
* **Resource contention** – ``PriorityResource`` makes the four units of
  capacity shareable; lowering ``init`` to 3 or 2 amplifies queueing and
  risk.
* **Mitigations** – Try raising ``init`` or swapping ``PriorityResource``
  for a standard :class:`simpm.des.Resource` if you do not need
  priority-based allocation.

Tips
----

* Keep logging disabled (``log=False``) when running hundreds of trials
  to minimize overhead.
* ``dashboard`` only accepts ``True`` or ``False``; passing other values
  raises a ``ValueError`` in :func:`simpm.run`.
* Seed ``numpy`` (or Python's ``random``) so runs are reproducible.
* Point readers to ``example/test_cpm.py`` if they want the original
  single-run script without the Monte Carlo wrapper.

