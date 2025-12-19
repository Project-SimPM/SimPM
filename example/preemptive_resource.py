"""
Preemptive Resource Example – Demonstration of Resource Preemption

This example demonstrates SimPM's PreemptiveResource class, which allows
higher-priority entities to interrupt lower-priority entities that are
currently using the resource.

Key Concepts:
- PreemptiveResource: A resource that can interrupt lower-priority users
- Preemption: A high-priority request interrupts a low-priority user's work
- Priority Values: Higher (less negative) values = higher priority
- Use Cases: Emergency repairs interrupting regular work, critical tasks
  preempting standard operations

In this example:
- Entity e1 starts using the resource with low-priority work (10 time units)
- Entity e2 waits 5 time units, then requests the resource with higher priority
  and preempt=True, interrupting e1's work
- e1's work is interrupted mid-way
- e2 completes its work
- e1 resumes or restarts

Expected Behavior:
At t=5, when e2 requests with preempt=True, e1's ongoing work should be interrupted
and e2 should take control of the resource.

@author: naimeh Sadeghi
"""
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 
import simpm
from simpm.des import *

# ============================================================================
# Process Functions – Define entity behavior
# ============================================================================

def p1(a: Entity, R):
    """
    Entity e1 process: performs work with preemptible operations.
    
    This entity starts using the resource for 10 time units of work.
    If interrupted by a higher-priority entity, the work is interrupted
    (not completed), and the resource is released.
    
    Parameters:
    - a: The entity (e1)
    - R: The PreemptiveResource being used
    """
    # Request the resource (with default priority)
    print(f'{a.env.now:.2f}: {a.name} requests the resource to do work')
    yield a.get(R, 1, False)
    
    # Perform work that can be interrupted
    print(f'{a.env.now:.2f}: {a.name} starts work (interruptible operation, 10 time units)')
    try:
        # Use interruptive_do for work that can be preempted
        yield a.interruptive_do('something', 10)
        print(f'{a.env.now:.2f}: {a.name} completed work successfully')
    except simpm.des.Interrupt:
        # Work was interrupted by a higher-priority entity
        print(f'{a.env.now:.2f}: {a.name} work was INTERRUPTED by higher priority entity!')
    
    # Release the resource
    print(f'{a.env.now:.2f}: {a.name} releases the resource')
    yield a.put(R)

def p2(b: Entity, R):
    """
    Entity e2 process: performs lower-priority work, then interrupts e1 with
    higher-priority work.
    
    This entity demonstrates preemption: it starts work at low priority,
    then uses preempt=True to interrupt the current user (e1) and take
    control of the resource.
    
    Parameters:
    - b: The entity (e2)
    - R: The PreemptiveResource being used
    """
    # First, perform some independent work (doesn't use the resource)
    print(f'{b.env.now:.2f}: {b.name} performs preliminary work (5 time units)')
    yield b.do('b_act', 5)
    
    # Now request the resource with preemption capability
    print(f'{b.env.now:.2f}: {b.name} requests resource with PREEMPTION (higher priority)')
    r = b.get(R, 1, priority=-1, preempt=True)  # Higher priority with preempt=True
    yield r
    
    print(f'{b.env.now:.2f}: {b.name} got the resource (interrupted e1)')
    
    # Perform work with the preempted resource
    print(f'{b.env.now:.2f}: {b.name} performs critical work (5 time units)')
    yield b.do('b_act2', 5)
    
    # Release the resource when done
    print(f'{b.env.now:.2f}: {b.name} releases the resource')
    yield b.put(R)

# ============================================================================
# Main Simulation Setup
# ============================================================================

# Create simulation environment
env = Environment()

# Create entities
e1 = Entity(env, 'e1', print_actions=True, log=True)  # Low-priority worker
e2 = Entity(env, 'e2', print_actions=True, log=True)  # High-priority interrupting worker

# Create a PreemptiveResource that allows interruption of lower-priority users
# - name: 'Truck'
# - print_actions: True (print all get/put operations)
R = PreemptiveResource(env, 'Truck', print_actions=True, log=True)

# Start both processes
env.process(p1(e1, R))  # e1 starts using resource immediately
env.process(p2(e2, R))  # e2 waits 5 time units, then preempts e1

# ============================================================================
# Run Simulation and View Results
# ============================================================================

# Run simulation with optional dashboard
simpm.run(env, dashboard=True)

# ============================================================================
# Key Observations
# ============================================================================
#
# 1. At t=0, e1 requests the resource and starts work (10 time units planned)
#
# 2. At t=5, e2 makes a request with preempt=True
#    This should interrupt e1's ongoing work at t=5
#
# 3. e1's 10-time-unit work is cut short; it was only at t=5 when interrupted
#
# 4. e2 takes over the resource and completes 5 time units of work
#    (from t=5 to t=10)
#
# 5. At t=10, e2 releases the resource
#    e1 could resume work if it had more to do
#
# Real-world applications:
# - Emergency repairs interrupting regular maintenance
# - Urgent patient care interrupting routine procedures
# - Critical system failures interrupting standard operations
# - VIP work preempting regular work
#
