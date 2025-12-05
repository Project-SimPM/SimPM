==================================================
``simpm.dashboard`` --- Dashboard helper components
==================================================

``simpm.dashboard`` provides Plotly Dash dashboards for SimPM runs. Use
``simpm.run(..., dashboard=True|False)`` to launch a post-run dashboard
without wiring up Dash yourself. Advanced users can also call the dashboard
helpers directly when they already manage the environment.

Usage
-----

.. code-block:: python

   import simpm

   # After running a simulation, open the post-run dashboard
   simpm.run(project, dashboard=True)

   # Expert users may call the dashboard helpers directly
   # simpm.dashboard.run_post_dashboard(project)

.. currentmodule:: simpm.dashboard

.. autosummary::
   :toctree: generated/
   :nosignatures:

   run_post_dashboard
   build_app

.. automodule:: simpm.dashboard
   :members: run_post_dashboard, build_app
   :undoc-members:
   :show-inheritance:
