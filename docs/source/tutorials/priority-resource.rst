Priority-Based Resource Scheduling
===================================

.. contents:: On this page
   :local:

Overview
--------

In real-world project management, not all requests for resources are equal. Emergency repairs,
critical work, and VIP tasks often need priority over routine operations. SimPM's 
:class:`~simpm.des.PriorityResource` allows entities to request resources with different
priority levels, ensuring that higher-priority work gets served first—regardless of arrival order.

This tutorial explores priority-based resource scheduling, showing you how to model scenarios
where work importance matters as much as work timing.

Key Concepts
~~~~~~~~~~~~

**Priority Resource**
  A :class:`~simpm.des.PriorityResource` uses priority values to order requests in the queue.
  Higher priority requests are served before lower priority ones, even if they arrived later.

**Priority Values**
  - Positive values (1, 2, 3...): Standard priority; lower numbers = higher priority
  - Negative values (-1, -2, -3...): Higher priority; more negative = higher priority
  - Example: priority=-3 > priority=2 > priority=1

**Service Order**
  When multiple entities request a resource, SimPM serves them in order of their priority values,
  not their arrival order. Once served, entities hold the resource until they release it.

Use Cases
~~~~~~~~~

Priority-based resources are essential for:

- **Emergency repairs** – Broken equipment gets fixed before routine maintenance
- **Maintenance scheduling** – Critical maintenance preempts regular work
- **Hospital operations** – Emergency patients served before routine appointments
- **Construction site management** – Safety issues get immediate crew attention
- **IT operations** – Critical system failures get immediate technician response

Scenario: Equipment Supply Queue
---------------------------------

Imagine a construction site with a limited equipment depot supplying trucks:

- **Depot capacity**: 3 trucks available
- **Three contractors** requesting trucks:

  - Contractor A (regular work): priority=1, needs 3 trucks
  - Contractor B (important project): priority=2, needs 2 trucks
  - Contractor C (urgent repair): priority=-3 (very high), needs 2 trucks, arrives late

- **Depot operator**: Periodically releases trucks back to the depot (adds supply)

The question: In what order do contractors get served?

Answer: By priority! Contractor C (highest priority) gets trucks first, despite arriving last.

Detailed Code Example
---------------------

Here's the complete priority resource example with step-by-step explanation:

.. code-block:: python

    import simpm
    from simpm.des import *

    # ========================================
    # 1. Define Process Functions
    # ========================================

    def contractor_a_process(env, entity, resource):
        """
        Contractor A: Regular work at priority 1 (low).
        Requests 3 trucks; will wait due to lower priority.
        """
        print(f'{env.now:.2f}: {entity.name} requests 3 trucks (priority 1)')
        yield entity.get(resource, 3, priority=1)
        print(f'{env.now:.2f}: {entity.name} got 3 trucks')

    def contractor_b_process(env, entity, resource):
        """
        Contractor B: Important project at priority 2 (medium).
        Requests 2 trucks; served after high-priority work.
        """
        print(f'{env.now:.2f}: {entity.name} requests 2 trucks (priority 2)')
        yield entity.get(resource, 2, priority=2)
        print(f'{env.now:.2f}: {entity.name} got 2 trucks')

    def contractor_c_process(env, entity, resource):
        """
        Contractor C: Urgent repair at priority -3 (highest).
        Waits 1 time unit, then requests; gets trucks FIRST due to high priority.
        """
        yield entity.do('wait', 1)
        print(f'{env.now:.2f}: {entity.name} requests 2 trucks (priority -3 - URGENT)')
        yield entity.get(resource, 2, priority=-3)
        print(f'{env.now:.2f}: {entity.name} got 2 trucks (SERVED FIRST)')

    def depot_operator_process(env, operator, resource):
        """
        Depot Operator: Periodically releases trucks back to inventory.
        
        Schedule:
        - t=3: Return 3 trucks
        - t=6: Return 2 trucks
        - t=8: Return 3 trucks
        """
        yield operator.do('wait', 3)
        print(f'{env.now:.2f}: Depot returns 3 trucks')
        yield operator.add(resource, 3)
        
        yield operator.do('wait', 3)
        print(f'{env.now:.2f}: Depot returns 2 trucks')
        yield operator.add(resource, 2)
        
        yield operator.do('wait', 2)
        print(f'{env.now:.2f}: Depot returns 3 trucks')
        yield operator.add(resource, 3)

    # ========================================
    # 2. Set Up Simulation
    # ========================================

    env = Environment()

    # Create entities (contractors and operator)
    contractor_a = Entity(env, 'Contractor_A', log=True)
    contractor_b = Entity(env, 'Contractor_B', log=True)
    contractor_c = Entity(env, 'Contractor_C', log=True)
    operator = Entity(env, 'Depot_Operator', log=True)

    # Create PriorityResource (depot with limited trucks)
    depot = PriorityResource(
        env, 
        'Truck_Depot', 
        init=0,              # Start empty (no trucks)
        capacity=3,          # Maximum 3 trucks
        print_actions=True,  # Print all get/add operations
        log=True             # Log all events
    )

    # ========================================
    # 3. Start Processes
    # ========================================

    env.process(contractor_a_process(env, contractor_a, depot))
    env.process(contractor_b_process(env, contractor_b, depot))
    env.process(operator_process(env, operator, depot))
    env.process(contractor_c_process(env, contractor_c, depot))

    # ========================================
    # 4. Run Simulation
    # ========================================

    simpm.run(env, dashboard=True)

How It Works
~~~~~~~~~~~~

**Timeline of Events:**

.. code-block:: text

    t=0.00: Contractor_A requests 3 trucks (priority 1)
            → Waits (depot empty)
            
    t=0.00: Contractor_B requests 2 trucks (priority 2)
            → Waits (depot empty, lower priority than C)
            
    t=0.00: Depot_Operator starts work
            → Will return trucks at t=3, t=6, t=8
            
    t=1.00: Contractor_C requests 2 trucks (priority -3 - HIGHEST)
            → Waits (depot empty, but is now first in queue)
            
    t=3.00: Depot returns 3 trucks
            → Contractor_C gets 2 trucks FIRST (priority -3)
            → 1 truck remains in depot
            
    t=6.00: Depot returns 2 trucks
            → 3 trucks now available
            → Contractor_B gets 2 trucks (priority 2)
            → 1 truck remains
            
    t=8.00: Depot returns 3 trucks
            → 4 trucks available
            → Contractor_A gets 3 trucks (priority 1)
            → 1 truck remains

**Key Observations:**

1. **Priority overrides arrival order**: Contractor C arrives at t=1, but gets trucks at t=3
   when they become available, because priority=-3 > priority=2 > priority=1.

2. **Queue management**: The resource automatically maintains a priority queue and serves
   highest-priority requests first when capacity becomes available.

3. **Waiting times**: 
   - Contractor A: Arrives t=0, served t=8 (waits 8 time units)
   - Contractor B: Arrives t=0, served t=6 (waits 6 time units)
   - Contractor C: Arrives t=1, served t=3 (waits only 2 time units, thanks to high priority!)

Advanced Topics
----------------

**Multiple Priority Levels**

You can use any integer priority value. For example, in a hospital:

.. code-block:: python

    routine_checkup = Priority(priority=10)      # Low priority
    important_surgery = priority(priority=0)     # Medium priority
    emergency_trauma = priority(priority=-100)   # Very high priority

**Combining with Other Resource Types**

Priority resources work alongside regular resources:

.. code-block:: python

    # Regular resource (FIFO queue)
    general_crew = Resource(env, 'General_Crew', capacity=2)
    
    # Priority resource (ordered by priority value)
    emergency_crew = PriorityResource(env, 'Emergency_Crew', capacity=1)

    # Entity requests both
    yield entity.get(general_crew, 1)      # Gets in line, first come first served
    yield entity.get(emergency_crew, 1)    # Gets in line by priority

**Dynamic Priority Changes**

Priorities can be adjusted during simulation based on conditions:

.. code-block:: python

    # Initial request at low priority
    yield entity.get(resource, 1, priority=10)
    
    # If conditions change, higher-priority request can interrupt (see PreemptiveResource)
    yield entity.get(resource, 1, priority=-10, preempt=True)

Try It Yourself
---------------

**Experiment 1: Change Priority Values**

What happens if you change Contractor C's priority from -3 to 3? Now it has the lowest
priority! Try it and observe the new service order.

**Experiment 2: Add More Contractors**

Add a fourth contractor with priority=0 (between B and C). How does this change the
service order?

**Experiment 3: Increase Depot Capacity**

Change ``capacity=3`` to ``capacity=5``. Do all contractors get served immediately when
trucks are available?

**Experiment 4: Use the Dashboard**

Enable the dashboard (default: ``dashboard=True``). Explore:
- Timeline view: See when each contractor gets trucks
- Queue view: See how the priority queue changes over time
- Resource utilization: How many trucks are in use at each time?

Next Steps
----------

* Learn about **preemptive resources** where high-priority work can interrupt 
  low-priority work: :doc:`preemptive-resource`

* Apply priority resources in real projects with :doc:`equipment-maintenance`

* Explore resource bottlenecks with :doc:`resource-bottlenecks`

* Check out the :doc:`../api_reference/simpm.des` reference for detailed API documentation
