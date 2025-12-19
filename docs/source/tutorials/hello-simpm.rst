Hello SimPM: first project simulation
======================================

.. contents:: On this page
   :local:

Overview
--------

The objective here is to build a minimal project simulation using SimPM's discrete-event engine.
This walkthrough mirrors the runnable example in ``example/simple earthmoving.py``
and shows how to inspect queueing and utilization once the run finishes.

Scenario
--------

Model a simple earthmoving loop:

* Ten trucks cycle through **load → haul → dump → return**.
* A single loader is the shared resource; only one truck can load at a time.
* We track how long the loader is busy, how long trucks wait, and how much
  dirt is moved.

Full example (from the examples folder)
---------------------------------------

The complete, well-documented example with comprehensive comments and results analysis:

.. code-block:: python

   """
   Simple Earthmoving Operation Simulation

   This simulation models a basic earthmoving project with:
   - 1 loader that loads dirt into trucks
   - 10 trucks that haul dirt from pit to dump site
   - Goal: Calculate loader utilization and truck waiting times

   PROCESS FLOW:
       1. Truck waits for loader to be available (if queued)
       2. Loader loads 60 units of dirt into truck (7 minutes)
       3. Truck hauls to dump site (17 minutes)
       4. Truck dumps dirt (3 minutes)
       5. Truck returns to pit (13 minutes)
       6. Truck returns to step 1

   KEY METRICS:
       - Loader utilization percentage
       - Average truck waiting time at loader
       - Total project completion time
   """
   import simpm
   import simpm.des as des

   def truck_cycle(truck: des.Entity, loader: des.Resource, dumped_dirt: des.Resource):
       """
       Truck operation cycle process.
       
       Simulates the complete cycle of a truck in the earthmoving operation:
       loading dirt, hauling to dump site, dumping, and returning to pit.
       """
       while True:
           # LOADING PHASE: Wait for loader availability, then load 60 units
           yield truck.get(loader, 1)  # Acquire the loader (wait if busy)
           yield truck.do("loading", 7)  # Loading takes 7 minutes
           yield truck.put(loader, 1)  # Release the loader for next truck

           # HAULING PHASE: Transport loaded dirt to dump site
           yield truck.do("hauling", 17)  # Hauling takes 17 minutes
           
           # DUMPING PHASE: Dump the 60 units of dirt
           yield truck.do("dumping", 3)   # Dumping takes 3 minutes
           yield truck.add(dumped_dirt, 60)  # Record the dumped dirt
           
           # RETURN PHASE: Return to pit for next load
           yield truck.do("return", 13)  # Return journey takes 13 minutes

   # Create the discrete event simulation environment
   env = des.Environment("Earthmoving")

   # Create the loader resource (only 1 loader available)
   loader = des.Resource(env, "loader", init=1, capacity=1, log=True)

   # Create counter for total dumped dirt (tracks project progress)
   dumped_dirt = des.Resource(env, "dirt", init=0, capacity=100000, log=True)

   # Create 10 truck entities
   trucks = env.create_entities("truck", 10, print_actions=False, log=True)

   # Start the truck cycle process for each truck
   for t in trucks:
       env.process(truck_cycle(t, loader, dumped_dirt))

   # Run the simulation until all processes complete
   simpm.run(env, dashboard=False)

   # Print results and analysis
   print(f"Project finished at t = {env.now:.2f} minutes")
   print(f"Loader Utilization: {loader.average_utilization()*100:.2f}%")
   print("Loader queue stats:\n", loader.waiting_time().describe())
   print("Truck 0 schedule sample:\n", trucks[0].schedule().head())

How it works
------------

1. **Environment and resources** – :class:`simpm.des.Environment` keeps
   simulation time. :class:`simpm.des.Resource` tracks capacity and queue
   behavior (``log=True`` records status changes for later analysis).

2. **Entities and processes** – :meth:`simpm.des.Environment.create_entities` produces
   :class:`simpm.des.Entity` objects. ``get`` and ``put`` wrap resource
   requests; ``do`` performs time-consuming activities; ``add`` deposits
   output into an inventory-like resource.

