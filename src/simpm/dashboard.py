"""Streamlit dashboard for SimPM runs."""
from __future__ import annotations

import argparse
import base64
import json
import logging
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

import pandas as pd
import plotly.express as px

try:  # pragma: no cover - handled at runtime
    import streamlit as st
except ImportError as exc:  # pragma: no cover - handled at runtime
    raise ImportError(
        "Streamlit is required for dashboard mode. Install with `pip install streamlit plotly`."
    ) from exc

from simpm.dashboard_data import RunSnapshot, collect_run_data

logger = logging.getLogger(__name__)


_ACTIVE_DASHBOARD: "StreamlitDashboard | None" = None


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


def _render_compact_table(df: pd.DataFrame, *, caption: str | None = None) -> None:
    """Render a compact HTML table similar to the log previews."""

    if df.empty:
        st.info("No data available to display.")
        return

    html = df.to_html(index=False, escape=False)
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

    col = st.selectbox("Select numeric column", list(numeric_df.columns))
    time_axis = time_col or _find_time_column(df.drop(columns=[col], errors="ignore"))
    st.markdown(f"#### {col}")
    tab_stats, tab_series, tab_hist, tab_cdf = st.tabs(
        ["Statistics", "Time series", "Histogram (PDF)", "Empirical CDF"]
    )

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
        fig = px.histogram(df, x=col, nbins=min(30, max(5, len(df))), histnorm="probability density")
        fig.update_traces(marker_color="#5bbd89")
        st.plotly_chart(fig, width="stretch")

    with tab_cdf:
        fig = px.ecdf(df, x=col)
        fig.update_traces(line_color="#3a7859")
        st.plotly_chart(fig, width="stretch")


def _render_duration_analysis(
    df: pd.DataFrame, *, duration_col: str = "duration", start_col: str | None = None
) -> None:
    """Visualize duration trends while keeping axes aligned.

    Plotly raises a ``ValueError`` when the ``x`` and ``y`` arrays have different
    lengths. This helper normalizes both axes by dropping rows with missing
    duration (and start times when provided) before plotting, preventing
    mismatched lengths from crashing the dashboard.
    """

    if duration_col not in df.columns:
        st.info("No duration column available to analyze.")
        return

    cleaned = df.copy()
    cleaned[duration_col] = pd.to_numeric(cleaned[duration_col], errors="coerce")
    cleaned = cleaned.dropna(subset=[duration_col])

    if cleaned.empty:
        st.info("No valid duration data available to plot.")
        return

    if start_col and start_col in cleaned.columns:
        cleaned[start_col] = pd.to_numeric(cleaned[start_col], errors="coerce")
        cleaned = cleaned.dropna(subset=[start_col])
        x_axis = cleaned[start_col]
        x_label = start_col
        if cleaned.empty:
            st.info("No valid start times available to plot durations against.")
            return
    else:
        cleaned = cleaned.reset_index(drop=True)
        x_axis = cleaned.index
        x_label = "Index"

    fig = px.line(x=x_axis, y=cleaned[duration_col], labels={"x": x_label, "y": duration_col})
    fig.update_traces(line_color="#3a7859")
    st.plotly_chart(fig, width="stretch")


