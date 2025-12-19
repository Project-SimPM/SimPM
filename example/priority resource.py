"""
Priority Resource Example – Demonstration of Resource Request Prioritization

This example demonstrates SimPM's PriorityResource class, which allows entities
to request resources with different priority levels. Higher priority requests
are served first, regardless of arrival order.

Key Concepts:
- PriorityResource: A resource where requests are served based on priority values
- Priority Values: Higher (less negative) values = higher priority
  * priority=1: Low priority
  * priority=2: Medium priority  
  * priority=-3: Very high priority (negative = higher priority than positive)
- Use Cases: Emergency repairs, VIP tasks, preemptive maintenance

In this example:
- Entity e1 requests 3 units at priority 1 (low)
- Entity e2 requests 2 units at priority 2 (medium)
- Entity e3 requests 2 units at priority -3 (very high, arrives later but served first)
- Entity er (provider) periodically adds units back to the resource

Expected Behavior:
Entity e3 should be served first despite arriving last, because priority=-3 > priority=2 > priority=1

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

def p1(env, a, R):
    """
    Entity e1 process: requests 3 units at priority 1 (low priority).
    
    This entity arrives first and requests immediately, but will wait
    because higher priority entities arrive later.
    """
    print(f'{env.now:.2f}: {a.name} wants to get 3 units at priority 1')
    yield a.get(R, 3, priority=1)  # Request 3 units at priority 1
    print(f'{env.now:.2f}: {a.name} got 3 units (waited due to lower priority)')

def p2(env, b, R):
    """
    Entity e2 process: requests 2 units at priority 2 (medium priority).
    
    This entity arrives second with medium priority. It will be served after
    e3 (which has higher priority) but before e1.
    """
    print(f'{env.now:.2f}: {b.name} wants to get 2 units at priority 2')
    yield b.get(R, 2, priority=2)  # Request 2 units at priority 2
    print(f'{env.now:.2f}: {b.name} got 2 units (served after e3)')

def p3(env, b, R):
    """
    Entity e3 process: waits 1 time unit, then requests 2 units at 
    priority -3 (very high priority).
    
    This entity arrives later than e1 and e2, but has the highest priority.
    It should be served first, demonstrating priority-based scheduling.
    
    Note: Negative priority values indicate higher priority than positive values.
    """
    yield b.do('wait', 1)  # Wait 1 time unit before requesting
    print(f'{env.now:.2f}: {b.name} wants to get 2 units at priority -3 (HIGHEST)')
    yield b.get(R, 2, priority=-3)  # Request 2 units at very high priority
    print(f'{env.now:.2f}: {b.name} got 2 units (served FIRST despite arriving later)')

def pr(env, d, R):
    """
    Provider process: entity er periodically adds units back to the resource.
    
    This simulates a resource provider that replenishes the resource over time,
    allowing waiting entities to eventually get served.
    
    Timeline:
    - Wait 3 time units, then add 3 units
    - Wait 3 more time units, then add 2 units
    - Wait 2 more time units, then add 3 units
    """
    yield d.do('wait', 3)  # Wait 3 time units
    print(f'{env.now:.2f}: {d.name} adds 3 units to resource')
    yield d.add(R, 3)  # Add 3 units to the resource
    
    yield d.do('wait', 3)  # Wait 3 more time units
    print(f'{env.now:.2f}: {d.name} adds 2 units to resource')
    yield d.add(R, 2)  # Add 2 units
    
    yield d.do('wait', 2)  # Wait 2 more time units
    print(f'{env.now:.2f}: {d.name} adds 3 units to resource')
    yield d.add(R, 3)  # Add 3 units
    
# ============================================================================
# Main Simulation Setup
# ============================================================================

# Create simulation environment
env = Environment()

# Create entities (resource requesters and provider)
e1 = Entity(env, 'e1', log=True)  # Low priority requester
e2 = Entity(env, 'e2', log=True)  # Medium priority requester
e3 = Entity(env, 'e3', log=True)  # High priority requester
er = Entity(env, 'er', log=True)  # Resource provider

# Create a PriorityResource with:
#   - name: 'Truck'
#   - init: 0 (starts empty)
#   - capacity: 3 (maximum 3 units)
#   - print_actions: True (print all get/put/add actions)
R = PriorityResource(env, 'Truck', init=0, capacity=3, print_actions=True, log=True)

# Start all processes
env.process(p1(env, e1, R))  # e1 requests with priority 1
env.process(p2(env, e2, R))  # e2 requests with priority 2
env.process(pr(env, er, R))  # er adds units periodically (starts immediately)
env.process(p3(env, e3, R))  # e3 requests with priority -3 (starts at t=1)

# ============================================================================
# Run Simulation and View Results
# ============================================================================

# Run simulation with optional dashboard
simpm.run(env, dashboard=True)

# ============================================================================
# Key Observations
# ============================================================================
# 
# 1. Despite e3 arriving last (at t=1), it should get served first because
#    of its higher priority value (-3 > 2 > 1).
#
# 2. The order of service should be: e3, then e2, then e1 (based on priority,
#    not arrival order).
#
# 3. This demonstrates that PriorityResource is useful for:
#    - Emergency tasks that need to jump the queue
#    - Maintenance work that has higher priority than regular operations
#    - VIP work that needs priority over standard work
#
env=Environment()
e1=Entity(env,'e1')
e2=Entity(env,'e2')
e3=Entity(env,'e3')
er=Entity(env,'er')
R=PriorityResource(env,'Truck',init=0,capacity=3,print_actions=True)
env.process(p1(env,e1,R))
env.process(p2(env,e2,R))
env.process(pr(env,er,R))
env.process(p3(env,e3,R))

simpm.run(env, dashboard=True)
