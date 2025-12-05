"""Streamlit dashboard for SimPM runs."""
from __future__ import annotations

import io
import inspect
import logging
import threading
from dataclasses import dataclass, field
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

from simpm.dashboard_data import collect_run_data

logger = logging.getLogger(__name__)


_ACTIVE_DASHBOARD: "StreamlitDashboard | None" = None


def _find_time_column(df: pd.DataFrame) -> str | None:
    """Return the first column name that looks like a simulation time axis."""

    for col in df.columns:
        if "time" in str(col).lower():
            return col
    return None


def _download_button(label: str, df: pd.DataFrame, file_prefix: str) -> None:
    """Render a CSV download button for the given dataframe."""

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label,
        data=io.BytesIO(csv_bytes),
        file_name=f"{file_prefix}.csv",
        mime="text/csv",
        use_container_width=True,
    )


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
    """Render analysis tabs for every numeric column in the dataframe."""

    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty:
        st.info("No numeric columns available for analysis.")
        return

    for col in numeric_df.columns:
        st.markdown(f"### {col} insights")
        time_axis = time_col or _find_time_column(df.drop(columns=[col], errors="ignore"))
        tab_series, tab_hist, tab_cdf, tab_stats = st.tabs(
            ["Time series", "Histogram (PDF)", "Empirical CDF", "Statistics"]
        )

        with tab_series:
            x = df[time_axis] if time_axis and time_axis in df.columns else df.index
            fig = px.line(x=x, y=df[col], labels={"x": time_axis or "Index", "y": col})
            fig.update_traces(line_color="#3a7859")
            st.plotly_chart(fig, use_container_width=True)

        with tab_hist:
            fig = px.histogram(df, x=col, nbins=min(30, max(5, len(df))), histnorm="probability density")
            fig.update_traces(marker_color="#5bbd89")
            st.plotly_chart(fig, use_container_width=True)

        with tab_cdf:
            fig = px.ecdf(df, x=col)
            fig.update_traces(line_color="#3a7859")
            st.plotly_chart(fig, use_container_width=True)

        with tab_stats:
            stats_df = _basic_statistics(df[col])
            st.dataframe(stats_df, use_container_width=True)


def _render_table_with_preview(title: str, df: pd.DataFrame, key_prefix: str) -> None:
    """Display the first/last five rows of a dataframe and downloads."""

    st.markdown(f"## {title}")
    if df.empty:
        st.info("No records available yet.")
        return

    st.caption("First 5 rows")
    st.dataframe(df.head(5), use_container_width=True)
    st.caption("Last 5 rows")
    st.dataframe(df.tail(5), use_container_width=True)
    _download_button("Download CSV", df, file_prefix=key_prefix)
    _render_numeric_analysis(df, time_col=_find_time_column(df))


def _load_logo() -> bytes | None:
    logo_path = Path(__file__).resolve().parent.parent / "docs" / "source" / "images" / "simpm_logo.png"
    if logo_path.exists():
        return logo_path.read_bytes()
    return None


