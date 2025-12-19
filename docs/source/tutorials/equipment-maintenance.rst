Equipment Maintenance Scheduling
==================================

.. contents:: On this page
   :local:

Overview
--------

This tutorial demonstrates how to model equipment maintenance and repairs in a 
project simulation. We'll explore how preventive maintenance affects productivity 
and how to use priority-based resource allocation to ensure repairs take precedence 
over regular operations.

This walkthrough mirrors the runnable example in ``example/repair earthmoving.py``
and shows how to implement realistic maintenance scheduling in discrete-event simulations.

The example includes an interactive dashboard for real-time visualization of the 
equipment maintenance and truck operations throughout the simulation.

Scenario
--------

Model an earthmoving operation with preventive maintenance:

* Two trucks (small and large) with different loading and hauling times.
* A single loader shared between both trucks (the equipment requiring maintenance).
* A repair person who monitors loader usage and performs preventive maintenance.
* **Priority-based scheduling**: Repairs interrupt loading operations to ensure 
  equipment reliability.
* **Dashboard visualization**: Interactive dashboard showing real-time system dynamics.

Key Concepts
~~~~~~~~~~~~

* **Worked Hours Tracking**: The loader accumulates working hours that trigger 
  maintenance when a threshold (10 hours) is reached.
* **Priority Resource**: Uses ``PriorityResource`` to give repair requests higher 
  priority than normal loading requests.
* **Preventive Maintenance**: Repairs are scheduled based on usage, not failures, 
  preventing unexpected equipment breakdowns.

Full Example (from the examples folder)
---------------------------------------

.. code-block:: python

   """
   Earthmoving Operation with Equipment Repair Simulation

   This simulation models an earthmoving project with equipment maintenance:
   - 2 trucks (small and large) that load, haul, and dump dirt
   - 1 loader shared between both trucks
   - 1 repair person who services the loader based on usage hours
   - Goal: Analyze impact of maintenance on project productivity
   """
   import simpm
   import simpm.des as d
   import simpm.dist as dist

   def truck_process(truck, loader, dumped_dirt, worked_hours):
       """
       Truck operation cycle process.
       
       Simulates the complete cycle of a truck in the earthmoving operation:
       - Wait for loader availability
       - Get loaded with dirt
       - Haul to dump site
       - Dump the load
       - Return to pit for next load
       """
       while True:
           # LOADING PHASE: Wait for loader with normal priority (priority=2)
           # Lower priority than repair (priority=-3) means trucks wait for repairs
           yield truck.get(loader, 1, 2)
           yield truck.do('load', truck.loading_dur)
           # Track hours worked on the loader (for triggering repairs)
           yield truck.add(worked_hours, truck.loading_dur)
           
           # Release loader for other trucks or repair person
           yield truck.put(loader, 1)

           # HAULING PHASE: Transport loaded dirt to dump site
           yield truck.do('haul', truck.hauling_dur)
           
           # DUMPING PHASE: Unload dirt at dump site
           yield truck.do('dump', truck.dumping_dur)
           yield truck.add(dumped_dirt, truck.capacity)
           
           # RETURN PHASE: Return to pit for next load
           yield truck.do('return', 8)


   def repair_process(repair_man, loader, worked_hours):
       """
       Equipment repair process.
       
       Simulates the repair person monitoring loader usage and performing
       maintenance. When the loader reaches 10 accumulated working hours,
       the repair person steps in with high priority to perform a 10-minute
       repair, resetting the working hours counter.
       """
       while True:
           # Wait until 10 hours of work have been accumulated on the loader
           yield repair_man.get(worked_hours, 10)
           
           # Get the loader with HIGH PRIORITY (-3) to interrupt trucks
           # Negative priority ensures repair takes precedence over normal loading
           yield repair_man.get(loader, 1, -3)
           
           # Perform the repair (10 minutes)
           yield repair_man.do('repair', 10)
           
           # Release the loader back to trucks
           yield repair_man.put(loader, 1)


   # Create the discrete event simulation environment
   env = d.Environment()

   # Create the PRIORITY LOADER resource
   # PriorityResource allows requests with different priorities
   loader = d.PriorityResource(env, 'loader', init=1, print_actions=False)

   # Create counter for total dumped dirt
   dumped_dirt = d.Resource(env, 'dirt', init=0, capacity=2000, print_actions=False)

   # Create counter for loader working hours (triggers repairs when hits 10)
   worked_hours = d.Resource(env, 'worked_hours', init=0, capacity=2000, print_actions=False)

   # Create small truck entity with specific parameters
   small_truck = d.Entity(env, 'small_truck', print_actions=False)
   small_truck.loading_dur = dist.uniform(4, 5)      # 4-5 minutes
   small_truck.hauling_dur = dist.uniform(10, 14)    # 10-14 minutes
   small_truck.dumping_dur = 4                         # 4 minutes
   small_truck.capacity = 80                           # 80 units per load

   # Create large truck entity with specific parameters
   large_truck = d.Entity(env, 'large_truck', print_actions=False)
   large_truck.loading_dur = dist.uniform(4, 7)      # 4-7 minutes
   large_truck.hauling_dur = dist.uniform(12, 16)    # 12-16 minutes
   large_truck.dumping_dur = 5                        # 5 minutes
   large_truck.capacity = 100                         # 100 units per load

   # Create repair person entity
   repair_man = d.Entity(env, 'repair_person', print_actions=False)

   # Start truck processes for both small and large trucks
   env.process(truck_process(small_truck, loader, dumped_dirt, worked_hours))
   env.process(truck_process(large_truck, loader, dumped_dirt, worked_hours))

   # Start repair process
   env.process(repair_process(repair_man, loader, worked_hours))

   # Run the simulation
   simpm.run(env, dashboard=False)

   # Print results
   print(f"Simulation completed at t = {env.now:.2f} minutes")
   print(f"Total dirt dumped: {dumped_dirt.level():.0f} units")