def _render_table_preview(title: str, df: pd.DataFrame, key_prefix: str) -> None:
    """Render a table preview with a download button."""

    st.caption(
        "Showing the first 5 rows" + (f" of {len(df)} total" if len(df) > 5 else "")
    )
    download_icon_b64 = _asset_base64("download.png")
    csv_b64 = base64.b64encode(df.to_csv(index=False).encode("utf-8")).decode("utf-8")
    file_name = f"{key_prefix or title}.csv"
    icon_html = ""
    if download_icon_b64:
        icon_html = (
            "<a "
            f"href='data:text/csv;base64,{csv_b64}' "
            f"download='{file_name}' "
            "style='position:absolute; top:8px; left:8px; z-index:2;' "
            "aria-label='Download CSV'>"
            "<img "
            f"src='data:image/png;base64,{download_icon_b64}' "
            "style='width:24px; height:24px; cursor:pointer;' "
            "alt='Download CSV' />"
            "</a>"
        )

    preview_df = df.head(5).copy()
    if len(df) > 5:
        ellipsis_row = {col: "" for col in df.columns}
        if len(df.columns) > 0:
            ellipsis_cell = (
                "<a "
                "style='text-decoration: none; font-size: 1.2rem;' "
                "title='Table truncated for readability. Download the CSV to view the complete dataset.' "
                "aria-label='Download full table' "
                f"href='data:text/csv;base64,{csv_b64}' "
                f"download='{file_name}'>...</a>"
            )
            ellipsis_row[df.columns[0]] = ellipsis_cell
        preview_df.loc["..."] = ellipsis_row

    table_html = preview_df.to_html(index=True, escape=False)
    container_html = (
        "<div style='position:relative; display:inline-block;'>"
        f"{icon_html}"
        f"{table_html}"
        "</div>"
    )
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


def _render_duration_analysis(df: pd.DataFrame, *, start_col: str | None = None) -> None:
    """Render duration-only visuals with the start column used as a time axis."""

    duration_col = None
    for candidate in ("duration", "activity_duration"):
        if candidate in df.columns:
            duration_col = candidate
            break

    if duration_col is None:
        finish_col = next((c for c in ("finish_time", "finish") if c in df.columns), None)
        start_candidate = start_col or next(
            (c for c in ("start_time", "start") if c in df.columns), None
        )
        if finish_col and start_candidate:
            df = df.copy()
            df["duration"] = pd.to_numeric(df[finish_col], errors="coerce") - pd.to_numeric(
                df[start_candidate], errors="coerce"
            )
            duration_col = "duration"
            start_col = start_candidate

    if duration_col is None:
        st.info("No duration data available to visualize.")
        return

    duration_series = pd.to_numeric(df[duration_col], errors="coerce").dropna()
    if duration_series.empty:
        st.info("No duration data available to visualize.")
        return

    tab_stats, tab_series, tab_hist, tab_cdf = st.tabs(
        ["Statistics", "Time series", "Histogram (PDF)", "Empirical CDF"]
    )

    if start_col and start_col in df.columns:
        x_axis_full = df[start_col]
        x_label = start_col
    else:
        x_axis_full = df.index
        x_label = "Index"

    aligned_series = pd.to_numeric(df[duration_col], errors="coerce")
    valid_mask = aligned_series.notna()
    x_axis = x_axis_full[valid_mask]
    aligned_series = aligned_series[valid_mask]

    with tab_stats:
        stats_df = _basic_statistics(aligned_series)
        _render_compact_table(stats_df)

    with tab_series:
        fig = px.line(x=x_axis, y=aligned_series, labels={"x": x_label, "y": duration_col})
        fig.update_traces(line_color="#3a7859")
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, width="stretch")

    with tab_hist:
        fig = px.histogram(aligned_series, nbins=min(30, max(5, len(aligned_series))), labels={"value": duration_col})
        fig.update_traces(marker_color="#5bbd89")
        st.plotly_chart(fig, width="stretch")

    with tab_cdf:
        fig = px.ecdf(aligned_series, labels={"value": duration_col})
        fig.update_traces(line_color="#3a7859")
        st.plotly_chart(fig, width="stretch")


