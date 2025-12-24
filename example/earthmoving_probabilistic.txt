"""
Earthmoving Operation with Probabilistic Durations

OVERVIEW:
    Demonstrates probabilistic (random) durations for truck operations.
    Real-world operations vary due to equipment variability, worker
    performance, environmental factors, and unexpected delays.

PURPOSE:
    - Use probability distributions for realistic operation durations
    - Compare deterministic vs. stochastic simulation outcomes
    - Show how variability affects project scheduling
    - Run multiple replicates to understand outcome distribution

DISTRIBUTIONS (Match earthmoving_monte_carlo.py):
    - Loading: Normal(5+size/20, 0.5-0.8) - varies by truck size
    - Hauling: Normal(17, 4) - traffic and road conditions
    - Dumping: Uniform(2, 5) - site conditions create uncertainty
    - Return: Normal(13, 3) - traffic and driver variability

KEY PATTERN:
    Pass distribution objects directly to do() - SimPM samples internally
    on each simulation step for elegant, efficient code.

@author: SimPM Example
@version: 2.0 (factory pattern with replicates)
"""
import simpm
import simpm.des as des
from simpm.dist import norm, uniform
import numpy as np
import statistics
from typing import List

np.random.seed(42)

_CURRENT_TRUCK_COUNT = 3


def truck_cycle_probabilistic(truck: des.Entity, loader: des.Resource,
                              dumped_dirt: des.Resource,
                              loading_dists: dict):
    """
    Truck cycle with probabilistic durations.
    
    Distributions passed directly to do() - SimPM samples internally
    on each simulation step, creating realistic variability.
    
    Args:
        truck: Truck entity with 'size' attribute
        loader: Shared loader resource
        dumped_dirt: Accumulator for total dirt moved
        loading_dists: Truck-specific loading distributions
    """
    truck_id = int(truck.name.split('_')[1]) if '_' in truck.name else 0

    while True:
        yield truck.get(loader, 1)
        yield truck.do("loading", loading_dists[truck_id])
        yield truck.put(loader, 1)
        yield truck.do("hauling", norm(17, 4))
        yield truck.do("dumping", uniform(2, 5))
        yield truck.add(dumped_dirt, truck["size"])
        yield truck.do("return", norm(13, 3))


def env_factory() -> des.Environment:
    """
    Create a fresh earthmoving environment.
    
    Called by simpm.run() for each replicate.
    Global _CURRENT_TRUCK_COUNT determines fleet size.
    
    Returns:
        Environment ready to simulate
    """
    global _CURRENT_TRUCK_COUNT

    env = des.Environment(f"Earthmoving ({_CURRENT_TRUCK_COUNT} trucks)")
    loader = des.Resource(env, "loader", init=1, capacity=1, log=True)
    dumped_dirt = des.Resource(env, "dirt", init=0, capacity=100000, log=True)

    trucks = env.create_entities("truck", _CURRENT_TRUCK_COUNT, log=True)
    truck_sizes = [30, 35, 50]
    loading_dists = {}

    for i, truck in enumerate(trucks):
        size = truck_sizes[i % len(truck_sizes)]
        truck["size"] = size
        loading_dists[i] = norm(5 + size / 20, 0.5 + (0.1 * (i % 3)))

    for truck in trucks:
        env.process(truck_cycle_probabilistic(truck, loader, dumped_dirt, loading_dists))

    return env


def extract_stats(env: des.Environment) -> dict:
    """Extract project statistics from completed environment."""
    loader = [r for r in env.resources if r.name == "loader"][0]
    dumped_dirt = [r for r in env.resources if r.name == "dirt"][0]

    return {
        "duration": env.now,
        "total_dirt": dumped_dirt.level(),
        "loader_util": loader.average_utilization(),
        "wait_times": loader.waiting_time(),
    }


def run_probabilistic_example(truck_counts: List[int], num_replicates: int = 10):
    """Run probabilistic simulations with different truck counts."""
    global _CURRENT_TRUCK_COUNT

    print(f"\n{'='*80}")
    print(f"EARTHMOVING - PROBABILISTIC SIMULATION (Factory Pattern)")
    print(f"{'='*80}\n")

    for num_trucks in truck_counts:
        _CURRENT_TRUCK_COUNT = num_trucks

        print(f"\nRunning {num_replicates} replicates with {num_trucks} trucks...")
        all_envs = simpm.run(env_factory, dashboard=False,
                            number_runs=num_replicates, start_async=False)

        durations = [env.now for env in all_envs]
        dirt_totals = []
        loader_utils = []
        all_waits = []

        for env in all_envs:
            stats = extract_stats(env)
            dirt_totals.append(stats["total_dirt"])
            loader_utils.append(stats["loader_util"])
            all_waits.extend(stats["wait_times"])

        mean_duration = statistics.mean(durations)
        std_duration = statistics.stdev(durations) if len(durations) > 1 else 0
        mean_dirt = statistics.mean(dirt_totals)
        mean_util = statistics.mean(loader_utils)
        mean_wait = statistics.mean(all_waits) if all_waits else 0

        print(f"\n{num_trucks} Trucks Summary ({num_replicates} replicates):")
        print(f"  Project duration: {mean_duration:.2f} min "
              f"({std_duration:.2f}, range {min(durations):.0f}-{max(durations):.0f})")
        print(f"  Total dirt moved: {mean_dirt:.0f} m (avg)")
        print(f"  Loader utilization: {mean_util*100:.1f}%")
        print(f"  Avg truck wait time: {mean_wait:.2f} min")


if __name__ == "__main__":
    print(f"\n{'='*80}")
    print(f"PROBABILISTIC EARTHMOVING SIMULATION")
    print(f"Factory Pattern with Multiple Replicates")
    print(f"{'='*80}")

    print("""
OVERVIEW:
    Uses simpm.run() with a factory function to run multiple replicates
    of a stochastic (probabilistic) earthmoving simulation.

KEY PATTERN:
    1. Define env_factory() that creates fresh environments
    2. Call simpm.run(env_factory, number_runs=10) for replicates
    3. Extract statistics from each completed environment
    4. Compare across truck configurations

DISTRIBUTIONS (Match earthmoving_monte_carlo.py):
    - Loading: norm(5+size/20, 0.5-0.8) by truck size
    - Hauling: norm(17, 4) - high variability
    - Dumping: uniform(2, 5) - uniform uncertainty
    - Return: norm(13, 3) - high variability

WHY DISTRIBUTIONS MATTER:
    - Realistic representation of operational variability
    - Identify risks and bottlenecks
    - Plan for worst-case scenarios
    - Monte Carlo: run multiple times for outcome distribution
    """)

    truck_counts = [3, 5, 7]
    num_replicates = 10

    run_probabilistic_example(truck_counts, num_replicates)

    print(f"\n{'='*80}\n")
