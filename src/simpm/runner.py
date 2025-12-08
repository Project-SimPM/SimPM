"""
High-level runner and dashboard integration for SimPM.

This module provides the public :func:`run` entry point that you typically
use as:

    >>> import simpm
    >>> import simpm.des as des
    >>> import simpm.dist as dist
    >>>
    >>> def env_factory():
    ...     env = des.Environment("My model")
    ...     # build the model on env ...
    ...     return env
    ...
    >>> all_envs = simpm.run(env_factory, number_runs=200, dashboard=True)

or, for a single pre-built environment:

    >>> env = des.Environment("Single run")
    >>> # build model ...
    >>> simpm.run(env, until=100, dashboard=True)

The actual event loop is handled by :meth:`simpm.des.Environment.run`,
which wraps :class:`simpy.Environment.run` and records per-run metadata.
"""

from __future__ import annotations

import sys
from typing import Any, Callable, List, Union

from .des import Environment
from .dashboard import run_post_dashboard

EnvOrFactory = Union[Environment, Callable[[], Environment]]


def run(
    env_or_factory: EnvOrFactory,
    *,
    until: float | None = None,
    dashboard: bool = False,
    dashboard_host: str = "127.0.0.1",
    dashboard_port: int = 8050,
    dashboard_async: bool | None = None,
    number_runs: int = 1,
    **env_run_kwargs: Any,
) -> Union[Environment, List[Environment]]:
    """
    Run one or many SimPM simulations.

    Parameters
    ----------
    env_or_factory :
        Either

        * a ready-made :class:`simpm.des.Environment` instance, or
        * a *factory* callable with signature ``() -> Environment`` that
          builds a fresh environment for each replication.

    until :
        Optional simulation end time passed to :meth:`Environment.run`.

    dashboard :
        If True, launch the Streamlit dashboard after the run(s) complete.
        For multi-run experiments, the dashboard is currently bound to the
        **last** environment in the sequence.

    dashboard_host, dashboard_port :
        Address and port for the dashboard server.

    dashboard_async :
        Whether to start the Streamlit process asynchronously.

        * If None (default): synchronous on Windows, async elsewhere.
        * If True: start Streamlit in a background process where supported.
        * If False: blocking call (post-run launch).

    number_runs :
        Number of independent replications to execute when a factory is used.
        If ``env_or_factory`` is a concrete Environment, this must be 1.

    **env_run_kwargs :
        Additional keyword arguments forwarded to :meth:`Environment.run`
        (e.g. ``until=...``). The ``num_runs`` keyword is reserved and will
        be set automatically based on ``number_runs``.

    Returns
    -------
    Environment or list[Environment]
        * A single Environment when running once on a concrete env.
        * A list of Environments when ``number_runs > 1`` and a factory
          is used.

    Notes
    -----
    - :meth:`Environment.run` always executes **one** event loop and records
      per-run metadata in ``run_history`` and ``finishedTime``, together with
      a ``run_id`` derived from ``run_number``.
    - In the factory-based multi-run case, this function:
        * calls the factory ``number_runs`` times,
        * passes ``num_runs=number_runs`` as a *hint* to each run,
        * lets your recorder/dashboard use ``run_id``/``num_runs`` metadata.
    """
    if "num_runs" in env_run_kwargs:
        raise TypeError(
            "The 'num_runs' keyword is reserved by simpm.run and is set "
            "automatically based on 'number_runs'. Please remove it from "
            "env_run_kwargs."
        )

    if number_runs < 1:
        raise ValueError("number_runs must be >= 1")

    # Default dashboard_async behaviour:
    # - On Windows: synchronous (safer for Streamlit)
    # - Elsewhere: async
    if dashboard_async is None:
        dashboard_async = not sys.platform.startswith("win")

    # ------------------------------------------------------------------
    # Case 1: user passed a concrete Environment instance
    # ------------------------------------------------------------------
    if isinstance(env_or_factory, Environment):
        if number_runs != 1:
            raise ValueError(
                "number_runs > 1 requires an environment *factory*; "
                "you passed a concrete Environment instance."
            )

        env: Environment = env_or_factory

        run_kwargs = dict(env_run_kwargs)
        if until is not None:
            run_kwargs["until"] = until

        # Hint for observers/dashboard: planned total number of runs
        run_kwargs.setdefault("num_runs", number_runs)

        env.run(**run_kwargs)

        if dashboard:
            run_post_dashboard(
                env,
                host=dashboard_host,
                port=dashboard_port,
                start_async=dashboard_async,
            )

        return env

    # ------------------------------------------------------------------
    # Case 2: user passed a factory callable () -> Environment
    # ------------------------------------------------------------------
    if not callable(env_or_factory):
        raise TypeError(
            "First argument to simpm.run must be either an Environment "
            "or a factory callable () -> Environment."
        )

    factory: Callable[[], Environment] = env_or_factory
    all_envs: List[Environment] = []

    for i in range(number_runs):
        env = factory()
        if not isinstance(env, Environment):
            raise TypeError(
                f"env_factory() must return simpm.des.Environment, "
                f"got {type(env)!r} on run {i + 1}."
            )

        run_kwargs = dict(env_run_kwargs)
        if until is not None:
            run_kwargs["until"] = until

        # Planned total number of runs is passed as a hint
        run_kwargs.setdefault("num_runs", number_runs)

        env.run(**run_kwargs)
        all_envs.append(env)

    if dashboard and all_envs:
        # For now, show the dashboard for the last replication.
        run_post_dashboard(
            all_envs[-1],
            host=dashboard_host,
            port=dashboard_port,
            start_async=dashboard_async,
        )

    return all_envs
