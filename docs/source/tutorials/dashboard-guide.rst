04 – Dashboard Guide
====================

.. contents:: On this page
   :local:

Overview
--------

The SimPM dashboard is an interactive Streamlit-based web interface for visualizing and analyzing discrete-event simulation results. 
It provides comprehensive insights into entity behavior, resource utilization, and activity timelines across single or multiple simulation runs.

Starting the Dashboard
----------------------

To launch the dashboard after a simulation run, pass the ``dashboard=True`` parameter to :func:`simpm.run`:

.. code-block:: python

   import simpm
   import simpm.des as des

   env = des.Environment("My Project")
   # ... setup your simulation ...
   
   simpm.run(env, dashboard=True)  # Opens the dashboard automatically

The dashboard will open in your default web browser, typically at ``http://localhost:8501``.

Dashboard Layout
----------------

The dashboard is organized into four main sections:

1. **Overview** – Environment metadata and run selection
2. **Simulation Runs** – Execution time statistics across all runs
3. **Navigation** – Tabs to switch between Entities, Resources, and Activity views
4. **Content Views** – Detailed analysis for the selected tab

Overview Section
^^^^^^^^^^^^^^^^

**Environment Metric**
  Displays the name of your simulation environment (set when you create the ``Environment`` object).

**Run ID Selector**
  
  - If your simulation contains only a single run, the Run ID is displayed as a metric.
  - If multiple runs exist (e.g., from Monte Carlo simulations), a dropdown menu lets you:
    
    - Select **"All runs"** to view aggregated statistics
    - Select a specific **Run ID** to filter all visualizations to that run

This selector is persistent across all views, so switching between Entities, Resources, and Activity always respects your run filter.

Simulation Runs Section
^^^^^^^^^^^^^^^^^^^^^^^

This section shows aggregated execution statistics across all runs (or a filtered run if selected).

**Table Tab**
  Displays a preview of simulation run metadata including:
  
  - ``run_id`` – Unique identifier for each run
  - ``simulation_time`` – Total wall-clock or simulation duration

  Use the download button in the top-left to export the full table as CSV.

**Statistics Tab**
  Shows key metrics for simulation times:
  
  - **Count** – Number of runs
  - **Mean** – Average simulation time
  - **Median** – Middle value (robust to outliers)
  - **Min/Max** – Fastest and slowest runs
  - **Std** – Standard deviation (variability)

**Histogram Tab**
  Visualizes the distribution of simulation times as a bar chart.
  Helps identify whether execution times are consistent or highly variable.

**Box Plot Tab**
  Displays quartiles, median, and outliers in a compact format.
  The box spans the 25th–75th percentile; the line inside is the median; whiskers extend to min/max.

Navigation Section
^^^^^^^^^^^^^^^^^^^

After the Simulation Runs section, three tabs appear:

- **Entities** – Schedules, waiting times, and activity logs per entity
- **Resources** – Queue lengths, utilization, and status history per resource
- **Activity** – Unified event feed of all activities across the simulation

Select a tab to switch views. Your run filter (selected in the Overview) persists across all views.

Entities View
^^^^^^^^^^^^^

This view provides per-entity analysis:

**Entity Selector**
  A dropdown to choose which entity to analyze. For simulations with many entities, 
  search or scroll to find the one you want.

**Schedule Section**
  Table preview of the entity's activity timeline:
  
  - ``start_time`` – When the activity began
  - ``finish_time`` – When the activity ended
  - ``duration`` – How long the activity took
  - ``activity_name`` or ``activity_id`` – What the entity was doing
  - Additional columns depend on your logged metadata
  
  **Visualizations:**
  
  - **Statistics** – Summary (count, mean, median, min, max, std dev) for activity durations
  - **Time series** – Line graph showing activity durations over simulation time (includes range slider for zoom)
  - **Histogram** – Distribution of activity durations across all activities in the schedule
  - **Box plot** – Quartile-based summary of activity duration distribution

