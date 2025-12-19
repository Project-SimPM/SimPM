"""
Pallet Factory Simulation

This simulation models a pallet manufacturing and installation system using Discrete Event Simulation (DES).
The model answers the question: "How long does it take to install 20,000 pallets?"

SYSTEM DESCRIPTION:
    - Pallet Production: Pallets are created at the factory at a rate of 10 pallets every 3-5 hours
    - Transportation: Two trucks transport pallets (450 pallets per trip each)
    - Travel Times: Outbound travel to installation site: 50-65 hours (triangular distribution)
                   Return travel to factory: 50-65 hours
    - Installation: Two workers at the delivery site install pallets
                   Worker 1: 1-1.5 hours per pallet
                   Worker 2: 1.5-2 hours per pallet
    - Target: Install a total of 20,000 pallets

ANALYSIS PERFORMED:
    - Total simulation time to complete 20,000 installations
    - Waiting time analysis for each truck and worker
    - Probability distribution plots for waiting times

@author: Naima Sadeghi
@version: 1.0
@date: December 2025
"""
import os
import sys
import inspect
import matplotlib.pyplot as plt
import numpy as np
import random

# Add parent directory to path to allow imports from src/simpm module
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 

import simpm
import simpm.des as des
import simpm.dist as dist

# =============================================================================
# RANDOM SEED FOR REPRODUCIBILITY
# =============================================================================
# Set a seed value to ensure all runs produce identical results
# Change this seed to get different random sequences
RANDOM_SEED = 42

# Set seeds for all random number generators
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

print(f"Simulation initialized with random seed: {RANDOM_SEED}")
print(f"(All runs with this seed will produce identical results)\n")

# =============================================================================
# PROCESS FUNCTIONS - Define the behavior of entities in the simulation
# =============================================================================

def create_pallets(factory: des.Environment, res, damage_pallets_factory):
    """
    Factory pallet creation process.
    
    Simulates continuous pallet production at the factory. Pallets are created
    at regular intervals (every 3-5 hours) at a rate of 10 pallets per batch.
    
    Args:
        factory (des.Environment): The factory entity representing the production facility
        res (des.Resource): The factory pallet resource (inventory)
        damage_pallets_factory (des.Resource): Resource tracking damaged pallets at factory
    
    Yields:
        Simulation events: Work intervals and pallet additions
    """
    while True:
        # Simulate production work with uniform distribution between 3-5 hours
        yield factory.do("work", dist.uniform(3, 5))
        # Add 10 pallets to factory inventory after work is completed
        yield factory.add(res, 10)
    

def truck_process(truck, pallets, site_pallets, damage_pallets_site, damage_pal_fact):
    """
    Truck transportation process.
    
    Simulates truck operation: picking up pallets from factory, traveling to 
    installation site, and returning to factory. Each truck makes repeated trips
    carrying up to 450 pallets per load.
    
    Args:
        truck (des.Entity): The truck entity
        pallets (des.Resource): Factory pallet inventory (source)
        site_pallets (des.Resource): Site pallet inventory (destination)
        damage_pallets_site (des.Resource): Damaged pallets at installation site
        damage_pal_fact (des.Resource): Damaged pallets at factory
    
    Yields:
        Simulation events: Loading, travel, and unloading operations
    """
    while True:
        # Pick up 450 pallets from factory inventory
        yield truck.get(pallets, 450)
        # Travel to installation site (triangular distribution: min=50, mode=60, max=65 hours)
        yield truck.do("travel", dist.triang(50, 60, 65))
        # Deliver pallets to installation site
        yield truck.add(site_pallets, 450)
        # Travel back to factory for next load
        yield truck.do("travel", dist.triang(50, 60, 65))
       

def worker1_process(worker, site_pallets, installed_pallets):
    """
    Worker 1 installation process.
    
    Worker 1 installs pallets at the installation site with a faster rate
    (1-1.5 hours per pallet). Process continues until 20,000 pallets are installed.
    
    Args:
        worker (des.Entity): Worker 1 entity
        site_pallets (des.Resource): Site pallet inventory (source)
        installed_pallets (des.Resource): Installed pallets counter
    
    Yields:
        Simulation events: Picking up pallets and installation work
    """
    while True:
        # Get one pallet from site inventory
        yield worker.get(site_pallets, 1)
        # Perform installation work (1-1.5 hours per pallet)
        yield worker.do('install', dist.uniform(1, 1.5))
        # Add completed pallet to installed count
        yield worker.add(installed_pallets, 1)
        # Stop when target of 20,000 installed pallets is reached
        if installed_pallets.level() >= 20000:
            break


def worker2_process(worker, site_pallets, installed_pallets):
    """
    Worker 2 installation process.
    
    Worker 2 installs pallets with a slower rate (1.5-2 hours per pallet).
    Process continues until 20,000 pallets are installed.
    
    Args:
        worker (des.Entity): Worker 2 entity
        site_pallets (des.Resource): Site pallet inventory (source)
        installed_pallets (des.Resource): Installed pallets counter
    
    Yields:
        Simulation events: Picking up pallets and installation work
    """
    while True:
        # Get one pallet from site inventory
        yield worker.get(site_pallets, 1)
        # Perform installation work (1.5-2 hours per pallet)
        yield worker.do('install', dist.uniform(1.5, 2))
        # Add completed pallet to installed count
        yield worker.add(installed_pallets, 1)
        # Stop when target of 20,000 installed pallets is reached
        if installed_pallets.level() >= 20000:
            break

            
