"""
Earthmoving Operation with Truck Size Attributes

OVERVIEW:
    This simulation demonstrates how entity ATTRIBUTES impact project outcomes.
    Different trucks with different load capacities are used in the same operation.
    
PURPOSE:
    Show how attributes (truck["size"]) affect:
    - Loading time (proportional to truck capacity)
    - Dump truck efficiency (smaller vs. larger loads)
    - Overall project completion time
    - Resource utilization
    - Total dirt moved per truck

PROCESS FLOW:
    1. Create 3 trucks with different size attributes (30, 35, 50 cubic meters)
    2. Each truck waits for loader availability
    3. Loading time = 5 + (truck_size / 20) minutes
       - 30m³ truck: 5 + 1.5 = 6.5 minutes
       - 35m³ truck: 5 + 1.75 = 6.75 minutes
       - 50m³ truck: 5 + 2.5 = 7.5 minutes
    4. Truck hauls (17 min), dumps (3 min), returns (13 min)
    5. Track how much each truck contributes based on its size

KEY INSIGHT:
    Larger trucks take slightly longer to load but move more dirt per trip.
    This example shows the trade-off: is the extra load worth the extra loading time?

@author: SimPM Example
@version: 2.0
"""
import simpm
import simpm.des as des


# =============================================================================
# PROCESS FUNCTIONS
# =============================================================================

def truck_cycle(truck: des.Entity, loader: des.Resource, dumped_dirt: des.Resource):
    """
    Truck operation cycle with size-dependent loading times.
    
    This process demonstrates how ATTRIBUTES impact simulation behavior.
    The truck["size"] attribute determines how long loading takes and how much
    dirt is dumped per cycle.
    
    Args:
        truck (des.Entity): The truck entity with "size" attribute (cubic meters)
        loader (des.Resource): Shared loader resource (capacity = 1)
        dumped_dirt (des.Resource): Accumulator for total dirt moved
    
    Process Steps:
        1. LOADING: Time depends on truck size
           - Acquire loader resource (wait if busy)
           - Loading duration = 5 + (size / 20) minutes
           - Release loader for next truck
        2. HAULING: Transport dirt to dump site (17 minutes)
        3. DUMPING: Unload dirt at dump site (3 minutes)
           - Add truck["size"] cubic meters to total
        4. RETURN: Travel back to pit (13 minutes)
        - Cycle repeats indefinitely
    
    Yields:
        Simulation events for each operation phase
    """
    while True:
        # =====================================================================
        # LOADING PHASE
        # =====================================================================
        # Wait for loader availability - if multiple trucks need the loader,
        # they form a queue. Smaller trucks may not wait less (depends on
        # which truck finishes loading first)
        yield truck.get(loader, 1)
        
        # Loading time is attribute-dependent
        # truck["size"] is in cubic meters (30, 35, or 50)
        # Formula: base_time (5 min) + size_factor (size/20)
        loading_time = 5 + truck["size"] / 20
        yield truck.do("loading", loading_time)
        
        # Release the loader so next truck can use it
        yield truck.put(loader, 1)

        # =====================================================================
        # HAULING PHASE
        # =====================================================================
        # All trucks take the same time to haul (distance is constant)
        # Truck size doesn't affect hauling time in this model
        yield truck.do("hauling", 17)
        
        # =====================================================================
        # DUMPING PHASE
        # =====================================================================
        # Dumping duration is constant, but amount dumped depends on truck size
        yield truck.do("dumping", 3)
        
        # Key insight: Each truck dumps its unique load size
        # truck["size"] was set during entity creation
        # This demonstrates attribute usage in calculations
        yield truck.add(dumped_dirt, truck["size"])

        # =====================================================================
        # RETURN PHASE
        # =====================================================================
        # Return trip time is constant (same distance, independent of load)
        yield truck.do("return", 13)
        
        # Cycle repeats - truck goes back to loading


# =============================================================================
# ENVIRONMENT SETUP
# =============================================================================

# Create the discrete event simulation environment
env = des.Environment("Earthmoving with truck sizes")

# Create the LOADER RESOURCE
# This is the bottleneck - only 1 loader shared by 3 trucks
# log=True tracks all events for analysis
loader = des.Resource(env, "loader", init=1, capacity=1, log=True)

