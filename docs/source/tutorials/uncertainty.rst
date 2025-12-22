1. Modeling Uncertainty with Probability Distributions
=====================================================

.. contents:: On this page
   :local:

1.1 Overview
----------

In real-world projects, durations are rarely fixed. Equipment speed varies, 
workers perform differently, and environmental factors create unpredictability. 
This tutorial shows how to model uncertainty using **probability distributions**, 
turning deterministic simulations into **stochastic** ones that reflect real-world 
variability.

1.2 Why Uncertainty Matters
-----------------------

A deterministic model (fixed durations) tells you "how long if everything 
goes perfectly." A stochastic model (random durations) shows you:

- **Best case, worst case, and likely case** scenarios
- **Risk assessment**: What's the probability of exceeding a deadline?
- **Buffer planning**: How much contingency time do we really need?
- **Sensitivity analysis**: Which operation's variability matters most?

Without modeling uncertainty, you miss critical risks.

1.3 Available Distributions
-----------------------

SimPM includes several probability distributions. Each is suited to different 
types of operational variability:

.. code-block:: python

   from simpm.dist import norm, uniform, triang, expon, beta

   # Normal (Gaussian): Symmetric variation around a mean
   # Use for: Loading times, travel times, processing durations
   # Example: Most loads take ~7 min, rarely outside 5-9 min
   loading_dist = norm(mean=7, std=1.5)

   # Uniform: Any value in range equally likely
   # Use for: Bounded ranges with no preferred value
   # Example: Dumping takes 2-4 minutes, any time equally likely
   dumping_dist = uniform(a=2, b=4)

   # Triangular: Min, max, and mode (peak) all specified
   # Use for: Expert estimates with "most likely" value
   # Example: Optimistic 5 min, pessimistic 15 min, likely 8 min
   return_dist = triang(a=5, c=8, b=15)

   # Exponential: Right-skewed, long tail
   # Use for: Random event times (equipment failures, arrivals)
   # Example: ~50 min average, occasional much longer
   failure_dist = expon(scale=50)

**Which distribution to choose?**

- **Normal**: When variation is symmetric (natural randomness)
- **Uniform**: When min/max are hard bounds, no preference inside
- **Triangular**: When you have optimistic, pessimistic, and best-guess estimates
- **Exponential**: When modeling rare but long delays

1.4 Earthmoving with Uncertainty
-----------------------------

Let's extend the earthmoving scenario with realistic variability. Here's 
the basic idea:

.. code-block:: python

   import simpm
   import simpm.des as des
   from simpm.dist import norm, uniform
   import numpy as np

   # Set seed for reproducible randomness
   np.random.seed(42)

   env = des.Environment("Earthmoving with uncertainty")
   loader = des.Resource(env, "loader", init=1, capacity=1, log=True)
   dumped_dirt = des.Resource(env, "dirt", init=0, capacity=100000, log=True)

   # Create trucks with size attributes
   trucks = env.create_entities("truck", 3, log=True)
   for t, size in zip(trucks, [30, 35, 50]):
       t["size"] = size

   def truck_cycle(truck: des.Entity, loader: des.Resource, dumped_dirt: des.Resource):
       while True:
           # Loading duration varies with truck size (larger trucks take longer to load)
           # We model this as a normal distribution centered on 5 + size/20
           yield truck.get(loader, 1)
           loading_mean = 5 + truck["size"] / 20  # Expected loading time
           loading_dist = norm(loading_mean, std=0.5)  # ±0.5 min variation
           yield truck.do("loading", loading_dist.sample())
           yield truck.put(loader, 1)

           # Hauling time varies due to traffic, weather, and road conditions
           # Model as normal: mean 17 minutes, std 2 minutes
           hauling_dist = norm(17, 2)
           yield truck.do("hauling", hauling_dist.sample())

           # Dumping time depends on site conditions (equipment availability, queue)
           # Model as uniform: anywhere from 2 to 4 minutes equally likely
           dumping_dist = uniform(2, 4)
           yield truck.do("dumping", dumping_dist.sample())
           yield truck.add(dumped_dirt, truck["size"])

           # Return trip also has variation (traffic, driver difference)
           # Model as normal: mean 13 minutes, std 1.5 minutes
           return_dist = norm(13, 1.5)
           yield truck.do("return", return_dist.sample())

   # Create and run the simulation
   for truck in trucks:
       env.process(truck_cycle(truck, loader, dumped_dirt))

   simpm.run(env, dashboard=False, until=480)

   # Print results
   print(f"Project completed in {env.now:.2f} minutes")
   print(f"Total dirt moved: {dumped_dirt.level():.0f} m³")

