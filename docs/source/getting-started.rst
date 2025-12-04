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
The activity waits until the crew is available, works for a random duration, and then finishes.
This example shows how to:

- Create a :class:`simpm.des.Environment`
- Define a simple :class:`simpm.des.Resource`
- Run the simulation
- Inspect basic outputs (duration and finish time)

.. code-block:: python

   from simpm.des import Environment, Resource
   from simpm.dist import norm

   # 1) Create the simulation environment
   env = Environment()

   # 2) Define resources (e.g., one crew)
   crew = Resource(env, capacity=1, name="Crew 1")

   # 3) Define an activity process
   def activity(env, resource, name):
       # Request one unit of the crew resource and wait until it is available
       yield resource.request()

       # Perform the work
       duration = norm(10, 2).sample()
       yield env.timeout(duration)

       print(f"{env.now:.2f}: {name} finished (duration={duration:.2f})")

   # 4) Create entities / activities
   env.process(activity(env, crew, "Activity A"))

   # 5) Run the simulation
   env.run()

   print(f"Project finished at t={env.now:.2f}")

Next steps
----------

* Read :doc:`concepts/project-modeling` to understand how
  activities, resources, and distributions fit together.
* Try the first full tutorial at :doc:`tutorials/hello-simpm`.