**Waiting Log Section**
  Displays periods when the entity was blocked waiting for a resource:
  
  - ``start_waiting`` – When the entity began waiting
  - ``end_waiting`` – When the wait ended
  - ``waiting_duration`` – Total time spent waiting
  
  **Metric Selector:**
    Choose which metric to visualize: waiting duration, start time, or finish time.
  
  **Visualizations:**
  
  - **Statistics** – Summary statistics for the selected waiting metric
  - **Histogram** – Distribution showing how often each waiting duration occurs
  - **Box plot** – Quartile summary of waiting times

**Status Log Section** (if enabled)
  Shows entity status changes over time (availability, busy/idle, etc.):
  
  - ``time`` – Simulation time of the status change
  - ``status`` – Current state (e.g., "busy", "idle")
  
  **Metric Selector:**
    Choose which status metric to analyze (options depend on logged data).
  
  **Visualizations:**
  
  - **Statistics** – Time-weighted statistics (values weighted by how long each state lasted)
  - **Time series** – Step graph showing status changes throughout the simulation
  - **Histogram** – Time-weighted distribution of how much simulation time was spent in each state
  - **Box plot** – Time-weighted quartile summary

Resources View
^^^^^^^^^^^^^^^

This view provides per-resource analysis:

**Resource Selector**
  A dropdown to choose which resource to analyze (e.g., loader, dumping site, equipment).

**Queue Log Section**
  Tracks requests waiting for or using the resource:
  
  - ``resource_id`` – Identifier of the resource
  - ``entity_id`` – Which entity made the request
  - ``start_time`` – When the request began waiting
  - ``finish_time`` – When the request was fulfilled
  - ``waiting_duration`` – Queue time (``finish_time - start_time``)
  
  **Metric Selector:**
    Choose between waiting duration, start time, or finish time.
  
  **Visualizations:**
  
  - **Statistics** – Summary of the selected metric
  - **Histogram** – Shows how many requests experienced each waiting duration
  - **Box plot** – Quartile breakdown of waiting times

**Status Log Section**
  Tracks resource state changes (in-use, idle, queue length, etc.):
  
  - ``time`` – Simulation time
  - ``in_use`` – Number of units currently in use
  - ``idle`` – Number of available units
  - ``queue_length`` – Entities waiting for the resource
  
  **Metric Selector:**
    Choose which status metric to visualize.
  
  **Visualizations:**
  
  - **Statistics** – Time-weighted statistics for the selected metric
  - **Time series** – Step graph showing how the metric changed over time
  - **Histogram** – Time-weighted distribution (e.g., how much time the resource was fully utilized)
  - **Box plot** – Time-weighted quartile summary

Activity View
^^^^^^^^^^^^^

This view presents a unified, searchable feed of all activities across the entire simulation:

**Activity Table**
  Consolidated log combining:
  
  - Entity schedules (what each entity did and when)
  - Entity waiting logs (when entities were blocked)
  - Resource queue logs (who waited for each resource)
  - Environment and custom logs (any other events)
  
  **Columns typically include:**
  
  - ``run_id`` – Run identifier (if multiple runs)
  - ``time`` or ``start_time`` – When the activity occurred
  - ``entity_name`` / ``entity_id`` – The entity involved
  - ``activity_name`` / ``activity_id`` – The activity or event type
  - ``source`` – Whether the log came from an entity, resource, or environment
  - Additional columns from your custom logging

  Use the download button to export the entire activity log as CSV for further analysis in spreadsheets or data science tools.

Understanding the Visualizations
---------------------------------

Time Series Graphs
^^^^^^^^^^^^^^^^^^

**Purpose:** Show how a metric evolves over simulation time.

**Interactive features:**
  
  - Hover over points to see exact values and times
  - Use the range slider at the bottom to zoom into specific time periods
  - Double-click to reset the view

**Step graphs** (used for status/queue length):
  The line jumps instantly when a status change occurs, reflecting discrete-event behavior.

**Line graphs** (used for durations and timings):
  Connect points linearly, useful for spotting trends and anomalies.

Histograms
^^^^^^^^^^

**Purpose:** Show the distribution (frequency) of a metric's values.