Key Concepts
~~~~~~~~~~~~

1.4.1 **Distribution parameters** – Each distribution has parameters defining its shape:
   
   - ``norm(mean, std)`` – mean is the center, std controls spread
   - ``uniform(a, b)`` – a and b are the min and max bounds
   - ``triang(a, c, b)`` – a/b are bounds, c is the peak (mode)

1.4.2 **Sampling** – Each time you call ``dist.sample()``, you get a random value 
   drawn from that distribution. The value is different each time (unless you 
   fix the random seed).

1.4.3 **Seeding for reproducibility** – Call ``np.random.seed(42)`` at the start 
   of your simulation. This ensures the same "random" sequence every time, 
   making your results repeatable while still showing variability.

1.4.4 **Stochastic vs. deterministic** – With a seed, results are replicable but 
   vary from the fixed-duration model. Running the same simulation again 
   produces identical output (same seed). Running with a different seed 
   produces different but realistic variability.

1.5 Comparison: Deterministic vs. Stochastic
-----------------------------------------

Let's compare the same earthmoving project with and without uncertainty:

**Deterministic Model** (Fixed Durations):

.. code-block:: python

   # All durations fixed
   yield truck.do("loading", 6.5)      # Always 6.5 minutes
   yield truck.do("hauling", 17)       # Always 17 minutes
   yield truck.do("dumping", 3)        # Always 3 minutes
   yield truck.do("return", 13)        # Always 13 minutes

   # Run 1: 37 cycles, 1,330 m³
   # Run 2: 37 cycles, 1,330 m³ (identical)
   # Run 3: 37 cycles, 1,330 m³ (identical)

**Stochastic Model** (Random Durations):

.. code-block:: python

   # All durations vary based on distributions
   yield truck.do("loading", norm(6.5, 0.5).sample())  # 5.5-7.5 typical
   yield truck.do("hauling", norm(17, 2).sample())     # 15-19 typical
   yield truck.do("dumping", uniform(2, 4).sample())   # 2-4 equally likely
   yield truck.do("return", norm(13, 1.5).sample())    # 11.5-14.5 typical

   # Run 1: 37 cycles, 1,330 m³ (with seed=42)
   # Run 2: 37 cycles, 1,330 m³ (identical with same seed)
   # Run 3: 36 cycles, 1,295 m³ (different with seed=99)

**Key Differences:**

+---------------------------+--------------------+--------------------+
| Aspect                    | Deterministic      | Stochastic         |
+===========================+====================+====================+
| Durations                 | Fixed (6.5 min)    | Random (5.5-7.5)   |
+---------------------------+--------------------+--------------------+
| Repeatability             | Always same        | Same with same seed|
+---------------------------+--------------------+--------------------+
| Realism                   | Simplified         | Realistic          |
+---------------------------+--------------------+--------------------+
| Worst-case planning       | Not captured       | Can measure        |
+---------------------------+--------------------+--------------------+
| Risk assessment           | Single estimate    | Range of outcomes  |
+---------------------------+--------------------+--------------------+

1.6 Practical Example: The Seed in Action
-------------------------------------

Here's a complete minimal example showing the seed effect:

