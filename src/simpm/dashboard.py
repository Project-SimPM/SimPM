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
from typing import Any, Iterable

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
            "Metric": ["Count", "Mean", "Median", "Min", "Max", "Std"],
            "Value": [
                int(series.count()),
                series.mean(),
                series.median(),
                series.min(),
                series.max(),
                series.std(ddof=0),
            ],
        }
    )


def _render_numeric_analysis(df: pd.DataFrame, time_col: str | None = None) -> None:
    """Render analysis tabs for a selected numeric column in the dataframe."""

    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty:
        st.info("No numeric columns available for analysis.")
        return

    col = st.selectbox("Select numeric column", list(numeric_df.columns))
    time_axis = time_col or _find_time_column(df.drop(columns=[col], errors="ignore"))
    tab_series, tab_hist, tab_cdf, tab_stats = st.tabs(
        ["Time series", "Histogram (PDF)", "Empirical CDF", "Statistics"]
    )

    with tab_series:
        x = df[time_axis] if time_axis and time_axis in df.columns else df.index
        fig = px.line(x=x, y=df[col], labels={"x": time_axis or "Index", "y": col})
        fig.update_traces(line_color="#3a7859")
        st.plotly_chart(fig, width="stretch")

    with tab_hist:
        fig = px.histogram(df, x=col, nbins=min(30, max(5, len(df))), histnorm="probability density")
        fig.update_traces(marker_color="#5bbd89")
        st.plotly_chart(fig, width="stretch")

    with tab_cdf:
        fig = px.ecdf(df, x=col)
        fig.update_traces(line_color="#3a7859")
        st.plotly_chart(fig, width="stretch")

    with tab_stats:
        stats_df = _basic_statistics(df[col])
        st.dataframe(stats_df, width="stretch")


def _render_table_with_preview(title: str, df: pd.DataFrame, key_prefix: str) -> None:
    """Display a truncated preview of a dataframe with download support."""

    st.markdown(f"## {title}")
    if df.empty:
        st.info("No records available yet.")
        return

    st.caption(
        "Showing the first 5 rows" + (f" of {len(df)} total" if len(df) > 5 else "")
    )
    download_icon_b64 = _asset_base64("download.png")
    csv_b64 = base64.b64encode(df.to_csv(index=False).encode("utf-8")).decode("utf-8")
    icon_html = ""
    if download_icon_b64:
        icon_html = (
            "<img "
            f"src='data:image/png;base64,{download_icon_b64}' "
            "style='position:absolute; top:6px; left:6px; "
            "width:24px; height:24px; cursor:pointer;' "
            f"onclick=\"window.location.href='data:text/csv;base64,{csv_b64}'\" "
            "alt='Download CSV' />"
        )

    table_html = df.head(5).to_html(index=True)
    container_html = (
        "<div style='position:relative; display:inline-block; padding-left:32px;'>"
        f"{icon_html}"
        f"{table_html}"
        "</div>"
    )
    st.markdown(container_html, unsafe_allow_html=True)

    if len(df) > 5:
        st.info(
            "Table truncated for readability. Download the CSV to view the complete dataset."
        )
    _render_numeric_analysis(df, time_col=_find_time_column(df))


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
        .stTabs [data-baseweb="tab"] {background-color: #f4fbf7; border-radius: 8px; color: #1f3f2b; border: 1px solid #cce8d9;}
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

        header_cols = st.columns([1, 2, 1])
        with header_cols[1]:
            _render_logo(_load_logo())

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

        schedule_df = pd.DataFrame(entity.get("schedule_log", []))
        if not schedule_df.empty:
            _render_table_with_preview("Schedule", schedule_df, key_prefix=f"entity-{entity['id']}-schedule")

        waiting_df = pd.DataFrame(entity.get("waiting_log", []))
        if not waiting_df.empty:
            _render_table_with_preview("Waiting log", waiting_df, key_prefix=f"entity-{entity['id']}-waiting")

        status_df = pd.DataFrame(entity.get("status_log", []))
        if not status_df.empty:
            _render_table_with_preview("Status log", status_df, key_prefix=f"entity-{entity['id']}-status")

        waiting_time = entity.get("waiting_time", []) or []
        if waiting_time:
            waiting_df = pd.DataFrame({"waiting_time": waiting_time})
            _render_table_with_preview(
                "Waiting durations", waiting_df, key_prefix=f"entity-{entity['id']}-waiting-time"
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

        queue_df = pd.DataFrame(resource.get("queue_log", []))
        if not queue_df.empty:
            _render_table_with_preview("Queue log", queue_df, key_prefix=f"resource-{resource['id']}-queue")

        status_df = pd.DataFrame(resource.get("status_log", []))
        if not status_df.empty:
            _render_table_with_preview("Status log", status_df, key_prefix=f"resource-{resource['id']}-status")

        waits = resource.get("waiting_time", []) or []
        if waits:
            waits_df = pd.DataFrame({"waiting_time": waits})
            _render_table_with_preview(
                "Waiting durations", waits_df, key_prefix=f"resource-{resource['id']}-waiting-time"
            )

    def _render_activity_view(self) -> None:
        st.markdown("### Activity feed")
        activity_df = _activity_dataframe(self.snapshot)

        if activity_df.empty:
            st.info("No activity recorded for this run.")
            return

        with st.container():
            st.markdown("<div class='simpm-panel'>", unsafe_allow_html=True)
            st.caption("Unified view across system, entities, and resources")
            _render_table_with_preview("Activity", activity_df, key_prefix="activity")
            st.markdown("</div>", unsafe_allow_html=True)

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