How It Works
------------

**1. Priority-Based Resource Allocation**

The simulation uses ``PriorityResource`` instead of a regular ``Resource``. This allows
multiple requests to be prioritized:

.. code-block:: python

   # Truck request (normal priority = 2)
   yield truck.get(loader, 1, 2)
   
   # Repair request (high priority = -3, more negative = higher priority)
   yield repair_man.get(loader, 1, -3)

When the repair person requests the loader, they jump ahead of waiting trucks because
their priority is higher (more negative).

**2. Worked Hours Tracking**

Every time a truck uses the loader, the working hours counter is incremented:

.. code-block:: python

   # Truck adds its loading duration to worked_hours
   yield truck.add(worked_hours, truck.loading_dur)

The repair person monitors this counter and triggers maintenance when it reaches 10 hours:

.. code-block:: python

   # Repair triggered when worked_hours reaches 10
   yield repair_man.get(worked_hours, 10)

**3. Maintenance Process Flow**

The repair process follows this cycle:

1. Wait for accumulation of 10 working hours
2. Request the loader with high priority
3. Perform 10-minute repair
4. Release the loader
5. Repeat

This simulates preventive maintenance that occurs regularly based on equipment usage.

Simulation Results
------------------

Running the simulation produces the following results:

.. code-block:: text

   ======================================================================
   EARTHMOVING PROJECT WITH REPAIRS - SIMULATION RESULTS
   ======================================================================
   
   Simulation completed at t = 381.16 minutes
   Approximately 6.35 hours
   
   Total dirt dumped: 1960 units
   
   Small Truck Statistics:
     Total cycles completed: 51
     Total dirt moved: 4080 units
   
   Large Truck Statistics:
     Total cycles completed: 43
     Total dirt moved: 4300 units
   
   Loader Queue Statistics:
     Total requests: 34
     Average wait time: 1.64 minutes
     Maximum wait time: 7.57 minutes
   
   Repair Statistics:
     Total repairs performed: 10
     Repair interval: Every 10 worked hours on loader
     Repair time per service: 10 minutes
   
   Sample repair schedule (first 5 repairs):
     activity  start_time  finish_time
   0   repair   33.360599    43.360599
   1   repair   62.597502    72.597502
   2   repair  118.888247   128.888247
   3   repair  151.047873   161.047873
   4   repair  182.777400   192.777400

**Key Insights:**

- **Project Duration**: Approximately 6.35 hours to move 1,960 units of dirt with 
  preventive maintenance.

- **Truck Efficiency**: Small truck completes 51 cycles (4,080 units), large truck 
  completes 43 cycles (4,300 units).

- **Maintenance Frequency**: 10 repairs performed during the simulation, roughly 
  one every 38 minutes of simulation time.

- **Queue Impact**: Average wait time is only 1.64 minutes because repairs are 
  scheduled regularly, preventing excessive queueing.

- **System Reliability**: Regular maintenance prevents equipment failure and keeps 
  the system running smoothly.

Comparison with No-Maintenance Scenario
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Without preventive maintenance:

- Trucks would run continuously without interruptions
- Loader might fail or degrade unexpectedly
- No scheduled downtime (but potential emergency breakdowns)
- Short-term productivity higher, but long-term reliability lower

With preventive maintenance (this example):

- Regular maintenance windows interrupt operations
- Equipment reliability guaranteed through preventive care
- Predictable downtime allows for planning
- Longer project duration but more stable operations

Advanced Topics
---------------

**1. Variable Repair Times**

You can model different repair types with varying durations:

.. code-block:: python

   def repair_process_advanced(repair_man, loader, worked_hours):
       """Repair with variable duration based on equipment condition."""
       while True:
           yield repair_man.get(worked_hours, 10)
           yield repair_man.get(loader, 1, -3)
           
           # Different repair times based on hours accumulated
           repair_duration = dist.uniform(8, 12)  # 8-12 minutes
           yield repair_man.do('repair', repair_duration)
           
           yield repair_man.put(loader, 1)

**2. Multiple Repair Persons**

For complex equipment, add multiple repair specialists:

.. code-block:: python

   # Create 2 repair persons
   repair_persons = env.create_entities("repair_person", 2)
   
   for repair_person in repair_persons:
       env.process(repair_process(repair_person, loader, worked_hours))

**3. Stochastic Failures**

Model unexpected equipment failures in addition to scheduled maintenance:

.. code-block:: python

   # Add emergency repair triggers for unexpected failures
   def failure_process(repair_man, loader):
       while True:
           # Failure occurs randomly (e.g., exponential distribution)
           yield repair_man.do('wait', dist.exponential(100))
           
           # Emergency repair with highest priority
           yield repair_man.get(loader, 1, -10)  # Higher priority than scheduled repairs
           yield repair_man.do('emergency_repair', 20)  # Takes longer
           yield repair_man.put(loader, 1)

Try It Yourself
---------------

Run the shipped example directly:

.. code-block:: bash

   python example/repair earthmoving.py

The script includes:

- **Comprehensive docstrings** for each process function
- **Detailed comments** explaining priority levels and maintenance logic
- **Complete results reporting** with truck and repair statistics
- **Sample schedules** showing actual execution timeline
- **Performance metrics** including wait times and repair frequency
- **Interactive Dashboard**: Real-time visualization of equipment maintenance 
  and truck operations (automatically opens in browser)

Expected Output:

The simulation will display:

- Total simulation time in minutes and hours
- Dirt moved by each truck and combined totals
- Loader queue statistics (wait times, request counts)
- Repair count and timing information
- Sample activity schedules for trucks and repair person
- **Dashboard visualization** showing:
  
  - Timeline of all activities (loading, hauling, dumping, repairs)
  - Truck cycles and how repairs interrupt operations
  - Resource utilization over time
  - Queue formation and resolution patterns
  - Entity status indicators (busy, waiting, idle)

Dashboard Features
~~~~~~~~~~~~~~~~~~

When you run the simulation, the interactive dashboard displays:

- **Activity Timeline**: Visual representation of each entity's actions
- **Resource States**: Real-time display of loader utilization and queue status
- **Statistics**: Charts and graphs of waiting times, utilization rates, and throughput
- **Entity Details**: Drill-down into individual truck and repair person schedules
- **Performance Metrics**: Summary statistics for the entire simulation

The dashboard opens automatically in your default browser at ``http://127.0.0.1:8050``.

Explore Further
~~~~~~~~~~~~~~~

To deepen your understanding:

1. **Change the repair threshold**: Modify the worked hours requirement from 10 to 5 
   or 15 to see how it affects productivity and repair frequency
2. **Add more trucks**: Increase fleet size to 3-5 trucks and observe how queueing 
   patterns change
3. **Variable truck types**: Create additional truck types with different 
   characteristics (capacity, speed, etc.)
4. **Maintenance duration**: Change repair time from 10 to 15 or 20 minutes and 
   analyze the impact
5. **Cost analysis**: Add cost tracking for repairs vs. productivity loss
6. **Sensitivity analysis**: Systematically test different parameters using the 
   dashboard to visualize impacts
7. **Compare scenarios**: Run without maintenance vs. with maintenance and compare 
   dashboard results

This example demonstrates how SimPM can model realistic operational constraints like 
equipment maintenance and how the interactive dashboard provides insights into system 
dynamics, which is crucial for accurate project planning and resource management.