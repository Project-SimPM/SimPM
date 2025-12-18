01 – Hello SimPM: first project simulation
==========================================

.. contents:: On this page
   :local:

Overview
--------

The objective here is to build a minimal project simulation using SimPM's discrete-event engine.
This walkthrough mirrors the runnable example in ``example/test_simple_earthmoving.py``
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

.. code-block:: python

   import simpm
   import simpm.des as des

   def truck_cycle(truck: des.Entity, loader: des.Resource, dumped_dirt: des.Resource):
       while True:
           # Queue for the loader, then load 60 units of dirt
           yield truck.get(loader, 1)
           yield truck.do("loading", 7)
           yield truck.put(loader, 1)

           # Haul to the dump site
           yield truck.do("hauling", 17)
           yield truck.do("dumping", 3)
           yield truck.add(dumped_dirt, 60)

           # Return to the pit
           yield truck.do("return", 13)

   env = des.Environment("Earthmoving")
   loader = des.Resource(env, "loader", init=1, capacity=1, log=True)
   dumped_dirt = des.Resource(env, "dirt", init=0, capacity=100000, log=True)

   trucks = env.create_entities("truck", 10, print_actions=False, log=True)
   for t in trucks:
       env.process(truck_cycle(t, loader, dumped_dirt))

   simpm.run(env, dashboard=True)

   print(f"Project finished at t={env.now:.2f} minutes")
   print("Loader utilization:", loader.average_utilization())
   print("Loader queue stats:\n", loader.waiting_time().describe())
   print("Truck 0 schedule sample:\n", trucks[0].schedule().head())

How it works
------------

1. **Environment and resources** – :class:`simpm.des.Environment` keeps
   simulation time. :class:`simpm.des.Resource` tracks capacity and queue
   behavior (``log=True`` records status changes for later analysis).
2. **Entities** – :meth:`simpm.des.Environment.create_entities` produces
   :class:`simpm.des.Entity` objects. ``get`` and ``put`` wrap resource
   requests; ``do`` performs time-consuming activities; ``add`` deposits
   output into an inventory-like resource.
3. **Processes** – ``env.process`` schedules ``truck_cycle`` for each truck;
   ``simpm.run`` executes until no future events remain (showing the
   post-run dashboard if available).
4. **Outputs** – ``status_log()``, ``waiting_time()``, and
   ``average_utilization()`` expose queueing and productivity insights,
   while ``schedule()`` reports per-entity activity timing.

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

   python example/test_simple_earthmoving.py

Then open the generated logs to see which trucks waited longest and
how hard the loader was pushed.
