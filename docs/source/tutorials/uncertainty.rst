1. Modeling Uncertainty with Probability Distributions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. contents:: On this page
   :local:

1.1 Overview
~~~~~~~~~~~~

In real-world projects, durations are rarely fixed. Equipment speed varies, 
workers perform differently, and environmental factors create unpredictability. 
This tutorial shows how to model uncertainty using **probability distributions**, 
turning deterministic simulations into **stochastic** ones that reflect real-world 
variability.

1.2 Why Uncertainty Matters
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A deterministic model (fixed durations) tells you "how long if everything 
goes perfectly." A stochastic model (random durations) shows you:

- **Best case, worst case, and likely case** scenarios
- **Risk assessment**: What's the probability of exceeding a deadline?
- **Buffer planning**: How much contingency time do we really need?
- **Sensitivity analysis**: Which operation's variability matters most?

Without modeling uncertainty, you miss critical risks.

1.3 Available Distributions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
   return_dist = triang(5, 8, b=15)

   # Exponential: Right-skewed, long tail
   # Use for: Random event times (equipment failures, arrivals)
   # Example: ~50 min average, occasional much longer
   failure_dist = expon(50)

**Which distribution to choose?**

- **Normal**: When variation is symmetric (natural randomness)
- **Uniform**: When min/max are hard bounds, no preference inside
- **Triangular**: When you have optimistic, pessimistic, and best-guess estimates
- **Exponential**: When modeling rare but long delays

1.4 Earthmoving with Uncertainty
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
           # Model as normal: mean 17 minutes, std 4 minutes (high variability)
           yield truck.do("hauling", norm(17, 4))

           # Dumping time depends on site conditions (equipment availability, queue)
           # Model as uniform: anywhere from 2 to 5 minutes equally likely
           yield truck.do("dumping", uniform(2, 5))
           yield truck.add(dumped_dirt, truck["size"])

           # Return trip also has variation (traffic, driver difference)
           # Model as normal: mean 13 minutes, std 3 minutes
           yield truck.do("return", norm(13, 3))

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

1.4.2 **Sampling via do()** – In SimPM, sampling happens automatically when you 
   pass a distribution object to ``entity.do()``. Each time ``do()`` executes 
   (in each simulation replicate), it draws a fresh random sample from that 
   distribution. You don't need to call ``.sample()`` explicitly – just pass 
   the distribution object directly to ``do()``.

1.4.3 **Seeding for reproducibility** – Call ``np.random.seed(42)`` at the start 
   of your simulation. This ensures the same "random" sequence every time, 
   making your results repeatable while still showing variability.

1.4.4 **Stochastic vs. deterministic** – With a seed, results are replicable but 
   vary from the fixed-duration model. Running the same simulation again 
   produces identical output (same seed). Running with a different seed 
   produces different but realistic variability.

1.5 Comparison: Deterministic vs. Stochastic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
   # SimPM's do() method accepts distribution objects directly
   # and samples internally on each replicate run
   yield truck.do("loading", norm(6.5, 0.5))  # 5.5-7.5 typical
   yield truck.do("hauling", norm(17, 4))     # 13-21 typical (higher variability)
   yield truck.do("dumping", uniform(2, 5))   # 2-5 equally likely
   yield truck.do("return", norm(13, 3))      # 10-16 typical (higher variability)

   # Run 1: 37 cycles, 1,330 m³ (with seed=42)
   # Run 2: 37 cycles, 1,330 m³ (identical with same seed)
   # Run 3: 36 cycles, 1,295 m³ (different with seed=99)

**Key Pattern: Direct Distribution Objects**

Note: In SimPM, you pass **distribution objects directly** to ``do()``, 
not pre-sampled values. The ``do()`` method automatically samples from the 
distribution on each simulation run:

.. code-block:: python

   # CORRECT: Pass the distribution object directly
   yield truck.do("hauling", norm(17, 4))     # SimPM samples internally

   # NOT: Don't pre-sample before passing
   # yield truck.do("hauling", norm(17, 4).sample())  # Inefficient

This approach is elegant because:
- Distribution definition is clear and concise
- Each replicate gets different random samples automatically
- Works seamlessly with ``simpm.run(factory, number_runs=10)``

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

1.7 Monte Carlo: Running Multiple Scenarios
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

**Results from Monte Carlo Analysis (10 replicates per configuration):**

