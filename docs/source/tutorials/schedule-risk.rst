Schedule risk analysis with Monte Carlo
=========================================

.. contents:: On this page
   :local:

Objective
---------

The objective here is to explore how SimPM performs Monte Carlo simulations to estimate project
schedule risk. This tutorial runs a small CPM-style network hundreds of times and shows 
completion time distributions and percentiles.

Scenario
--------

We will run a seven-activity project with shared resources and precedence links:

* Task 1 depends on 0.
* Task 2 depends on 0.
* Task 3 depends on 1 and 2.
* Task 4 depends on 1; task 5 depends on 2.
* Task 6 depends on 3, 4, and 5.

Each activity consumes a limited pool of priority-controlled resources
with uncertain durations drawn from :mod:`simpm.dist` (triangular and normal distributions).

Simulation code
---------------

.. code-block:: python

   import simpm
   import simpm.des as des
   import simpm.dist as dist


   def env_factory() -> des.Environment:
       """Build and return ONE fresh CPM environment with priorities."""

       # Data mirrors example/probabilistic_cpm.py
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
       PRIORITIES = [1, 2, 1, 1, 3, 1, 1]  # lower = higher priority

       env = des.Environment("Probabilistic CPM with priorities")

       tasks = env.create_entities("task", len(DURATIONS), print_actions=False, log=True)
       pool = des.PriorityResource(env, "total_resources", init=4, print_actions=False, log=True)

       def run_task(i: int, prereq=None):
           if prereq is not None:
               yield prereq
           yield tasks[i].get(pool, RESOURCES[i], PRIORITIES[i])
           yield tasks[i].do(f"activity-{i}", DURATIONS[i])
           yield tasks[i].put(pool, RESOURCES[i])

       p0 = env.process(run_task(0))
       p1 = env.process(run_task(1, prereq=p0))
       p2 = env.process(run_task(2, prereq=p0))
       p3 = env.process(run_task(3, prereq=(p1 & p2)))
       p4 = env.process(run_task(4, prereq=p1))
       p5 = env.process(run_task(5, prereq=p2))
       p6 = env.process(run_task(6, prereq=(p3 & p4 & p5)))  # noqa: F841

       return env


   # Run 200 Monte Carlo trials with interactive dashboard
   all_envs = simpm.run(env_factory, dashboard=True, number_runs=200, start_async=True)

   # Check completion times from first and last runs
   first = all_envs[0].run_history[-1]["duration"]
   last = all_envs[-1].run_history[-1]["duration"]
   print(f"First run duration: {first:.2f}")
   print(f"Last run duration: {last:.2f}")

Printing Statistics
-------------------

After the Monte Carlo runs complete, print percentile-based statistics:

.. code-block:: python

   import numpy as np
   
   # Extract completion times from all runs
   all_durations = [env.run_history[-1]["duration"] for env in all_envs]
   
   # Calculate percentiles
   p50, p80, p95 = np.percentile(all_durations, [50, 80, 95])
   p_min = min(all_durations)
   p_max = max(all_durations)
   p_mean = np.mean(all_durations)
   p_std = np.std(all_durations)
   
   print("=" * 50)
   print("SCHEDULE RISK ANALYSIS (Monte Carlo)")
   print("=" * 50)
   print(f"Number of runs: {len(all_durations)}")
   print(f"Minimum completion time: {p_min:.2f}")
   print(f"Maximum completion time: {p_max:.2f}")
   print(f"Mean completion time:    {p_mean:.2f}")
   print(f"Std Dev:                 {p_std:.2f}")
   print(f"Median (P50):            {p50:.2f}")
   print(f"80th percentile (P80):   {p80:.2f}")
   print(f"95th percentile (P95):   {p95:.2f}")
   print(f"Schedule risk (P95-P50): {p95 - p50:.2f}")
   print("=" * 50)