# Create counter for TOTAL DIRT DUMPED
# This accumulates the total across all trucks
# Capacity of 100,000 cubic meters (plenty of space)
dumped_dirt = des.Resource(env, "dirt", init=0, capacity=100000, log=True)

# =========================================================================
# CREATE TRUCKS WITH SIZE ATTRIBUTES
# =========================================================================
# Create 3 truck entities
trucks = env.create_entities("truck", 3, log=True)

# CRITICAL STEP: Assign size attributes to each truck
# truck["size"] is a custom attribute that persists throughout simulation
# Different trucks have different capacities (cubic meters per load)
truck_sizes = [30, 35, 50]  # cubic meters per load

for truck, size in zip(trucks, truck_sizes):
    truck["size"] = size  # Set the size attribute
    # Truck 0: 30 m³ (smallest, fastest to load)
    # Truck 1: 35 m³ (medium, balanced)
    # Truck 2: 50 m³ (largest, more cargo, slower to load)

# Start the truck cycle process for each truck
for truck in trucks:
    env.process(truck_cycle(truck, loader, dumped_dirt))


# =============================================================================
# RUN SIMULATION
# =============================================================================

# Run the simulation for 480 minutes (8 hours)
# This gives trucks enough time to complete multiple cycles
simpm.run(env, dashboard=False, until=480)


# =============================================================================
# RESULTS AND ANALYSIS
# =============================================================================

print(f"\n{'='*80}")
print(f"EARTHMOVING WITH TRUCK SIZES - SIMULATION RESULTS")
print(f"{'='*80}\n")

# Simulation end time
print(f"Simulation Duration: {env.now:.2f} minutes ({env.now/60:.2f} hours)\n")

# =========================================================================
# LOADER UTILIZATION ANALYSIS
# =========================================================================
loader_util = loader.average_utilization()
print(f"LOADER UTILIZATION:")
print(f"  Utilization Rate: {loader_util*100:.2f}%")
print(f"  (Loader was busy {loader_util*100:.2f}% of the time)")
print(f"  Note: Higher utilization indicates the loader is well-used\n")

# =========================================================================
# QUEUE STATISTICS
# =========================================================================
waiting_times = loader.waiting_time()
print(f"LOADER QUEUE STATISTICS:")
print(f"  Total waiting instances: {len(waiting_times)}")
if len(waiting_times) > 0:
    avg_wait = sum(waiting_times) / len(waiting_times)
    max_wait = max(waiting_times)
    min_wait = min(waiting_times)
    print(f"  Average truck waiting time: {avg_wait:.2f} minutes")
    print(f"  Maximum truck waiting time: {max_wait:.2f} minutes")
    print(f"  Minimum truck waiting time: {min_wait:.2f} minutes")
    print(f"  (Shows how much congestion at the loader)\n")
else:
    print(f"  No trucks had to wait (loader was always available)\n")

# =========================================================================
# TRUCK PERFORMANCE ANALYSIS
# =========================================================================
print(f"{'='*80}")
print(f"TRUCK PERFORMANCE ANALYSIS (Impact of Size Attribute)")
print(f"{'='*80}\n")

# Analyze each truck's performance
for i, truck in enumerate(trucks):
    truck_size = truck["size"]
    truck_log = truck.schedule()
    
    # Count cycles (number of times truck did "loading")
    loading_activities = truck_log[truck_log['activity'] == 'loading']
    num_cycles = len(loading_activities)
    
    # Calculate average loading time for this truck
    if num_cycles > 0:
        loading_activities = loading_activities.copy()
        loading_activities['duration'] = loading_activities['finish_time'] - loading_activities['start_time']
        avg_loading_time = loading_activities['duration'].mean()
        total_dirt_moved = truck_size * num_cycles
    else:
        avg_loading_time = 0
        total_dirt_moved = 0
    
    print(f"TRUCK {i} - Size: {truck_size} m³ per load")
    print(f"  Completed cycles: {num_cycles}")
    print(f"  Expected loading time: 5 + {truck_size}/20 = {5 + truck_size/20:.2f} minutes")
    print(f"  Average actual loading time: {avg_loading_time:.2f} minutes")
    print(f"  Total dirt moved: {total_dirt_moved:.0f} m³")
    print(f"  Efficiency (dirt per cycle): {truck_size:.0f} m³\n")

# Analyze each truck's performance
total_cycles = 0
for i, truck in enumerate(trucks):
    truck_log = truck.schedule()
    loading_activities = truck_log[truck_log['activity'] == 'loading']
    cycles = len(loading_activities)
    total_cycles += cycles