With **actual distributions** norm(5+size/20, 0.5-0.8) for loading, 
norm(17, 4) for hauling, uniform(2, 5) for dumping, and norm(13, 3) for return:

+----------+---------------+----------+-----------+---------------------+
| Trucks   | Mean (hours)  | Std Dev  | Min (hrs) | Risk > 300 hours    |
+==========+===============+==========+===========+=====================+
| 3        | 593.14        | 1.50 min | 590.81    | 100% (all 10 runs)  |
+----------+---------------+----------+-----------+---------------------+
| 5        | 393.41        | 24.35min | 392.65    | 100% (all 10 runs)  |
+----------+---------------+----------+-----------+---------------------+
| 7        | 297.85        | 26.11min | 297.41    | 0% (all runs < 300) |
+----------+---------------+----------+-----------+---------------------+
| 10       | 290.31        | 21.06min | 289.60    | 0% (all runs < 300) |
+----------+---------------+----------+-----------+---------------------+

**Key Insights:**

1. **Clear Decision Point** – The 300-hour target creates meaningful risk differentiation:
   - 3 trucks: 100% overrun (all 10 replicates exceed 300 hours) – **not viable**
   - 5 trucks: 100% overrun (all 10 replicates exceed 300 hours) – **not viable**
   - 7 trucks: 0% overrun risk (all 10 replicates complete within 300 hours) – **viable**
   - 10 trucks: 0% overrun risk (all 10 replicates complete within 300 hours) – **viable**

2. **Variability Pattern** – Interestingly, more trucks doesn't always mean lower variability 
   in this case. With high variability in hauling (std=4) and return (std=3), the pattern 
   is more complex than with low-uncertainty models.

3. **Efficiency Gains Diminish** – Adding trucks shows decreasing marginal benefit:
   - 3→5 trucks: saves 199.73 hours (33.7% reduction)
   - 5→7 trucks: saves 95.56 hours (24.3% reduction)
   - 7→10 trucks: saves 7.54 hours (2.5% reduction)
   The first jump (3→5 trucks) provides the biggest scheduling improvement.

4. **Distribution Impact** – Using realistic, high-variability distributions 
   (norm(17, 4), uniform(2, 5), norm(13, 3)) creates meaningful uncertainty that 
   deterministic models miss. These values reflect real-world earthmoving conditions 
   with traffic, weather, and operational variability.

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See these complete, documented examples in the ``example/`` folder:

- **earthmoving_with_truck_sizes.py** – Deterministic with attributes (fixed durations)
- **earthmoving_probabilistic.py** – Stochastic single run with factory pattern (10 replicates)
- **earthmoving_monte_carlo.py** – Monte Carlo analysis across fleet configurations

**Key Pattern Used:**

All examples use the **factory pattern** with ``simpm.run()``::

   def env_factory() -> des.Environment:
       # Create fresh environment with current truck count
       env = des.Environment(...)
       # ... set up resources and processes ...
       return env

   all_envs = simpm.run(env_factory, number_runs=10)
   durations = [env.now for env in all_envs]

**Distributions in All Probabilistic Examples:**

- Loading: ``norm(5 + size/20, 0.5 + 0.1*(i%3))`` – varies by truck size
- Hauling: ``norm(17, 4)`` – high variability (traffic, conditions)
- Dumping: ``uniform(2, 5)`` – site conditions uncertain
- Return: ``norm(13, 3)`` – traffic and route variability

**Important:** Distributions are passed **directly** to ``do()``, not sampled::

   yield truck.do("loading", loading_dists[truck_id])  # Correct
   # NOT: yield truck.do("loading", loading_dists[truck_id].sample())

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
~~~~~~~~~~~~

Probability distributions transform simulations from "best case" to "real world":

1. **Use distributions** to model realistic variability in durations
2. **Choose appropriate distribution** for each operation (normal, uniform, etc.)
3. **Set random seed** (``np.random.seed``) for reproducible randomness
4. **Run Monte Carlo** (multiple runs with different seeds) to understand outcomes
5. **Use results for planning** – Confidence intervals, risk assessment, optimization

1.12 Next Steps
~~~~~~~~~~~~~~~

- Read the :doc:`hello-simpm` tutorial for basic concepts and entity attributes
- Explore the complete probabilistic examples in ``example/``
- Try adding uncertainty to your own simulations
- See also the :doc:`dashboard-guide` for analyzing simulation results visually
