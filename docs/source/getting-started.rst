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

This minimal model represents a single project activity that requires one crew. The activity waits until the crew is available, performs the work, and then releases the resource. The SimPM engine models activities with ``do`` (time spent working) and ``get`` / ``put`` (queueing for and releasing resources), rather than raw ``timeout`` calls.

This example shows how to:

* Create a :class:`simpm.des.Environment`.
* Define a simple :class:`simpm.des.Resource`.
* Model work with :class:`simpm.des.Entity` using ``get`` / ``do`` / ``put``.
* Run the simulation and inspect basic outputs.

.. code-block:: python

    import simpm
    from simpm.des import Environment, Resource, Entity
    from simpm.dist import norm

    # 1) Create the simulation environment
    env = Environment("Single activity")

    # 2) Define resources (e.g., one crew)
    crew = Resource(env, name="Crew", capacity=1)

    # 3) Create an entity to perform the activity
    activity = Entity(env, "Activity", print_actions=False, log=True)

    # 4) Define the activity process
    def activity_process(entity, resource):
        # Request one unit of the crew resource and wait until it is available
        yield entity.get(resource, 1)

        # Perform the work (duration drawn from a normal distribution)
        # Note: Entity.do accepts either a numeric duration or a simpm.dist distribution.
        yield entity.do("work", norm(10, 2))

        # Release the crew
        yield entity.put(resource, 1)

        print(f"{entity.env.now:.2f}: {entity} finished.")

    env.process(activity_process(activity, crew))

    # 5) Run the simulation
    simpm.run(env)

    print(f"Project finished at t={env.now:.2f}")
    print(activity.schedule())


Next steps
----------

* Read :doc:`concepts/project-modeling` to understand how activities, resources,
  and distributions fit together.

* Try the full tutorial at :doc:`tutorials/index`.
* Check out the API reference at :doc:`api_reference/index`.