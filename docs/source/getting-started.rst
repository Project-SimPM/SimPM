Getting started with SimPM
==========================

.. contents:: On this page
   :local:

Installation
------------

Install SimPM from PyPI:

.. code-block:: bash

   pip install simpm

A minimal example
-----------------

This minimal model represents a single project activity that requires one crew.
The activity waits until the crew is available, performs the work, and then releases
the resource. The SimPM engine models activities with ``do`` (time spent working)
and ``get`` / ``put`` (queueing for and releasing resources), rather than raw
``timeout`` calls.

This example shows how to:

- Create a :class:`simpm.des.Environment`
- Define a simple :class:`simpm.des.Resource`
- Model work with :class:`simpm.des.Entity` using ``do`` and ``get``
- Create entities with :meth:`simpm.des.Environment.create_entities`
- Run the simulation and inspect basic outputs

.. code-block:: python

   import simpm
   from simpm.des import Environment, Resource
   from simpm.dist import norm

   # 1) Create the simulation environment
   env = Environment("Single activity")

   # 2) Define resources (e.g., one crew). ``capacity=1`` means only one
   # entity can use this crew at a time.
   crew = Resource(env, name="Crew 1", capacity=1)

   # 3) Create an entity to perform the activity. ``log=True`` stores detailed
   # action timing so you can inspect wait and idle durations after the run.
   # ``create_entities`` returns a list, so we grab the first created entity.
   entity1 = env.create_entities("Activity", 1, print_actions=False, log=True)[0]

   # 4) Define the activity process
   def activity(entity, resource):
       # Request one unit of the crew resource and wait until it is available
       yield entity.get(resource, 1)

       # Perform the work
       duration = norm(10, 2).sample()
       yield entity.do("work", duration)

       # Release the crew
       yield entity.put(resource, 1)

       print(f"{entity.env.now:.2f}: {entity} finished (duration={duration:.2f})")

   env.process(activity(entity1, crew))

   # 5) Run the simulation
   simpm.run(env)

   print(f"Project finished at t={env.now:.2f}")
   print(entity1.schedule())

   # Inspect how long the activity waited for the crew (idle/wait time)
   print("Waiting durations:", entity1.waiting_time())
   print("Waiting log:\n", entity1.waiting_log())

Next steps
----------

* Read :doc:`concepts/project-modeling` to understand how
  activities, resources, and distributions fit together.
* Try the first full tutorial at :doc:`tutorials/hello-simpm`.