def worker3_process(worker, site_pallets, installed_pallets):
    """
    Worker 3 installation process.
    
    Worker 3 installs pallets with the same faster rate as Worker 1 (1-1.5 hours per pallet).
    Process continues until 20,000 pallets are installed.
    
    Args:
        worker (des.Entity): Worker 3 entity
        site_pallets (des.Resource): Site pallet inventory (source)
        installed_pallets (des.Resource): Installed pallets counter
    
    Yields:
        Simulation events: Picking up pallets and installation work
    """
    while True:
        # Get one pallet from site inventory
        yield worker.get(site_pallets, 1)
        # Perform installation work (1-1.5 hours per pallet, same as worker1)
        yield worker.do('install', dist.uniform(1, 1.5))
        # Add completed pallet to installed count
        yield worker.add(installed_pallets, 1)
        # Stop when target of 20,000 installed pallets is reached
        if installed_pallets.level() >= 20000:
            break

                        
# =============================================================================
# ENVIRONMENT SETUP - Initialize simulation entities and resources
# =============================================================================

# Create the discrete event simulation environment
env = des.Environment()

# Create factory entity (represents the production facility)
factory = des.Entity(env, 'factory')

# Define resources (queues/inventories) for the system:
# Factory pallet inventory - stores pallets before transport (max capacity: 10,000)
pallets = des.Resource(env, 'factory_pallet', init=0, capacity=10000)

# Site pallet inventory - stores pallets at installation site before installation (max: 10,000)
site_pallets = des.Resource(env, 'site_pallet', init=0, capacity=10000)

# Installed pallet counter - tracks total pallets successfully installed (max: 30,000)
installed_pallets = des.Resource(env, 'installed_pallet', init=0, capacity=30000)

# Create three worker entities for parallel installation work
worker1 = des.Entity(env, 'worker_1')
worker2 = des.Entity(env, 'worker_2')
worker3 = des.Entity(env, 'worker_3')

# Create two truck entities for parallel transportation
truck = env.create_entities('truck', 2)

# Tracking resources for damaged pallets (optional - for future damage simulation)
damage_pallets_site = des.Resource(env, "damage_pallets_site", 0)
damage_pallets_factory = des.Resource(env, "damage_pallets_factory", 0)


# =============================================================================
# PROCESS INSTANTIATION - Start all simulation processes
# =============================================================================

# Start pallet creation process at the factory
env.process(create_pallets(factory, pallets, damage_pallets_factory))

# Start truck 1 and truck 2 transportation processes
env.process(truck_process(truck[0], pallets, site_pallets, damage_pallets_site, damage_pallets_factory))
env.process(truck_process(truck[1], pallets, site_pallets, damage_pallets_site, damage_pallets_factory))

# Start worker processes and store process references to monitor completion
p1 = env.process(worker1_process(worker1, site_pallets, installed_pallets))
p2 = env.process(worker2_process(worker2, site_pallets, installed_pallets))
p3 = env.process(worker3_process(worker3, site_pallets, installed_pallets))


# =============================================================================
# RUN SIMULATION
# =============================================================================

# Run simulation until all workers complete their 20,000 pallet target
# (simulation runs until all worker processes are completed)
simpm.run(env, dashboard=False, until=p1 & p2 & p3)

# Display total simulation time (in hours)
print(f"\n{'='*60}")
print(f"SIMULATION COMPLETED")
print(f"{'='*60}")
print(f"Total time to install 20,000 pallets: {env.now:.2f} hours")
print(f"Approximately {env.now/24:.2f} days\n")


# =============================================================================
# ANALYSIS - Collect and analyze waiting times
# =============================================================================

# Collect waiting time statistics for each truck
truck_1_waiting_times = truck[0].waiting_time()
truck_2_waiting_times = truck[1].waiting_time()

# Collect waiting time statistics for workers
worker_1_waiting_times = worker1.waiting_time()
worker_2_waiting_times = worker2.waiting_time()

# Create empirical probability distributions from waiting time data
# (for visualization and statistical analysis)
truck_1_dist = dist.empirical(truck_1_waiting_times)
truck_2_dist = dist.empirical(truck_2_waiting_times)
worker_1_dist = dist.empirical(worker_1_waiting_times)
worker_2_dist = dist.empirical(worker_2_waiting_times)

# Generate probability distribution plots
print("Generating waiting time distribution plots...\n")

# Truck 1 waiting time distribution
fig1 = truck_1_dist.plot_pdf()
if fig1 is not None:
    fig1.suptitle('Truck 1 - Waiting Time Distribution', fontsize=14, fontweight='bold')
    fig1.axes[0].set_xlabel('Waiting Time (hours)', fontsize=12)
    fig1.axes[0].set_ylabel('Probability Density', fontsize=12)
    fig1.tight_layout()