total_dirt = dumped_dirt.level()

print(f"{'='*80}")
print(f"PROJECT SUMMARY")
print(f"{'='*80}\n")
print(f"Total dirt moved: {total_dirt:.0f} m³")
print(f"Total load cycles: {total_cycles}")
print(f"Average dirt per cycle: {total_dirt / total_cycles if total_cycles > 0 else 0:.2f} m³")
print(f"Project duration: {env.now:.2f} minutes ({env.now/60:.2f} hours)\n")


# =============================================================================
# INSIGHTS AND CONCLUSIONS
# =============================================================================
"""
KEY INSIGHTS FROM THIS SIMULATION:

1. ATTRIBUTE IMPACT ON LOADING TIME:
   - Truck 0 (30m³):  Loading = 5 + 30/20 = 6.5 minutes  (FASTEST)
   - Truck 1 (35m³):  Loading = 5 + 35/20 = 6.75 minutes (MEDIUM)
   - Truck 2 (50m³):  Loading = 5 + 50/20 = 7.5 minutes  (SLOWEST)
   
   The larger truck takes 15% longer to load (7.5 vs 6.5 min), but moves
   67% more dirt per trip (50 vs 30 m³). This shows the trade-off between
   speed and capacity.

2. CYCLE COMPLETION TIME (per truck):
   Each truck's full cycle = Loading + Hauling (17) + Dumping (3) + Return (13)
   - Truck 0: 6.5 + 17 + 3 + 13 = 39.5 minutes per cycle
   - Truck 1: 6.75 + 17 + 3 + 13 = 39.75 minutes per cycle
   - Truck 2: 7.5 + 17 + 3 + 13 = 40.5 minutes per cycle
   
   Differences are small (1.3%) but accumulate over many cycles.

3. BOTTLENECK ANALYSIS:
   - The LOADER is the bottleneck (shared resource with capacity=1)
   - The larger truck (Truck 2) takes longest to load
   - If Truck 2 is loading, Trucks 0 and 1 must wait
   - Queue times depend on which truck finishes its cycle first

4. EFFICIENCY COMPARISON:
   Dirt per minute of loader time (productivity):
   - Truck 0: 30 m³ / 6.5 min = 4.62 m³/min
   - Truck 1: 35 m³ / 6.75 min = 5.19 m³/min
   - Truck 2: 50 m³ / 7.5 min = 6.67 m³/min
   
   Larger trucks are MORE efficient per minute of loader time!

5. TOTAL CONTRIBUTION:
   Over 480 minutes (8 hours), trucks complete different numbers of cycles.
   The total dirt moved reflects:
   - How many cycles each truck completes (depends on queuing/timing)
   - The size attribute of each truck
   - Any waiting time at the loader

6. QUEUE DYNAMICS:
   With only 1 loader and 3 trucks:
   - Loader utilization should be high (75-85% range)
   - Average wait times indicate congestion
   - Larger trucks might cause longer queues for smaller trucks

DEMONSTRATION OF ATTRIBUTES:
   This example shows how entity attributes (truck["size"]) are used to:
   ✓ Calculate durations: loading_time = 5 + truck["size"] / 20
   ✓ Track quantities: dumped_dirt.add(truck["size"])
   ✓ Analyze results: Efficiency ratios and comparisons
   
   Attributes are PERSISTENT - once set, they stay with the entity
   throughout the simulation and can be accessed anywhere in the code.

VARIATIONS TO EXPLORE:
   1. Change truck sizes: What if all trucks were 50m³?
   2. Add a 4th smaller truck (20m³) - does it improve throughput?
   3. Increase loader capacity to 2 - how much does efficiency improve?
   4. Make loading time NOT size-dependent - constant 6 minutes
   5. Add variable hauling times - does it change optimal truck size?
"""

print(f"{'='*80}\n")

# =============================================================================
# SAMPLE TRUCK SCHEDULES (First 15 actions from each truck)
# =============================================================================
print(f"TRUCK SCHEDULES (First 15 Actions Each)\n")

for i, truck in enumerate(trucks):
    print(f"Truck {i} (Size: {truck['size']} m³):")
    schedule = truck.schedule()
    if len(schedule) > 0:
        # Show first 15 rows
        print(schedule[['activity', 'start_time', 'finish_time']].head(15).to_string(index=False))
    else:
        print("  No activities recorded")
    print()

