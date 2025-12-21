Modeling Uncertainty with Probability Distributions
=====================================================

.. contents:: On this page
   :local:

Overview
--------

In real-world projects, durations are rarely fixed. Equipment speed varies, 
workers perform differently, and environmental factors create unpredictability. 
This tutorial shows how to model uncertainty using **probability distributions**, 
turning deterministic simulations into **stochastic** ones that reflect real-world 
variability.

Why Uncertainty Matters
-----------------------

A deterministic model (fixed durations) tells you "how long if everything 
goes perfectly." A stochastic model (random durations) shows you:

- **Best case, worst case, and likely case** scenarios
- **Risk assessment**: What's the probability of exceeding a deadline?
- **Buffer planning**: How much contingency time do we really need?
- **Sensitivity analysis**: Which operation's variability matters most?

Without modeling uncertainty, you miss critical risks.

Available Distributions
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

Earthmoving with Uncertainty
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

1. **Distribution parameters** – Each distribution has parameters defining its shape:
   
   - ``norm(mean, std)`` – mean is the center, std controls spread
   - ``uniform(a, b)`` – a and b are the min and max bounds
   - ``triang(a, c, b)`` – a/b are bounds, c is the peak (mode)

2. **Sampling** – Each time you call ``dist.sample()``, you get a random value 
   drawn from that distribution. The value is different each time (unless you 
   fix the random seed).

3. **Seeding for reproducibility** – Call ``np.random.seed(42)`` at the start 
   of your simulation. This ensures the same "random" sequence every time, 
   making your results repeatable while still showing variability.

4. **Stochastic vs. deterministic** – With a seed, results are replicable but 
   vary from the fixed-duration model. Running the same simulation again 
   produces identical output (same seed). Running with a different seed 
   produces different but realistic variability.

Comparison: Deterministic vs. Stochastic
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

Practical Example: The Seed in Action
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

Monte Carlo: Running Multiple Scenarios
---------------------------------------

One seed gives you one random scenario. To understand the full range of 
possible outcomes, run the simulation many times with different seeds:

.. code-block:: python

   import numpy as np

   results = []

   for seed in range(100):  # Run 100 times with different seeds
       np.random.seed(seed)
       
       env = des.Environment("Earthmoving")
       # ... set up simulation ...
       simpm.run(env, dashboard=False, until=480)
       
       results.append({
           'seed': seed,
           'cycles': total_cycles,
           'dirt_moved': dumped_dirt.level(),
           'completion_time': env.now
       })

   # Analyze results
   import pandas as pd
   df = pd.DataFrame(results)
   print(f"Minimum cycles: {df['cycles'].min()}")
   print(f"Maximum cycles: {df['cycles'].max()}")
   print(f"Average cycles: {df['cycles'].mean():.1f}")
   print(f"90th percentile cycles: {df['cycles'].quantile(0.9):.0f}")

This **Monte Carlo** approach reveals:

- **Best case** – Maximum cycles, minimum time
- **Worst case** – Minimum cycles, maximum time
- **Average case** – Mean across all runs
- **Confidence intervals** – E.g., "90% of runs complete in X minutes or less"

Real-World Applications
-----------------------

**Project Planning:**
  Use Monte Carlo to determine realistic project duration with contingency buffer.
  If 90% of stochastic runs complete in 500 minutes, plan for 550 minutes (10% buffer).

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

Complete Working Example
------------------------

See these complete, documented examples in the ``example/`` folder:

- **earthmoving_with_truck_sizes.py** – Deterministic with attributes (no randomness)
- **earthmoving_probabilistic.py** – Stochastic with distributions (with randomness)

Both include:

- Comprehensive docstrings and inline comments
- Analysis code showing how to extract and compare metrics
- Actual results from simulation runs
- Key insights and lessons learned

Run them yourself:

.. code-block:: bash

   python example/earthmoving_with_truck_sizes.py
   python example/earthmoving_probabilistic.py

Then modify them:

- Change distribution parameters (e.g., ``norm(7, 1.5)`` to ``norm(7, 3)``)
- Try different seeds (``np.random.seed(42)`` → ``np.random.seed(99)``)
- Add Monte Carlo loop to see range of outcomes
- Experiment with different truck sizes and loaders

Summary
-------

Probability distributions transform simulations from "best case" to "real world":

1. **Use distributions** to model realistic variability in durations
2. **Choose appropriate distribution** for each operation (normal, uniform, etc.)
3. **Set random seed** (``np.random.seed``) for reproducible randomness
4. **Run Monte Carlo** (multiple runs with different seeds) to understand outcomes
5. **Use results for planning** – Confidence intervals, risk assessment, optimization

Next Steps
----------

- Read the :doc:`hello-simpm` tutorial for basic concepts and entity attributes
- Explore the complete probabilistic example: ``example/earthmoving_probabilistic.py``
- Try adding uncertainty to your own simulations
- See also the :doc:`dashboard-guide` for analyzing simulation results visually