.. code-block:: python

   import numpy as np
   from simpm.dist import norm

   # Create a normal distribution
   loading_dist = norm(mean=7, std=1.5)

   # With seed 42
   np.random.seed(42)
   values_1 = [loading_dist.sample() for _ in range(5)]
   print("Run 1:", values_1)
   # Output: [6.48, 6.20, 7.53, 6.88, 7.12]

   # Run again with same seed → identical values
   np.random.seed(42)
   values_2 = [loading_dist.sample() for _ in range(5)]
   print("Run 2:", values_2)
   # Output: [6.48, 6.20, 7.53, 6.88, 7.12]  ← SAME!

   # Run with different seed → different values
   np.random.seed(99)
   values_3 = [loading_dist.sample() for _ in range(5)]
   print("Run 3:", values_3)
   # Output: [7.21, 6.56, 8.04, 6.35, 7.89]  ← DIFFERENT

**Why this matters:**

- **Seeding ensures reproducibility** – You can verify your code doesn't have bugs
- **Different seeds let you explore outcomes** – Run with seed 1, 2, 3... to see 
  the range of possibilities
- **Scientific rigor** – You can document exactly which randomness you used

1.7 Monte Carlo: Running Multiple Scenarios
---------------------------------------

One seed gives you one random scenario. To understand the full range of 
possible outcomes, run the simulation many times with different seeds.

**Modern Approach with simpm.run():**

SimPM provides a factory pattern for elegantly running Monte Carlo experiments. 
Define an environment factory function and let simpm.run() handle multiple 
replicates:

.. code-block:: python

   import simpm
   import simpm.des as des
   from simpm.dist import norm, uniform
   import statistics

   # Global variable for truck count
   _CURRENT_TRUCK_COUNT = 3

   def env_factory() -> des.Environment:
       """Create a fresh earthmoving environment."""
       global _CURRENT_TRUCK_COUNT
       
       env = des.Environment(f"Earthmoving ({_CURRENT_TRUCK_COUNT} trucks)")
       loader = des.Resource(env, "loader", init=1, capacity=1, log=True)
       dumped_dirt = des.Resource(env, "dirt", init=0, capacity=100000, log=True)
       
       trucks = env.create_entities("truck", _CURRENT_TRUCK_COUNT, log=True)
       for i, truck in enumerate(trucks):
           truck["size"] = [30, 35, 50][i % 3]
       
       # Set up truck processes with probabilistic durations
       for truck in trucks:
           env.process(truck_cycle(truck, loader, dumped_dirt))
       
       return env

   # Run 10 replicates with 5 trucks
   _CURRENT_TRUCK_COUNT = 5
   all_envs = simpm.run(env_factory, dashboard=False, number_runs=10)
   
   # Extract completion times
   durations = [env.now for env in all_envs]
   
   # Analyze results
   print(f"Mean duration: {statistics.mean(durations):.2f} minutes")
   print(f"Std deviation: {statistics.stdev(durations):.2f} minutes")
   print(f"Min: {min(durations):.2f}, Max: {max(durations):.2f}")

This **Monte Carlo** approach reveals:

- **Best case** – Maximum cycles, minimum time
- **Worst case** – Minimum cycles, maximum time
- **Average case** – Mean across all runs
- **Confidence intervals** – E.g., "90% of runs complete in X minutes or less"

1.8 Real-World Example: Earthmoving with Variable Fleet Size
------------------------------------------------------------

A practical example combining all concepts: **earthmoving_monte_carlo.py** 
runs 10 replicates for each truck configuration (3, 5, 7, 10 trucks), collecting 
actual project completion times from each run.

**Results from Monte Carlo Analysis (300-hour project target):**

+----------+---------------+-----------+----------+---------------------+
| Trucks   | Mean (hours)  | Std Dev   | Min      | Risk of Missing 300h|
+==========+===============+===========+==========+=====================+
| 3        | 593.78        | 1.49      | 591.30   | 100%                |
+----------+---------------+-----------+----------+---------------------+
| 5        | 393.45        | 0.85      | 392.48   | 100%                |
+----------+---------------+-----------+----------+---------------------+
| 7        | 298.40        | 0.42      | 297.81   | 0%                  |
+----------+---------------+-----------+----------+---------------------+
| 10       | 290.46        | 0.39      | 289.82   | 0%                  |
+----------+---------------+-----------+----------+---------------------+

**Key Insights:**

