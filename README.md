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

Subpackages:
- des (discrete event simulation)
- dists (probability distributions) modules

## Using SimPM
Getting started quickly:
```
pip install simpm
```

### Dashboard mode
SimPM can visualize runs in a Plotly Dash dashboard. Install the optional dependencies and run your environment with ``dashboard`` set to ``"post"`` to launch an interactive summary once the simulation finishes:

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