print(f"{'='*80}\n")


# =============================================================================
# ACTUAL SIMULATION RESULTS (480-minute run)
# =============================================================================
"""
==========================================================================
EARTHMOVING WITH TRUCK SIZES - SIMULATION RESULTS
==========================================================================

Simulation Duration: 480.00 minutes (8.00 hours)

LOADER UTILIZATION:
  Utilization Rate: 52.53%
  (Loader was busy 52.53% of the time)
  Note: Higher utilization indicates the loader is well-used

LOADER QUEUE STATISTICS:
  Total waiting instances: 37
  Average truck waiting time: 0.53 minutes
  Maximum truck waiting time: 13.25 minutes
  Minimum truck waiting time: 0.00 minutes
  (Shows how much congestion at the loader)

==========================================================================
TRUCK PERFORMANCE ANALYSIS (Impact of Size Attribute)
==========================================================================

TRUCK 0 - Size: 30 m³ per load
  Completed cycles: 13
  Expected loading time: 5 + 30/20 = 6.50 minutes
  Average actual loading time: 6.50 minutes
  Total dirt moved: 390 m³
  Efficiency (dirt per cycle): 30 m³

TRUCK 1 - Size: 35 m³ per load
  Completed cycles: 12
  Expected loading time: 5 + 35/20 = 6.75 minutes
  Average actual loading time: 6.75 minutes
  Total dirt moved: 420 m³
  Efficiency (dirt per cycle): 35 m³

TRUCK 2 - Size: 50 m³ per load
  Completed cycles: 12
  Expected loading time: 5 + 50/20 = 7.50 minutes
  Average actual loading time: 7.50 minutes
  Total dirt moved: 600 m³
  Efficiency (dirt per cycle): 50 m³

==========================================================================
PROJECT SUMMARY
==========================================================================

Total dirt moved: 1330 m³
Total load cycles: 37
Average dirt per cycle: 35.95 m³
Project duration: 480.00 minutes (8.00 hours)

==========================================================================
TRUCK SCHEDULES (First 15 Activities Each)
==========================================================================

Truck 0 (Size: 30 m³):
activity  start_time  finish_time
 loading         0.0          6.5
 hauling         6.5         23.5
 dumping        23.5         26.5
  return        26.5         39.5
 loading        39.5         46.0
 hauling        46.0         63.0
 dumping        63.0         66.0
  return        66.0         79.0
 loading        79.0         85.5
 hauling        85.5        102.5
 dumping       102.5        105.5
  return       105.5        118.5
 loading       118.5        125.0
 hauling       125.0        142.0
 dumping       142.0        145.0

Truck 1 (Size: 35 m³):
activity  start_time  finish_time
 loading        6.50        13.25
 hauling       13.25        30.25
 dumping       30.25        33.25
  return       33.25        46.25
 loading       46.25        53.00
 hauling       53.00        70.00
 dumping       70.00        73.00
  return       73.00        86.00
 loading       86.00        92.75
 hauling       92.75       109.75
 dumping      109.75       112.75
  return      112.75       125.75
 loading      125.75       132.50
 hauling      132.50       149.50
 dumping      149.50       152.50

Truck 2 (Size: 50 m³):
activity  start_time  finish_time
 loading       13.25        20.75
 hauling       20.75        37.75
 dumping       37.75        40.75
  return       40.75        53.75
 loading       53.75        61.25
 hauling       61.25        78.25
 dumping       78.25        81.25
  return       81.25        94.25
 loading       94.25       101.75
 hauling      101.75       118.75
 dumping      118.75       121.75
  return      121.75       134.75
 loading      134.75       142.25
 hauling      142.25       159.25
 dumping      159.25       162.25

==========================================================================

KEY FINDINGS FROM RESULTS:
- Truck 0 (30m³) completed 13 cycles - smallest truck, fastest loading
- Truck 1 (35m³) completed 12 cycles - medium truck
- Truck 2 (50m³) completed 12 cycles - largest truck, more total dirt moved (600 vs 390)
- Larger trucks are more efficient overall: Truck 2 moved 53% more dirt than Truck 0
  despite having similar cycle counts
- Loader utilization at 52.53% suggests room for more trucks
- Average wait time of 0.53 minutes indicates minimal congestion
"""
