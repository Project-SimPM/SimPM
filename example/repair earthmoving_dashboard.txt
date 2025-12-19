"""
Earthmoving Operation with Equipment Repair Simulation

This simulation models an earthmoving project with equipment maintenance:
- 2 trucks (small and large) that load, haul, and dump dirt
- 1 loader shared between both trucks
- 1 repair person who services the loader based on usage hours
- Goal: Analyze impact of maintenance on project productivity

SYSTEM DESCRIPTION:
    Small Truck:
        - Loading time: 4-5 minutes (uniform distribution)
        - Hauling time: 10-14 minutes
        - Dumping time: 4 minutes
        - Capacity: 80 units
    
    Large Truck:
        - Loading time: 4-7 minutes (uniform distribution)
        - Hauling time: 12-16 minutes
        - Dumping time: 5 minutes
        - Capacity: 100 units
    
    Repair System:
        - Repair person monitors worked hours on loader
        - When loader reaches 10 worked hours, repair is triggered
        - Repair takes 10 minutes and takes priority over loading
        - Uses PriorityResource for loader to handle repair priorities

ANALYSIS PERFORMED:
    - Total simulation time to complete all operations
    - Loader utilization with repairs
    - Truck waiting times and idle periods
    - Number of repairs performed
    - Total dirt moved before repairs become necessary

@author: Naima Sadeghi
@version: 2.0
@date: December 2025
"""
import os
import sys
import inspect
import random
import numpy as np

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 

import simpm
import simpm.des as d
import simpm.dist as dist

# =============================================================================
# RANDOM SEED FOR REPRODUCIBILITY
# =============================================================================
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

print(f"Simulation initialized with random seed: {RANDOM_SEED}\n")


# =============================================================================
# PROCESS FUNCTIONS
# =============================================================================

def truck_process(truck, loader, dumped_dirt, worked_hours):
    """
    Truck operation cycle process.
    
    Simulates the complete cycle of a truck in the earthmoving operation:
    - Wait for loader availability
    - Get loaded with dirt
    - Haul to dump site
    - Dump the load
    - Return to pit for next load
    
    The truck attributes (loadingDur, haulingDur, capacity, etc.) are set
    on the entity and define truck-specific parameters.
    
    Args:
        truck (des.Entity): The truck entity with custom attributes
        loader (des.Resource): Loader resource (shared, capacity = 1)
        dumped_dirt (des.Resource): Counter for total dumped dirt
        worked_hours (des.Resource): Tracks cumulative loader working hours
    
    Yields:
        Simulation events: Loading, hauling, dumping, and return operations
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
    
    Args:
        repair_man (des.Entity): The repair person entity
        loader (des.Resource): Loader resource to repair
        worked_hours (des.Resource): Tracks cumulative loader working hours
    
    Yields:
        Simulation events: Waiting for repair trigger and repair work
    """
    while True:
        # Wait until 10 hours of work have been accumulated on the loader
        # This triggers the need for maintenance
        yield repair_man.get(worked_hours, 10)
        
        # Get the loader with HIGH PRIORITY (-3) to interrupt trucks
        # Negative priority ensures repair takes precedence over normal loading (priority=2)
        yield repair_man.get(loader, 1, -3)
        
        # Perform the repair (10 minutes)
        yield repair_man.do('repair', 10)
        
        # Release the loader back to trucks
        yield repair_man.put(loader, 1)


# =============================================================================
# ENVIRONMENT SETUP
# =============================================================================

# Create the discrete event simulation environment
env = d.Environment()

# Create the PRIORITY LOADER resource
# PriorityResource allows requests with different priorities
# Higher priority (more negative numbers) are served first
loader = d.PriorityResource(env, 'loader', init=1, print_actions=False)

# Create counter for total dumped dirt
dumped_dirt = d.Resource(env, 'dirt', init=0, capacity=2000, print_actions=False)

# Create counter for loader working hours (triggers repairs when hits 10)
worked_hours = d.Resource(env, 'worked_hours', init=0, capacity=2000, print_actions=False)

# Create small truck entity with specific parameters
small_truck = d.Entity(env, 'small_truck', print_actions=False)
small_truck.loading_dur = dist.uniform(4, 5)      # 4-5 minutes
small_truck.hauling_dur = dist.uniform(10, 14)    # 10-14 minutes
small_truck.dumping_dur = 4                         # 4 minutes (constant)
small_truck.capacity = 80                           # 80 units per load

# Create large truck entity with specific parameters
large_truck = d.Entity(env, 'large_truck', print_actions=False)
large_truck.loading_dur = dist.uniform(4, 7)      # 4-7 minutes (longer than small)
large_truck.hauling_dur = dist.uniform(12, 16)    # 12-16 minutes
large_truck.dumping_dur = 5                        # 5 minutes (constant)
large_truck.capacity = 100                         # 100 units per load (larger)

# Create repair person entity
repair_man = d.Entity(env, 'repair_person', print_actions=False)


# =============================================================================
# PROCESS INSTANTIATION
# =============================================================================

# Start truck processes for both small and large trucks
env.process(truck_process(small_truck, loader, dumped_dirt, worked_hours))
env.process(truck_process(large_truck, loader, dumped_dirt, worked_hours))

# Start repair process
env.process(repair_process(repair_man, loader, worked_hours))


# =============================================================================
# RUN SIMULATION
# =============================================================================

# Run the simulation with dashboard to visualize results
simpm.run(env, dashboard=True)
