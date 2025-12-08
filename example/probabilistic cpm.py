import numpy as np

import simpm
import simpm.des as des
import simpm.dist as dist
from simpm.dashboard import run_post_dashboard
from simpm.dashboard_data import RunSnapshot

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
RESOURCES = [1, 3, 2, 3, 1, 2, 2]
PRIORITIES = [1, 2, 1, 1, 3, 1, 1]

def simulate_once(seed: int) -> float:
    """Run one CPM-like schedule and return total duration (env.now)."""
    np.random.seed(seed)
    env = des.Environment(f"Run {seed}")

    # We don't need detailed logs here; we're mainly interested in total time
    tasks = env.create_entities("task", len(DURATIONS), print_actions=False, log=False)
    pool = des.PriorityResource(env, "totalres", init=4, print_actions=False, log=False)

    def run_task(i: int, prereq=None):
        if prereq is not None:
            yield prereq
        yield tasks[i].get(pool, RESOURCES[i], PRIORITIES[i])
        yield tasks[i].do(f"activity-{i}", DURATIONS[i])
        yield tasks[i].put(pool, RESOURCES[i])

    p0 = env.process(run_task(0))
    p1 = env.process(run_task(1, p0))
    p2 = env.process(run_task(2, p0))
    p3 = env.process(run_task(3, p1 & p2))
    p4 = env.process(run_task(4, p1))
    p5 = env.process(run_task(5, p2))
    p6 = env.process(run_task(6, p4 & p5 & p3))

    # Just run the environment; don't launch the dashboard here
    env.run()
    return env.now


# --- Run many trials and collect durations + dashboard logs ---

NUM_RUNS = 200
durations: list[float] = []
logs: list[dict] = []

for seed in range(NUM_RUNS):
    total_time = simulate_once(seed)
    durations.append(total_time)

    # One log event per run, in the format expected by _simulation_time_df
    logs.append(
        {
            "time": 0.0,  # not important for histogram; can be 0
            "source_type": "environment",
            "source_id": "CPM-MonteCarlo",
            "message": "Simulation run finished",
            "metadata": {
                "run_id": seed,                  # this is what the run dropdown will use
                "simulation_time": float(total_time),
            },
        }
    )

# Percentiles as before
p50, p80, p95 = np.percentile(durations, [50, 80, 95])
print(f"Median completion: {p50:.2f}h")
print(f"P80 completion: {p80:.2f}h")
print(f"P95 completion: {p95:.2f}h")

# --- Build aggregate snapshot for the dashboard ---

snapshot = RunSnapshot(
    environment={
        "name": "CPM Monte Carlo example",
        "run_id": None,  # we rely on per-event run_id instead
        "time": {"start": None, "end": None},
        # if in your local dashboard_data you also added "simulation_runs",
        # it's fine to omit it here; the dashboard uses logs + metadata.
    },
    entities=[],   # not needed for this example
    resources=[],  # not needed for this example
    logs=logs,
)

# Launch the dashboard once, with all runs included
run_post_dashboard(snapshot, host="127.0.0.1", port=8050, start_async=False)
