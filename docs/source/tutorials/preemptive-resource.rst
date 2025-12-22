Preemptive Resource Scheduling
===============================

.. contents:: On this page
   :local:

Overview
--------

Sometimes higher-priority work doesn't just need to wait in a queue—it needs to interrupt
lower-priority work that's already happening. SimPM's :class:`~simpm.des.PreemptiveResource`
allows high-priority entities to interrupt lower-priority users, making space for urgent tasks.

This tutorial explores preemptive scheduling, showing you how to model scenarios where
emergency work, critical failures, or VIP tasks can interrupt ongoing operations.

Key Concepts
~~~~~~~~~~~~

**Preemptive Resource**
  A :class:`~simpm.des.PreemptiveResource` allows a high-priority request to interrupt
  a lower-priority entity that is currently using the resource. The low-priority entity's
  work is interrupted (not completed), and the resource is taken over.

**Preemption vs. Priority**
  - **Priority Resource**: High-priority work waits in queue, gets served when resource
    becomes free (non-preemptive)
  - **Preemptive Resource**: High-priority work interrupts lower-priority work in progress
    (preemptive)

**Interruption**
  When an entity's work is interrupted, it receives an ``Interrupt`` event. The entity
  can catch this exception and handle it gracefully (save work, log failure, etc.).

Use Cases
~~~~~~~~~

Preemptive resources are essential for:

- **Emergency repairs** – Critical equipment failure stops routine maintenance immediately
- **Emergency services** – Critical patient overrides scheduled surgery
- **IT systems** – Critical security incident stops routine maintenance
- **Construction sites** – Safety hazard stops all work on site
- **Power systems** – Emergency load shedding stops non-critical operations

Scenario: Machine Maintenance with Emergency Repairs
-----------------------------------------------------

Imagine a manufacturing facility with a repair technician:

- **Regular maintenance**: Scheduled routine work (10 hours)
- **Emergency repair**: Unexpected machine breakdown (5 hours)
- **Technician**: Only one available; can switch to emergency work if needed

Normal scenario (without preemption):
  Routine work finishes (10 hours), then emergency happens, then we wait
  Result: Total time = 15 hours (sequential)

With preemption:
  Routine work is interrupted by emergency (at hour 5)
  Result: Total time = 10 hours (routine waits, emergency priority)

Detailed Code Example
---------------------

Here's the complete preemptive resource example:

.. code-block:: python

    import simpm
    from simpm.des import *

    # ========================================
    # 1. Define Process Functions
    # ========================================

    def routine_maintenance(entity, resource):
        """
        Regular maintenance: 10 time units of work that CAN be interrupted.
        
        This uses interruptive_do() so the work can be stopped by emergency tasks.
        """
        print(f'{entity.env.now:.2f}: {entity.name} requests technician for routine work')
        yield entity.get(resource, 1)
        
        print(f'{entity.env.now:.2f}: {entity.name} starts routine maintenance (10 hours)')
        try:
            # Use interruptive_do for work that can be interrupted
            yield entity.interruptive_do('routine_maintenance', 10)
            print(f'{entity.env.now:.2f}: {entity.name} completed routine maintenance')
        except simpm.des.Interrupt:
            # Maintenance was interrupted by emergency work
            print(f'{entity.env.now:.2f}: {entity.name} routine work INTERRUPTED by emergency!')
        
        print(f'{entity.env.now:.2f}: {entity.name} releases technician')
        yield entity.put(resource)

    def emergency_repair(entity, resource):
        """
        Emergency repair: High-priority work that can PREEMPT routine work.
        
        This waits 5 time units (allowing routine work to start),
        then requests the technician with preempt=True.
        """
        # Wait for routine work to start (5 time units)
        print(f'{entity.env.now:.2f}: {entity.name} waiting for problem to develop...')
        yield entity.do('wait', 5)
        
        print(f'{entity.env.now:.2f}: {entity.name} EMERGENCY! Requests technician (preempt=True)')
        # Request with preempt=True to interrupt the routine worker
        yield entity.get(resource, 1, priority=-1, preempt=True)
        
        print(f'{entity.env.now:.2f}: {entity.name} got technician (routine work interrupted)')
        
        # Do emergency repair
        print(f'{entity.env.now:.2f}: {entity.name} performs emergency repair (5 hours)')
        yield entity.do('emergency_repair', 5)
        
        print(f'{entity.env.now:.2f}: {entity.name} releases technician')
        yield entity.put(resource)

    # ========================================
    # 2. Set Up Simulation
    # ========================================

    env = Environment()

    # Create entities
    routine_worker = Entity(env, 'Routine_Worker', print_actions=True, log=True)
    emergency_worker = Entity(env, 'Emergency_Worker', print_actions=True, log=True)

    # Create PreemptiveResource (single technician)
    technician = PreemptiveResource(
        env, 
        'Technician', 
        print_actions=True,  # Print all get/put operations
        log=True             # Log all events
    )

    # ========================================
    # 3. Start Processes
    # ========================================

    env.process(routine_maintenance(routine_worker, technician))
    env.process(emergency_repair(emergency_worker, technician))

    # ========================================
    # 4. Run Simulation
    # ========================================

    simpm.run(env, dashboard=True)

