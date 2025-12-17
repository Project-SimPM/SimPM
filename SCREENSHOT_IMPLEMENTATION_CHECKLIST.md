DASHBOARD SCREENSHOTS - IMPLEMENTATION CHECKLIST
==================================================

Use this checklist to systematically add screenshots to the dashboard documentation.

PREPARATION
===========

□ Set up test scenario
  - Create/run a simulation that produces rich output
  - Recommendation: Use the earthmoving example (simple, clear results)
  - Ensure entities have waiting periods (shows waiting log)
  - Ensure resources have queue buildup (shows queue behavior)

□ Create image directory
  - Run: mkdir -p docs/source/tutorials/images/dashboard

□ Verify dashboard is working
  - Run your simulation with simpm.run(env, dashboard=True)
  - Ensure all sections load and display data

SCREENSHOT CAPTURE (In Order)
=============================

OVERVIEW SECTION
================
□ Capture: 01-overview.png
  - URL: http://localhost:8501
  - What to show: 
    * SimPM logo (if present)
    * "Overview" heading
    * Environment metric
    * Run selector dropdown/metric
  - Expected height: ~250px
  - Tips: 
    * If multiple runs, show dropdown expanded
    * Show value clearly
    * Include padding around metrics

SIMULATION RUNS SECTION
=======================
□ Capture: 02-simulation-runs-table.png
  - What to show: 
    * "Simulation runs" heading
    * Table tab (active)
    * Table with columns: run_id, simulation_time
    * Download icon in top-left corner
    * First 5 rows visible
  - Expected height: ~200px
  - Tips:
    * Make sure download icon is visible
    * Show at least 2-3 rows
    * Include column headers

□ Capture: 03-simulation-runs-stats.png
  - What to show:
    * "Simulation runs" heading
    * Statistics tab (active)
    * Table with: Count, Mean, Median, Min, Max, Std
    * At least 2-3 rows of data
  - Expected height: ~150px
  - Tips:
    * Make sure values are visible
    * Ensure column headers are clear

□ Capture: 04-simulation-runs-histogram.png
  - What to show:
    * Histogram graph of simulation times
    * X-axis label (simulation_time)
    * Y-axis label (count)
    * Multiple bars showing distribution
    * Legend (if any)
  - Expected height: ~400px
  - Tips:
    * Zoom in slightly so bars are visible
    * Include full graph frame
    * Show axis labels clearly

□ Capture: 05-simulation-runs-boxplot.png
  - What to show:
    * Box plot graph
    * Box with quartiles
    * Median line visible
    * Whiskers showing range
    * Y-axis label (simulation_time)
  - Expected height: ~400px
  - Tips:
    * Position so box is in center
    * Include full graph frame

NAVIGATION SECTION
==================
□ Capture: 06-navigation-tabs.png
  - What to show:
    * Three radio buttons: Entities, Resources, Activity
    * Styled buttons with background/border
    * One button selected (e.g., Entities)
  - Expected height: ~80px
  - Tips:
    * Show full width of all three buttons
    * Make selection obvious
    * Show just the button row, exclude content below

ENTITIES VIEW
=============

