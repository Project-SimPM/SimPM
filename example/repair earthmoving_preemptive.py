"""
Earthmoving Operation with Preemptive Equipment Repair

This simulation models an earthmoving project with PREEMPTIVE equipment maintenance.
The key difference from PriorityResource: repairs can INTERRUPT ongoing truck loading!

COMPARISON:
    PriorityResource (see repair_earthmoving.py):
    - Repair waits in queue until truck finishes loading
    - Loader finishes 4-7 minutes of work, then repair takes over
    - High priority (priority=-3) ensures repair is next in queue
    
    PreemptiveResource (this example):
    - Repair can INTERRUPT truck loading immediately
    - Truck's loading work is interrupted mid-operation
    - Repair happens right away; truck must restart loading
    - Demonstrates true preemption for emergency maintenance

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
    
    Repair System (PREEMPTIVE):
        - Repair person monitors worked hours on loader
        - When loader reaches 10 worked hours, repair is triggered
        - Repair INTERRUPTS ongoing truck loading immediately
        - Interrupted truck's work is lost; must start loading again
        - Repair takes 10 minutes
        - Uses PreemptiveResource for immediate interruption

ANALYSIS PERFORMED:
    - Total simulation time to complete all operations
    - Loader utilization with preemptive repairs
    - Truck waiting times and interrupted work
    - Number of repairs performed and interruptions
    - Total dirt moved (affected by lost work from interruptions)
    - Comparison with non-preemptive version

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
    Truck operation cycle process with INTERRUPTIBLE loading.
    
    Simulates the complete cycle of a truck in the earthmoving operation:
    - Wait for loader availability
    - Get loaded with dirt (CAN BE INTERRUPTED by emergency repair)
    - Haul to dump site
    - Dump the load
    - Return to pit for next load
    
    KEY DIFFERENCE from PriorityResource version:
    - Uses interruptive_do() for loading phase
    - Loading can be INTERRUPTED by emergency repair
    - If interrupted, loading time is lost; truck must restart
    
    Args:
        truck (des.Entity): The truck entity with custom attributes
        loader (des.Resource): PreemptiveResource (can interrupt work)
        dumped_dirt (des.Resource): Counter for total dumped dirt
        worked_hours (des.Resource): Tracks cumulative loader working hours
    
    Yields:
        Simulation events: Loading, hauling, dumping, and return operations
    """
    while True:
        # LOADING PHASE: Get loader access
        yield truck.get(loader, 1, priority=2)
        
        # Try to load (CAN BE INTERRUPTED by emergency repair)
        loading_duration = truck.loading_dur.sample()
        try:
            # Use interruptive_do() to allow preemption
            # Regular do() cannot be interrupted
            yield truck.interruptive_do('load', loading_duration)
            # If no interruption, add the work time to loader hours
            yield truck.add(worked_hours, loading_duration)
            
        except d.Interrupt:
            # Loading was INTERRUPTED by emergency repair!
            # Work is lost; truck must release and try again
            print(f'{truck.env.now:.2f}: {truck.name} loading INTERRUPTED by emergency repair!')
        
        # Release loader (whether completed or interrupted)
        yield truck.put(loader, 1)

        # HAULING PHASE: Transport loaded dirt to dump site
        # (only happens if loading was completed, not interrupted)
        yield truck.do('haul', truck.hauling_dur.sample())
        
        # DUMPING PHASE: Unload dirt at dump site
        yield truck.do('dump', truck.dumping_dur)
        yield truck.add(dumped_dirt, truck.capacity)
        
        # RETURN PHASE: Return to pit for next load
        yield truck.do('return', 8)


def repair_process(repair_man, loader, worked_hours):
    """
    Equipment repair process with PREEMPTION capability.
    
    Simulates the repair person monitoring loader usage and performing
    EMERGENCY maintenance. When the loader reaches 10 accumulated working hours,
    the repair person IMMEDIATELY PREEMPTS any truck loading to perform repairs.
    
    KEY DIFFERENCE from PriorityResource version:
    - Repair request uses preempt=True
    - This INTERRUPTS ongoing truck loading
    - Interrupted truck work is lost (must restart)
    - Repair takes priority immediately
    
    Args:
        repair_man (des.Entity): The repair person entity
        loader (des.Resource): PreemptiveResource (can preempt work)
        worked_hours (des.Resource): Tracks cumulative loader working hours
    
    Yields:
        Simulation events: Waiting for repair trigger and repair work
    """
    repairs_triggered = 0
    
    while True:
        # Wait until 10 hours of work have been accumulated on the loader
        # This triggers the need for maintenance
        yield repair_man.get(worked_hours, 10)
        
        # Get the loader with PREEMPTION
        # preempt=True means if a truck is loading, it gets interrupted
        yield repair_man.get(loader, 1, priority=-3, preempt=True)
        
        repairs_triggered += 1
        print(f'{repair_man.env.now:.2f}: Repair #{repairs_triggered} - Emergency maintenance (preemptive)')
        
        # Perform the repair (10 minutes)
        yield repair_man.do('repair', 10)
        
        # Release the loader back to trucks
        yield repair_man.put(loader, 1)


# =============================================================================
# ENVIRONMENT SETUP
# =============================================================================

# Create the discrete event simulation environment
env = d.Environment()

# Create the PREEMPTIVE LOADER resource
# PreemptiveResource allows interruption of ongoing work
# preempt=True in get() will interrupt lower-priority entities
loader = d.PreemptiveResource(env, 'loader', print_actions=False, log=True)

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

# Start repair process with PREEMPTION capability
env.process(repair_process(repair_man, loader, worked_hours))


# =============================================================================
# RUN SIMULATION
# =============================================================================

# Run the simulation without dashboard (pure simulation)
simpm.run(env, dashboard=False)