**Reading the graph:**
  
  - X-axis: Metric value (e.g., duration in minutes)
  - Y-axis: Frequency (number of times that value or range occurred)
  - Tall bars = common values; short bars = rare values
  - Shape indicates distribution type: symmetric bell = normal; skewed = imbalanced (e.g., many short waits, few long waits)

**Use cases:**
  
  - Identify bottlenecks: If most activity durations cluster at a certain value, you've found a constraint
  - Check variability: A wide histogram suggests unpredictable behavior; a narrow one suggests consistency

Box Plots
^^^^^^^^^

**Purpose:** Summarize distribution using quartiles in a compact format.

**Reading the plot:**
  
  - **Box** (colored rectangle): Middle 50% of data (25th to 75th percentile)
  - **Line inside box**: Median (50th percentile, the middle value)
  - **Whiskers** (lines extending from box): Extend to minimum and maximum (or to 1.5× interquartile range)
  - **Dots beyond whiskers**: Outliers (unusually high or low values)

**Use cases:**
  
  - Compare distributions side-by-side (if your dashboard adds multiple resources)
  - Spot asymmetry: If the median line is off-center, the distribution is skewed
  - Identify outliers: Points beyond the whiskers suggest unusual events

Statistics Tables
^^^^^^^^^^^^^^^^^

**Displayed metrics:**
  
  - **Count**: Number of data points
  - **Mean**: Average value
  - **Median**: Middle value (50th percentile)
  - **Min**: Smallest value
  - **Max**: Largest value
  - **Std**: Standard deviation (how spread out values are; higher = more variability)

**Time-weighted statistics** (used for status logs):
  Each value is weighted by its duration. For example, if a resource was idle for 100 minutes 
  and busy for 10 minutes, the time-weighted average state is ~91% idle. Regular averages would 
  give equal weight to each measurement, incorrectly suggesting 50–50 busy/idle.

Exporting Data
--------------

**CSV Download Buttons**
  Most table sections include a download icon (📥) in the top-left corner.
  Clicking it exports the full data as a CSV file for use in:
  
  - Excel or Google Sheets (pivot tables, charts)
  - Python/R (advanced analysis, additional visualizations)
  - Custom reporting tools

**Activity Log Export**
  Export the entire activity log from the Activity view for comprehensive post-processing.

Tips & Troubleshooting
----------------------

No Data in a Section
^^^^^^^^^^^^^^^^^^^^^

**Cause:** The metric was not logged during the simulation.

**Solution:** When creating entities or resources, ensure ``log=True``:

.. code-block:: python

   truck = des.Entity(env, name="truck", log=True)
   loader = des.Resource(env, name="loader", log=True)

Empty Visualizations
^^^^^^^^^^^^^^^^^^^^^

**Cause:** The selected metric has no valid numeric values.

**Solution:** Check that your log columns contain numbers (not text or missing values).

Dashboard Freezes or Runs Slowly
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause:** Very large simulations (millions of events) can overwhelm the browser.

**Solution:**
  
  - Export the data to CSV and use Python/R for custom analysis
  - Use the Activity view's search/filter features (if available) to focus on a subset
  - Consider running a smaller scenario to prototype visualizations

Multiple Runs
^^^^^^^^^^^^^

**Overview**
  If you ran multiple simulations (e.g., Monte Carlo or sensitivity analysis), the dashboard aggregates results.

**Using the Run Selector**
  
  - Select **"All runs"** to see aggregate statistics (mean, distribution across all runs)
  - Select a **specific Run ID** to zoom into that run's details

**Statistics interpretation**
  
  - Histogram with narrow distribution = consistent results across runs (stable model)
  - Histogram with wide spread = high variability between runs (check for stochasticity, sensitivity)

Advanced Usage
--------------

Logging Custom Metrics
^^^^^^^^^^^^^^^^^^^^^^

To log additional metrics beyond the standard schedule, waiting, and status logs:

.. code-block:: python

   # Log custom data
   truck.log(category="custom_event", data={"load_amount": 60, "truck_id": truck.id})

These custom logs will appear in the Activity view with your metadata.

Analyzing Results Externally
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Export CSV data and use pandas/matplotlib for deeper analysis:
