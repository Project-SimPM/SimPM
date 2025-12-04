"""User-facing entry point for running simulations with optional dashboards.

``simpm.run`` simply forwards to ``env.run`` when dashboards are disabled, so
existing scripts that call ``env.run`` continue to work. Use this wrapper when
you want to launch the live or post-run dashboard without changing your
simulation code.
"""
from __future__ import annotations

from typing import Any

from simpm.recorder import RunRecorder, StreamingRunRecorder


def run(env, until: Any | None = None, dashboard: str = "none", collect_logs: bool = True, host: str = "127.0.0.1", port: int = 8050, **kwargs):
    """
    Execute a simulation environment and optionally launch a dashboard.

    Parameters
    ----------
    env: simpm.des.Environment
        Simulation environment to execute.
    until: optional
        Passed directly to ``env.run``.
    dashboard: str
        One of ``"none"``, ``"post"``, or ``"live"``.
    collect_logs: bool
        Whether to collect log events for dashboards.
    host, port: str, int
        Binding information for the dashboard server.
    kwargs:
        Additional arguments forwarded to ``env.run``.
    """
    mode = dashboard.lower()
    recorder = None

    if mode not in {"none", "post", "live"}:
        raise ValueError("dashboard must be one of 'none', 'post', or 'live'")

    if mode == "none":
        return env.run(until=until, **kwargs)

    if mode == "post":
        from simpm.dashboard import run_post_dashboard  # imported lazily to keep dependency optional

        recorder = RunRecorder(collect_logs=collect_logs)
        env.register_observer(recorder)
        env.run(until=until, **kwargs)
        run_post_dashboard(recorder.run_data, host=host, port=port)
        return recorder.run_data

    # live mode
    from simpm.dashboard import run_live_dashboard  # imported lazily to keep dependency optional

    recorder = StreamingRunRecorder(collect_logs=collect_logs)
    env.register_observer(recorder)
    run_live_dashboard(recorder.run_data, recorder.event_queue, host=host, port=port)
    env.run(until=until, **kwargs)
    return recorder.run_data
