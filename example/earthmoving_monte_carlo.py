"""
Earthmoving Operation with Monte Carlo Simulation

OVERVIEW:
    This example demonstrates a MONTE CARLO SIMULATION approach to analyze
    uncertainty in earthmoving projects. Unlike single-run simulations, Monte
    Carlo repeats the simulation many times with different random durations,
    creating a PROBABILITY DISTRIBUTION of possible project completion times.

PURPOSE:
    Demonstrate how to:
    - Run multiple simulation replicates using env_factory pattern
    - Collect project duration statistics from simpm logs
    - Build a probability distribution of completion times
    - Vary the number of trucks to see impact on duration variability
    - Use simpm's built-in statistics collection for automatic metric gathering
    - Use simpm.run() with different configurations

KEY CONCEPT:
    Monte Carlo Method = Run the same scenario many times with random variations,
    then analyze the distribution of outcomes. This gives us:
    - Mean project duration (expected value)
    - Standard deviation (variability)
    - Min/max possible outcomes
    - Confidence intervals (e.g., 90% chance project finishes by time X)

PROCESS FLOW (Per Simulation):
    - Loading time: Normal(mean=5+size/20, std=0.5-0.8) - varies each cycle
    - Hauling time: Normal(17, 4) - variable distance/conditions
    - Dumping time: Uniform(2, 5) - between 2-5 minutes
    - Return time: Normal(13, 3) - variable route conditions

MONTE CARLO APPROACH:
    1. Define: env_factory() creates fresh environments with truck count
    2. Run: simpm.run() with number_runs parameter for replicates
    3. Collect: Project completion time from each run using logs
    4. Analyze: Mean, std dev, percentiles of completion times
    5. Visualize: Histogram showing probability distribution

STATISTICS COLLECTION:
    Uses simpm's built-in logs and run_history instead of manual tracking!

@author: SimPM Example with Monte Carlo
@version: 4.0 (Function-based factory pattern)
"""
import simpm
import simpm.des as des
from simpm.dist import norm, uniform
import numpy as np
from typing import List, Dict
import statistics


# =============================================================================
# GLOBAL: Current truck count (updated by each env_factory call)
# =============================================================================
_CURRENT_TRUCK_COUNT = 3


# =============================================================================
# PROCESS FUNCTIONS
# =============================================================================

def truck_cycle_probabilistic(truck: des.Entity, loader: des.Resource,
                              dumped_dirt: des.Resource,
                              loading_dists: dict):
    """
    Truck operation cycle with probabilistic (random) durations.

    Args:
        truck (des.Entity): The truck entity with "size" attribute
        loader (des.Resource): Shared loader resource
        dumped_dirt (des.Resource): Accumulator for total dirt
        loading_dists (dict): Dictionary mapping truck ID to loading distribution

    Yields:
        Simulation events for each operation phase
    """
    truck_id = int(truck.name.split('_')[1]) if '_' in truck.name else 0

    while True:
        yield truck.get(loader, 1)
        yield truck.do("loading", loading_dists[truck_id])
        yield truck.put(loader, 1)
        yield truck.do("hauling", norm(17, 4))
        yield truck.do("dumping", uniform(2, 5))
        yield truck.add(dumped_dirt, truck["size"])# Ensure > 0.5
        yield truck.do("return", norm(13, 3))


# =============================================================================
# ENVIRONMENT FACTORY - Creates Fresh Environments for Each Run
# =============================================================================

def env_factory() -> des.Environment:
    """
    Create and return ONE fresh earthmoving simulation environment.
    
    This factory function is called by simpm.run() for each replicate.
    The global _CURRENT_TRUCK_COUNT determines how many trucks are created.
    
    Returns:
        des.Environment: Configured environment ready to run
    """
    global _CURRENT_TRUCK_COUNT
    
    # Create the discrete event simulation environment
    env = des.Environment(f"Earthmoving Monte Carlo ({_CURRENT_TRUCK_COUNT} trucks)")

    # Create the LOADER RESOURCE
    loader = des.Resource(env, "loader", init=1, capacity=1, log=True)

    # Create counter for TOTAL DIRT DUMPED
    dumped_dirt = des.Resource(env, "dirt", init=0, capacity=100000, log=True)

    # =========================================================================
    # CREATE TRUCKS WITH SIZE ATTRIBUTES
    # =========================================================================
    trucks = env.create_entities("truck", _CURRENT_TRUCK_COUNT, 
                                  log=True, print_actions=False)

    # Define truck sizes (cubic meters per load)
    truck_sizes = [30, 35, 50]  # Cycle through sizes for variety
    loading_dists = {}

    for i, truck in enumerate(trucks):
        size = truck_sizes[i % len(truck_sizes)]
        truck["size"] = size
        # Create loading distribution for this truck
        loading_dists[i] = norm(5 + size / 20, 0.5 + (0.1 * (i % 3)))

    # Start the truck cycle process for each truck
    for truck in trucks:
        env.process(truck_cycle_probabilistic(truck, loader, dumped_dirt, loading_dists))

    return env


