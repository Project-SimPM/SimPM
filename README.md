# SimPM - Simulation Tool in Project Management

![Github Workflow Deploy Package](https://img.shields.io/github/actions/workflow/status/Project-SimPM/SimPM/python-publish.yml?label=deploy)
[![Documentation Status](https://readthedocs.org/projects/simpm/badge/?version=latest)](https://simpm.readthedocs.io/en/latest/?badge=latest)
![Github Release Version](https://img.shields.io/github/v/release/Project-SimPM/SimPM)
![PyPi Package Version](https://img.shields.io/pypi/v/simpm)
![Github Release Date](https://img.shields.io/github/release-date/Project-SimPM/SimPM)
![PyPi Package Downloads](https://img.shields.io/pypi/dm/simpm)
![Github License](https://img.shields.io/github/license/Project-SimPM/SimPM)
![Github Issues](https://img.shields.io/github/issues/Project-SimPM/SimPM)
![Github Pull Requests](https://img.shields.io/github/issues-pr/Project-SimPM/SimPM)

SimPM offers a discrete event simulation library for project management in Python.

## Relationship to SimPy

SimPM follows the same process-based discrete-event simulation style as
libraries like [SimPy](https://simpy.readthedocs.io/): you describe system
behaviour with Python functions that yield waiting times and resource
requests, and the engine advances simulation time and orders events.

You do **not** need to know or install SimPy to use SimPM. SimPM is a
self-contained toolkit inspired by that style, but focused on project and
construction management.

On top of a general DES core, SimPM adds:

- **Project-oriented modeling** – entities as activities or work items, resources as crews or equipment.
- **Schedule-friendly distributions** (`simpm.dist`) – triangular, beta, trapezoidal, normal, exponential, uniform, and empirical, suitable for three-point estimates and Monte Carlo schedule risk.
- **Automatic tabular logging** – events, queue lengths, utilization, and project duration ready for analysis with pandas and plotting.
- **Optional dashboards** – `simpm.run(..., dashboard="post"|"live"|"none")` to explore timelines, queues, and bottlenecks in Plotly Dash.
- **Central logging config** – `simpm.log_cfg.LogConfig` to control console/file logging across multiple runs.

The goal is to cut boilerplate around questions like: *How long will this project take, how uncertain is it, and where are the bottlenecks?*

Subpackages:
- des (discrete event simulation)
- dists (probability distributions) modules

## Using SimPM
Getting started quickly:
```
pip install simpm
```

### Dashboard mode
``simpm.run`` is a convenience wrapper around ``env.run`` that optionally starts a dashboard after (or during) execution. You can continue to call ``env.run`` directly for headless runs; switch to ``simpm.run`` when you want dashboards without changing your simulation logic. Install the optional dependencies and run your environment with ``dashboard`` set to ``"post"`` to launch an interactive summary once the simulation finishes:

```
pip install simpm[dash]

import simpm.des as des
import simpm

env = des.Environment()
worker = env.create_entities("worker", 1, log=True)[0]
machine = des.Resource(env, "machine", init=1, capacity=1, log=True)

def job(entity, resource):
    yield entity.get(resource, 1)
    yield entity.do("work", 2)
    yield entity.put(resource, 1)

env.process(job(worker, machine))

simpm.run(env, dashboard="post", host="127.0.0.1", port=8050)
```

Use ``dashboard="live"`` to watch the simulation progress in real time, or ``dashboard="none"`` to disable the dashboard entirely.
## Community
- [Github Discussions](https://github.com/Project-SimPM/SimPM/discussions)

## Contributing back to SimPM
If you run into an issue, please file a new [issue](https://github.com/Project-SimPM/SimPM/issues) for us to discuss. If possible, follow up with a pull request.

If you would like to add a feature, please reach out via [issue](https://github.com/Project-SimPM/SimPM/issues). A feature is most likely to be added if you build it!
