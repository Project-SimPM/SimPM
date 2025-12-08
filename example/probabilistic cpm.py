"""
@author: Naimeh Sadeghi
Probabilistic CPM example with priorities using SimPM.

- Activities have stochastic durations (triangular / normal / fixed).
- All activities share a limited PriorityResource.
- Lower PRIORITY values => higher priority for resources.
- We run the model multiple times via `simpm.run(env_factory, number_runs=...)`.

Author: Naimeh Sadeghi
"""

import simpm
import simpm.des as des
import simpm.dist as dist


def env_factory() -> des.Environment:
    """Build and return ONE fresh CPM environment with priorities."""

    # Data mirrors example/test_cpm.py
    DURATIONS = [
        dist.triang(2, 3, 4),   # activity 0
        dist.triang(1, 3, 5),   # activity 1
        5,                      # activity 2 (deterministic)
        1,                      # activity 3
        dist.triang(3.5, 5, 6), # activity 4
        4,                      # activity 5
        dist.norm(2.5, 1),      # activity 6
    ]
    RESOURCES  = [1, 3, 2, 3, 1, 2, 2]
    PRIORITIES = [1, 2, 1, 1, 3, 1, 1]  # lower = higher priority

    # 1) Create the simulation environment
    env = des.Environment("Probabilistic CPM with priorities")

    # 2) Create entities (one per activity).
    #    Logging is off for entities here; we mainly care about total project time.
    tasks = env.create_entities("task", len(DURATIONS), print_actions=False, log=False)

    # 3) Define a shared prioritized resource pool with 4 units.
    pool = des.PriorityResource(env, "total_resources", init=4, print_actions=False, log=False)

    # 4) Define the activity process.
    def run_task(i: int, prereq=None):
        # Wait for predecessors if any
        if prereq is not None:
            yield prereq

        # Request RESOURCES[i] units with PRIORITIES[i]
        # PriorityResource.get(entity, amount, priority)
        yield tasks[i].get(pool, RESOURCES[i], PRIORITIES[i])

        # Perform the work with stochastic duration; Entity.do supports distributions
        yield tasks[i].do(f"activity-{i}", DURATIONS[i])

        # Release the resources
        yield tasks[i].put(pool, RESOURCES[i])

    # 5) Define CPM precedence relationships:
    #
    #   0 -> (1, 2)
    #   1 -> (3, 4)
    #   2 -> (3, 5)
    #   3, 4, 5 -> 6
    #
    p0 = env.process(run_task(0))
    p1 = env.process(run_task(1, prereq=p0))
    p2 = env.process(run_task(2, prereq=p0))
    p3 = env.process(run_task(3, prereq=(p1 & p2)))
    p4 = env.process(run_task(4, prereq=p1))
    p5 = env.process(run_task(5, prereq=p2))
    # Final activity 6 waits for 3, 4, and 5 to finish
    p6 = env.process(run_task(6, prereq=(p3 & p4 & p5)))

    # Return the configured environment (not yet run)
    return env



all_envs = simpm.run(env_factory, dashboard=True, number_runs=200)

# Example: print first and last run durations from run_history
first = all_envs[0].run_history[-1]["duration"]
last = all_envs[-1].run_history[-1]["duration"]
print(f"First run duration: {first:.2f}")
print(f"Last  run duration: {last:.2f}")