def _render_schedule_summary(df: pd.DataFrame, key_prefix: str) -> None:
    """Render a schedule table with a compact bar visualization for top activities."""

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
        df["waiting_duration"] = pd.to_numeric(df["end_waiting"], errors="coerce") - pd.to_numeric(
            df["start_waiting"], errors="coerce"
        )

    _render_table_preview("Waiting log", df, key_prefix)

    if "waiting_duration" not in df.columns or df["waiting_duration"].dropna().empty:
        st.info("No waiting duration data available to plot.")
        return

    raw_durations = pd.to_numeric(df["waiting_duration"], errors="coerce")
    valid_mask = raw_durations.notna()
    aligned_durations = raw_durations[valid_mask]
    duration_df = pd.DataFrame({"waiting_duration": aligned_durations})

    st.markdown("#### waiting_duration")
    tab_stats, tab_series, tab_hist, tab_box = st.tabs(
        ["Statistics", "Time series", "Histogram", "Box plot"]
    )

    with tab_stats:
        stats_df = _basic_statistics(duration_df["waiting_duration"])
        _render_compact_table(stats_df)

    with tab_series:
        time_axis = (
            df.loc[valid_mask, "start_waiting"] if "start_waiting" in df.columns else duration_df.index
        )
        fig = px.line(
            x=time_axis,
            y=aligned_durations,
            labels={"x": "start_waiting" if "start_waiting" in df.columns else "Index", "y": "waiting_duration"},
        )
        fig.update_traces(line_color="#3a7859")
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, width="stretch")

    with tab_hist:
        fig = px.histogram(duration_df, x="waiting_duration", nbins=min(30, max(5, len(duration_df))))
        fig.update_traces(marker_color="#5bbd89")
        st.plotly_chart(fig, width="stretch")

    with tab_box:
        fig = px.box(duration_df, y="waiting_duration")
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
        df["waiting_duration"] = pd.to_numeric(df["finish_time"], errors="coerce") - pd.to_numeric(
            df["start_time"], errors="coerce"
        )

    _render_table_preview("Queue log", df, key_prefix)

    if "waiting_duration" not in df.columns or df["waiting_duration"].dropna().empty:
        st.info("No waiting duration data available to plot.")
        return

    raw_durations = pd.to_numeric(df["waiting_duration"], errors="coerce")
    valid_mask = raw_durations.notna()
    duration_series = raw_durations[valid_mask]
    duration_df = pd.DataFrame({"waiting_duration": duration_series})

    st.markdown("#### waiting_duration")
    tab_stats, tab_series, tab_hist, tab_box = st.tabs(
        ["Statistics", "Time series", "Histogram", "Box plot"]
    )

    with tab_stats:
        stats_df = _basic_statistics(duration_df["waiting_duration"])
        _render_compact_table(stats_df)

    with tab_series:
        time_axis = df.loc[valid_mask, "start_time"] if "start_time" in df.columns else duration_df.index
        fig = px.line(
            x=time_axis,
            y=duration_df["waiting_duration"],
            labels={"x": "start_time" if "start_time" in df.columns else "Index", "y": "waiting_duration"},
        )
        fig.update_traces(line_color="#3a7859")
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, width="stretch")

    with tab_hist:
        fig = px.histogram(duration_df, x="waiting_duration", nbins=min(30, max(5, len(duration_df))))
        fig.update_traces(marker_color="#5bbd89")
        st.plotly_chart(fig, width="stretch")

    with tab_box:
        fig = px.box(duration_df, y="waiting_duration")
        fig.update_traces(marker_color="#3a7859")
        st.plotly_chart(fig, width="stretch")


def _render_resource_status(df: pd.DataFrame, key_prefix: str) -> None:
    """Render resource status log with selectable metric plots."""

    st.markdown("## Status log")
    if df.empty:
        st.info("No status records available yet.")
        return

    metric_cols = [col for col in ("in_use", "idle", "queue_length") if col in df.columns]
    time_axis = _find_time_column(df) or "time"
    if time_axis not in df.columns:
        df["time"] = df.index
        time_axis = "time"

    _render_table_preview("Status log", df, key_prefix)

    if not metric_cols:
        st.info("No status metrics available to plot.")
        return

    st.markdown("#### status metrics")
    selected_metric = st.selectbox(
        "Select metric to visualize",
        metric_cols,
        key=f"{key_prefix}-status-selection",
    )
    tab_stats, tab_series, tab_hist = st.tabs(["Statistics", "Time series", "Histogram"])

    with tab_stats:
        stats_df = _basic_statistics(pd.to_numeric(df[selected_metric], errors="coerce"))
        _render_compact_table(stats_df)

    with tab_series:
        fig = px.line(
            df,
            x=time_axis,
            y=selected_metric,
            labels={"value": "Value", time_axis: time_axis, selected_metric: selected_metric},
        )
        fig.update_traces(line_shape="hv", selector=None, line_color="#3a7859")
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, width="stretch")

    with tab_hist:
        fig = px.histogram(df, x=selected_metric, nbins=min(30, max(5, len(df))))
        fig.update_traces(marker_color="#5bbd89")
        st.plotly_chart(fig, width="stretch")