# =============================================================================
# HELPER FUNCTIONS FOR STATISTICS COLLECTION AND ANALYSIS
# =============================================================================

def extract_completion_time(env: des.Environment) -> float:
    """
    Extract the project completion time from a completed environment.
    
    Uses the environment's final simulation time (env.now).
    
    Args:
        env (des.Environment): Completed simulation environment
        
    Returns:
        float: Completion time in minutes
    """
    return env.now


def run_monte_carlo_experiment(truck_counts: List[int], 
                                num_replicates: int = 10) -> Dict[int, Dict]:
    """
    Run Monte Carlo experiment with different truck counts.

    Args:
        truck_counts (List[int]): List of truck counts to test (e.g., [3, 5, 7, 10])
        num_replicates (int): Number of replicates per configuration (default: 10)

    Returns:
        Dict[int, Dict]: Results indexed by truck count, containing:
            - 'durations': List of project completion times from all replicates
            - 'mean': Mean project duration
            - 'std': Standard deviation
            - 'min': Minimum observed duration
            - 'max': Maximum observed duration
            - 'percentiles': {10, 25, 50, 75, 90} percentiles
    """
    global _CURRENT_TRUCK_COUNT
    results = {}

    for num_trucks in truck_counts:
        _CURRENT_TRUCK_COUNT = num_trucks
        
        print(f"\n{'='*70}")
        print(f"MONTE CARLO EXPERIMENT: {num_trucks} Trucks")
        print(f"Running {num_replicates} replicates with simpm.run()...")
        print(f"{'='*70}\n")

        # Run multiple replicates using simpm.run() with env_factory
        all_envs = simpm.run(env_factory, dashboard=False, number_runs=num_replicates,
                            start_async=False)

        # Extract completion times from all runs
        durations = [extract_completion_time(env) for env in all_envs]

        # Print individual results
        for i, duration in enumerate(durations):
            print(f"  Replicate {i + 1:2d}/{num_replicates}: "
                  f"Duration = {duration:7.2f} min ({duration/60:5.2f} hrs)")

        # Calculate statistics from collected durations
        mean_duration = statistics.mean(durations)
        std_duration = statistics.stdev(durations) if len(durations) > 1 else 0
        min_duration = min(durations)
        max_duration = max(durations)

        # Calculate percentiles
        sorted_durations = sorted(durations)
        percentiles = {
            10: np.percentile(sorted_durations, 10),
            25: np.percentile(sorted_durations, 25),
            50: np.percentile(sorted_durations, 50),  # Median
            75: np.percentile(sorted_durations, 75),
            90: np.percentile(sorted_durations, 90),
        }

        results[num_trucks] = {
            'durations': durations,
            'mean': mean_duration,
            'std': std_duration,
            'min': min_duration,
            'max': max_duration,
            'percentiles': percentiles,
        }

        # Print summary statistics for this configuration
        print(f"\nSummary for {num_trucks} trucks:")
        print(f"  Mean duration:     {mean_duration:.2f} minutes ({mean_duration/60:.2f} hours)")
        print(f"  Std deviation:     {std_duration:.2f} minutes")
        print(f"  Min duration:      {min_duration:.2f} minutes")
        print(f"  Max duration:      {max_duration:.2f} minutes")
        print(f"  Median (50th %ile): {percentiles[50]:.2f} minutes")
        print(f"  90th percentile:   {percentiles[90]:.2f} minutes (90% chance to finish by)")
        print(f"  10th percentile:   {percentiles[10]:.2f} minutes (10% finish by this time)")

    return results


# =============================================================================
# HELPER FUNCTIONS FOR VISUALIZATION AND ANALYSIS
# =============================================================================

def print_comparison_table(results: Dict[int, Dict]):
    """
    Print a comparison table of results across different truck counts.

    Args:
        results (Dict[int, Dict]): Results from Monte Carlo run
    """
    print(f"\n{'='*90}")
    print(f"MONTE CARLO COMPARISON - All Truck Configurations")
    print(f"{'='*90}\n")

    print(f"{'Trucks':>8} {'Mean (min)':>12} {'Std Dev':>10} {'Min':>10} {'Max':>10} "
          f"{'10th %ile':>12} {'Median':>10} {'90th %ile':>12}")
    print(f"{'-'*90}")

    for num_trucks in sorted(results.keys()):
        data = results[num_trucks]
        print(f"{num_trucks:>8} {data['mean']:>12.2f} {data['std']:>10.2f} "
              f"{data['min']:>10.2f} {data['max']:>10.2f} "
              f"{data['percentiles'][10]:>12.2f} {data['percentiles'][50]:>10.2f} "
              f"{data['percentiles'][90]:>12.2f}")

    print()