This prints summary statistics like::

   ==================================================
   SCHEDULE RISK ANALYSIS (Monte Carlo)
   ==================================================
   Number of runs: 200
   Minimum completion time: 23.45
   Maximum completion time: 38.92
   Mean completion time:    29.83
   Std Dev:                 3.21
   Median (P50):            29.15
   80th percentile (P80):   33.02
   95th percentile (P95):   36.75
   Schedule risk (P95-P50): 7.60
   ==================================================

Advanced: Entity and Resource Statistics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Print activity variance across all runs:

.. code-block:: python

   import pandas as pd
   
   # Collect activity schedules from all runs
   all_activities = []
   for env in all_envs:
       for entity in env.entities:
           schedule = entity.schedule()
           if not schedule.empty:
               schedule['run_id'] = env.run_number
               schedule['duration'] = schedule['finish_time'] - schedule['start_time']
               all_activities.append(schedule)
   
   if all_activities:
       activity_df = pd.concat(all_activities, ignore_index=True)
       
       # Show which activities have the most variance
       print("\nActivity Duration Statistics (across all runs):")
       print(activity_df.groupby('activity')['duration'].describe())
       
       # Identify the critical activities
       variance = activity_df.groupby('activity')['duration'].std()
       print("\nActivities ranked by variance (risk drivers):")
       print(variance.sort_values(ascending=False))

Print resource utilization statistics:

.. code-block:: python

   # Collect resource metrics from all runs
   resource_stats = []
   for env in all_envs:
       for resource in env.resources:
           resource_stats.append({
               'run_id': env.run_number,
               'resource': resource.name,
               'avg_utilization': resource.average_utilization(),
               'total_idle_time': resource.total_time_idle(),
               'total_use_time': resource.total_time_in_use(),
           })
   
   if resource_stats:
       stats_df = pd.DataFrame(resource_stats)
       
       print("\nResource Utilization Summary:")
       print(stats_df.groupby('resource')[['avg_utilization', 'total_idle_time']].describe())
       
       # Identify bottleneck resources
       print("\nAverage utilization by resource (bottleneck indicators):")
       print(stats_df.groupby('resource')['avg_utilization'].mean().sort_values(ascending=False))

How it works
------------

1. **``env_factory()``** – Encapsulates the project network and resource constraints.
   :func:`simpm.run` calls this factory ``number_runs`` times, each time creating a fresh 
   environment with new random samples from the distributions.

2. **``simpm.run(..., number_runs=200)``** – Runs the simulation 200 times, each time 
   executing the project with different random durations. This generates a sample of 
   completion times representing the range of possible outcomes.

3. **``dashboard=True``** – Shows an interactive Streamlit dashboard that displays:
   
   - **Finish time distribution** – Histogram and box plot of completion times
   - **Entity schedules** – Activity start/finish times for each task
   - **Resource usage** – Queue lengths and utilization over time
   
   Click on the **Simulation runs** tab to see finish time statistics and visualizations.

4. **``start_async=True``** – Runs Monte Carlo trials in the background, allowing the
   dashboard to load while simulations execute.

Understanding the results
--------------------------

* **Wide finish time spread (P50 to P95)** – Indicates substantial schedule risk.
  For example, if P50 = 25h but P95 = 35h, there is 10 hours of schedule variance.

* **Shift the distribution** – Increase variance in one activity and re-run to see
  how it affects overall risk. For example, change ``dist.norm(2.5, 1)`` to 
  ``dist.norm(2.5, 2.5)`` for activity 6.

* **Resource contention** – Lower the resource pool (change ``init=4`` to ``init=2``)
  to see how contention amplifies queueing and extends the schedule.

* **Mitigations** – Try raising the pool capacity or comparing ``PriorityResource``
  against a standard :class:`simpm.des.Resource` if priorities are not needed.

Tips
----

* **Reduce logging for speed** – Set ``log=False`` when possible to speed up batch runs.
* **Larger sample sizes** – Increase ``number_runs`` to 500 or 1000 for smoother tail 
  estimates (P80, P95).
* **Reproducibility** – Set ``np.random.seed()`` before importing distributions if you 
  need repeatable results.
* **Single run debugging** – Create a minimal script without ``env_factory`` to debug 
  a single run interactively.