def _activity_dataframe(snapshot: RunSnapshot) -> pd.DataFrame:
    """Build a unified activity feed from environment, entity, and resource logs."""

    records: list[dict[str, Any]] = []

    for entry in snapshot.logs:
        rec = dict(entry)
        rec.setdefault("source", "environment")
        rec.setdefault("category", "log")
        records.append(rec)

    for entity in snapshot.entities:
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
                    }
                )

    for resource in snapshot.resources:
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
                    }
                )

    return pd.DataFrame(records)


def _load_logo() -> bytes | None:
    logo_paths = [
        Path(__file__).resolve().parent.parent / "docs" / "_build" / "html" / "_static" / "simpm_logo.png",
        Path(__file__).resolve().parent.parent / "docs" / "source" / "images" / "simpm_logo.png",
        Path(__file__).resolve().parent / "assets" / "simpm_logo.png",
    ]

    for logo_path in logo_paths:
        if logo_path.exists():
            return logo_path.read_bytes()
    return None


def _render_logo(logo: bytes | None) -> None:
    if not logo:
        st.caption("SimPM")
        return

    encoded = base64.b64encode(logo).decode("utf-8")
    st.markdown(
        f"<div class='simpm-logo-card'><img src='data:image/png;base64,{encoded}' alt='SimPM logo'></div>",
        unsafe_allow_html=True,
    )