3. **Process lifecycle** – ``env.process`` schedules ``truck_cycle`` for each truck.
   The process uses ``yield`` statements to represent time-consuming activities.
   Once scheduled, ``simpm.run`` executes the simulation until no events remain.

4. **Analysis outputs** – Methods like ``status_log()``, ``waiting_time()``, 
   ``average_utilization()``, and ``schedule()`` expose queueing and productivity 
   insights after the run completes.

Simulation Results
------------------

Running the simulation produces the following results:

.. code-block:: text

   ============================================================================
   EARTHMOVING PROJECT SIMULATION RESULTS
   ============================================================================
   
   Project finished at t = 11752.00 minutes
   Approximately 195.87 hours
   
   Loader Utilization: 100.00%
   (Loader was busy 100.00% of the time)
   
   Loader Queue Statistics:
     Total waiting samples: 1676
     Average truck waiting time: 30.01 minutes
     Maximum truck waiting time: 63.00 minutes
     Minimum truck waiting time: 0.00 minutes
   
   Sample Schedule (Truck 0 first 10 actions):
     activity  start_time  finish_time
   0  loading           0            7
   1  hauling           7           24
   2  dumping          24           27
   3   return          27           40
   4  loading          70           77
   5  hauling          77           94
   6  dumping          94           97
   7   return          97          110
   8  loading         140          147
   9  hauling         147          164
   
   Total dirt dumped: 99960 units
   Total load cycles completed: 1666 loads

**Key Insights:**

- **Project Duration**: The project takes approximately 196 hours (11,752 minutes) to 
  move nearly 100,000 units of dirt with 10 trucks and 1 loader.

- **Loader is the Bottleneck**: The loader operates at 100% utilization, meaning it
  is never idle. This indicates the loader is the constraining resource.

- **Truck Waiting Times**: Trucks wait an average of 30 minutes per cycle to access
  the loader, with a maximum wait of 63 minutes. This queuing delay represents lost
  productivity.

- **Production Rate**: The system completes 1,666 load cycles (roughly 167 loads per truck),
  indicating that truck utilization is reduced due to waiting at the loader.

- **Optimization Opportunities**:
  
  - Adding a second loader would significantly reduce truck waiting times
  - Faster loading equipment could increase throughput
  - Different fleet sizes could be tested to find optimal truck-to-loader ratio
  - Variable travel times would provide more realistic modeling

Entity attributes in action
---------------------------

Entities behave like dictionaries for arbitrary metadata. You can
store custom attributes (such as truck size) and use them inside the
process logic with square-bracket access:

.. code-block:: python

   env = des.Environment("Earthmoving with sizes")
   loader = des.Resource(env, "loader", init=1, capacity=1, log=True)
   dumped_dirt = des.Resource(env, "dirt", init=0, capacity=100000, log=True)

   # Attach a size attribute (cubic meters per load) to each truck
   trucks = env.create_entities("truck", 3, log=True)
   for t, size in zip(trucks, [30, 35, 50]):
       t["size"] = size

   def truck_cycle(truck: des.Entity, loader: des.Resource, dumped_dirt: des.Resource):
       while True:
           # Load time grows with truck size
           yield truck.get(loader, 1)
           yield truck.do("loading", 5 + truck["size"] / 20)
           yield truck.put(loader, 1)

           # Haul and dump exactly the truck's load size
           yield truck.do("hauling", 17)
           yield truck.do("dumping", 3)
           yield truck.add(dumped_dirt, truck["size"])

           yield truck.do("return", 13)

This pattern keeps the tutorial scenario the same, but shows how
truck-level attributes influence both durations (loading time) and
production (dirt moved per cycle).

Try it yourself
---------------

Run the shipped example directly:

.. code-block:: bash

   python example/simple earthmoving.py

The script includes:

- **Comprehensive docstrings** explaining each process and its parameters
- **Detailed inline comments** describing each simulation phase
- **Organized code sections** separating processes, setup, execution, and analysis
- **Complete results reporting** with statistics and insights
- **Performance metrics** including utilization, waiting times, and throughput

Then review the generated output to see which trucks waited longest, how hard 
the loader was pushed, and how much dirt was successfully moved.