How It Works
~~~~~~~~~~~~

**Timeline of Events:**

.. code-block:: text

    t=0.00: Routine_Worker requests technician
            → Gets technician immediately (no one else waiting)
            → Starts routine maintenance (planned duration: 10 hours)
            
    t=5.00: Emergency_Worker emergency occurs!
            → Requests technician with preempt=True
            → Routine_Worker's work is INTERRUPTED
            → Emergency_Worker takes technician
            
    t=5.00: Emergency_Worker starts emergency repair (5 hours)
            
    t=10.00: Emergency_Worker finishes repair
            → Releases technician
            → Routine_Worker could resume (if configured)

**Without Preemption (for comparison):**

.. code-block:: text

    t=0.00: Routine_Worker starts (10 hours)
    t=10.00: Routine_Worker finishes
    t=10.00: Emergency_Worker requests (waits)
    t=10.00: Emergency_Worker starts (5 hours)
    t=15.00: Emergency_Worker finishes
    
    Result: Routine work completes even though emergency happened!

**With Preemption (our example):**

.. code-block:: text

    t=0.00: Routine_Worker starts (10 hours)
    t=5.00: Emergency_Worker INTERRUPTS with preempt=True
    t=5.00: Emergency_Worker starts (5 hours)
    t=10.00: Emergency_Worker finishes
    
    Result: Emergency handled immediately; routine waits!

Handling Interruptions
~~~~~~~~~~~~~~~~~~~~~~

When a task is interrupted, you must handle the ``Interrupt`` exception:

.. code-block:: python

    def interruptible_work(entity, resource):
        yield entity.get(resource, 1)
        
        try:
            # This work can be interrupted
            yield entity.interruptive_do('work', duration=10)
            print(f"Work completed successfully")
            
        except simpm.des.Interrupt as interrupt:
            # Work was interrupted; do cleanup if needed
            print(f"Work was interrupted!")
            # Save partial results, log failure, notify others, etc.
        
        yield entity.put(resource)

**Important**: Use ``interruptive_do()`` (not regular ``do()``) for work that can be interrupted.
Regular ``do()`` cannot be interrupted.

Advanced Topics
----------------

**Multiple Priority Levels with Preemption**

You can combine priority values with preemption:

.. code-block:: python

    # Regular routine work
    yield entity.get(resource, 1, priority=10)
    
    # Important work (can interrupt priority 10 or higher)
    yield entity.get(resource, 1, priority=5, preempt=True)
    
    # Critical emergency (can interrupt everything)
    yield entity.get(resource, 1, priority=-10, preempt=True)

**Partial Completion vs. Restart**

When work is interrupted, you can decide whether to:

1. **Resume later** – Save state and restart where interrupted:
   
   .. code-block:: python
   
       remaining_time = 10
       try:
           yield entity.interruptive_do('work', remaining_time)
       except simpm.des.Interrupt:
           remaining_time -= entity.env.now  # Calculate remaining
           # Later: resume with remaining_time

