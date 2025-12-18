Architecture & Visualizations
=============================

This page provides visual representations of SimPM's structure, class hierarchies, and component relationships.

.. contents:: On this page
   :local:

SimPM Architecture
------------------

The following diagram shows the core components of SimPM and how they interact:

.. graphviz::

   digraph SimPM_Architecture {
       graph [rankdir=LR, bgcolor=white, splines=ortho];
       node [shape=box, style="filled,rounded", fillcolor=lightblue, margin="0.3,0.2"];
       edge [color=gray];
       
       // Core modules
       Environment [label="Environment\n(Simulation Clock)", fillcolor=lightcoral, fontcolor=white, fontweight=bold];
       Entity [label="Entity\n(Agents/Items)", fillcolor=lightblue];
       Resource [label="Resource\n(Capacity Pools)", fillcolor=lightyellow];
       Distribution [label="Distribution\n(Random Variables)", fillcolor=lightcyan];
       
       // Process management
       Process [label="Process\n(Generator Functions)", fillcolor=lightgray];
       Event [label="Event Queue\n(Event Scheduler)", fillcolor=lightpink];
       
       // Logging & Output
       Recorder [label="Recorder\n(Data Collection)", fillcolor=lightyellow];
       Dashboard [label="Dashboard\n(Streamlit UI)", fillcolor=lightgreen];
       Logger [label="Logger Config\n(Log Management)", fillcolor=lightsteelblue];
       
       // Relationships
       Environment -> Entity [label="creates\ninstances"];
       Environment -> Resource [label="manages"];
       Environment -> Process [label="schedules"];
       Environment -> Event [label="drives"];
       
       Entity -> Process [label="runs"];
       Entity -> Resource [label="requests"];
       Entity -> Recorder [label="records to"];
       
       Resource -> Recorder [label="logs state"];
       Distribution -> Entity [label="provides\ndurations"];
       
       Recorder -> Dashboard [label="feeds data"];
       Recorder -> Logger [label="configured by"];
   }

**Key Components:**

- **Environment** – Central simulation engine that manages time and events
- **Entity** – Agents that execute processes and interact with resources
- **Resource** – Shared capacities that entities compete for (crews, equipment, etc.)
- **Distribution** – Probabilistic models for durations and quantities
- **Process** – Generator functions that define entity lifecycles
- **Event Queue** – Priority queue that drives simulation forward
- **Recorder** – Collects and logs simulation data
- **Dashboard** – Interactive web interface for visualization
- **Logger** – Centralized logging configuration

Class Hierarchy
---------------

The following diagram shows the relationship between SimPM's main classes:

.. graphviz::

   digraph SimPM_ClassHierarchy {
       graph [rankdir=TB, bgcolor=white];
       node [shape=box, style="filled", fillcolor=lightblue, margin="0.3,0.2"];
       edge [arrowhead=empty, style=bold];
       
       // Base class
       SimObject [label="SimObject\n(Base Class)", fillcolor=lightcoral, fontcolor=white, fontweight=bold];
       
       // Main classes
       Environment [label="Environment\n(Simulation World)", fillcolor=lightcoral];
       Entity [label="Entity\n(Agents)"];
       Resource [label="Resource\n(Basic Capacity)", fillcolor=lightyellow];
       
       // Resource variants
       PriorityResource [label="PriorityResource\n(Priority Queuing)", fillcolor=lightgreen];
       PreemptiveResource [label="PreemptiveResource\n(Preemptive)", fillcolor=lightgreen];
       GeneralResource [label="GeneralResource\n(Generic Wrapper)", fillcolor=lightsteelblue];
       
       // Inheritance relationships
       SimObject -> Environment;
       SimObject -> Entity;
       SimObject -> Resource;
       
       Resource -> PriorityResource;
       Resource -> PreemptiveResource;
       Resource -> GeneralResource;
   }

**Class Descriptions:**

- **SimObject** – Base class for all simulation objects
- **Environment** – Container and clock for simulation
- **Entity** – Items/agents that move through the system
- **Resource** – FIFO capacity with queue management
- **PriorityResource** – Resources with priority-based queue ordering
- **PreemptiveResource** – High-priority tasks can interrupt low-priority ones
- **GeneralResource** – Generic wrapper for custom resource types

Simulation Workflow
-------------------

The typical workflow for creating and running a SimPM simulation:

.. graphviz::

   digraph SimPM_Workflow {
       graph [rankdir=TB, bgcolor=white];
       node [shape=box, style="filled", fillcolor=lightblue, margin="0.3,0.2"];
       edge [color=gray];
       
       Start [shape=ellipse, label="Start\nSimulation Design", fillcolor=lightgreen, fontweight=bold];
       
       Step1 [label="1. Create Environment\n\nenv = des.Environment('Project Name')"];
       Step2 [label="2. Define Resources\n\nloader = des.Resource(env, 'loader')\ntrucks = des.Resource(env, 'trucks')"];
       Step3 [label="3. Create Entities\n\nentities = env.create_entities('truck', 10)"];
       Step4 [label="4. Define Processes\n\ndef process(entity, resource):\n    yield entity.get(resource)\n    yield entity.do('work', duration)\n    yield entity.put(resource)"];
       Step5 [label="5. Schedule Processes\n\nenv.process(process(...))"];
       Step6 [label="6. Run Simulation\n\nsimpm.run(env, dashboard=True)"];
       Step7 [label="7. Analyze Results\n\nresults = entity.schedule()\nutils = resource.average_utilization()"];
       
       End [shape=ellipse, label="End\nReview & Iterate", fillcolor=lightgreen, fontweight=bold];
       
       Start -> Step1 -> Step2 -> Step3 -> Step4 -> Step5 -> Step6 -> Step7 -> End;
       
       // Styling
       Step1 [fillcolor=lightcyan];
       Step2 [fillcolor=lightyellow];
       Step3 [fillcolor=lightcyan];
       Step4 [fillcolor=lightyellow];
       Step5 [fillcolor=lightcyan];
       Step6 [fillcolor=lightyellow, fontweight=bold];
       Step7 [fillcolor=lightgreen];
   }

