"""User-facing entry point for running simulations with an optional dashboard.

``simpm.run`` simply forwards to ``env.run`` when dashboards are disabled, so
existing scripts that call ``env.run`` continue to work. Use this wrapper when
you want to launch the post-run dashboard without changing your simulation
code.
"""
from __future__ import annotations

from typing import Any

from simpm.dashboard_data import collect_run_data


def run(
    env,
    until: Any | None = None,
    dashboard: bool = True,
    collect_logs: bool = True,
    host: str = "127.0.0.1",
    port: int = 8050,
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
    host, port: str, int
        Binding information for the dashboard server.
    kwargs:
        Additional arguments forwarded to ``env.run``.
    """
    if not isinstance(dashboard, bool):
        raise ValueError("dashboard must be a boolean")

    result = env.run(until=until, **kwargs)

    if not dashboard:
        return result

    from simpm.dashboard import run_post_dashboard  # imported lazily to keep dependency optional

    snapshot = collect_run_data(env) if collect_logs else None
    if snapshot is not None:
        run_post_dashboard(snapshot, host=host, port=port, start_async=False)
        return snapshot.as_dict()
    return result
