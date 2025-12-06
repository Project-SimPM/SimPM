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

SimPM - Simulation Tool in Project Management
============================================

SimPM is a discrete-event simulation library for modelling projects, construction operations,
and other resource-constrained workflows in Python.

It is designed to help you answer questions like:

- How long will this project or work package take?
- How much variability is there in the completion time?
- Where are the bottlenecks in crews, equipment, or workspaces?

What is SimPM?
--------------

SimPM uses a process-based discrete-event simulation engine: you describe activities,
resources, and logic using plain Python, and the environment advances simulation time
while handling queues, waiting, and resource constraints.

The focus is **project and construction management**:
activities are tasks or work items, resources are crews, equipment, or workspaces,
and you can run scenarios or experiments to explore “what-if” questions.

Typical use cases include:

- Schedule risk analysis and Monte Carlo simulations.
- Evaluating different crew allocations or equipment plans.
- Studying queues and waiting times at critical resources.
- Comparing alternative construction methods or phasing plans.

Key capabilities
----------------

SimPM builds a project-oriented layer on top of a general DES core:

- **Project-oriented modelling**

  - Entities as activities or work items.
  - Resources as crews, equipment, or workspaces with capacities, priorities, and (optionally) preemption.

- **Schedule-friendly probability distributions** (`simpm.dist`)

  - Triangular, beta, trapezoidal, normal, exponential, uniform, and empirical distributions.
  - Well suited to three-point estimates and Monte Carlo schedule risk analysis.

- **Automatic tabular logging**

  - Events, queue lengths, waiting times, resource utilization, and project duration.
  - Logs are stored in pandas-friendly tables, ready for further analysis and plotting.

- **Optional dashboards**

  - `simpm.run(..., dashboard=True|False)` for Plotly Dash dashboards (enabled by default).
  - Inspect timelines, queues, and bottlenecks interactively after a run completes.

- **Central logging configuration**

  - `simpm.log_cfg.LogConfig` to control console and file logging for single runs or large experiments.

Relationship to SimPy
---------------------

SimPM follows the same process-based discrete-event simulation style popularized by libraries
like SimPy, but it is a **self-contained** toolkit focused on project and construction management.

You do **not** need to install or know SimPy to use SimPM: you work directly with `simpm.des`,
`simpm.dist`, and the higher-level project modelling and dashboard features described above.

## Using SimPM
Getting started quickly:
```
pip install simpm
```

### Dashboard mode
``simpm.run`` is a convenience wrapper around ``env.run`` that optionally starts a dashboard after execution. You can continue to call ``env.run`` directly for headless runs; switch to ``simpm.run`` when you want dashboards without changing your simulation logic. Install the optional dependencies and run your environment with dashboards enabled (the default) to launch an interactive summary once the simulation finishes:

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

simpm.run(env, dashboard=True, host="127.0.0.1", port=8050)
```

Use ``dashboard=False`` to disable the dashboard entirely.
## Community
- [Github Discussions](https://github.com/Project-SimPM/SimPM/discussions)

## Contributing back to SimPM
If you run into an issue, please file a new [issue](https://github.com/Project-SimPM/SimPM/issues) for us to discuss. If possible, follow up with a pull request.

If you would like to add a feature, please reach out via [issue](https://github.com/Project-SimPM/SimPM/issues). A feature is most likely to be added if you build it!

## Building the documentation locally
The documentation is built with Sphinx. Install the doc requirements and the project itself in editable mode so autodoc can import SimPM:

```
pip install -r docs/requirements.txt
pip install -e .
```

Then generate the HTML output:

- Linux/macOS: `make -C docs html` or `python -m sphinx -b html docs/source docs/_build/html`
- Windows (Command Prompt, without `make`): `docs\make.bat html` or `set PYTHONPATH=src && python -m sphinx -b html docs/source docs/_build/html`
- Windows (PowerShell, without `make`): `./docs/make.bat html` or `$env:PYTHONPATH="src"; python -m sphinx -b html docs/source docs/_build/html`

Open `docs/_build/html/index.html` in your browser to preview the rendered site.