Data Flow
---------

How data flows through SimPM during a simulation:

.. graphviz::

   digraph SimPM_DataFlow {
       graph [rankdir=LR, bgcolor=white];
       node [shape=box, style="filled", margin="0.3,0.2"];
       edge [color=gray];
       
       // Input
       UserCode [label="User Code\n(Simulation Definition)", shape=note, fillcolor=lightyellow];
       
       // Processing
       Environment [label="Environment\n(Event Processing)", fillcolor=lightcoral, fontcolor=white];
       Entities [label="Entities\n(Process Execution)", fillcolor=lightblue];
       Resources [label="Resources\n(Queue Management)", fillcolor=lightyellow];
       
       // Recording
       Recorder [label="Recorder\n(Data Collection)", fillcolor=lightsteelblue];
       ScheduleLog [label="Schedule Log\n(Activities)", shape=database, fillcolor=lightgray];
       QueueLog [label="Queue Log\n(Waits)", shape=database, fillcolor=lightgray];
       StatusLog [label="Status Log\n(States)", shape=database, fillcolor=lightgray];
       
       // Output
       Dashboard [label="Dashboard\n(Visualization)", fillcolor=lightgreen];
       CSVExport [label="CSV Export\n(Data Analysis)", shape=note, fillcolor=lightgreen];
       
       // Flow
       UserCode -> Environment;
       Environment -> Entities;
       Environment -> Resources;
       
       Entities -> Recorder;
       Resources -> Recorder;
       
       Recorder -> ScheduleLog;
       Recorder -> QueueLog;
       Recorder -> StatusLog;
       
       ScheduleLog -> Dashboard;
       QueueLog -> Dashboard;
       StatusLog -> Dashboard;
       
       Dashboard -> CSVExport;
   }

Module Dependencies
-------------------

Here's an overview of the main SimPM modules and their dependencies:

**Core Modules:**

- :mod:`simpm.des` – Discrete-event simulation engine
  
  - Environment
  - Entity
  - Resource variants (Resource, PriorityResource, PreemptiveResource)
  
- :mod:`simpm.dist` – Probability distributions
  
  - Triangular, Normal, Exponential, Beta, etc.
  - Supports 3-point and PERT estimates

- :mod:`simpm.recorder` – Data recording and logging
  
  - Entity schedule logging
  - Resource queue logging
  - Status change logging

- :mod:`simpm.dashboard` – Interactive web interface
  
  - Streamlit-based visualization
  - CSV export functionality
  - Multiple run support

- :mod:`simpm.log_cfg` – Centralized logging configuration
  
  - Console and file logging setup
  - Log level management

**Typical Import Pattern:**

.. code-block:: python

   import simpm
   import simpm.des as des
   import simpm.dist as dist
   
   # Create simulation environment
   env = des.Environment("My Project")
   
   # Define resources with logging
   loader = des.Resource(env, "loader", log=True)
   
   # Create entities
   trucks = env.create_entities("truck", 10, log=True)
   
   # Define stochastic durations
   load_time = dist.triang(5, 7, 9)
   
   # Run with dashboard
   simpm.run(env, dashboard=True)

Key Design Patterns
-------------------

**1. Generator-based Processes**

SimPM uses Python generators to define entity processes:

.. code-block:: python

   def truck_process(truck, loader, dumped_dirt):
       while True:
           # Wait for resource
           yield truck.get(loader, 1)
           
           # Perform activity
           yield truck.do("loading", 7)
           
           # Release resource
           yield truck.put(loader, 1)
           
           # Output to inventory
           yield truck.add(dumped_dirt, 60)

**2. Dictionary-like Attributes**

Entities support arbitrary metadata:

.. code-block:: python

   truck["load_size"] = 40
   truck["priority"] = 2
   truck["wbs_code"] = "A-123"
   
   # Access in process
   def process(entity, resource):
       duration = 5 + entity["load_size"] / 20
       yield entity.do("loading", duration)

**3. Time-weighted Statistics**

Resource and entity status logs are weighted by duration:

.. code-block:: python

   # Time-weighted average utilization
   loader.average_utilization()
   
   # Time-weighted statistics
   loader.status_log().describe()

**4. Composable Resources**

Multiple resource types for different scenarios:

.. code-block:: python

   # FIFO queue
   basic_res = des.Resource(env, "basic")
   
   # Priority queue
   priority_res = des.PriorityResource(env, "priority")
   
   # Preemptive (can interrupt)
   preempt_res = des.PreemptiveResource(env, "preempt")

See Also
--------

- :doc:`../getting-started` – Quick start guide
- :doc:`../concepts/project-modeling` – Conceptual overview
- :doc:`../api_reference/index` – Complete API reference
- :doc:`../tutorials/index` – Detailed tutorials