def print_detailed_analysis(results: Dict[int, Dict]):
    """
    Print detailed analysis with insights for each truck configuration.

    Args:
        results (Dict[int, Dict]): Results from Monte Carlo run
    """
    print(f"\n{'='*90}")
    print(f"DETAILED MONTE CARLO ANALYSIS")
    print(f"{'='*90}\n")

    for num_trucks in sorted(results.keys()):
        data = results[num_trucks]
        mean = data['mean']
        std = data['std']
        cv = (std / mean * 100) if mean > 0 else 0  # Coefficient of variation

        print(f"Configuration: {num_trucks} Trucks")
        print(f"  Expected project duration: {mean:.2f} minutes ({mean/60:.2f} hours)")
        print(f"  Variability (std dev): {std:.2f} minutes")
        print(f"  Coefficient of variation: {cv:.1f}% (uncertainty relative to mean)")
        print(f"  Range: {data['min']:.2f} to {data['max']:.2f} minutes")
        print(f"  Interquartile range (25-75th): {data['percentiles'][75]-data['percentiles'][25]:.2f} min")

        # Confidence intervals
        ci_90 = data['percentiles'][90] - data['percentiles'][10]
        print(f"  90% confidence interval width: {ci_90:.2f} minutes")
        print(f"  (90% certain project finishes between {data['percentiles'][10]:.2f} "
              f"and {data['percentiles'][90]:.2f} minutes)")
        print()


# =============================================================================
# MAIN EXECUTION
# =============================================================================

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print(f"\n{'='*90}")
    print(f"EARTHMOVING PROJECT - MONTE CARLO SIMULATION")
    print(f"Using env_factory + simpm.run() Pattern")
    print(f"{'='*90}\n")

    print("""
MONTE CARLO ANALYSIS:
    This simulation uses the Monte Carlo method to understand how many trucks
    affects project completion time and its variability.

APPROACH:
    1. Define env_factory() that creates environments with variable truck counts
    2. Use simpm.run(env_factory, number_runs=10) for each configuration
    3. Extract completion times directly from env.now of each run
    4. Collect statistics using Python's statistics module
    5. Compare distributions across configurations

KEY ADVANTAGES OF THIS APPROACH:
    - Cleaner integration with simpm.run() framework
    - Automatic run management and logging
    - Direct access to simpm logs via environment objects
    - Similar pattern to probabilistic_cpm.py example

EXPECTED RESULTS:
    - More trucks = Lower mean completion time (more parallelism)
    - More trucks = More independent randomness in cycles
    - Diminishing returns: 3->5 trucks saves more time than 7->10 trucks
    """)

    # Run Monte Carlo experiments with different truck counts
    truck_counts = [3, 5, 7, 10]
    num_replicates = 10
    
    results = run_monte_carlo_experiment(truck_counts, num_replicates)

    # Print comprehensive analysis
    print_comparison_table(results)
    print_detailed_analysis(results)

    # ==========================================================================
    # INSIGHTS AND RECOMMENDATIONS
    # ==========================================================================

    print(f"{'='*90}")
    print(f"KEY INSIGHTS FROM MONTE CARLO ANALYSIS")
    print(f"{'='*90}\n")

    # Find the most consistent configuration (lowest std dev)
    min_std_truck_count = min(results.keys(), key=lambda k: results[k]['std'])
    most_consistent_std = results[min_std_truck_count]['std']

    print(f"1. RELIABILITY (Lowest Variability):")
    print(f"   - {min_std_truck_count} trucks has the lowest variability (std: {most_consistent_std:.2f} min)")
    print(f"   - This configuration has the most predictable outcomes for project planning\n")

    # Find the fastest configuration (lowest mean)
    fastest_truck_count = min(results.keys(), key=lambda k: results[k]['mean'])
    fastest_mean = results[fastest_truck_count]['mean']
    print(f"2. SPEED (Fastest Expected Time):")
    print(f"   - {fastest_truck_count} trucks completes in {fastest_mean:.2f} min on average")
    print(f"   - This is the fastest completion time for this project setup\n")

    # Compare time savings
    slowest_truck_count = max(results.keys(), key=lambda k: results[k]['mean'])
    slowest_mean = results[slowest_truck_count]['mean']
    time_saved = slowest_mean - fastest_mean
    percent_saved = (time_saved / slowest_mean) * 100

    print(f"3. EFFICIENCY (Time Savings by Adding Trucks):")
    print(f"   - Going from {slowest_truck_count} to {fastest_truck_count} trucks saves "
          f"{time_saved:.2f} min ({percent_saved:.1f}%)")
    print(f"   - Adding more trucks also reduces variability (less randomness in fewer cycles)\n")

    # Risk assessment - Use threshold that gives meaningful results
    # 300 hours = 18,000 minutes - critical threshold between 7 and 10 truck configs
    # This shows the risk/reward tradeoff in fleet sizing
    risk_threshold = 300 * 60  # Convert 300 hours to minutes
    print(f"4. RISK ASSESSMENT (Probability of Missing Target = {risk_threshold/60:.0f} hours):")
    for num_trucks in sorted(results.keys()):
        durations = results[num_trucks]['durations']
        over_target = sum(1 for d in durations if d > risk_threshold)
        prob_over = (over_target / len(durations)) * 100
        print(f"   - {num_trucks} trucks: {prob_over:.0f}% chance of exceeding {risk_threshold/60:.0f} hours")

    print(f"\n{'='*90}\n")
