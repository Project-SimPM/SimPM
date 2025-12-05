"""User-facing entry point for running simulations with an optional dashboard.

``simpm.run`` simply forwards to ``env.run`` when dashboards are disabled, so
existing scripts that call ``env.run`` continue to work. Use this wrapper when
you want to launch the post-run dashboard without changing your simulation
code.
"""
from __future__ import annotations

import platform
from typing import Any

from simpm.dashboard_data import collect_run_data


def run(
    env,
    until: Any | None = None,
    dashboard: bool = True,
    collect_logs: bool = True,
    host: str = "127.0.0.1",
    port: int = 8050,
    dashboard_async: bool | None = None,
    **kwargs,
):
    """
    Execute a simulation environment and optionally launch a dashboard.

    Parameters
    ----------
    env: simpm.des.Environment
        Simulation environment to execute.
    until: optional
        Passed directly to ``env.run``.
    dashboard: bool
        ``True`` (default) launches the post-run dashboard; ``False`` skips it.
    collect_logs: bool
        Whether to collect log events for dashboards.
    dashboard_async: bool | None
        Launch dashboards asynchronously when ``True`` (default on non-Windows platforms).
        Windows defaults to synchronous dashboards to avoid background thread signal issues.
    host, port: str, int
        Binding information for the dashboard server.
    kwargs:
        Additional arguments forwarded to ``env.run``.
    """
    if not isinstance(dashboard, bool):
        raise ValueError("dashboard must be a boolean")

    if dashboard_async is None:
        # Streamlit installs signal handlers that fail when launched from background threads
        # on some platforms (notably Windows). Default to synchronous dashboards there.
        dashboard_async = platform.system() != "Windows"

    if not dashboard:
        return env.run(until=until, **kwargs)

    from simpm.dashboard import run_post_dashboard  # imported lazily to keep dependency optional

    if dashboard_async:
        # Start the dashboard at the beginning of the simulation to allow live updates.
        run_post_dashboard(env, host=host, port=port, start_async=True)
        env.run(until=until, **kwargs)
    else:
        # Run the simulation first, then launch the dashboard in the main thread to
        # avoid signal issues on platforms that disallow signal handlers in workers.
        env.run(until=until, **kwargs)
        run_post_dashboard(env, host=host, port=port, start_async=False)
    return collect_run_data(env).as_dict()
