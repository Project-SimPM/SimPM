"""Streamlit dashboard for SimPM runs."""

from __future__ import annotations

import argparse
import base64
import json
import logging
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from numbers import Integral
from pathlib import Path
from typing import Any, Callable, Iterable, List

import pandas as pd
import plotly.express as px

try:  # pragma: no cover - handled at runtime
    import streamlit as st
except ImportError as exc:  # pragma: no cover - handled at runtime
    raise ImportError("Streamlit is required for dashboard mode. Install with `pip install streamlit plotly`.") from exc

from simpm.dashboard_data import RunSnapshot, collect_run_data

logger = logging.getLogger(__name__)

_ACTIVE_DASHBOARD: "StreamlitDashboard | None" = None
DEFAULT_DECIMAL_DIGITS = 3


# ---------------------------------------------------------------------------
# Helpers for run IDs and simulation time
# ---------------------------------------------------------------------------


def _find_time_column(df: pd.DataFrame) -> str | None:
    """Return the first column name that looks like a simulation time axis."""
    for col in df.columns:
        if "time" in str(col).lower():
            return col
    return None


def _basic_statistics(series: pd.Series) -> pd.DataFrame:
    """Return a dataframe with basic stats for a numeric column."""
    if series.empty:
        return pd.DataFrame()
    return pd.DataFrame(
        {
            "Count": [int(series.count())],
            "Mean": [series.mean()],
            "Median": [series.median()],
            "Min": [series.min()],
            "Max": [series.max()],
            "Std": [series.std(ddof=0)],
        }
    )


def _extract_run_id_from_event(event: dict[str, Any], env_run_id: Any = None) -> Any:
    """Extract run_id from a log event, falling back to the environment run_id."""
    if "run_id" in event and event["run_id"] is not None:
        return event["run_id"]
    metadata = event.get("metadata") or {}
    if "run_id" in metadata and metadata["run_id"] is not None:
        return metadata["run_id"]
    return env_run_id


def _available_runs(environment: dict[str, Any], logs: list[dict[str, Any]]) -> list[Any]:
    """Collect all distinct run IDs from environment metadata and logs."""
    run_ids: set[Any] = set()

    # Prefer run_history if present (Monte Carlo aggregation)
    for rh in environment.get("run_history") or []:
        rid = rh.get("run_id")
        if rid is not None:
            run_ids.add(rid)

    # Fallback to environment + log events
    if not run_ids:
        env_run_id = environment.get("run_id")
        if env_run_id is not None:
            run_ids.add(env_run_id)

        for event in logs or []:
            rid = _extract_run_id_from_event(event, environment.get("run_id"))
            if rid is not None:
                run_ids.add(rid)

    return sorted(run_ids, key=lambda v: str(v))


def _standardize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Sort dataframe by run_id (if present), move run_id right after index, and reset index.
    
    This ensures consistent column ordering and sorting across all log displays.
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Sort by run_id if it exists, preserving other sort orders within each run
    if "run_id" in df.columns:
        df = df.sort_values(by="run_id", ignore_index=False)
        
        # Move run_id to be the first column (right after implicit index)
        cols = [col for col in df.columns if col != "run_id"]
        df = df[["run_id"] + cols]
    
    # Reset index to make it clean
    df = df.reset_index(drop=True)
    
    return df


def _simulation_time_df(environment: dict[str, Any], logs: list[dict[str, Any]]) -> pd.DataFrame:
    """Build a dataframe with per-run finish times (simulation end times).

    We first look at ``environment["run_history"]`` (the canonical source),
    and fall back to synthetic log entries that have ``category="simulation_time"``.
    """
    records: list[dict[str, Any]] = []

    # Preferred: environment["run_history"]
    for rh in environment.get("run_history") or []:
        run_id = rh.get("run_id")
        end_time = rh.get("end_time")
        if run_id is None or end_time is None:
            continue
        try:
            sim_val = float(end_time)
        except (TypeError, ValueError):
            continue
        records.append({"run_id": run_id, "finish_time": sim_val})

    # Fallback: look into logs (older / alternative recorders)
    if not records:
        env_run_id = environment.get("run_id")
        for event in logs or []:
            sim_time = None
            if event.get("category") == "simulation_time":
                sim_time = event.get("time")
            else:
                metadata = event.get("metadata") or {}
                sim_time = metadata.get("simulation_time")

            if sim_time is None:
                continue

            run_id = _extract_run_id_from_event(event, env_run_id)
            try:
                sim_val = float(sim_time)
            except (TypeError, ValueError):
                continue
            records.append({"run_id": run_id, "finish_time": sim_val})

    return pd.DataFrame.from_records(records)


def _get_decimal_digits() -> int:
    """Return the configured decimal precision for numeric displays."""
    return int(st.session_state.get("simpm_decimal_digits", DEFAULT_DECIMAL_DIGITS))


def _format_id_value(value: Any) -> Any:
    """Format an identifier value without decimals."""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass

    if isinstance(value, Integral):
        return int(value)
    try:
        float_val = float(value)
    except (TypeError, ValueError):
        return value
    return int(float_val)


def _format_numeric_value(value: Any, digits: int) -> Any:
    """Format non-identifier numeric values with the configured precision."""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass

    if isinstance(value, Integral):
        return value

    try:
        float_val = float(value)
    except (TypeError, ValueError):
        return value

    if float_val.is_integer():
        return int(float_val)
    formatted = f"{float_val:.{digits}f}".rstrip("0").rstrip(".")
    return formatted


