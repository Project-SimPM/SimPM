03 – Resource bottlenecks and utilization
=========================================

.. contents:: On this page
   :local:

Overview
--------

Analyze how limited capacities affect throughput and schedule. This
example reuses ``example/test_priority_resource.py`` to show how queues
behave when multiple entities compete for scarce capacity and how
priority settings change the outcome.

Scenario
--------

Three work crews request the same truck fleet, but capacity is only
three units and the trucks arrive in batches. One crew waits with a
higher priority to demonstrate preemption of the queue order.

Simulation code (priority bottleneck)
-------------------------------------

.. code-block:: python

   import simpm
   from simpm.des import Entity, Environment, PriorityResource

   def crew_one(env, entity: Entity, trucks: PriorityResource):
       print("Crew 1 wants 3 trucks at:", env.now)
       yield entity.get(trucks, 3, priority=1)
       print("Crew 1 got 3 trucks at:", env.now)

   def crew_two(env, entity: Entity, trucks: PriorityResource):
       print("Crew 2 wants 2 trucks at:", env.now)
       yield entity.get(trucks, 2, priority=2)
       print("Crew 2 got 2 trucks at:", env.now)

   def crew_three(env, entity: Entity, trucks: PriorityResource):
       # Arrives later but with higher priority (negative is highest)
       yield entity.do("wait", 1)
       print("Crew 3 wants 2 trucks at:", env.now)
       yield entity.get(trucks, 2, priority=-3)
       print("Crew 3 got 2 trucks at:", env.now)

   def fleet_arrivals(env, entity: Entity, trucks: PriorityResource):
       # Trucks arrive gradually, freeing capacity
       yield entity.do("wait", 3)
       yield entity.add(trucks, 3)
       yield entity.do("wait", 3)
       yield entity.add(trucks, 2)
       yield entity.do("wait", 2)
       yield entity.add(trucks, 3)

   env = Environment()
   crew1 = Entity(env, "crew1")
   crew2 = Entity(env, "crew2")
   crew3 = Entity(env, "crew3")
   fleet = Entity(env, "fleet")
   trucks = PriorityResource(env, "Truck", init=0, capacity=3, print_actions=True)

   env.process(crew_one(env, crew1, trucks))
   env.process(crew_two(env, crew2, trucks))
   env.process(crew_three(env, crew3, trucks))
   env.process(fleet_arrivals(env, fleet, trucks))

   simpm.run(env, dashboard=True)

What to look for
----------------

* **Queue order** – Crew 3 jumps ahead because it requests trucks with a
  higher priority even though it arrives later.
* **Utilization** – ``PriorityResource`` logs show when the three
  available trucks are idle versus allocated. Inspect ``status_log`` if
  you need time-stamped detail.
* **Capacity sensitivity** – Increase ``capacity`` or the ``add`` amounts
  to see how quickly the queue clears; decrease them to stress-test the
  bottleneck.
* **Preemption vs. fairness** – Switching to :class:`simpm.des.Resource`
  (no priority) will force first-come-first-served behavior.

Where to go next
----------------

Refer to the :doc:`../concepts/project-modeling` guide for deeper
conceptual background or explore the :doc:`../api_reference/index`
for full API details. Run ``python example/test_priority_resource.py`` to
experiment with the original script.