# =============================================================================
# RESULTS AND ANALYSIS
# =============================================================================

print(f"\n{'='*70}")
print(f"EARTHMOVING PROJECT WITH PREEMPTIVE REPAIRS - SIMULATION RESULTS")
print(f"{'='*70}\n")

# Simulation completion time
print(f"Simulation completed at t = {env.now:.2f} minutes")
print(f"Approximately {env.now/60:.2f} hours\n")

# Total dirt moved
total_dirt = dumped_dirt.level()
print(f"Total dirt dumped: {total_dirt:.0f} units")

# Small truck statistics
small_truck_schedule = small_truck.schedule()
small_truck_cycles = len(small_truck_schedule)
print(f"\nSmall Truck Statistics:")
print(f"  Total cycles completed: {small_truck_cycles}")
print(f"  Total dirt moved: {small_truck_cycles * 80:.0f} units")

# Large truck statistics  
large_truck_schedule = large_truck.schedule()
large_truck_cycles = len(large_truck_schedule)
print(f"\nLarge Truck Statistics:")
print(f"  Total cycles completed: {large_truck_cycles}")
print(f"  Total dirt moved: {large_truck_cycles * 100:.0f} units")

# Loader statistics
loader_waiting = loader.waiting_time()
print(f"\nLoader Queue Statistics:")
print(f"  Total requests: {len(loader_waiting)}")
if len(loader_waiting) > 0:
    avg_wait = sum(loader_waiting) / len(loader_waiting)
    max_wait = max(loader_waiting)
    print(f"  Average wait time: {avg_wait:.2f} minutes")
    print(f"  Maximum wait time: {max_wait:.2f} minutes")

# Repair statistics
repair_schedule = repair_man.schedule()
if len(repair_schedule) > 0:
    repair_count = len(repair_schedule)
    print(f"\nRepair Statistics (PREEMPTIVE):")
    print(f"  Total repairs performed: {repair_count}")
    print(f"  Repair interval: Every 10 worked hours on loader")
    print(f"  Repair time per service: 10 minutes")
    print(f"  KEY DIFFERENCE: These repairs INTERRUPTED ongoing truck loading!")
    print(f"  Lost work from interruptions may delay project completion")
else:
    print(f"\nRepair Statistics (PREEMPTIVE):")
    print(f"  No repairs recorded (simulation too short)")

# Sample schedules
print(f"\nSmall Truck Schedule Sample (first 5 actions):")
if len(small_truck_schedule) > 0:
    print(small_truck_schedule.head(5))

print(f"\nLarge Truck Schedule Sample (first 5 actions):")
if len(large_truck_schedule) > 0:
    print(large_truck_schedule.head(5))

print(f"\nRepair Person Schedule Sample (first 5 actions):")
if len(repair_schedule) > 0:
    print(repair_schedule.head(5))

print(f"\n{'='*70}\n")


# =============================================================================
# COMPARISON: PREEMPTIVE vs NON-PREEMPTIVE
# =============================================================================
print(f"{'='*70}")
print(f"PREEMPTIVE vs NON-PREEMPTIVE REPAIR COMPARISON")
print(f"{'='*70}\n")

print(f"PREEMPTIVE RESOURCE (this simulation):")
print(f"  - Repairs can INTERRUPT truck loading immediately")
print(f"  - Interrupted loading work is LOST")
print(f"  - Truck must restart loading from scratch")
print(f"  - Impact: More total time needed (lost work), fewer cycles completed")
print(f"  - Current run: {small_truck_cycles} small + {large_truck_cycles} large trucks")
print(f"  - Total output: {total_dirt:.0f} units\n")

print(f"NON-PREEMPTIVE / PRIORITY RESOURCE (see repair_earthmoving.py):")
print(f"  - Repairs wait in queue until truck finishes loading")
print(f"  - Loader completes current 4-7 minute loading, then repair happens")
print(f"  - No lost work; loading is completed before interruption")
print(f"  - Impact: Higher productivity, more cycles, more output")
print(f"  - Expected: More truck cycles and more dirt dumped\n")

print(f"WHEN TO USE EACH:")
print(f"  Use PreemptiveResource when:")
print(f"    - Emergency maintenance cannot wait (safety critical)")
print(f"    - Repair time is critical for system health")
print(f"    - Lost work is acceptable (cost of delay > cost of restart)")
print(f"    - Example: Emergency fire suppression, safety shutdowns\n")

print(f"  Use PriorityResource when:")
print(f"    - Planned maintenance can wait briefly")
print(f"    - Completing current work is important")
print(f"    - Minimizing rework is critical")
print(f"    - Example: Scheduled maintenance, routine repairs\n")

print(f"{'='*70}\n")

# =============================================================================
# SIMULATION RESULTS SUMMARY
# =============================================================================
#
# KEY INSIGHTS ABOUT PREEMPTIVE RESOURCES:
#
# 1. INTERRUPTION COST: Preemption interrupts work mid-cycle.
#    This means:
#    - Loading time already invested is LOST
#    - Truck must restart loading from beginning
#    - Cumulative: Reduces cycles completed vs non-preemptive
#
# 2. RESOURCE BEHAVIOR:
#    - PreemptiveResource allows immediate interruption
#    - Regular Resource / PriorityResource only queue-based (wait for release)
#    - Priority=-3 on PreemptiveResource uses preempt=True for interruption
#
# 3. USE CASE: Emergency maintenance
#    - Fire suppression: Can't wait for truck to finish loading
#    - Safety shutdowns: Must stop immediately
#    - Critical repairs: Cannot delay by current job duration
#    
# 4. PENALTY: More preemptions = more lost work = longer project
#    - Each interruption costs loading time + restart
#    - If repair happens during first minute of 5-minute load, 4 min lost
#
# =============================================================================