1. **Clear Decision Point** – The 300-hour target creates meaningful risk differentiation:
   - 3 trucks: 100% overrun (exceeds 300 hours in all runs) – not viable
   - 5 trucks: 100% overrun (exceeds 300 hours in all runs) – not viable
   - 7 trucks: 0% overrun risk (all runs complete within 300 hours) – viable
   - 10 trucks: 0% overrun risk (all runs complete within 300 hours) – viable

2. **Variability Decreases with Fleet Size** – More trucks = lower standard deviation:
   - 3 trucks: ±1.49 hours variability
   - 5 trucks: ±0.85 hours variability
   - 7 trucks: ±0.42 hours variability
   - 10 trucks: ±0.39 hours variability
   This shows that larger fleets reduce schedule unpredictability.

3. **Efficiency Gains Diminish** – From 3→5 trucks saves 200 hours; from 7→10 trucks saves only 8 hours:
   - 3→5 trucks: 200.33 hour reduction (33.7%)
   - 5→7 trucks: 94.95 hour reduction (24.2%)
   - 7→10 trucks: 7.94 hour reduction (2.7%)
   Adding more trucks yields diminishing returns in schedule improvement.

4. **Distribution Shape** – Higher uncertainty in distributions (increased std dev in 
   normal distributions and wider uniform ranges) reveals realistic project variability 
   that deterministic models miss.

**Running the Example:**

See the complete working implementation in ``example/earthmoving_monte_carlo.py``:

.. code-block:: bash

   python example/earthmoving_monte_carlo.py

The script:
- Defines ``env_factory()`` to create fresh environments with variable truck counts
- Uses ``simpm.run(env_factory, number_runs=10)`` for each configuration
- Extracts completion times directly from ``env.now``
- Calculates percentiles, confidence intervals, and risk assessments
- Compares configurations to guide fleet sizing decisions

1.9 Real-World Applications
-----------------------

**Project Planning:**
  Use Monte Carlo to determine realistic project duration with contingency buffer.
  If 90% of stochastic runs complete in 310 hours, plan for 330 hours (10% buffer).

**Resource Optimization:**
  Run stochastic simulations with different fleet sizes. What fleet minimizes 
  cost while meeting reliability targets?

**Risk Management:**
  Identify which operations' variability drives project risk. Invest in reducing 
  that variability (better equipment, training, etc.).

**Decision Support:**
  Compare alternatives (different loaders, truck sizes, schedules) using 
  stochastic simulation. Make decisions based on confidence intervals, not 
  just averages.

1.10 Complete Working Examples
------------------------

See these complete, documented examples in the ``example/`` folder:

- **earthmoving_with_truck_sizes.py** – Deterministic with attributes (no randomness)
- **earthmoving_probabilistic.py** – Stochastic single run (with randomness)
- **earthmoving_monte_carlo.py** – Monte Carlo with multiple fleet configurations

All include:

- Comprehensive docstrings and inline comments
- Analysis code showing how to extract and compare metrics
- Actual results from simulation runs
- Key insights and lessons learned

Run them yourself:

.. code-block:: bash

   python example/earthmoving_with_truck_sizes.py
   python example/earthmoving_probabilistic.py
   python example/earthmoving_monte_carlo.py

Then modify them:

- Change distribution parameters (e.g., ``norm(7, 1.5)`` to ``norm(7, 3)``)
- Try different truck counts
- Adjust the risk threshold for different project targets
- Experiment with different truck sizes and loaders

1.11 Summary
-------

Probability distributions transform simulations from "best case" to "real world":

1. **Use distributions** to model realistic variability in durations
2. **Choose appropriate distribution** for each operation (normal, uniform, etc.)
3. **Set random seed** (``np.random.seed``) for reproducible randomness
4. **Run Monte Carlo** (multiple runs with different seeds) to understand outcomes
5. **Use results for planning** – Confidence intervals, risk assessment, optimization

1.12 Next Steps
----------

- Read the :doc:`hello-simpm` tutorial for basic concepts and entity attributes
- Explore the complete probabilistic examples in ``example/``
- Try adding uncertainty to your own simulations
- See also the :doc:`dashboard-guide` for analyzing simulation results visually