def _format_dataframe_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of the dataframe with IDs and numerics formatted for display."""
    display_df = df.copy()
    digits = _get_decimal_digits()
    id_cols = [col for col in display_df.columns if "id" in str(col).lower()]

    # Format ID-like columns without decimals
    for col in id_cols:
        display_df[col] = display_df[col].apply(_format_id_value)

    # Detect numeric columns
    numeric_cols: list[str] = []
    for col in display_df.columns:
        if col in id_cols:
            continue

        try:
            converted = pd.to_numeric(display_df[col])
        except (TypeError, ValueError):
            continue
        else:
            if pd.api.types.is_numeric_dtype(converted):
                display_df[col] = converted
                numeric_cols.append(col)

    for col in numeric_cols:
        display_df[col] = display_df[col].apply(lambda val: _format_numeric_value(val, digits))

    return display_df


def _format_attributes_inline(attributes: dict[str, Any]) -> str:
    """Format an attributes mapping into an inline text representation."""
    parts: list[str] = []
    for key, value in attributes.items():
        if isinstance(value, str):
            if value.strip().startswith("dist.") or "(" in value:
                formatted = value
            else:
                formatted = f'"{value}"'
        elif isinstance(value, (dict, list)):
            formatted = json.dumps(value, ensure_ascii=False)
        else:
            formatted = str(value)
        parts.append(f"{key}={formatted}")
    return ", ".join(parts)


def _render_compact_table(df: pd.DataFrame, *, caption: str | None = None) -> None:
    """Render a compact HTML table similar to the log previews."""
    if df.empty:
        st.info("No data available to display.")
        return

    html = _format_dataframe_for_display(df).to_html(index=False, escape=False)
    st.markdown(
        "<div class='simpm-table-wrapper simpm-compact-table'>" f"{html}" "</div>",
        unsafe_allow_html=True,
    )
    if caption:
        st.caption(caption)


def _render_numeric_analysis(df: pd.DataFrame, time_col: str | None = None) -> None:
    """Render analysis tabs for a selected numeric column in the dataframe."""
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty:
        st.info("No numeric columns available for analysis.")
        return

    col = _compact_selectbox(
        "Numeric column",
        options=list(numeric_df.columns),
    )
    time_axis = time_col or _find_time_column(df.drop(columns=[col], errors="ignore"))
    st.markdown(f"#### {col}")
    tab_stats, tab_series, tab_hist, tab_box = st.tabs(["Statistics", "Time series", "Histogram", "Box plot"])

    with tab_stats:
        stats_df = _basic_statistics(df[col])
        _render_compact_table(stats_df)

    with tab_series:
        x = df[time_axis] if time_axis and time_axis in df.columns else df.index
        fig = px.line(x=x, y=df[col], labels={"x": time_axis or "Index", "y": col})
        fig.update_traces(line_color="#3a7859")
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, width="stretch")

    with tab_hist:
        fig = px.histogram(df, x=col, nbins=min(30, max(5, len(df))))
        fig.update_traces(marker_color="#5bbd89")
        st.plotly_chart(fig, width="stretch")

    with tab_box:
        fig = px.box(df, y=col)
        fig.update_traces(marker_color="#3a7859")
        st.plotly_chart(fig, width="stretch")


def _asset_base64(name: str) -> str | None:
    """Return a base64 string for the given asset file if it exists."""
    asset_path = Path(__file__).resolve().parent / "assets" / name
    if not asset_path.exists():
        return None
    return base64.b64encode(asset_path.read_bytes()).decode("utf-8")


def _render_table_preview(
    title: str,
    df: pd.DataFrame,
    key_prefix: str,
    *,
    show_index: bool = True,
    indent_table_for_icon: bool = False,
) -> None:
    """Render a table preview with a download button."""
    # Standardize dataframe: sort by run_id, move it to first position, and reset index
    df = _standardize_dataframe_columns(df)
    
    st.caption("Showing the first 5 rows" + (f" of {len(df)} total" if len(df) > 5 else ""))
    download_icon_b64 = _asset_base64("download.png")
    csv_b64 = base64.b64encode(df.to_csv(index=False).encode("utf-8")).decode("utf-8")
    file_name = f"{key_prefix or title}.csv"
    icon_html = ""
    if download_icon_b64:
        icon_html = "<a " f"href='data:text/csv;base64,{csv_b64}' " f"download='{file_name}' " "style='position:absolute; top:8px; left:8px; z-index:2;' " "aria-label='Download CSV'>" "<img " f"src='data:image/png;base64,{download_icon_b64}' " "style='width:24px; height:24px; cursor:pointer;' " "alt='Download CSV' />" "</a>"

    preview_df = _format_dataframe_for_display(df.head(5))
    if len(df) > 5:
        ellipsis_row = {col: "" for col in df.columns}
        if len(df.columns) > 0:
            ellipsis_cell = "<a " "style='text-decoration: none; font-size: 1.2rem;' " "title='Table truncated for readability. Download the CSV to view the complete dataset.' " "aria-label='Download full table' " f"href='data:text/csv;base64,{csv_b64}' " f"download='{file_name}'>...</a>"
            ellipsis_row[df.columns[0]] = ellipsis_cell
        preview_df.loc["..."] = ellipsis_row

    table_html = preview_df.to_html(index=show_index, escape=False)

    # For tables where the icon overlaps the first column (e.g., Simulation runs),
    # we can add some left padding so the header text is not covered.
    if icon_html and indent_table_for_icon:
        table_html = f"<div style='padding-left: 40px;'>{table_html}</div>"

    container_html = "<div style='position:relative; display:inline-block;'>" f"{icon_html}" f"{table_html}" "</div>"
    st.markdown(container_html, unsafe_allow_html=True)


def _render_table_with_preview(
    title: str,
    df: pd.DataFrame,
    key_prefix: str,
    *,
    analysis_renderer: Callable[[pd.DataFrame, str | None], None] | None = _render_numeric_analysis,
) -> None:
    """Display a truncated preview of a dataframe with optional analysis."""
    st.markdown(f"## {title}")
    if df.empty:
        st.info("No records available yet.")
        return

    _render_table_preview(title, df, key_prefix)
    if analysis_renderer:
        st.markdown(f"#### Visualizations for {title}")
        analysis_renderer(df, time_col=_find_time_column(df))


def _render_duration_analysis(df: pd.DataFrame, *, duration_col: str | None = None, start_col: str | None = None, show_metric_selector: bool = True) -> None:
    """Render statistics and visuals for duration or time-based metrics with optional metric selection."""
    # Determine available metrics
    available_metrics = {}
    
    # Add duration if available
    duration_candidate = duration_col if duration_col in df.columns else None
    if duration_candidate is None:
        for candidate in ("duration", "activity_duration"):
            if candidate in df.columns:
                duration_candidate = candidate
                break

    if duration_candidate is None:
        finish_col = next((c for c in ("finish_time", "finish") if c in df.columns), None)
        start_candidate = start_col or next((c for c in ("start_time", "start") if c in df.columns), None)
        if finish_col and start_candidate:
            df = df.copy()
            df["duration"] = pd.to_numeric(df[finish_col], errors="coerce") - pd.to_numeric(df[start_candidate], errors="coerce")
            duration_candidate = "duration"
            start_col = start_candidate

    if duration_candidate and duration_candidate in df.columns:
        available_metrics["duration"] = duration_candidate

    # Add start_time if available
    start_candidate = start_col or next((c for c in ("start_time", "start", "start_at") if c in df.columns), None)
    if start_candidate and start_candidate in df.columns:
        available_metrics["start_time"] = start_candidate

    # Add finish_time if available
    finish_candidate = next((c for c in ("finish_time", "finish", "finish_at", "end", "end_time") if c in df.columns), None)
    if finish_candidate and finish_candidate in df.columns:
        available_metrics["finish_time"] = finish_candidate

    if not available_metrics:
        st.info("No duration or time data available to visualize.")
        return

    # Select metric to display
    if show_metric_selector and len(available_metrics) > 1:
        metric_choice = _compact_selectbox(
            "Metric",
            options=list(available_metrics.keys()),
            index=0 if "duration" in available_metrics else 0,
            key="metric-selector"
        )
        selected_col = available_metrics[metric_choice]
    else:
        selected_col = available_metrics.get("duration") or next(iter(available_metrics.values()))

    # Get valid data for selected metric
    metric_series = pd.to_numeric(df[selected_col], errors="coerce")
    valid_mask = metric_series.notna()
    
    if valid_mask.sum() == 0:
        st.info(f"No valid data available for {selected_col}.")
        return

    aligned_series = metric_series[valid_mask]

    # Render tabs without "Time series"
    tab_stats, tab_hist, tab_box = st.tabs(["Statistics", "Histogram", "Box plot"])

    with tab_stats:
        stats_df = _basic_statistics(aligned_series)
        _render_compact_table(stats_df)

    with tab_hist:
        hist_df = pd.DataFrame({selected_col: aligned_series})
        if "run_id" in df.columns:
            hist_df["run_id"] = df.loc[valid_mask, "run_id"].values
            hist_df = _standardize_dataframe_columns(hist_df)
        fig = px.histogram(hist_df, x=selected_col, nbins=min(30, max(5, len(hist_df))))
        fig.update_traces(marker_color="#5bbd89")
        st.plotly_chart(fig, width="stretch")

    with tab_box:
        box_df = pd.DataFrame({selected_col: aligned_series})
        if "run_id" in df.columns:
            box_df["run_id"] = df.loc[valid_mask, "run_id"].values
            box_df = _standardize_dataframe_columns(box_df)
        fig = px.box(box_df, y=selected_col)
        fig.update_traces(marker_color="#3a7859")
        st.plotly_chart(fig, width="stretch")


def _render_schedule_summary(df: pd.DataFrame, key_prefix: str) -> None:
    """Render a schedule table."""
    st.markdown("## Schedule")
    if df.empty:
        st.info("No records available yet.")
        return
    _render_table_preview("Schedule", df, key_prefix)


def _render_waiting_log(df: pd.DataFrame, key_prefix: str) -> None:
    """Render waiting log table with duration-focused plots."""
    st.markdown("## Waiting log")
    if df.empty:
        st.info("No records available yet.")
        return

    df = df.copy()
    if "waiting_duration" not in df.columns and {
        "end_waiting",
        "start_waiting",
    }.issubset(df.columns):
        df["waiting_duration"] = pd.to_numeric(df["end_waiting"], errors="coerce") - pd.to_numeric(df["start_waiting"], errors="coerce")

    _render_table_preview("Waiting log", df, key_prefix)

    # Build list of available waiting-related metrics
    available_metrics = []
    metric_labels = {}
    
    if "waiting_duration" in df.columns and not df["waiting_duration"].dropna().empty:
        available_metrics.append("waiting_duration")
        metric_labels["waiting_duration"] = "waiting_duration"
    
    if "start_waiting" in df.columns and not df["start_waiting"].dropna().empty:
        available_metrics.append("start_waiting")
        metric_labels["start_waiting"] = "start waiting"
    
    if "end_waiting" in df.columns and not df["end_waiting"].dropna().empty:
        available_metrics.append("end_waiting")
        metric_labels["end_waiting"] = "finish waiting"

    if not available_metrics:
        st.info("No waiting duration data available to plot.")
        return

    # Dropdown to select which metric to display
    selected_metric = _compact_selectbox(
        "Metric",
        options=available_metrics,
        format_func=lambda x: metric_labels.get(x, x),
        key=f"{key_prefix}-waiting-selection",
        index=0,  # Default to first available metric (usually waiting_duration)
    )

    # Prepare data for selected metric
    raw_values = pd.to_numeric(df[selected_metric], errors="coerce")
    valid_mask = raw_values.notna()
    selected_values = raw_values[valid_mask]
    metric_df = pd.DataFrame({selected_metric: selected_values})
    
    # Include run_id if available to show which run each value came from
    if "run_id" in df.columns:
        metric_df["run_id"] = df.loc[valid_mask, "run_id"].values
    
    # Standardize column ordering and sorting
    metric_df = _standardize_dataframe_columns(metric_df)

    tab_stats, tab_hist, tab_box = st.tabs(["Statistics", "Histogram", "Box plot"])

    with tab_stats:
        stats_df = _basic_statistics(metric_df[selected_metric])
        _render_compact_table(stats_df)

    with tab_hist:
        fig = px.histogram(metric_df, x=selected_metric, nbins=min(30, max(5, len(metric_df))))
        fig.update_traces(marker_color="#5bbd89")
        st.plotly_chart(fig, width="stretch")

    with tab_box:
        fig = px.box(metric_df, y=selected_metric)
        fig.update_traces(marker_color="#3a7859")
        st.plotly_chart(fig, width="stretch")


def _render_queue_waiting_log(df: pd.DataFrame, key_prefix: str) -> None:
    """Render queue log with waiting-duration-focused visuals for resources."""
    st.markdown("## Queue log")
    if df.empty:
        st.info("No queue records available yet.")
        return

    df = df.copy()
    if "waiting_duration" not in df.columns and {"finish_time", "start_time"}.issubset(df.columns):
        df["waiting_duration"] = pd.to_numeric(df["finish_time"], errors="coerce") - pd.to_numeric(df["start_time"], errors="coerce")

    _render_table_preview("Queue log", df, key_prefix)

    # Build list of available waiting-related metrics
    available_metrics = []
    metric_labels = {}
    
    if "waiting_duration" in df.columns and not df["waiting_duration"].dropna().empty:
        available_metrics.append("waiting_duration")
        metric_labels["waiting_duration"] = "waiting_duration"
    
    if "start_time" in df.columns and not df["start_time"].dropna().empty:
        available_metrics.append("start_time")
        metric_labels["start_time"] = "start waiting"
    
    if "finish_time" in df.columns and not df["finish_time"].dropna().empty:
        available_metrics.append("finish_time")
        metric_labels["finish_time"] = "finish waiting"

    if not available_metrics:
        st.info("No waiting duration data available to plot.")
        return

    # Dropdown to select which metric to display
    selected_metric = _compact_selectbox(
        "Metric",
        options=available_metrics,
        format_func=lambda x: metric_labels.get(x, x),
        key=f"{key_prefix}-queue-waiting-selection",
        index=0,  # Default to first available metric (usually waiting_duration)
    )

    # Prepare data for selected metric
    raw_values = pd.to_numeric(df[selected_metric], errors="coerce")
    valid_mask = raw_values.notna()
    selected_values = raw_values[valid_mask]
    metric_df = pd.DataFrame({selected_metric: selected_values})
    
    # Include run_id if available to show which run each value came from
    if "run_id" in df.columns:
        metric_df["run_id"] = df.loc[valid_mask, "run_id"].values
    
    # Standardize column ordering and sorting
    metric_df = _standardize_dataframe_columns(metric_df)

    st.markdown(f"#### {metric_labels.get(selected_metric, selected_metric)}")
    tab_stats, tab_hist, tab_box = st.tabs(["Statistics", "Histogram", "Box plot"])

    with tab_stats:
        stats_df = _basic_statistics(metric_df[selected_metric])
        _render_compact_table(stats_df)

    with tab_hist:
        fig = px.histogram(metric_df, x=selected_metric, nbins=min(30, max(5, len(metric_df))))
        fig.update_traces(marker_color="#5bbd89")
        st.plotly_chart(fig, width="stretch")

    with tab_box:
        fig = px.box(metric_df, y=selected_metric)
        fig.update_traces(marker_color="#3a7859")
        st.plotly_chart(fig, width="stretch")




def _remove_duplicate_status_rows(df: pd.DataFrame, time_col: str, metric_col: str) -> pd.DataFrame:
    """Remove rows with duplicate values at the same simulation time, keeping only the last occurrence.
    
    Parameters
    ----------
    df : pd.DataFrame
        Status log dataframe with time and metric columns
    time_col : str
        Name of the time column
    metric_col : str
        Name of the metric column
    
    Returns
    -------
    pd.DataFrame
        Dataframe with duplicates at same time removed, keeping only the last row per time point.
    """
    if df.empty or time_col not in df.columns or metric_col not in df.columns:
        return df
    
    df = df.copy()
    # Sort by time to ensure proper ordering
    df = df.sort_values(by=time_col, ignore_index=True)
    
    # Group by time and keep only the last row for each time point
    df = df.drop_duplicates(subset=[time_col], keep='last')
    
    return df.reset_index(drop=True)


def _time_weighted_statistics(df: pd.DataFrame, time_col: str, value_col: str) -> pd.DataFrame:
    """Calculate time-weighted statistics where values are weighted by their duration.
    
    Each status value is weighted by the time duration until the next status change.
    The last value is weighted until the end of simulation.
    
    Parameters
    ----------
    df : pd.DataFrame
        Status log dataframe sorted by time
    time_col : str
        Name of the time column
    value_col : str
        Name of the value column to analyze
    
    Returns
    -------
    pd.DataFrame
        Statistics including time-weighted mean, weighted median approximation, etc.
    """
    if df.empty or time_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame()
    
    df = df.copy().sort_values(by=time_col, ignore_index=True)
    
    # Get numeric values
    values = pd.to_numeric(df[value_col], errors='coerce')
    times = pd.to_numeric(df[time_col], errors='coerce')
    
    if values.isna().all() or times.isna().all():
        return pd.DataFrame()
    
    # Calculate time intervals (duration for each value)
    durations = times.diff()
    durations.iloc[0] = times.iloc[0] if len(times) > 0 else 0  # First duration starts from 0
    
    # For the last point, assume it lasts until the end of simulation
    if len(durations) > 0:
        durations.iloc[-1] = times.iloc[-1] - times.iloc[-2] if len(times) > 1 else times.iloc[-1]
    
    # Calculate weighted statistics
    total_duration = durations.sum()
    
    if total_duration == 0:
        return _basic_statistics(values)
    
    # Weighted mean
    weighted_mean = (values * durations).sum() / total_duration if total_duration > 0 else values.mean()
    
    # Weighted min/max (just regular min/max)
    val_min = values.min()
    val_max = values.max()
    
    # Weighted median approximation: use cumulative weighted distribution
    cumsum = (values * durations).cumsum() / total_duration
    median_idx = (cumsum - 0.5).abs().idxmin()
    weighted_median = values.iloc[median_idx]
    
    # Weighted std (approximate)
    weighted_var = ((values - weighted_mean) ** 2 * durations).sum() / total_duration
    weighted_std = weighted_var ** 0.5
    
    return pd.DataFrame(
        {
            "Count": [int(len(values))],
            "Mean": [weighted_mean],
            "Median": [weighted_median],
            "Min": [val_min],
            "Max": [val_max],
            "Std": [weighted_std],
        }
    )


def _generate_time_weighted_samples(df: pd.DataFrame, time_col: str, value_col: str, num_samples: int = 1000) -> list[float]:
    """Generate synthetic samples from time-weighted distribution for histogram/boxplot.
    
    This implements a Monte Carlo approach: for each time interval, samples are drawn
    proportionally to the duration of that interval.
    
    Parameters
    ----------
    df : pd.DataFrame
        Status log dataframe sorted by time
    time_col : str
        Name of the time column
    value_col : str
        Name of the value column
    num_samples : int
        Number of synthetic samples to generate (default 1000)
    
    Returns
    -------
    list[float]
        Synthetic samples representing the time-weighted distribution
    """
    if df.empty or time_col not in df.columns or value_col not in df.columns:
        return []
    
    df = df.copy().sort_values(by=time_col, ignore_index=True)
    
    values = pd.to_numeric(df[value_col], errors='coerce')
    times = pd.to_numeric(df[time_col], errors='coerce')
    
    if values.isna().all() or times.isna().all():
        return []
    
    # Calculate durations for each interval
    durations = times.diff()
    durations.iloc[0] = times.iloc[0] if len(times) > 0 else 0
    if len(durations) > 0:
        durations.iloc[-1] = times.iloc[-1] - times.iloc[-2] if len(times) > 1 else times.iloc[-1]
    
    total_duration = durations.sum()
    if total_duration == 0:
        # If no time variation, just repeat the value
        return [values.iloc[0]] * num_samples
    
    # Calculate sampling weights: proportion of time for each value
    weights = durations / total_duration
    
    # Generate samples proportional to time duration
    samples = []
    for val, weight in zip(values, weights):
        num_samples_for_this_val = max(1, int(round(num_samples * weight)))
        samples.extend([val] * num_samples_for_this_val)
    
    # Adjust to exact sample count
    samples = samples[:num_samples]
    if len(samples) < num_samples:
        samples.extend([values.iloc[-1]] * (num_samples - len(samples)))
    
    return samples


def _render_resource_status(df: pd.DataFrame, key_prefix: str) -> None:
    """Render resource status log with selectable metric plots using time-weighted statistics.
    
    This function:
    1. Removes duplicate rows at the same simulation time (keeps only the last)
    2. Calculates time-weighted statistics (values weighted by duration)
    3. Generates time-weighted histograms/boxplots using Monte Carlo approach
    """
    st.markdown("## Status log")
    if df.empty:
        st.info("No status records available yet.")
        return

    # Standardize column ordering and sorting before any processing
    df = _standardize_dataframe_columns(df)
    
    metric_cols = [col for col in ("in_use", "idle", "queue_length") if col in df.columns]
    time_axis = _find_time_column(df) or "time"
    if time_axis not in df.columns:
        df["time"] = df.index
        time_axis = "time"

    _render_table_preview("Status log", df, key_prefix)

    if not metric_cols:
        st.info("No status metrics available to plot.")
        return

    selected_metric = _compact_selectbox(
        "Metric",
        options=metric_cols,
        key=f"{key_prefix}-status-selection",
    )

    # Remove duplicate rows at same time, keeping only the last occurrence
    df_clean = _remove_duplicate_status_rows(df, time_axis, selected_metric)

    tab_stats, tab_series, tab_hist, tab_box = st.tabs(["Statistics", "Time series", "Histogram", "Box plot"])

    with tab_stats:
        # Use time-weighted statistics
        st.markdown("**Time-weighted statistics** (values weighted by duration between status changes)")
        stats_df = _time_weighted_statistics(df_clean, time_axis, selected_metric)
        if not stats_df.empty:
            _render_compact_table(stats_df)
        else:
            st.info("Unable to calculate statistics for this metric.")

    with tab_series:
        fig = px.line(
            df_clean,
            x=time_axis,
            y=selected_metric,
            labels={"value": "Value", time_axis: time_axis, selected_metric: selected_metric},
        )
        fig.update_traces(line_shape="hv", selector=None, line_color="#3a7859")
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, width="stretch", key=f"{key_prefix}-series")

    with tab_hist:
        # Generate time-weighted samples for histogram
        st.markdown("**Time-weighted histogram** (distribution weighted by time duration)")
        samples = _generate_time_weighted_samples(df_clean, time_axis, selected_metric, num_samples=1000)
        if samples:
            hist_df = pd.DataFrame({selected_metric: samples})
            fig = px.histogram(hist_df, x=selected_metric, nbins=min(30, max(5, len(set(samples)))))
            fig.update_traces(marker_color="#5bbd89")
            st.plotly_chart(fig, width="stretch", key=f"{key_prefix}-hist")
        else:
            st.info("Unable to generate histogram for this metric.")

    with tab_box:
        # Generate time-weighted samples for boxplot
        st.markdown("**Time-weighted boxplot** (quartiles based on time-weighted distribution)")
        samples = _generate_time_weighted_samples(df_clean, time_axis, selected_metric, num_samples=1000)
        if samples:
            box_df = pd.DataFrame({selected_metric: samples})
            fig = px.box(box_df, y=selected_metric)
            fig.update_traces(marker_color="#3a7859")
            st.plotly_chart(fig, width="stretch", key=f"{key_prefix}-box")
        else:
            st.info("Unable to generate boxplot for this metric.")


def _activity_dataframe(snapshot: RunSnapshot) -> pd.DataFrame:
    """Build a unified activity feed from environment, entity, and resource logs."""
    records: list[dict[str, Any]] = []

    env_run_id = snapshot.environment.get("run_id")

    # Environment / run-level logs
    for entry in snapshot.logs:
        rec = dict(entry)
        rec.setdefault("source", "environment")
        rec.setdefault("category", "log")
        rec["run_id"] = _extract_run_id_from_event(entry, env_run_id)
        records.append(rec)

    # Entity logs
    for entity in snapshot.entities:
        ent_run_id = entity.get("run_id")
        for log_key in ("schedule_log", "waiting_log", "status_log"):
            for row in entity.get(log_key, []):
                rec = dict(row)
                rec.update(
                    {
                        "source": "entity",
                        "entity_id": entity.get("id"),
                        "entity_name": entity.get("name"),
                        "category": log_key,
                    }
                )
                rec.setdefault("run_id", ent_run_id)
                records.append(rec)
        if entity.get("waiting_time"):
            for idx, value in enumerate(entity.get("waiting_time", [])):
                records.append(
                    {
                        "source": "entity",
                        "entity_id": entity.get("id"),
                        "entity_name": entity.get("name"),
                        "category": "waiting_time",
                        "index": idx,
                        "value": value,
                        "run_id": ent_run_id,
                    }
                )

    # Resource logs
    for resource in snapshot.resources:
        res_run_id = resource.get("run_id")
        for log_key in ("queue_log", "status_log"):
            for row in resource.get(log_key, []):
                rec = dict(row)
                rec.update(
                    {
                        "source": "resource",
                        "resource_id": resource.get("id"),
                        "resource_name": resource.get("name"),
                        "category": log_key,
                    }
                )
                rec.setdefault("run_id", res_run_id)
                records.append(rec)
        if resource.get("waiting_time"):
            for idx, value in enumerate(resource.get("waiting_time", [])):
                records.append(
                    {
                        "source": "resource",
                        "resource_id": resource.get("id"),
                        "resource_name": resource.get("name"),
                        "category": "waiting_time",
                        "index": idx,
                        "value": value,
                        "run_id": res_run_id,
                    }
                )

    return pd.DataFrame(records)



def _styled_container() -> None:
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.5rem;}
        .stTabs [data-baseweb="tab"] {background-color: #f4fbf7; border-radius: 8px; color: #1f3f2b; border: 1px solid #cce8d9; padding: 0.5rem 1.05rem; margin-right: 0.35rem;}
        .stTabs [aria-selected="true"] {border: 1px solid #7fd3a8 !important; color: #0c2a1b;}
        .stButton>button {border-radius: 10px; border: 1px solid #7fd3a8; color: #0c2a1b; background: white;}
        .stButton>button[data-testid="baseButton-primary"] {background: #e8f5ed; border-color: #7fd3a8; box-shadow: 0 0 0 1px #b6e3c8 inset;}
        .status-chip {padding: 0.35rem 0.75rem; border-radius: 999px; border: 1px solid #7fd3a8; display: inline-block;}
        .simpm-panel {padding: 1rem 1.25rem; border: 1px solid #cce8d9; border-radius: 12px; background: #ffffff; box-shadow: 0 4px 12px rgba(0,0,0,0.03);}
        .simpm-logo-card {background: #f4fbf7; border: 1px solid #cce8d9; border-radius: 12px; padding: 0.75rem; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(0,0,0,0.04);}
        .simpm-logo-card img {max-height: 80px; width: auto; display: block;}
        .simpm-table-wrapper {position: relative;}
        .simpm-table-wrapper table {width: 100%; border-collapse: collapse;}
        .simpm-table-wrapper table th, .simpm-table-wrapper table td {border: 1px solid #d6eadf; padding: 0.5rem; font-size: 0.9rem;}
        .simpm-table-wrapper table th {background: #f4fbf7; color: #1f3f2b;}
        .simpm-compact-table {display: inline-block; max-width: 520px; min-width: 320px;}
        .simpm-compact-table table {width: auto;}
        .simpm-attributes {font-size: 1.05rem; margin-top: 0.25rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _compact_selectbox(
    label: str,
    options: list[Any],
    *,
    key: str | None = None,
    index: int = 0,
    format_func: Callable[[Any], str] = str,  # <- always callable
) -> Any:
    """Render a smaller selectbox inline with its label."""
    col_label, col_widget, _ = st.columns([0.12, 0.32, 0.56])
    with col_label:
        st.markdown(f"**{label}**")
    with col_widget:
        return st.selectbox(
            label,
            options,
            index=index,
            key=key,
            format_func=format_func,  # always a function now
            label_visibility="collapsed",
        )


# ---------------------------------------------------------------------------
# Dashboard class
# ---------------------------------------------------------------------------


@dataclass
class StreamlitDashboard:
    """Encapsulates the post-run dashboard rendering logic."""

    snapshot: RunSnapshot

    # --------- top-level render ------------------------------------------------

    def render(self) -> None:
        """Render the full dashboard."""
        st.session_state.setdefault("simpm_view", "Entities")
        st.session_state.setdefault("simpm_decimal_digits", DEFAULT_DECIMAL_DIGITS)

        st.set_page_config(
            page_title=f"SimPM Dashboard • {self.snapshot.environment.get('name', 'Environment')}",
            layout="wide",
        )
        _styled_container()

        # 1) Overview + run selector
        self._render_overview_switcher()
        # 2) Simulation runs block (table + stats/plots in tabs)
        self._render_simulation_time_overview()
        # 3) Navigation (Entities / Resources / Activity)
        self._render_navigation()

        view = st.session_state.get("simpm_view", "Entities")

        if view == "Entities":
            self._render_entities_view()
        elif view == "Resources":
            self._render_resources_view()
        elif view == "Activity":
            self._render_activity_view()
        else:
            self._render_entities_view()

    # --------- overview / runs / navigation -----------------------------------

    def _model_summary(self, run_filter: str) -> dict[str, int]:
        def _matches_run(row: dict[str, Any]) -> bool:
            if run_filter == "All runs":
                return True
            return str(row.get("run_id")) == str(run_filter)

        filtered_entities = [ent for ent in self.snapshot.entities if _matches_run(ent)]
        filtered_resources = [res for res in self.snapshot.resources if _matches_run(res)]

        activity_df = _activity_dataframe(self.snapshot)
        if "run_id" in activity_df.columns and run_filter != "All runs":
            activity_df = activity_df[activity_df["run_id"].astype(str) == str(run_filter)]

        def _has_activity_identifier(df: pd.DataFrame) -> pd.Series:
            name_series = df["activity_name"] if "activity_name" in df.columns else pd.Series([None] * len(df))
            id_series = df["activity_id"] if "activity_id" in df.columns else pd.Series([None] * len(df))

            name_mask = name_series.notna() & name_series.astype(str).str.strip().ne("")
            id_mask = id_series.notna() & id_series.astype(str).str.strip().ne("")
            return name_mask | id_mask

        activity_count = int(_has_activity_identifier(activity_df).sum()) if not activity_df.empty else 0

        return {
            "entities": len(filtered_entities),
            "resources": len(filtered_resources),
            "activities": activity_count,
        }

    def _render_overview_switcher(self) -> None:
        """Show environment info and run selector."""
        env_info = self.snapshot.environment or {}
        st.markdown(
            """
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <h2 style="margin: 0;">Overview</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Environment name metric
        st.metric("Environment", env_info.get("name", "Environment"))

        # Run selector directly under the Environment metric
        runs = _available_runs(env_info, self.snapshot.logs or [])
        if len(runs) <= 1:
            run_value = runs[0] if runs else env_info.get("run_id", "-")
            st.metric("Run ID", run_value)
            st.session_state.setdefault("simpm_run_filter", "All runs")
        else:
            run_options = ["All runs"] + [str(r) for r in runs]
            current = st.session_state.get("simpm_run_filter")
            if current not in run_options:
                current = "All runs"
            _compact_selectbox(
                "Run",
                options=run_options,
                key="simpm_run_filter",
                index=run_options.index(current),
            )

    def _render_simulation_time_overview(self) -> None:
        """Render finish-time stats across runs, if available."""
        sim_df = _simulation_time_df(self.snapshot.environment or {}, self.snapshot.logs or [])
        if sim_df.empty:
            return

        run_filter = st.session_state.get("simpm_run_filter", "All runs")
        display_df = sim_df.copy()
        display_df["run_id"] = display_df["run_id"].astype(str)

        if run_filter != "All runs":
            display_df = display_df[display_df["run_id"] == str(run_filter)]

        if display_df.empty:
            return

        st.markdown("## Simulation runs")

        # One block: table + stats/plots in tabs (no time series)
        tab_table, tab_stats, tab_hist, tab_box = st.tabs(["Table", "Statistics", "Histogram", "Box plot"])

        with tab_table:
            _render_table_preview(
                "Simulation runs",
                display_df,
                key_prefix="simulation-runs",
                show_index=False,  # hide DataFrame index; only show run_id
                indent_table_for_icon=True,  # add padding so download icon doesn't overlap run_id
            )

        with tab_stats:
            stats_df = _basic_statistics(display_df["finish_time"])
            _render_compact_table(stats_df)

        with tab_hist:
            fig = px.histogram(
                display_df,
                x="finish_time",
                nbins=min(30, max(5, len(display_df))),
                labels={"finish_time": "Finish time"},
            )
            fig.update_traces(marker_color="#5bbd89")
            st.plotly_chart(fig, width="stretch")

        with tab_box:
            fig = px.box(display_df, y="finish_time")
            fig.update_traces(marker_color="#3a7859")
            st.plotly_chart(fig, width="stretch")

    def _render_navigation(self) -> None:
        """Render Entities/Resources/Activity navigation after Simulation runs."""
        run_filter = st.session_state.get("simpm_run_filter", "All runs")
        summary = self._model_summary(run_filter)

        st.markdown(
            """
            <style>
            div[data-testid="stHorizontalBlock"] div[role="radiogroup"] > label {
                border: 1px solid #d6eadf;
                border-radius: 8px;
                padding: 0.35rem 0.75rem;
                background-color: #f4fbf7;
                color: #1f5131;
                transition: background-color 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
            }

            div[data-testid="stHorizontalBlock"] div[role="radiogroup"] > label:hover {
                background-color: #e5f5ec;
                border-color: #b4e0c6;
            }

            div[data-testid="stHorizontalBlock"] div[role="radiogroup"] > label[data-selected="true"] {
                background-color: #d9f2e3;
                border-color: #6fc48f;
                box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.25) inset;
                font-weight: 600;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        nav_options = {
            "Entities": f"{summary['entities']} Entities",
            "Resources": f"{summary['resources']} Resources",
            "Activity": f"{summary['activities']} Activities",
        }
        active_view = st.session_state.get("simpm_view", "Entities")
        view_selection = st.radio(
            "Navigate dashboard views",
            options=list(nav_options.keys()),
            format_func=lambda key: nav_options[key],
            index=list(nav_options.keys()).index(active_view) if active_view in nav_options else 0,
            horizontal=True,
            key="nav-selector",
        )
        st.session_state["simpm_view"] = view_selection

    # --------- entity / resource / activity views -----------------------------

    def _render_entities_view(self) -> None:
        entities: Iterable[dict[str, Any]] = self.snapshot.entities
        run_filter = st.session_state.get("simpm_run_filter", "All runs")
        if run_filter != "All runs":
            entities = [ent for ent in entities if str(ent.get("run_id")) == str(run_filter)]
        if not entities:
            st.info("No entities available.")
            return

        # Group entities by ID for display, allowing selection across runs
        if run_filter == "All runs":
            entity_dict = {}
            for ent in entities:
                ent_id = ent.get("id")
                if ent_id not in entity_dict:
                    entity_dict[ent_id] = []
                entity_dict[ent_id].append(ent)
            options = {f"{entity_dict[eid][0].get('name', 'Entity')} ({eid})": eid for eid in entity_dict}
        else:
            options = {f"{ent['name']} ({ent['id']})": ent for ent in entities}
        
        default_label = st.session_state.get("simpm_entity_label")
        labels = list(options.keys())

        selected_label = _compact_selectbox(
            "Entity",
            options=labels,
            key="simpm_entity_label",
            index=labels.index(default_label) if default_label in labels else 0,
        )
        # ❌ remove this line:
        # st.session_state["simpm_entity_label"] = selected_label

        # Get all entities matching the selection
        if run_filter == "All runs":
            entity_id = options[selected_label]
            selected_entities = [ent for ent in entities if ent.get("id") == entity_id]
        else:
            selected_entities = [options[selected_label]]

        if not selected_entities:
            st.info("No entities available.")
            return

        # Display info for the first entity (they're all the same type)
        entity = selected_entities[0]
        entity_id = entity.get("id", "-")
        entity_name = str(entity.get("name", "")).strip() or f"Entity {entity_id}"
        st.markdown(f"### Entity {entity_id} • {entity_name}")
        st.caption(f"Type: {entity.get('type', 'Unknown')}")

        attributes = entity.get("attributes") or entity.get("attr") or {}
        if attributes:
            st.markdown(
                f"<div class='simpm-attributes'><strong>Attributes:</strong> {_format_attributes_inline(attributes)}</div>",
                unsafe_allow_html=True,
            )

        # Combine logs from all instances of this entity across runs
        schedule_df = pd.concat([pd.DataFrame(ent.get("schedule_log", [])) for ent in selected_entities], ignore_index=True)
        if not schedule_df.empty:
            _render_schedule_summary(schedule_df, key_prefix=f"entity-{entity_id}-schedule")

        waiting_df = pd.concat([pd.DataFrame(ent.get("waiting_log", [])) for ent in selected_entities], ignore_index=True)
        if not waiting_df.empty:
            _render_waiting_log(waiting_df, key_prefix=f"entity-{entity_id}-waiting")

        status_df = pd.concat([pd.DataFrame(ent.get("status_log", [])) for ent in selected_entities], ignore_index=True)
        if not status_df.empty:
            _render_table_with_preview(
                "Status log",
                status_df,
                key_prefix=f"entity-{entity_id}-status",
                analysis_renderer=None,
            )

    def _render_resources_view(self) -> None:
        resources: Iterable[dict[str, Any]] = self.snapshot.resources
        run_filter = st.session_state.get("simpm_run_filter", "All runs")
        if run_filter != "All runs":
            resources = [res for res in resources if str(res.get("run_id")) == str(run_filter)]
        if not resources:
            st.info("No resources available.")
            return

        # Group resources by ID for display, allowing selection across runs
        if run_filter == "All runs":
            resource_dict = {}
            for res in resources:
                res_id = res.get("id")
                if res_id not in resource_dict:
                    resource_dict[res_id] = []
                resource_dict[res_id].append(res)
            options = {f"{resource_dict[rid][0].get('name', 'Resource')} ({rid})": rid for rid in resource_dict}
        else:
            options = {f"{res['name']} ({res['id']})": res for res in resources}
        
        default_label = st.session_state.get("simpm_resource_label")
        labels = list(options.keys())
        selected_label = _compact_selectbox(
            "Resource",
            options=labels,
            key="simpm_resource_label",
            index=labels.index(default_label) if default_label in labels else 0,
        )
        
        # Get all resources matching the selection
        if run_filter == "All runs":
            resource_id = options[selected_label]
            selected_resources = [res for res in resources if res.get("id") == resource_id]
        else:
            selected_resources = [options[selected_label]]
        
        if not selected_resources:
            st.info("No resources available.")
            return

        # Display info for the first resource (they're all the same type)
        resource = selected_resources[0]

        res_id = resource.get("id", "-")
        res_name = str(resource.get("name", "")).strip() or f"Resource {res_id}"
        st.markdown(f"### Resource {res_id} • {res_name}")
        
        # Get initial level from status_log (first idle value) or from initial_level attribute
        initial_level = resource.get('initial_level', None)
        if initial_level is None or initial_level == '-':
            # Try to get from status_log: the first idle value represents initial available resources
            status_log = resource.get("status_log", [])
            if status_log and len(status_log) > 0:
                first_status = status_log[0]
                idle_val = first_status.get("idle")
                if idle_val is not None:
                    initial_level = idle_val
        if initial_level is None:
            initial_level = '-'
        
        st.caption(f"Type: {resource.get('type', 'Unknown')} • Initial: {initial_level} • Capacity: {resource.get('capacity', '-') }")
        attributes = resource.get("attributes") or resource.get("attr")
        if attributes:
            st.markdown(
                f"<div class='simpm-attributes'><strong>Attributes:</strong> {_format_attributes_inline(attributes)}</div>",
                unsafe_allow_html=True,
            )

        # Display average utilization and average queue length with tabs
        # Collect metrics from all selected resources (across runs if viewing "All runs")
        metrics_records = []
        for res in selected_resources:
            stats = res.get("stats", {})
            run_id = res.get("run_id")
            util = stats.get("average_utilization")
            queue = stats.get("average_queue_length")
            
            if util is not None or queue is not None:
                rec = {"run_id": run_id}
                if util is not None:
                    try:
                        rec["average_utilization"] = float(util)
                    except (TypeError, ValueError):
                        pass
                if queue is not None:
                    try:
                        rec["average_queue_length"] = float(queue)
                    except (TypeError, ValueError):
                        pass
                if len(rec) > 1:  # More than just run_id
                    metrics_records.append(rec)
        
        if metrics_records:
            metrics_df = pd.DataFrame(metrics_records)
            
            # Display tabs for each metric
            if "average_utilization" in metrics_df.columns:
                st.markdown("### Average Utilization")
                util_df = metrics_df[["run_id", "average_utilization"]].copy() if "run_id" in metrics_df.columns else metrics_df[["average_utilization"]].copy()
                
                tab_table, tab_stats, tab_hist, tab_box = st.tabs(["Table", "Statistics", "Histogram", "Box plot"])
                
                with tab_table:
                    _render_table_preview(
                        "Average Utilization",
                        util_df,
                        key_prefix=f"resource-{res_id}-util",
                        show_index=False,
                        indent_table_for_icon=True,
                    )
                
                with tab_stats:
                    stats_df = _basic_statistics(util_df["average_utilization"])
                    _render_compact_table(stats_df)
                
                with tab_hist:
                    fig = px.histogram(
                        util_df,
                        x="average_utilization",
                        nbins=min(30, max(5, len(util_df))),
                        labels={"average_utilization": "Average Utilization"},
                    )
                    fig.update_traces(marker_color="#5bbd89")
                    st.plotly_chart(fig, width='stretch', key=f"util-hist-{res_id}")
                
                with tab_box:
                    fig = px.box(util_df, y="average_utilization")
                    fig.update_traces(marker_color="#3a7859")
                    st.plotly_chart(fig, width='stretch', key=f"util-box-{res_id}")
            
            if "average_queue_length" in metrics_df.columns:
                st.markdown("### Average Queue Length")
                queue_df_display = metrics_df[["run_id", "average_queue_length"]].copy() if "run_id" in metrics_df.columns else metrics_df[["average_queue_length"]].copy()
                
                tab_table, tab_stats, tab_hist, tab_box = st.tabs(["Table", "Statistics", "Histogram", "Box plot"])
                
                with tab_table:
                    _render_table_preview(
                        "Average Queue Length",
                        queue_df_display,
                        key_prefix=f"resource-{res_id}-queue-length",
                        show_index=False,
                        indent_table_for_icon=True,
                    )
                
                with tab_stats:
                    stats_df = _basic_statistics(queue_df_display["average_queue_length"])
                    _render_compact_table(stats_df)
                
                with tab_hist:
                    fig = px.histogram(
                        queue_df_display,
                        x="average_queue_length",
                        nbins=min(30, max(5, len(queue_df_display))),
                        labels={"average_queue_length": "Average Queue Length"},
                    )
                    fig.update_traces(marker_color="#5bbd89")
                    st.plotly_chart(fig, width='stretch', key=f"queue-hist-{res_id}")
                
                with tab_box:
                    fig = px.box(queue_df_display, y="average_queue_length")
                    fig.update_traces(marker_color="#3a7859")
                    st.plotly_chart(fig, width='stretch', key=f"queue-box-{res_id}")

        # Combine logs from all instances of this resource across runs
        queue_df = pd.concat([pd.DataFrame(res.get("queue_log", [])) for res in selected_resources], ignore_index=True)
        if not queue_df.empty:
            _render_queue_waiting_log(queue_df, key_prefix=f"resource-{res_id}-queue")

        status_df = pd.concat([pd.DataFrame(res.get("status_log", [])) for res in selected_resources], ignore_index=True)
        if not status_df.empty:
            _render_resource_status(status_df, key_prefix=f"resource-{res_id}-status")

    def _render_activity_view(self) -> None:
        activity_df = _activity_dataframe(self.snapshot)

        if activity_df.empty:
            st.info("No activity recorded for this run.")
            return

        run_filter = st.session_state.get("simpm_run_filter", "All runs")
        if "run_id" in activity_df.columns and run_filter != "All runs":
            activity_df = activity_df[activity_df["run_id"].astype(str) == str(run_filter)]
        else:
            # Standardize the activity dataframe for proper ordering when viewing all runs
            activity_df = _standardize_dataframe_columns(activity_df)

        def _has_activity_identifier(df: pd.DataFrame) -> pd.Series:
            name_series = df["activity_name"] if "activity_name" in df.columns else pd.Series([None] * len(df))
            id_series = df["activity_id"] if "activity_id" in df.columns else pd.Series([None] * len(df))

            name_mask = name_series.notna() & name_series.astype(str).str.strip().ne("")
            id_mask = id_series.notna() & id_series.astype(str).str.strip().ne("")
            return name_mask | id_mask

        filtered_activity = activity_df[_has_activity_identifier(activity_df)].copy()

        if filtered_activity.empty:
            st.info("No activity records with names or IDs are available to display.")
            return

        standard_cols = [
            "activity_name",
            "start_time",
            "finish_time",
            "activity_id",
            "duration",
            "entity_id",
            "entity_name",
        ]
        
        # Always include run_id if it exists in the data
        run_filter = st.session_state.get("simpm_run_filter", "All runs")
        if "run_id" in filtered_activity.columns:
            standard_cols.insert(0, "run_id")

        # Display activity log
        st.markdown("## Activity Log")
        display_df = filtered_activity.copy()
        display_df["activity_name"] = display_df.get("activity_name")
        if "activity_name" not in display_df.columns or display_df["activity_name"].isna().all():
            display_df["activity_name"] = display_df.get("activity")
        for col in standard_cols:
            if col not in display_df.columns:
                display_df[col] = ""
        start_col = next((c for c in ("start_time", "start", "start_at") if c in display_df.columns), None)
        if start_col:
            display_df = display_df.sort_values(start_col, key=lambda s: pd.to_numeric(s, errors="coerce")).reset_index(drop=True)
        display_df = display_df[standard_cols].fillna("")

        _render_table_preview("Activity Log", display_df, key_prefix="activity")

        # Display activity by name section
        schedule_df = filtered_activity[filtered_activity["category"] == "schedule_log"].copy() if "category" in filtered_activity.columns else pd.DataFrame()

        label_col = next(
            (candidate for candidate in ["activity_name", "activity"] if candidate in schedule_df.columns),
            None,
        )

        if not (schedule_df.empty or not label_col):
            schedule_df = schedule_df[_has_activity_identifier(schedule_df)].copy()
            schedule_df["activity_label"] = schedule_df[label_col].astype(str)
            options = sorted(schedule_df["activity_label"].dropna().unique())


            if options:
                st.markdown("## Activity by Name")
                selected = _compact_selectbox(
                    "Activity",
                    options=options,
                    key="activity-name-filter",
                )

                if selected:
                    filtered = schedule_df[schedule_df["activity_label"] == selected].copy()

                    start_col = next((c for c in ("start_time", "start", "start_at") if c in filtered.columns), None)
                    end_col = next((c for c in ("finish_time", "end", "finish") if c in filtered.columns), None)

                    if "duration" not in filtered.columns and start_col and end_col:
                        filtered["duration"] = pd.to_numeric(filtered[end_col], errors="coerce") - pd.to_numeric(filtered[start_col], errors="coerce")

                    if "activity_name" not in filtered.columns or filtered["activity_name"].isna().all():
                        filtered["activity_name"] = filtered.get("activity", "")

                    for col in standard_cols:
                        if col not in filtered.columns:
                            filtered[col] = ""

                    display_df = filtered[standard_cols]
                    if start_col and start_col in display_df.columns:
                        display_df = display_df.sort_values(start_col, key=lambda s: pd.to_numeric(s, errors="coerce")).reset_index(drop=True)
                    display_df = display_df.fillna("")

                    _render_table_preview(
                        "Activity by name",
                        display_df,
                        key_prefix="activity-name",
                    )
                    
                    _render_duration_analysis(
                        filtered,
                        duration_col="duration" if "duration" in filtered.columns else None,
                        start_col=start_col,
                        show_metric_selector=True,
                    )


    # --------- launching ------------------------------------------------------

    def run(self, host: str = "127.0.0.1", port: int = 8050, async_mode: bool = False):
        """Start the Streamlit server for this dashboard."""
        global _ACTIVE_DASHBOARD
        _ACTIVE_DASHBOARD = self

        snapshot_file = Path(tempfile.mkdtemp()) / "simpm_snapshot.json"
        # default=str makes uniform/triang/... etc serializable using their __str__
        snapshot_file.write_text(json.dumps(self.snapshot.as_dict(), default=str))

        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(Path(__file__).resolve()),
            "--server.address",
            host,
            "--server.port",
            str(port),
            "--server.headless",
            "true",
            "--",
            "--data",
            str(snapshot_file),
        ]

        logger.info("Launching Streamlit dashboard with data file %s", snapshot_file)
        if async_mode:
            return subprocess.Popen(cmd)
        subprocess.run(cmd, check=False)


# ---------------------------------------------------------------------------
# Aggregation helpers and public entry points
# ---------------------------------------------------------------------------


def _aggregate_envs_to_snapshot(envs: List[Any]) -> RunSnapshot:
    """Aggregate multiple environments into a single :class:`RunSnapshot`.

    The dashboard can be launched after a Monte Carlo experiment where an
    environment factory was executed many times. Each replication maintains its
    own entities, resources, and log streams, but the dashboard should present
    the complete set rather than only the final run. This helper collects a
    snapshot per environment and *reindexes* every run to a unique ``run_id`` so
    that run filters, tables, and plots operate on all runs consistently.
    """

    def _with_run_id(snapshot: RunSnapshot, run_id: int) -> RunSnapshot:
        """Deep-copy a snapshot while forcing ``run_id`` fields to ``run_id``.

        This keeps per-run data aligned with the combined ``run_history`` and
        prevents multiple replications from reusing ``run_id=1`` (the default
        when each environment only executes once).
        """

        def _set_run_id(obj: Any) -> Any:
            if isinstance(obj, dict):
                updated: dict[str, Any] = {}
                for key, value in obj.items():
                    if key == "run_id":
                        updated[key] = run_id
                    else:
                        updated[key] = _set_run_id(value)
                return updated
            if isinstance(obj, list):
                return [_set_run_id(item) for item in obj]
            return obj

        return RunSnapshot(
            environment=_set_run_id(snapshot.environment),
            entities=[_set_run_id(ent) for ent in snapshot.entities],
            resources=[_set_run_id(res) for res in snapshot.resources],
            logs=[_set_run_id(log) for log in snapshot.logs],
        )

    snapshots: list[RunSnapshot] = []
    for env in envs:
        if isinstance(env, RunSnapshot):
            snapshots.append(env)
        else:
            snapshots.append(collect_run_data(env))

    if not snapshots:
        return RunSnapshot(environment={}, entities=[], resources=[], logs=[])

    # Use the last environment metadata as base
    base_env = dict(snapshots[-1].environment)
    all_entities: list[dict[str, Any]] = []
    all_resources: list[dict[str, Any]] = []
    all_logs: list[dict[str, Any]] = []
    combined_run_history: list[dict[str, Any]] = []

    for idx, snap in enumerate(snapshots, start=1):
        remapped_snap = _with_run_id(snap, idx)
        all_entities.extend(remapped_snap.entities)
        all_resources.extend(remapped_snap.resources)
        all_logs.extend(remapped_snap.logs)

        rh = snap.environment.get("run_history") or []
        if isinstance(rh, list):
            for row in rh:
                rh_row = dict(row)
                rh_row["run_id"] = idx
                combined_run_history.append(rh_row)

    # Re-index run_ids to 1..N for clarity in the dashboard
    for idx, rh in enumerate(combined_run_history, start=1):
        rh["run_id"] = idx

    if combined_run_history:
        base_env["run_history"] = combined_run_history
        base_env["run_id"] = combined_run_history[-1].get("run_id")
        base_env.setdefault("planned_runs", len(combined_run_history))

    return RunSnapshot(
        environment=base_env,
        entities=all_entities,
        resources=all_resources,
        logs=all_logs,
    )


def build_app(env) -> StreamlitDashboard:
    """Build a Streamlit dashboard bound to the given environment."""
    snapshot = collect_run_data(env)
    logger.debug("Prepared initial snapshot with %s entities", len(snapshot.entities))
    return StreamlitDashboard(snapshot=snapshot)


def run_post_dashboard(env_or_envs, host: str = "127.0.0.1", port: int = 8050, start_async: bool = True):
    """Launch the Streamlit dashboard for one or many environments."""
    if isinstance(env_or_envs, RunSnapshot):
        snapshot = env_or_envs
    elif isinstance(env_or_envs, list):
        snapshot = _aggregate_envs_to_snapshot(env_or_envs)
    else:
        snapshot = collect_run_data(env_or_envs)

    dashboard = StreamlitDashboard(snapshot=snapshot)
    logger.info("Starting Streamlit dashboard at http://%s:%s (async=%s)", host, port, start_async)
    dashboard.run(host=host, port=port, async_mode=start_async)
    return dashboard


def _load_snapshot_from_file(path: str | None) -> RunSnapshot | None:
    if not path:
        return None
    snapshot_path = Path(path)
    if not snapshot_path.exists():
        return None
    data = json.loads(snapshot_path.read_text())
    return RunSnapshot(
        environment=data.get("environment", {}),
        entities=data.get("entities", []),
        resources=data.get("resources", []),
        logs=data.get("logs", []),
    )


def main() -> None:  # pragma: no cover - executed by Streamlit runtime
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--data", type=str, default=None)
    args, _ = parser.parse_known_args()

    snapshot = _ACTIVE_DASHBOARD.snapshot if _ACTIVE_DASHBOARD is not None else _load_snapshot_from_file(args.data)
    if snapshot is None:
        st.title("SimPM Dashboard")
        st.warning("Run a simulation with dashboard=True to populate this view.")
        return
    StreamlitDashboard(snapshot=snapshot).render()


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