# Truck 2 waiting time distribution
fig2 = truck_2_dist.plot_pdf()
if fig2 is not None:
    fig2.suptitle('Truck 2 - Waiting Time Distribution', fontsize=14, fontweight='bold')
    fig2.axes[0].set_xlabel('Waiting Time (hours)', fontsize=12)
    fig2.axes[0].set_ylabel('Probability Density', fontsize=12)
    fig2.tight_layout()

# Worker 1 waiting time distribution
fig3 = worker_1_dist.plot_pdf()
if fig3 is not None:
    fig3.suptitle('Worker 1 - Waiting Time Distribution', fontsize=14, fontweight='bold')
    fig3.axes[0].set_xlabel('Waiting Time (hours)', fontsize=12)
    fig3.axes[0].set_ylabel('Probability Density', fontsize=12)
    fig3.tight_layout()

# Worker 2 waiting time distribution
fig4 = worker_2_dist.plot_pdf()
if fig4 is not None:
    fig4.suptitle('Worker 2 - Waiting Time Distribution', fontsize=14, fontweight='bold')
    fig4.axes[0].set_xlabel('Waiting Time (hours)', fontsize=12)
    fig4.axes[0].set_ylabel('Probability Density', fontsize=12)
    fig4.tight_layout()



# =============================================================================
# RESULTS AND STATISTICS
# =============================================================================

print(f"{'='*60}")
print(f"WAITING TIME STATISTICS")
print(f"{'='*60}")

# Calculate and display average waiting times
avg_truck_1_waiting = sum(truck_1_waiting_times) / len(truck_1_waiting_times) if len(truck_1_waiting_times) > 0 else 0
avg_truck_2_waiting = sum(truck_2_waiting_times) / len(truck_2_waiting_times) if len(truck_2_waiting_times) > 0 else 0
avg_worker_1_waiting = sum(worker_1_waiting_times) / len(worker_1_waiting_times) if len(worker_1_waiting_times) > 0 else 0
avg_worker_2_waiting = sum(worker_2_waiting_times) / len(worker_2_waiting_times) if len(worker_2_waiting_times) > 0 else 0

print(f"\nTruck Statistics:")
print(f"  Truck 1 - Average waiting time: {avg_truck_1_waiting:.2f} hours")
print(f"  Truck 2 - Average waiting time: {avg_truck_2_waiting:.2f} hours")

print(f"\nWorker Statistics:")
print(f"  Worker 1 - Average waiting time: {avg_worker_1_waiting:.2f} hours")
print(f"  Worker 2 - Average waiting time: {avg_worker_2_waiting:.2f} hours")

print(f"\n{'='*60}")
print(f"SIMULATION ANSWER:")
print(f"It takes {env.now:.2f} hours to install 20,000 pallets")
print(f"{'='*60}\n")


# =============================================================================
# SIMULATION RESULTS SUMMARY
# =============================================================================
# 
# LATEST RUN RESULTS (Random Seed: 42):
# 
# Total Simulation Time: 9,448.33 hours (approximately 393.68 days or ~13 months)
#
# Truck Statistics:
#   - Truck 1 Average Waiting Time: 238.90 hours
#   - Truck 2 Average Waiting Time: 246.80 hours
#   - Note: Trucks have significant waiting time as they wait for pallets 
#           to be produced at the factory
#
# Worker Statistics:
#   - Worker 1 Average Waiting Time: 0.03 hours
#   - Worker 2 Average Waiting Time: 0.04 hours
#   - Note: Workers have minimal waiting time as pallets are continuously
#           being delivered by trucks
#
# KEY INSIGHTS:
# - The bottleneck in this system is pallet PRODUCTION at the factory
# - Trucks are waiting for pallets to be produced (high waiting times)
# - Workers are adequately supplied with pallets from truck deliveries
# - The two-truck system with relatively fast production (10 pallets every 
#   3-5 hours) creates a balanced flow to the installation site
#
# =============================================================================
# IMPORTANT: TO GET MORE ACCURATE RESULTS
# =============================================================================
#
# This is a SINGLE RUN of the simulation. To obtain statistically reliable
# and robust results, you should:
#
# 1. RUN MULTIPLE REPLICATIONS: Execute the simulation 20-50 times with 
#    different random seeds and analyze the mean and variance of results
#    
# 2. INCREASE CONFIDENCE INTERVALS: Calculate 95% confidence intervals 
#    for the total time and waiting statistics
#    
# 3. VALIDATE RESULTS: Compare simulation results with real-world data 
#    if available
#    
# 4. SENSITIVITY ANALYSIS: Test how results change when you vary:
#    - Truck capacity (currently 450 pallets)
#    - Travel times (currently 50-65 hours)
#    - Worker rates (currently 1-2 hours per pallet)
#    - Number of workers (currently 3)
#    - Production rate (currently 10 per 3-5 hours)
#
# 5. WARM-UP PERIOD: Consider implementing a warm-up period to allow 
#    the system to reach steady-state before collecting statistics
#
# RECOMMENDATION: Modify this script to run multiple replications and 
# collect statistics across all runs for more reliable conclusions.
#
# =============================================================================