2. **Abandon and restart** – Discard partial work and start over:
   
   .. code-block:: python
   
       try:
           yield entity.interruptive_do('work', 10)
       except simpm.des.Interrupt:
           print("Work abandoned; restarting later")
           # Later: start fresh

**Queue Management with Preemption**

Preemptive resources automatically manage queue order:

.. code-block:: python

    # Three entities waiting
    yield entity1.get(resource, 1, priority=1)    # Low priority
    yield entity2.get(resource, 1, priority=5)    # Medium priority
    yield entity3.get(resource, 1, priority=-10, preempt=True)  # Highest, can preempt

    # When resource frees up:
    # 1. entity3 (preemptive, highest priority)
    # 2. entity2 (priority 5)
    # 3. entity1 (priority 1)

Try It Yourself
---------------

**Experiment 1: Remove Preemption**

Change ``preempt=True`` to ``preempt=False`` in the emergency request.
Now the emergency must wait in the queue. How long does routine work take?

**Experiment 2: Change Emergency Timing**

Change ``yield entity.do('wait', 5)`` to different values (0, 2, 8, 10).
When does the emergency interrupt the routine work?

**Experiment 3: Multiple Emergencies**

Add a third entity (second emergency) that requests at t=6. 
What happens if two emergencies occur?

**Experiment 4: Track Work Completion**

Modify the code to track:
- How much routine work was completed before interruption? (0 out of 10 hours)
- How much routine work remains? (10 hours)
- What if routine work needs to restart (vs. resume)?

**Experiment 5: Use the Dashboard**

Enable the dashboard. Observe:
- Timeline: When does interruption occur?
- Queue: How do priority and preemption affect queue order?
- Entity schedules: When does each entity work? When interrupted?

Real-World Example: Equipment Repair with Preemption
-----------------------------------------------------

An earthmoving project demonstrates preemptive maintenance versus scheduled maintenance:

**Scenario:**

Construction site with:
- **2 trucks** (small 80-unit, large 100-unit capacity)
- **1 shared loader** (resource)
- **1 repair person** who maintains the loader

**Non-Preemptive (see repair_earthmoving.py):**

Loader uses ``PriorityResource``. Repairs wait in queue with high priority:

.. code-block:: python

    # Truck loading (priority=2)
    yield truck.get(loader, 1, priority=2)
    yield truck.do('load', 5)  # Finishes 5-minute load
    yield truck.put(loader, 1)
    
    # Repair (priority=-3, waits until truck done)
    yield repair_man.get(loader, 1, priority=-3)
    yield repair_man.do('repair', 10)  # Repair starts next

Result: Truck finishes 5-minute load, then repair takes over. 
Repair happens quickly but doesn't interrupt ongoing work.

**Preemptive (this example: repair_earthmoving_preemptive.py):**

Loader uses ``PreemptiveResource``. Repairs can interrupt truck loading:

.. code-block:: python

    # Truck loading (priority=2, CAN BE INTERRUPTED)
    yield truck.get(loader, 1, priority=2)
    try:
        yield truck.interruptive_do('load', 5)  # CAN BE INTERRUPTED mid-operation
        yield truck.add(worked_hours, 5)
    except simpm.des.Interrupt:
        print(f"Loading interrupted! Restart from scratch")
    
    yield truck.put(loader, 1)
    
    # Repair (priority=-3, WITH PREEMPTION)
    yield repair_man.get(loader, 1, priority=-3, preempt=True)
    yield repair_man.do('repair', 10)  # Repair starts IMMEDIATELY

Result: If truck is loading when repair is needed, truck is interrupted IMMEDIATELY.
Loading work is lost; truck must restart. Repair happens right away.

**Comparison:**

+------------------------+---------------------+--------------------+
| Aspect                 | Non-Preemptive      | Preemptive         |
+========================+=====================+====================+
| Resource Type          | PriorityResource    | PreemptiveResource |
+------------------------+---------------------+--------------------+
| Repair Timing          | Waits for next free | Interrupts now     |
+------------------------+---------------------+--------------------+
| Truck Work Loss        | None (work done)    | Yes (lost work)    |
+------------------------+---------------------+--------------------+
| Project Timeline       | Longer (repair wait)| Shorter (no wait)  |
+------------------------+---------------------+--------------------+
| Total Dirt Moved       | Same outcome        | Same outcome       |
+------------------------+---------------------+--------------------+
| Use Case               | Planned maintenance | Emergency repair   |
+------------------------+---------------------+--------------------+