Schedule Table
□ Capture: 07-entity-schedule-table.png
  - What to show:
    * "Entities" view (active tab)
    * Entity selector dropdown (showing selected entity)
    * "Schedule" heading (## Schedule)
    * "Showing the first X rows" caption
    * Table with columns: start_time, finish_time, duration, activity_name/id
    * Download icon visible
    * At least 3-4 rows
  - Expected height: ~250px
  - Tips:
    * Show entity name in dropdown clearly
    * Make sure all column headers visible
    * Include download icon

Schedule Time Series
□ Capture: 08-entity-schedule-timeseries.png
  - What to show:
    * Schedule section with "Time series" tab (active)
    * Line graph showing activity durations over time
    * X-axis: time or index
    * Y-axis: duration
    * Range slider at bottom
    * Legend (if any)
  - Expected height: ~450px
  - Tips:
    * Show full graph including range slider
    * Make sure axis labels are visible
    * Line should be clearly visible (not too dense)

Schedule Histogram
□ Capture: 09-entity-schedule-histogram.png
  - What to show:
    * Schedule section with "Histogram" tab (active)
    * Bar chart showing distribution of durations
    * Multiple bars with varying heights
    * X-axis: duration value
    * Y-axis: frequency
  - Expected height: ~450px
  - Tips:
    * Show full histogram with clear distribution
    * Ensure axes labeled
    * Bars should be well-distributed (not all in one bar)

Waiting Log
□ Capture: 10-entity-waiting-log.png
  - What to show:
    * "Waiting log" heading (## Waiting log)
    * Metric selector dropdown (showing "waiting_duration" or similar)
    * Waiting log table with columns: start_waiting, end_waiting, waiting_duration
    * At least 2-3 rows
    * "Statistics" / "Histogram" / "Box plot" tabs visible
  - Expected height: ~300px
  - Tips:
    * Show metric selector dropdown clearly
    * Show table and first tab
    * Include table header

Status Log (if available)
□ Capture: 11-entity-status-log-timeseries.png
  - What to show:
    * "Status log" section (if it appears in your simulation)
    * Metric selector (e.g., "busy"/"idle" or similar)
    * "Time series" tab (active)
    * Step graph showing status changes
    * X-axis: time
    * Y-axis: status value
    * Range slider visible
  - Expected height: ~450px
  - Tips:
    * Step graph should show clear jumps at status changes
    * Show full graph with slider
    * Make axis labels visible
  - NOTE: Only capture if your simulation logs status changes

RESOURCES VIEW
==============

Queue Log
□ Capture: 12-resource-queue-log.png
  - What to show:
    * "Resources" view (active tab)
    * Resource selector dropdown (showing selected resource)
    * "Queue log" heading
    * Queue log table with columns: entity_id, start_time, finish_time, waiting_duration
    * Metric selector dropdown (showing a metric option)
    * At least 3-4 rows
    * "Statistics" / "Histogram" / "Box plot" tabs visible
  - Expected height: ~300px
  - Tips:
    * Show resource name in dropdown clearly
    * Show metric selector
    * Include table header
    * Make waiting_duration column visible

Status Log - Time Series
□ Capture: 13-resource-status-log-timeseries.png
  - What to show:
    * "Status log" section for resource
    * Metric selector (e.g., "in_use", "idle", "queue_length")
    * "Time series" tab (active)
    * Step graph showing metric changes over time
    * X-axis: time
    * Y-axis: metric value (number)
    * Range slider at bottom
  - Expected height: ~450px
  - Tips:
    * Step graph should show clear jumps when metric changes
    * Multiple steps show dynamic behavior
    * Show full graph with slider
    * Make axis labels visible

Status Log - Histogram
□ Capture: 14-resource-status-log-histogram.png
  - What to show:
    * Status log section with "Histogram" tab (active)
    * Bar chart showing time-weighted distribution
    * X-axis: metric value
    * Y-axis: frequency
    * Multiple bars showing distribution
  - Expected height: ~450px
  - Tips:
    * Show full histogram
    * Bars should show interesting distribution (not all in one)
    * Axes should be clearly labeled

ACTIVITY VIEW
=============

Unified Activity Log
□ Capture: 15-activity-view-table.png
  - What to show:
    * "Activity" view (active tab)
    * "Activity" or activity table section heading
    * Large table with columns: time/start_time, entity_name, activity_name, source, etc.
    * Download icon visible
    * At least 5-8 rows showing mix of activity types
    * "Showing the first X rows" caption
  - Expected height: ~300px
  - Tips:
    * Show diverse activity types (entity schedule, waiting, queue, etc.)
    * Make download icon visible
    * Ensure column headers are clear
    * Show mix of different sources if available

FILE ORGANIZATION
=================

After capturing all images:

□ Verify all 15 images exist in docs/source/tutorials/images/dashboard/
  - 01-overview.png
  - 02-simulation-runs-table.png
  - 03-simulation-runs-stats.png
  - 04-simulation-runs-histogram.png
  - 05-simulation-runs-boxplot.png
  - 06-navigation-tabs.png
  - 07-entity-schedule-table.png
  - 08-entity-schedule-timeseries.png
  - 09-entity-schedule-histogram.png
  - 10-entity-waiting-log.png
  - 11-entity-status-log-timeseries.png (optional if no status log)
  - 12-resource-queue-log.png
  - 13-resource-status-log-timeseries.png
  - 14-resource-status-log-histogram.png
  - 15-activity-view-table.png

□ Verify image quality
  - PNG format (lossless)
  - ~1200px width minimum
  - Clear and readable text
  - Good contrast

DOCUMENTATION UPDATES
=====================

□ Open docs/source/tutorials/dashboard-guide.rst

□ Find section: "Overview Section"
  Add after "Run ID Selector" subsection:
  
  .. image:: images/dashboard/01-overview.png
     :alt: Dashboard overview showing environment and run selector
     :width: 90%

□ Find section: "Simulation Runs Section"
  Add to "Table Tab" subsection:
  
  .. image:: images/dashboard/02-simulation-runs-table.png
     :alt: Simulation runs table preview with download button
     :width: 90%

  Add to "Statistics Tab" subsection:
  
  .. image:: images/dashboard/03-simulation-runs-stats.png
     :alt: Simulation runs statistics table
     :width: 90%

  Add to "Histogram Tab" subsection:
  
  .. image:: images/dashboard/04-simulation-runs-histogram.png
     :alt: Distribution of simulation times as histogram
     :width: 90%

  Add to "Box Plot Tab" subsection:
  
  .. image:: images/dashboard/05-simulation-runs-boxplot.png
     :alt: Simulation times as box plot with quartiles
     :width: 90%

□ Find section: "Navigation Section"
  Add after subsection text:
  
  .. image:: images/dashboard/06-navigation-tabs.png
     :alt: Navigation tabs for Entities, Resources, and Activity views
     :width: 90%

□ Find section: "Entities View"
  Under "Schedule Section", after the subsection heading:
  
  .. image:: images/dashboard/07-entity-schedule-table.png
     :alt: Entity schedule table showing activities and timing
     :width: 90%

  Under "Time series" visualization description:
  
  .. image:: images/dashboard/08-entity-schedule-timeseries.png
     :alt: Time series graph of activity durations with range slider
     :width: 90%

  Under "Histogram" visualization description:
  
  .. image:: images/dashboard/09-entity-schedule-histogram.png
     :alt: Histogram showing distribution of activity durations
     :width: 90%

  Under "Waiting Log Section" heading:
  
  .. image:: images/dashboard/10-entity-waiting-log.png
     :alt: Entity waiting log table with metric selector
     :width: 90%

  Under "Status Log Section" heading (if present in your docs):
  
  .. image:: images/dashboard/11-entity-status-log-timeseries.png
     :alt: Step graph showing entity status changes over simulation time
     :width: 90%

□ Find section: "Resources View"
  Under "Queue Log Section":
  
  .. image:: images/dashboard/12-resource-queue-log.png
     :alt: Resource queue log showing waiting times and entities
     :width: 90%

  Under "Status Log Section", after intro text:
  
  .. image:: images/dashboard/13-resource-status-log-timeseries.png
     :alt: Step graph of resource in-use, idle, and queue length metrics
     :width: 90%

  For histogram subsection:
  
  .. image:: images/dashboard/14-resource-status-log-histogram.png
     :alt: Time-weighted histogram of resource utilization
     :width: 90%

□ Find section: "Activity View"
  After subsection heading:
  
  .. image:: images/dashboard/15-activity-view-table.png
     :alt: Unified activity log showing all events across the simulation
     :width: 90%

VERIFICATION
============

□ Rebuild documentation
  cd docs
  make html

□ Check for build errors
  - Look for "image not found" warnings
  - Verify all images render in HTML output

□ Open in browser
  - Open docs/_build/html/tutorials/dashboard-guide.html
  - Scroll through and verify:
    ✓ All images appear
    ✓ Images are properly sized
    ✓ Captions display correctly
    ✓ No broken references

□ Visual review
  - Images match their sections
  - Images are clear and readable
  - Layout looks professional
  - Images enhance understanding

TESTING
=======

□ Test HTML documentation
  - Open in Chrome, Firefox, Safari
  - Verify responsive on mobile
  - Check image quality

□ Test PDF generation (optional)
  make latexpdf
  - Verify images print properly
  - Check spacing

FINALIZATION
============

□ Create image credit/attribution file (if needed)
  docs/source/tutorials/images/dashboard/README.md

□ Commit all changes
  git add docs/source/tutorials/images/dashboard/
  git add docs/source/tutorials/dashboard-guide.rst
  git commit -m "Add dashboard screenshots and visual guide"

□ Document in changelog/release notes

DONE! 🎉
========

Your dashboard documentation is now complete with:
✅ Comprehensive text explanations
✅ Visual screenshots for each section
✅ Clear layout and navigation
✅ Perfect for new users learning the dashboard

