from __future__ import annotations

import sys
from typing import Any, Callable, List, Union

from .des import Environment
from .dashboard import run_post_dashboard


def run(
    env_or_factory: Union[Environment, Callable[[], Environment]],
    *,
    until: float | None = None,
    dashboard: bool = False,
    host: str = "127.0.0.1",
    port: int = 8050,
    start_async: bool | None = None,
    number_runs: int = 1,
    **kwargs: Any,
):
    """Run one or many SimPM simulations.

    Parameters
    ----------
    env_or_factory:
        Either

        - a ready-made :class:`simpm.des.Environment` instance, or
        - a *factory* callable with signature ``() -> Environment`` that
          builds a fresh environment for each replication.

    until:
        Optional simulation end time passed to :meth:`Environment.run`.

    dashboard:
        If True, launch the Streamlit dashboard after the run(s).

    host, port:
        Address and port for the dashboard server.

    start_async:
        If True, start Streamlit in a background process.
        If None (default), uses False on Windows and True on other platforms.

    number_runs:
        Number of independent replications to execute when a factory is used.
        If ``env_or_factory`` is a concrete Environment, this must be 1.

    **kwargs:
        Additional keyword arguments forwarded to :meth:`Environment.run`.

    Returns
    -------
    Environment or list[Environment]
        - A single Environment when running once.
        - A list of Environments when ``number_runs > 1`` and a factory is used.
    """
    # Decide default async behaviour based on platform
    if start_async is None:
        start_async = not sys.platform.startswith("win")

    # --- Case 1: user passed a concrete Environment -------------------------
    if isinstance(env_or_factory, Environment):
        if number_runs != 1:
            raise ValueError("number_runs > 1 requires an environment *factory*; " "you passed a concrete Environment instance.")

        env: Environment = env_or_factory

        env_run_kwargs = dict(kwargs)
        if until is not None:
            env_run_kwargs["until"] = until

        # Hint for observers/dashboard: planned total number of runs
        env_run_kwargs.setdefault("num_runs", number_runs)

        env.run(**env_run_kwargs)

        if dashboard:
            run_post_dashboard(env, host=host, port=port, start_async=start_async)

        return env

    # --- Case 2: user passed a factory callable -----------------------------
    if not callable(env_or_factory):
        raise TypeError("First argument to simpm.run must be either an Environment " "or a factory callable () -> Environment.")

    if number_runs < 1:
        raise ValueError("number_runs must be >= 1")

    factory: Callable[[], Environment] = env_or_factory
    all_envs: List[Environment] = []

    for i in range(number_runs):
        env = factory()
        if not isinstance(env, Environment):
            raise TypeError(f"env_factory() must return simpm.des.Environment, " f"got {type(env)!r} on run {i + 1}.")

        env_run_kwargs = dict(kwargs)
        if until is not None:
            env_run_kwargs["until"] = until

        # Pass planned total number of runs as hint to Environment.run
        env_run_kwargs.setdefault("num_runs", number_runs)

        # Ensure each environment uses a unique run_id that matches the
        # replication index when running many times from a factory.
        env.run_number = i

        env.run(**env_run_kwargs)
        all_envs.append(env)

    if dashboard:
        # NEW: pass all environments so the dashboard can aggregate runs
        run_post_dashboard(all_envs, host=host, port=port, start_async=start_async)

    return all_envs