def _asset_base64(name: str) -> str | None:
    """Return a base64 string for the given asset file if it exists."""

    asset_path = Path(__file__).resolve().parent / "assets" / name
    if not asset_path.exists():
        return None
    return base64.b64encode(asset_path.read_bytes()).decode("utf-8")


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
        </style>
        """,
        unsafe_allow_html=True,
    )


@dataclass
class StreamlitDashboard:
    """Encapsulates the post-run dashboard rendering logic."""

    snapshot: RunSnapshot

    def render(self) -> None:
        """Render the dashboard using Streamlit primitives."""

        st.session_state.setdefault("simpm_view", "Entities")
        st.set_page_config(
            page_title=f"SimPM Dashboard • {self.snapshot.environment.get('name', 'Environment')}",
            layout="wide",
            page_icon=_load_logo() or None,
        )
        _styled_container()

        self._render_overview_switcher()
        view = st.session_state.get("simpm_view", "Entities")

        if view == "Entities":
            self._render_entities_view()
        elif view == "Resources":
            self._render_resources_view()
        elif view == "Activity":
            self._render_activity_view()
        else:
            self._render_entities_view()

    def _render_overview_switcher(self) -> None:
        """Show environment facts and clickable model summaries."""

        env_info = self.snapshot.environment or {}
        logo_b64 = _asset_base64("simpm_logo.png")
        logo_img = (
            f"<img src='data:image/png;base64,{logo_b64}' style='height: 40px; margin-right: 12px;' alt='SimPM logo'>"
            if logo_b64
            else ""
        )
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                {logo_img}
                <h2 style="margin: 0;">Overview</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
        cols = st.columns(3)
        cols[0].metric("Environment", env_info.get("name", "Environment"))
        cols[1].metric("Run ID", env_info.get("run_id", "-"))
        cols[2].metric("Finished at", env_info.get("time", {}).get("end", "-"))

        summary = self._model_summary()
        st.markdown("#### Model summary")
        st.markdown(
            """
            <style>
            /* Light green treatment for dashboard nav selector */
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
        selection = st.radio(
            "Navigate dashboard views",
            options=list(nav_options.keys()),
            format_func=lambda key: nav_options[key],
            index=list(nav_options.keys()).index(active_view)
            if active_view in nav_options
            else 0,
            horizontal=True,
            key="nav-selector",
        )
        st.session_state["simpm_view"] = selection

    def _model_summary(self) -> dict[str, int]:
        activities = sum(len(ent.get("activities", [])) for ent in self.snapshot.entities)
        return {
            "entities": len(self.snapshot.entities),
            "resources": len(self.snapshot.resources),
            "activities": activities,
        }

    def _render_system_view(self) -> None:
        snapshot = self.snapshot.as_dict()
        logs_df = pd.DataFrame(snapshot.get("logs", []))
        if not logs_df.empty:
            _render_table_with_preview("Environment logs", logs_df, key_prefix="environment-logs")
        else:
            st.info("No environment logs captured yet.")

    def _render_entities_view(self) -> None:
        entities: Iterable[dict[str, Any]] = self.snapshot.entities
        if not entities:
            st.info("No entities available.")
            return

        options = {f"{ent['name']} ({ent['id']})": ent for ent in entities}
        default_label = st.session_state.get("simpm_entity_label")
        labels = list(options.keys())
        selected_label = st.selectbox(
            "Select entity",
            labels,
            index=labels.index(default_label) if default_label in labels else 0,
        )
        st.session_state["simpm_entity_label"] = selected_label
        entity = options[selected_label]

        st.markdown(f"### Entity {entity['id']} • {entity['name']}")
        st.caption(f"Type: {entity.get('type', 'Unknown')}")

        attributes = entity.get("attributes") or entity.get("attr") or {}
        st.markdown("#### Attributes")
        if attributes:
            attr_rows = [
                {"Attribute": key, "Value": json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value}
                for key, value in attributes.items()
            ]
            attr_df = pd.DataFrame(attr_rows)
            _render_compact_table(attr_df)
        else:
            st.info("No attributes recorded for this entity.")

        schedule_df = pd.DataFrame(entity.get("schedule_log", []))
        if not schedule_df.empty:
            _render_schedule_summary(schedule_df, key_prefix=f"entity-{entity['id']}-schedule")

        waiting_df = pd.DataFrame(entity.get("waiting_log", []))
        if not waiting_df.empty:
            _render_waiting_log(waiting_df, key_prefix=f"entity-{entity['id']}-waiting")

        status_df = pd.DataFrame(entity.get("status_log", []))
        if not status_df.empty:
            _render_table_with_preview(
                "Status log",
                status_df,
                key_prefix=f"entity-{entity['id']}-status",
                analysis_renderer=None,
            )

    def _render_resources_view(self) -> None:
        resources: Iterable[dict[str, Any]] = self.snapshot.resources
        if not resources:
            st.info("No resources available.")
            return

        options = {f"{res['name']} ({res['id']})": res for res in resources}
        default_label = st.session_state.get("simpm_resource_label")
        labels = list(options.keys())
        selected_label = st.selectbox(
            "Select resource",
            labels,
            index=labels.index(default_label) if default_label in labels else 0,
        )
        st.session_state["simpm_resource_label"] = selected_label
        resource = options[selected_label]

        st.markdown(f"### Resource {resource['id']} • {resource['name']}")
        st.caption(
            f"Type: {resource.get('type', 'Unknown')} • Capacity: {resource.get('capacity', '-') }"
        )
        attributes = resource.get("attributes") or resource.get("attr")
        if attributes:
            st.markdown("**Attributes**")
            st.json(attributes)

        queue_df = pd.DataFrame(resource.get("queue_log", []))
        if not queue_df.empty:
            _render_queue_waiting_log(queue_df, key_prefix=f"resource-{resource['id']}-queue")

        status_df = pd.DataFrame(resource.get("status_log", []))
        if not status_df.empty:
            _render_resource_status(status_df, key_prefix=f"resource-{resource['id']}-status")

    def _render_activity_view(self) -> None:
        st.markdown("### Activity feed")
        activity_df = _activity_dataframe(self.snapshot)

        if activity_df.empty:
            st.info("No activity recorded for this run.")
            return

        standard_cols = [
            "activity",
            "start_time",
            "finish_time",
            "activity_id",
            "activity_name",
            "duration",
            "source",
            "entity_id",
            "entity_name",
        ]

        with st.container():
            st.markdown("<div class='simpm-panel'>", unsafe_allow_html=True)
            st.caption("Unified view across system, entities, and resources")
            tab_all, tab_by_name, tab_by_id = st.tabs(["All activity", "By activity name", "By activity id"])

            with tab_all:
                display_df = activity_df.copy()
                for col in standard_cols:
                    if col not in display_df.columns:
                        display_df[col] = None
                display_df = display_df[standard_cols]
                _render_table_preview("Activity", display_df, key_prefix="activity")
                st.markdown("#### duration")
                _render_duration_analysis(display_df, start_col="start_time")

            with tab_by_name:
                schedule_df = (
                    activity_df[activity_df["category"] == "schedule_log"].copy()
                    if "category" in activity_df.columns
                    else pd.DataFrame()
                )
                label_key = "activity-name-filter"
                self._render_activity_filter_tab(
                    activity_df,
                    label_candidates=["activity_name", "activity"],
                    label_key=label_key,
                    standard_cols=standard_cols,
                    label_title="Activity name",
                )

                name_col = None
                for candidate in ("activity_name", "activity", "activity_id"):
                    if candidate in schedule_df.columns:
                        name_col = candidate
                        break

                if schedule_df.empty or not name_col:
                    st.info("No scheduled activities with names are available to inspect.")
                    st.dataframe(activity_df, use_container_width=True)
                else:
                    schedule_df["activity_label"] = schedule_df[name_col].astype(str)
                    options = sorted(schedule_df["activity_label"].dropna().unique())

                    if not options:
                        st.info("No activity names found to display.")
                    else:
                        selected = st.multiselect(
                            "Select activities", options, default=options[:1], key=f"{label_key}-multi"
                        )

                        if not selected:
                            st.info("Choose at least one activity to view its schedule across entities.")
                        else:
                            filtered = schedule_df[schedule_df["activity_label"].isin(selected)].copy()

                            start_col = next((c for c in ("start_time", "start", "start_at") if c in filtered.columns), None)
                            end_col = next((c for c in ("finish_time", "end", "finish") if c in filtered.columns), None)
                            duration_col = "duration" if "duration" in filtered.columns else None
                            resource_col = next(
                                (c for c in ("resources_in_use", "resources", "resource", "resource_id", "resource_ids") if c in filtered.columns),
                                None,
                            )

                            if duration_col is None and start_col and end_col:
                                filtered["duration"] = pd.to_numeric(filtered[end_col], errors="coerce") - pd.to_numeric(
                                    filtered[start_col], errors="coerce"
                                )
                                duration_col = "duration"

                            columns_to_show: list[str] = []
                            label_map: dict[str, str] = {"activity_label": "Activity"}
                            for col, label in (
                                ("activity_label", "Activity"),
                                ("entity_name", "Entity"),
                                ("entity_id", "Entity ID"),
                                (start_col, "Start"),
                                (end_col, "Finish"),
                                (duration_col, "Duration"),
                                (resource_col, "Resources in use"),
                            ):
                                if col and col in filtered.columns:
                                    columns_to_show.append(col)
                                    label_map[col] = label

                            if not columns_to_show:
                                st.info("No activity timing details available for the selected name.")
                            else:
                                if start_col and start_col in filtered.columns:
                                    filtered = filtered.sort_values(start_col)
                                display_df = filtered[columns_to_show].rename(columns=label_map)
                                st.dataframe(display_df, use_container_width=True)
                                if duration_col:
                                    _render_duration_analysis(
                                        filtered,
                                        duration_col=duration_col,
                                        start_col=start_col,
                                    )
            st.markdown("</div>", unsafe_allow_html=True)

    def _render_activity_filter_tab(
        self,
        activity_df: pd.DataFrame,
        *,
        label_candidates: list[str],
        label_key: str,
        standard_cols: list[str],
        label_title: str,
    ) -> None:
        schedule_df = (
            activity_df[activity_df["category"] == "schedule_log"].copy()
            if "category" in activity_df.columns
            else pd.DataFrame()
        )

        label_col = next((candidate for candidate in label_candidates if candidate in schedule_df.columns), None)

        if schedule_df.empty or not label_col:
            st.info(f"No scheduled activities with {label_title.lower()}s are available to inspect.")
            fallback_df = activity_df.copy()
            for col in standard_cols:
                if col not in fallback_df.columns:
                    fallback_df[col] = None
            _render_table_preview("Activity", fallback_df[standard_cols], key_prefix=label_key)
            return

        schedule_df["activity_label"] = schedule_df[label_col].astype(str)
        options = sorted(schedule_df["activity_label"].dropna().unique())

        if not options:
            st.info(f"No {label_title.lower()}s found to display.")
            return

        selected = st.selectbox(
            f"Select {label_title.lower()}",
            options,
            index=0,
            key=label_key,
        )

        if not selected:
            st.info(f"Choose a {label_title.lower()} to view its schedule across entities.")
            return

        filtered = schedule_df[schedule_df["activity_label"] == selected].copy()
        start_col = next((c for c in ("start_time", "start", "start_at") if c in filtered.columns), None)
        end_col = next((c for c in ("finish_time", "end", "finish") if c in filtered.columns), None)

        if "duration" not in filtered.columns and start_col and end_col:
            filtered["duration"] = pd.to_numeric(filtered[end_col], errors="coerce") - pd.to_numeric(
                filtered[start_col], errors="coerce"
            )

        for col in standard_cols:
            if col not in filtered.columns:
                filtered[col] = None

        display_df = filtered[standard_cols]
        _render_table_preview(f"Activity by {label_title.lower()}", display_df, key_prefix=label_key)
        st.markdown("#### duration")
        _render_duration_analysis(display_df, start_col="start_time")

    def run(self, host: str = "127.0.0.1", port: int = 8050, async_mode: bool = False):
        """Start the Streamlit server for this dashboard."""

        global _ACTIVE_DASHBOARD
        _ACTIVE_DASHBOARD = self

        snapshot_file = Path(tempfile.mkdtemp()) / "simpm_snapshot.json"
        snapshot_file.write_text(json.dumps(self.snapshot.as_dict()))

        cmd = [
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


def build_app(env) -> StreamlitDashboard:
    """Build a Streamlit dashboard bound to the given environment."""

    snapshot = collect_run_data(env)
    logger.debug("Prepared initial snapshot with %s entities", len(snapshot.entities))
    return StreamlitDashboard(snapshot=snapshot)


def run_post_dashboard(env, host: str = "127.0.0.1", port: int = 8050, start_async: bool = True):
    """Launch the Streamlit dashboard for a simulation environment."""

    if isinstance(env, RunSnapshot):
        snapshot = env
    else:
        snapshot = collect_run_data(env)
    dashboard = StreamlitDashboard(snapshot=snapshot)
    logger.info(
        "Starting Streamlit dashboard at http://%s:%s (async=%s)", host, port, start_async
    )
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

    snapshot = _ACTIVE_DASHBOARD.snapshot if _ACTIVE_DASHBOARD else _load_snapshot_from_file(args.data)
    if snapshot is None:
        st.title("SimPM Dashboard")
        st.warning(
            "Run a simulation with dashboard=True to populate this view."
        )
        return
    StreamlitDashboard(snapshot=snapshot).render()


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