**Actual Results** (Random Seed 42):

+---------------------------+---------------------+--------------------+
| Metric                    | Non-Preemptive      | Preemptive         |
+===========================+=====================+====================+
| Total Project Time        | 381.16 min (6.35h)  | 364.96 min (6.08h) |
+---------------------------+---------------------+--------------------+
| Total Dirt Dumped         | 1,960 units         | 1,960 units        |
+---------------------------+---------------------+--------------------+
| Small Truck Cycles        | 51 cycles           | 51 cycles          |
+---------------------------+---------------------+--------------------+
| Large Truck Cycles        | 43 cycles           | 43 cycles          |
+---------------------------+---------------------+--------------------+
| Total Loader Requests     | 34 requests         | 35 requests        |
+---------------------------+---------------------+--------------------+
| Avg Truck Wait Time       | 1.64 minutes        | 0.49 minutes       |
+---------------------------+---------------------+--------------------+
| Max Truck Wait Time       | 7.57 minutes        | 4.66 minutes       |
+---------------------------+---------------------+--------------------+
| Repairs Performed         | 10 repairs          | 11 repairs         |
+---------------------------+---------------------+--------------------+
| Avg Repair Interval       | ~38 minutes         | ~32 minutes        |
+---------------------------+---------------------+--------------------+
| Total Repair Time         | 100 minutes (4.4%)  | 110 minutes (5.0%) |
+---------------------------+---------------------+--------------------+

**Key Findings:**

1. **Preemption Reduces Wait**: Average truck wait time drops from 1.64 to 0.49 minutes
   because repairs preempt instead of queuing. Repairs don't queue behind trucks.

2. **More Frequent Repairs**: Preemptive version performed 11 repairs vs 10 in non-preemptive.
   Earlier first repair (10.57 min vs 33.36 min) shows preemption triggers sooner.

3. **Project Timeline**: Preemptive (364.96 min) is ~16 minutes FASTER than non-preemptive
   (381.16 min) despite doing more repairs. Preemption eliminates queue wait, saving time overall.

4. **Same Final Output**: Both versions moved identical 1,960 units despite different strategies.
   Preemption didn't reduce truck productivity; it just changed repair timing.

5. **Lower Congestion**: Max truck wait reduced from 7.57 to 4.66 minutes. Fewer trucks
   stuck waiting when repairs preempt instead of queuing.

**When to use each:**

- **Non-Preemptive (PriorityResource)**:
  - Scheduled maintenance (known time, planned)
  - High-priority work but not emergency
  - Completing current work is important
  
- **Preemptive (PreemptiveResource)**:
  - Emergency repairs (safety critical)
  - Cannot wait for current work to finish
  - Risk of disaster justifies lost work
  - Example: Equipment failure, safety shutdown

See the complete examples:
- ``example/repair_earthmoving.py`` (non-preemptive with PriorityResource)
- ``example/repair_earthmoving_preemptive.py`` (preemptive with PreemptiveResource)

Real-World Hospital Example
---------------------------

A hospital with one operating room (PreemptiveResource):

.. code-block:: python

    # Scheduled surgery (routine, 3 hours)
    yield patient1.get(operating_room, 1, priority=2)
    yield patient1.interruptive_do('surgery', 3)
    
    # Emergency trauma (arrives during surgery)
    yield patient2.do('wait', 1)  # Arrives 1 hour into surgery
    yield patient2.get(operating_room, 1, priority=-10, preempt=True)
    yield patient2.interruptive_do('emergency_surgery', 2)

Result: Scheduled patient's surgery is interrupted for the emergency.
The emergency is handled immediately, potentially saving a life!

Next Steps
----------

* Combine **priority** and **preemption** in :doc:`equipment-maintenance`

* Learn about **non-preemptive priority scheduling** with :doc:`priority-resource`

* Explore multiple resource scenarios with :doc:`resource-bottlenecks`

* Check out the :doc:`../api_reference/simpm.des` reference for detailed API documentation
