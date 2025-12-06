"""User-facing entry point for executing simulations.

The :func:`run` helper mirrors ``env.run`` while optionally capturing data for
the Streamlit dashboard. Using it keeps existing scripts compatible with the
new dashboard experience without changing simulation code.
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
    """Run a simulation environment and optionally start the dashboard.

    Parameters
    ----------
    env : simpm.des.Environment
        Simulation environment to execute.
    until : Any, optional
        End condition passed directly to ``env.run`` (for example a timestamp
        or callable).
    dashboard : bool, default True
        When ``True`` a Streamlit dashboard is spawned after execution; when
        ``False`` the helper behaves like ``env.run``.
    collect_logs : bool, default True
        Collect entity/resource logs for dashboard rendering. Set to ``False``
        when you want dashboard UI without detailed event logs.
    host : str, default "127.0.0.1"
        Address used when starting the dashboard server.
    port : int, default 8050
        TCP port used when starting the dashboard server.
    **kwargs : Any
        Additional keyword arguments forwarded to ``env.run``.

    Returns
    -------
    Any | dict
        The original result from ``env.run`` when ``dashboard`` is ``False`` or
        log collection is disabled. When logs are collected, the returned value
        is a JSON-ready dictionary snapshot of the run for dashboard reuse.

    Examples
    --------
    Run a simulation without the dashboard::

        simpm.run(env, until=100, dashboard=False)

    Run and immediately open the dashboard on a custom port::

        simpm.run(env, until=200, host="0.0.0.0", port=8080)
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