def _styled_container() -> None:
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.5rem;}
        .stTabs [data-baseweb="tab"] {background-color: #f4fbf7; border-radius: 8px; color: #1f3f2b;}
        .stTabs [aria-selected="true"] {border: 1px solid #7fd3a8 !important; color: #0c2a1b;}
        .stButton>button {border-radius: 10px; border: 1px solid #7fd3a8; color: #0c2a1b; background: white;}
        .status-chip {padding: 0.35rem 0.75rem; border-radius: 999px; border: 1px solid #7fd3a8; display: inline-block;}
        </style>
        """,
        unsafe_allow_html=True,
    )


@dataclass
class DashboardObserver:
    """Observer used to track simulation lifecycle for the dashboard."""

    is_running: bool = False
    last_finished_at: float | None = None
    last_started_at: float | None = None

    def on_run_started(self, env) -> None:  # pragma: no cover - invoked at runtime
        self.is_running = True
        self.last_started_at = getattr(env, "now", None)

    def on_run_finished(self, env) -> None:  # pragma: no cover - invoked at runtime
        self.is_running = False
        self.last_finished_at = getattr(env, "now", None)


@dataclass
class StreamlitDashboard:
    """Encapsulates the live dashboard rendering logic."""

    env: Any
    observer: DashboardObserver = field(default_factory=DashboardObserver)

    def __post_init__(self) -> None:
        if hasattr(self.env, "register_observer"):
            self.env.register_observer(self.observer)

    def render(self) -> None:
        """Render the dashboard using Streamlit primitives."""

        st.set_page_config(
            page_title=f"SimPM Dashboard • {getattr(self.env, 'name', 'Environment')}",
            layout="wide",
            page_icon=_load_logo() or None,
        )
        _styled_container()

        st_autorefresh = getattr(st, "autorefresh", None)
        if callable(st_autorefresh):  # pragma: no branch - optional API
            st_autorefresh(interval=2000, limit=None, key="simpm-refresh")

        header_cols = st.columns([1, 3, 1])
        with header_cols[0]:
            logo = _load_logo()
            if logo:
                st.image(logo, width=96)
        with header_cols[1]:
            st.title("SimPM live dashboard")
            st.caption("Modern monitoring for your simulations")
        with header_cols[2]:
            status_label = "Running" if self.observer.is_running else "Completed"
            status_color = "#4caf50" if self.observer.is_running else "#607d8b"
            st.markdown(
                f"<span class='status-chip' style='color:{status_color};'>{status_label}</span>",
                unsafe_allow_html=True,
            )

        tabs = st.tabs(["System", "Entities", "Resources"])
        with tabs[0]:
            self._render_system_view()
        with tabs[1]:
            self._render_entities_view()
        with tabs[2]:
            self._render_resources_view()

    def _render_system_view(self) -> None:
        snapshot = collect_run_data(self.env).as_dict()
        env_info = snapshot.get("environment", {})

        st.markdown("### Overview")
        cols = st.columns(3)
        cols[0].metric("Environment", env_info.get("name", "Environment"))
        cols[1].metric("Run ID", env_info.get("run_id", "-"))
        cols[2].metric("Current sim time", getattr(self.env, "now", 0))

        logs_df = pd.DataFrame(snapshot.get("logs", []))
        if not logs_df.empty:
            _render_table_with_preview("Environment logs", logs_df, key_prefix="environment-logs")
        else:
            st.info("No environment logs captured yet.")

    def _render_entities_view(self) -> None:
        entities: Iterable[Any] = getattr(self.env, "entities", [])
        if not entities:
            st.info("No entities available.")
            return

        options = {f"{ent.name} ({ent.id})": ent for ent in entities}
        selected_label = st.selectbox("Select entity", list(options.keys()))
        entity = options[selected_label]

        st.markdown(f"### Entity {entity.id} • {entity.name}")
        st.caption(f"Type: {entity.__class__.__name__}")

        if hasattr(entity, "schedule"):
            schedule_df = entity.schedule()
            _render_table_with_preview("Schedule", schedule_df, key_prefix=f"entity-{entity.id}-schedule")

        if hasattr(entity, "waiting_log"):
            waiting_df = entity.waiting_log()
            _render_table_with_preview("Waiting log", waiting_df, key_prefix=f"entity-{entity.id}-waiting")

        if hasattr(entity, "status_log"):
            status_df = entity.status_log()
            _render_table_with_preview("Status log", status_df, key_prefix=f"entity-{entity.id}-status")

        if hasattr(entity, "waiting_time"):
            waiting_time = entity.waiting_time()
            waiting_df = pd.DataFrame({"waiting_time": waiting_time})
            _render_table_with_preview("Waiting durations", waiting_df, key_prefix=f"entity-{entity.id}-waiting-time")

    def _render_resources_view(self) -> None:
        resources: Iterable[Any] = getattr(self.env, "resources", [])
        if not resources:
            st.info("No resources available.")
            return

        options = {f"{res.name} ({res.id})": res for res in resources}
        selected_label = st.selectbox("Select resource", list(options.keys()))
        resource = options[selected_label]

        st.markdown(f"### Resource {resource.id} • {resource.name}")
        st.caption(f"Type: {resource.__class__.__name__} • Capacity: {getattr(resource, 'capacity', '-')}")

        if hasattr(resource, "queue_log"):
            queue_df = resource.queue_log()
            _render_table_with_preview("Queue log", queue_df, key_prefix=f"resource-{resource.id}-queue")

        if hasattr(resource, "status_log"):
            status_df = resource.status_log()
            _render_table_with_preview("Status log", status_df, key_prefix=f"resource-{resource.id}-status")

        if hasattr(resource, "waiting_time"):
            waits = resource.waiting_time()
            waits_df = pd.DataFrame({"waiting_time": waits})
            _render_table_with_preview("Waiting durations", waits_df, key_prefix=f"resource-{resource.id}-waiting-time")

    def run(self, host: str = "127.0.0.1", port: int = 8050, async_mode: bool = True):
        """Start the Streamlit server for this dashboard."""

        from streamlit.web import bootstrap

        global _ACTIVE_DASHBOARD
        _ACTIVE_DASHBOARD = self

        flag_options = {"server.address": host, "server.port": port, "server.headless": True}

        def _launch():  # pragma: no cover - starts a live server
            sig = inspect.signature(bootstrap.run)
            if "command_line" in sig.parameters:
                bootstrap.run(__file__, command_line=f"streamlit run {Path(__file__).resolve()}", args=[], flag_options=flag_options)
            else:
                bootstrap.run(__file__, args=[], flag_options=flag_options)

        if async_mode:
            thread = threading.Thread(target=_launch, daemon=True)
            thread.start()
            return thread
        _launch()


def build_app(env) -> StreamlitDashboard:
    """Build a Streamlit dashboard bound to the given environment."""

    snapshot = collect_run_data(env)
    logger.debug("Prepared initial snapshot with %s entities", len(snapshot.entities))
    return StreamlitDashboard(env=env)


def run_post_dashboard(env, host: str = "127.0.0.1", port: int = 8050, start_async: bool = True):
    """Launch the Streamlit dashboard for a simulation environment."""

    dashboard = build_app(env)
    logger.info(
        "Starting Streamlit dashboard at http://%s:%s (async=%s)", host, port, start_async
    )
    dashboard.run(host=host, port=port, async_mode=start_async)
    return dashboard


def main() -> None:  # pragma: no cover - executed by Streamlit runtime
    if _ACTIVE_DASHBOARD is None:
        st.title("SimPM Dashboard")
        st.warning(
            "Run a simulation with dashboard=True to populate this view."
        )
        return
    _ACTIVE_DASHBOARD.render()


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
