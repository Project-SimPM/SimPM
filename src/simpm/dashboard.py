"""Plotly Dash dashboard for SimPM runs."""
from __future__ import annotations

import json
import logging
import threading
from statistics import fmean, median, pstdev
from typing import Any

try:
    import dash
    from dash import Dash, Input, Output, State, callback_context, dash_table, dcc, html
    import plotly.express as px
except ImportError as exc:  # pragma: no cover - handled at runtime
    raise ImportError(
        "Plotly Dash is required for dashboard mode. Install with `pip install dash plotly`."
    ) from exc

from simpm.dashboard_data import collect_run_data


CONTENT_STYLE = {
    "maxWidth": "1240px",
    "margin": "0 auto",
    "padding": "0 18px 32px",
}

logger = logging.getLogger(__name__)

BUTTON_BASE_STYLE = {
    "borderRadius": "12px",
    "border": "1px solid transparent",
    "padding": "10px 14px",
    "margin": "6px",
    "cursor": "pointer",
    "boxShadow": "0 1px 3px rgba(0, 0, 0, 0.15)",
}


def _select_dash_runner(app: Dash):
    """Return the callable used to run a Dash app and its name for logging."""

    try:
        run_server_method = getattr(app, "run_server")
    except Exception:  # pragma: no cover - Dash may raise on obsolete attrs
        run_server_method = None

    if callable(run_server_method):
        return run_server_method, "run_server"

    run_method = getattr(app, "run", None)
    if callable(run_method):
        return run_method, "run"

    raise RuntimeError("Dash app provides neither 'run' nor 'run_server' methods")

ENTITY_BUTTON_STYLE = {
    "backgroundColor": "#e6f4ea",
    "borderColor": "#34a853",
    "color": "#0b3d1b",
}

RESOURCE_BUTTON_STYLE = {
    "backgroundColor": "#e6f0ff",
    "borderColor": "#1a73e8",
    "color": "#0b2a66",
}

ENVIRONMENT_BUTTON_STYLE = {
    "backgroundColor": "#f1f3f4",
    "borderColor": "#5f6368",
    "color": "#202124",
    "borderRadius": "4px",
}

ACTIVITY_BUTTON_STYLE = {
    "backgroundColor": "#fff4e6",
    "borderColor": "#f9ab00",
    "color": "#6a4a00",
}


def _styled_button(label: str, path: str, style: dict[str, str]):
    return html.Button(
        label,
        id={"type": "nav-node", "path": path},
        n_clicks=0,
        style={**BUTTON_BASE_STYLE, **style},
    )


def _activity_name_map(run_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Aggregate activities and logs keyed by activity name."""

    activities: dict[str, dict[str, Any]] = {}
    for entity in run_data.get("entities", []):
        name_to_ids: dict[str, set[int]] = {}
        for act in entity.get("activities", []):
            name = act.get("activity_name", "Activity")
            activity_entry = activities.setdefault(
                name,
                {
                    "durations": [],
                    "logs": [],
                    "instances": [],
                    "duration_specs": [],
                    "sampled_durations": [],
                },
            )
            activity_entry["instances"].append({"entity_id": entity.get("id"), **act})
            if act.get("duration") is not None:
                activity_entry["durations"].append(act["duration"])
            if act.get("duration_info"):
                activity_entry["duration_specs"].append(act["duration_info"])
            if act.get("sampled_duration") is not None:
                activity_entry["sampled_durations"].append(act["sampled_duration"])
            name_to_ids.setdefault(name, set()).add(act.get("activity_id"))

        for log in entity.get("logs", []):
            act_name = log.get("activity_name")
            if act_name:
                activities.setdefault(
                    act_name,
                    {"durations": [], "logs": [], "instances": [], "duration_specs": [], "sampled_durations": []},
                )["logs"].append(log)
                continue
            if log.get("source_type") == "activity":
                for candidate_name, activity_ids in name_to_ids.items():
                    if log.get("source_id") in activity_ids:
                        activities.setdefault(
                            candidate_name,
                            {"durations": [], "logs": [], "instances": [], "duration_specs": [], "sampled_durations": []},
                        )["logs"].append(log)
                        break
    for log in run_data.get("logs", []):
        if log.get("activity_name"):
            activities.setdefault(
                log["activity_name"],
                {"durations": [], "logs": [], "instances": [], "duration_specs": [], "sampled_durations": []},
            )["logs"].append(log)
    return activities


def _collect_logs(run_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect and flatten logs from environment, entities, and resources."""

    seen: set[str] = set()
    rows: list[dict[str, Any]] = []

    def _push(log: dict[str, Any]):
        key = json.dumps(log, sort_keys=True, default=str)
        if key in seen:
            return
        seen.add(key)
        entry = dict(log)
        metadata = entry.pop("metadata", None)
        if isinstance(metadata, dict):
            for meta_key, meta_value in metadata.items():
                entry[f"metadata.{meta_key}"] = meta_value
        rows.append(entry)

    for log in run_data.get("logs", []):
        if isinstance(log, dict):
            _push(log)

    for entity in run_data.get("entities", []):
        for log in entity.get("logs", []):
            if isinstance(log, dict):
                _push(log)

    for resource in run_data.get("resources", []):
        for log in resource.get("logs", []):
            if isinstance(log, dict):
                _push(log)

    return rows


def _describe(values: list[float]) -> list[dict[str, Any]]:
    """Return descriptive statistics for a series of numeric values."""

    if not values:
        return []
    ordered = sorted(values)
    stats = [
        {"Metric": "Count", "Value": len(ordered)},
        {"Metric": "Min", "Value": ordered[0]},
        {"Metric": "Max", "Value": ordered[-1]},
        {"Metric": "Mean", "Value": fmean(ordered)},
        {"Metric": "Median", "Value": median(ordered)},
    ]
    if len(ordered) > 1:
        stats.append({"Metric": "Std Dev", "Value": pstdev(ordered)})
    return stats


def _stat_grid(stats: list[dict[str, Any]]):
    if not stats:
        return html.Div("No statistics available.")
    return html.Div(
        [
            html.Div(
                [
                    html.Div(stat["Metric"], style={"fontWeight": "bold"}),
                    html.Div(f"{stat['Value']}", style={"fontSize": "0.95rem"}),
                ],
                className="mini-card",
            )
            for stat in stats
        ],
        className="mini-card-grid",
    )


def _distribution_tabs(values: list[float], title: str, x_label: str = "Value"):
    if not values:
        return html.Div("No data available for this distribution.")

    def _histogram(histnorm: str | None = None, cumulative: bool = False):
        fig = px.histogram(
            x=values,
            labels={"x": x_label},
            nbins=min(30, max(5, len(values))),
            histnorm=histnorm,
            title=title,
        )
        if cumulative:
            fig.update_traces(cumulative_enabled=True)
        fig.update_layout(height=320, margin={"t": 48, "r": 16, "l": 16, "b": 24})
        return fig

    def _box():
        fig = px.box(y=values, labels={"y": x_label}, points="all", title=title)
        fig.update_layout(height=320, margin={"t": 48, "r": 16, "l": 16, "b": 24})
        return fig

    tabs = [
        dcc.Tab(label="Histogram", children=dcc.Graph(figure=_histogram())),
        dcc.Tab(label="PDF", children=dcc.Graph(figure=_histogram(histnorm="probability density"))),
        dcc.Tab(label="CDF", children=dcc.Graph(figure=_histogram(histnorm="probability", cumulative=True))),
        dcc.Tab(label="Box", children=dcc.Graph(figure=_box())),
    ]

    if hasattr(dcc, "Tabs") and hasattr(dcc, "Tab"):
        return dcc.Tabs(children=tabs)
    return html.Div([tab.children for tab in tabs])


def _data_table(records: list[dict[str, Any]], empty_message: str, page_size: int = 10):
    if not records:
        return html.Div(empty_message)
    columns = [{"name": col, "id": col} for col in sorted({k for row in records for k in row.keys()})]
    return dash_table.DataTable(
        data=records,
        columns=columns,
        page_size=page_size,
        style_table={"overflowX": "auto"},
    )


def _section(title: str, children):
    return html.Div(
        [
            html.Div(title, className="section-title"),
            html.Div(children, className="nav-pill-grid"),
        ],
        className="panel-card selection-card",
    )


def _build_tab_selection(run_data: dict[str, Any], tab: str):
    entities = run_data.get("entities", [])
    resources = run_data.get("resources", [])
    env_name = run_data.get("environment", {}).get("name", "Environment")

    if tab == "environment":
        return _section(
            "Environment",
            _styled_button(
                env_name,
                "environment",
                {**ENVIRONMENT_BUTTON_STYLE, "padding": "8px 12px", "margin": "0"},
            ),
        )

    if tab == "entities":
        entity_buttons = [
            _styled_button(f"{ent['name']} (Entity {ent['id']})", f"entity:{ent['id']}", ENTITY_BUTTON_STYLE)
            for ent in entities
        ]
        return _section("Entities", entity_buttons or html.Div("No entities available."))

    if tab == "resources":
        resource_buttons = [
            _styled_button(f"{res['name']} (Resource {res['id']})", f"resource:{res['id']}", RESOURCE_BUTTON_STYLE)
            for res in resources
        ]
        return _section("Resources", resource_buttons or html.Div("No resources available."))

    activity_map = _activity_name_map(run_data)
    activity_buttons = [
        _styled_button(f"{name} ({len(data['instances'])} instances)", f"activity-name:{name}", ACTIVITY_BUTTON_STYLE)
        for name, data in sorted(activity_map.items())
    ]
    return _section("Activities", activity_buttons or html.Div("No activities available."))


def _build_tabs():
    tabs = [
        {"label": "Environment", "value": "environment"},
        {"label": "Entities", "value": "entities"},
        {"label": "Resources", "value": "resources"},
        {"label": "Activities", "value": "activities"},
    ]
    if hasattr(dcc, "Tabs") and hasattr(dcc, "Tab"):
        return dcc.Tabs(
            id="section-tabs",
            value="environment",
            className="main-tabs",
            children=[
                dcc.Tab(
                    label=tab["label"],
                    value=tab["value"],
                    className="tab-item",
                    selected_className="tab-item--selected",
                )
                for tab in tabs
            ],
        )
    # Fallback for environments where dcc.Tabs is unavailable. RadioItems still provides
    # a "value" property, keeping existing callbacks functional even without tab
    # components. If RadioItems is also unavailable (e.g., in minimal test stubs),
    # return a basic Div with the expected props so callbacks can bind safely.
    if hasattr(dcc, "RadioItems"):
        return dcc.RadioItems(
            id="section-tabs",
            options=tabs,
            value="environment",
            inline=True,
            labelStyle={"marginRight": "12px"},
        )
    return html.Div("Environment", id="section-tabs", value="environment", style={"marginBottom": "12px"})


def _build_overview_cards(run_data: dict[str, Any]):
    env = run_data.get("environment", {})
    end_time = env.get("time", {}).get("end")
    entities = run_data.get("entities", [])
    resources = run_data.get("resources", [])
    activities = [act for ent in entities for act in ent.get("activities", []) if act.get("duration") is not None]
    duration_stats = _describe([act["duration"] for act in activities if act.get("duration") is not None])

    cards = [
        html.Div(
            [
                html.Div(env.get("name", "Environment"), style={"fontWeight": "bold", "fontSize": "1.05rem"}),
                html.Div(f"Run ID: {env.get('run_id', '-')}", style={"color": "#5f6368"}),
                html.Div(f"Time span: 0 → {end_time if end_time is not None else '-'}"),
            ],
            className="stat-card stat-card--accent",
        ),
        html.Div(
            _stat_grid(
                [
                    {"Metric": "Entities", "Value": len(entities)},
                    {"Metric": "Resources", "Value": len(resources)},
                    {"Metric": "Activities", "Value": len(activities)},
                ]
            ),
            className="stat-card",
        ),
    ]

    if duration_stats:
        cards.append(
            html.Div(
                [
                    html.Div("Activity durations", style={"fontWeight": "bold"}),
                    _stat_grid(duration_stats),
                ],
                className="stat-card",
            )
        )

    return html.Div(cards, className="card-grid")


def _global_activity_plot(run_data: dict[str, Any]):
    durations = []
    for ent in run_data.get("entities", []):
        for act in ent.get("activities", []):
            if act.get("duration") is not None:
                durations.append(act["duration"])
    if not durations:
        return html.Div("No activity data available.")
    return html.Div(
        [
            html.Div("Activity duration statistics", className="section-title"),
            _stat_grid(_describe(durations)),
            _distribution_tabs(durations, "Activity duration distribution", x_label="Duration"),
        ],
        className="panel-card",
    )


def _environment_logs(run_data: dict[str, Any]):
    logs = _collect_logs(run_data)
    sections = []

    entity_waits = [t for ent in run_data.get("entities", []) for t in (ent.get("waiting_time") or [])]
    resource_waits = [t for res in run_data.get("resources", []) for t in (res.get("waiting_time") or [])]
    summary_cards = []
    if entity_waits:
        summary_cards.append(
            html.Div(
                [html.Div("Entity waiting durations", className="section-title"), _stat_grid(_describe(entity_waits))],
                className="panel-card",
            )
        )
    if resource_waits:
        summary_cards.append(
            html.Div(
                [html.Div("Resource waiting durations", className="section-title"), _stat_grid(_describe(resource_waits))],
                className="panel-card",
            )
        )
    if summary_cards:
        sections.append(html.Div(summary_cards, style={"display": "grid", "gridGap": "8px"}))

    if logs:
        columns = [
            {"name": col, "id": col}
            for col in sorted({k for row in logs for k in row.keys()})
        ]
        sections.append(
            html.Div(
                [
                    html.H5("Event log", className="section-title"),
                    dash_table.DataTable(
                        data=logs,
                        columns=columns,
                        page_size=10,
                        style_table={"overflowX": "auto"},
                    ),
                ]
                ,
                className="panel-card",
            )
        )
    else:
        sections.append(html.Div("No logs collected for this run.", className="panel-card"))

    waiting_rows = []
    for ent in run_data.get("entities", []):
        for episode in ent.get("waiting_log", []) or []:
            waiting_rows.append({"entity_id": ent.get("id"), **episode})

    waiting_table = _data_table(
        waiting_rows,
        "No waiting episodes recorded across entities.",
        page_size=10,
    )
    sections.append(
        html.Div(
            [
                html.H5("Entity waiting episodes", className="section-title"),
                waiting_table,
                _distribution_tabs(entity_waits, "Entity waiting durations", x_label="Duration"),
            ],
            className="panel-card",
        )
    )

    resource_queue_rows = []
    for res in run_data.get("resources", []):
        for entry in res.get("queue_log", []) or []:
            resource_queue_rows.append({"resource_id": res.get("id"), **entry})

    queue_table = _data_table(
        resource_queue_rows,
        "No queue activity recorded across resources.",
        page_size=10,
    )
    sections.append(
        html.Div(
            [
                html.H5("Resource queue log", className="section-title"),
                queue_table,
                _distribution_tabs(resource_waits, "Resource waiting durations", x_label="Duration"),
            ],
            className="panel-card",
        )
    )

    return html.Div(sections, className="panel-stack")


def _entity_timeline(entity: dict[str, Any]):
    activities = entity.get("activities", [])
    rows = []
    for act in activities:
        if act.get("end") is None:
            continue
        rows.append(
            {
                "Task": act["activity_name"],
                "Start": act["start"],
                "Finish": act["end"],
            }
        )
    if not rows:
        return html.Div("No completed activities to visualize.")
    fig = px.timeline(rows, x_start="Start", x_end="Finish", y="Task")
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=300)
    return dcc.Graph(figure=fig)


def _entity_logs(entity: dict[str, Any]):
    sections = []

    sections.append(
        html.Div(
            [html.H5("Schedule log", className="section-title"), _data_table(entity.get("schedule_log", []), "No schedule recorded.")],
            className="panel-card",
        )
    )
    sections.append(
        html.Div(
            [html.H5("Status log", className="section-title"), _data_table(entity.get("status_log", []), "No status changes recorded.")],
            className="panel-card",
        )
    )
    sections.append(
        html.Div(
            [
                html.H5("Waiting episodes", className="section-title"),
                _data_table(entity.get("waiting_log", []), "No waiting episodes recorded."),
            ],
            className="panel-card",
        )
    )

    waiting_times = entity.get("waiting_time") or []
    if waiting_times:
        sections.append(
            html.Div(
                [
                    html.Div("Waiting time statistics", className="section-title"),
                    _stat_grid(_describe(waiting_times)),
                    _distribution_tabs(waiting_times, "Waiting time distribution", x_label="Duration"),
                ],
                className="panel-card",
            )
        )
    else:
        sections.append(html.Div("No waiting durations recorded.", className="panel-card"))

    logs = entity.get("logs", [])
    sections.append(
        html.Div(
            [html.H5("Event log", className="section-title"), _data_table(logs, "No logs collected for this entity.")],
            className="panel-card",
        )
    )

    return html.Div(sections, className="panel-stack")


def _activity_distribution(entity: dict[str, Any], activity_id: int):
    durations = [act["duration"] for act in entity.get("activities", []) if act.get("activity_id") == activity_id and act.get("duration") is not None]
    if not durations:
        return html.Div("No duration data available for this activity.")
    return html.Div(
        [
            _stat_grid(_describe(durations)),
            _distribution_tabs(durations, "Activity duration distribution", x_label="Duration"),
        ],
        style={"display": "grid", "gridGap": "6px"},
    )


def _resource_usage(resource: dict[str, Any]):
    status_log = resource.get("status_log", [])
    if not status_log:
        return html.Div("No status records available for this resource.")

    times = [row.get("time") for row in status_log]
    in_use = [row.get("in_use") for row in status_log]
    queue = [row.get("queue_length") for row in status_log]

    fig = px.step(
        x=times,
        y=[in_use, queue],
        labels={"x": "Time", "value": "Count", "variable": "Series"},
    )
    fig.update_traces(mode="lines")
    fig.update_layout(
        height=320,
        title="Resource usage and queue over time",
        legend_title_text="",
    )
    fig.for_each_trace(lambda t: t.update(name="In use" if t.name == "wide_variable_0" else "Queue length"))
    return dcc.Graph(figure=fig)


def _resource_logs(resource: dict[str, Any]):
    sections = []
    sections.append(
        html.Div(
            [html.H5("Queue log", className="section-title"), _data_table(resource.get("queue_log", []), "No queue log recorded.")],
            className="panel-card",
        )
    )
    sections.append(
        html.Div(
            [html.H5("Status log", className="section-title"), _data_table(resource.get("status_log", []), "No status log recorded.")],
            className="panel-card",
        )
    )

    waiting_times = resource.get("waiting_time") or []
    if waiting_times:
        sections.append(
            html.Div(
                [
                    html.Div("Waiting time statistics", className="section-title"),
                    _stat_grid(_describe(waiting_times)),
                    _distribution_tabs(waiting_times, "Waiting times for resource", x_label="Duration"),
                ],
                className="panel-card",
            )
        )
    else:
        sections.append(html.Div("No waiting durations recorded.", className="panel-card"))

    stats = resource.get("stats", {}) or {}
    if stats:
        stat_rows = [{"Metric": k.replace("_", " ").title(), "Value": v} for k, v in stats.items()]
        sections.append(
            html.Div(
                _data_table(stat_rows, "No statistics available.", page_size=5), className="panel-card"
            )
        )
    else:
        sections.append(html.Div("No statistics available.", className="panel-card"))

    logs = resource.get("logs", [])
    sections.append(
        html.Div(
            [html.H5("Event log", className="section-title"), _data_table(logs, "No logs collected for this resource.")],
            className="panel-card",
        )
    )

    return html.Div(sections, className="panel-stack")


def build_app(env, live: bool = False, refresh_ms: int = 500) -> Dash:
    app = Dash(__name__)
    initial_data = collect_run_data(env).as_dict()
    app.layout = html.Div(
        [
            dcc.Store(id="run-data", data=initial_data),
            dcc.Store(id="selected-node", data="environment"),
            dcc.Interval(id="live-interval", interval=refresh_ms, n_intervals=0, disabled=not live),
            html.Div(
                [
                    _build_tabs(),
                    html.Div(id="selection-list", className="panel-wrapper"),
                    html.Div(id="detail-overview", className="panel-wrapper"),
                    html.Div(
                        [html.H4("Logs", className="section-title"), html.Div(id="detail-logs")],
                        className="panel-card",
                    ),
                ],
                style=CONTENT_STYLE,
                className="main-container",
            ),
        ],
        className="app-shell",
    )

    @app.callback(Output("run-data", "data"), Input("live-interval", "n_intervals"), prevent_initial_call=True)
    def _update_live_data(_):
        if not live:
            return dash.no_update
        return collect_run_data(env).as_dict()

    def _default_path(tab_value: str, data: dict[str, Any]) -> str:
        if tab_value == "environment":
            return "environment"
        if tab_value == "entities":
            entities = data.get("entities", [])
            return f"entity:{entities[0]['id']}" if entities else "entities"
        if tab_value == "resources":
            resources = data.get("resources", [])
            return f"resource:{resources[0]['id']}" if resources else "resources"
        activity_map = _activity_name_map(data)
        return f"activity-name:{sorted(activity_map.keys())[0]}" if activity_map else "activities"

    @app.callback(Output("selection-list", "children"), Input("run-data", "data"), Input("section-tabs", "value"))
    def _render_selection(data, tab_value):
        return _build_tab_selection(data, tab_value)

    @app.callback(
        Output("selected-node", "data"),
        Input({"type": "nav-node", "path": dash.ALL}, "n_clicks"),
        Input("section-tabs", "value"),
        State("selected-node", "data"),
        State("run-data", "data"),
        prevent_initial_call=True,
    )
    def _select_node(clicks, tab_value, current, data):
        ctx = callback_context
        if not ctx.triggered:
            return current
        trig = ctx.triggered_id
        if trig == "section-tabs":
            return _default_path(tab_value, data)
        if isinstance(trig, dict):
            return trig.get("path", current)
        return current

    @app.callback(Output("detail-overview", "children"), Output("detail-logs", "children"), Input("selected-node", "data"), State("run-data", "data"))
    def _render_detail(selected, data):
        if selected == "environment":
            return (
                html.Div(
                    [
                        html.Div(_build_overview_cards(data), className="panel-card"),
                        _global_activity_plot(data),
                    ],
                    className="panel-stack",
                ),
                _environment_logs(data),
            )

        if selected == "entities":
            return html.Div("Select an entity to inspect."), html.Div()

        if selected.startswith("entity:"):
            ent_id = int(selected.split(":")[1])
            entity = next((e for e in data.get("entities", []) if e.get("id") == ent_id), None)
            if not entity:
                return html.Div("Entity not found."), html.Div()
            return (
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(f"Entity {entity['id']}", className="section-title"),
                                html.Div(f"Type: {entity.get('type', '-')}", style={"marginBottom": "4px"}),
                                _entity_timeline(entity),
                            ],
                            className="panel-card",
                        )
                    ],
                    className="panel-stack",
                ),
                _entity_logs(entity),
            )

        if selected == "resources":
            return html.Div("Select a resource to inspect."), html.Div()

        if selected.startswith("activity:"):
            _, ent_id, act_id = selected.split(":")
            entity = next((e for e in data.get("entities", []) if e.get("id") == int(ent_id)), None)
            if not entity:
                return html.Div("Activity not found."), html.Div()
            activity = next((a for a in entity.get("activities", []) if a.get("activity_id") == int(act_id)), None)
            if not activity:
                return html.Div("Activity not found."), html.Div()
            overview = html.Div([
                html.H3(activity.get("activity_name", "Activity"), className="section-title"),
                html.Div(f"Entity {entity['id']}"),
            ])
            logs = [log for log in entity.get("logs", []) if log.get("source_type") == "activity" and log.get("source_id") == int(act_id)]
            log_table = dash_table.DataTable(
                data=logs,
                columns=[{"name": k, "id": k} for k in sorted(logs[0].keys())] if logs else [],
                page_size=10,
            ) if logs else html.Div("No logs for this activity.")
            return html.Div([overview, _activity_distribution(entity, int(act_id))], className="panel-stack"), log_table

        if selected == "activities":
            return html.Div("Select an activity to inspect."), html.Div()

        if selected.startswith("activity-name:"):
            activity_name = selected.split(":", 1)[1]
            activity_map = _activity_name_map(data)
            activity_data = activity_map.get(activity_name)
            if not activity_data:
                return html.Div("Activity not found."), html.Div()

            durations = activity_data.get("durations", [])
            if durations:
                fig = px.histogram(x=durations, labels={"x": "Duration"}, nbins=15, title="Duration distribution")
                fig.update_layout(height=300)
                duration_graph = dcc.Graph(figure=fig)
            else:
                duration_graph = html.Div("No duration data available for this activity name.")

            seen_specs: set[str] = set()
            spec_rows = []
            for spec in activity_data.get("duration_specs", []):
                spec_key = json.dumps(spec, sort_keys=True, default=str)
                if spec_key in seen_specs:
                    continue
                seen_specs.add(spec_key)
                spec_rows.append(
                    {
                        "Type": spec.get("type", "-"),
                        "Parameters": json.dumps(spec.get("parameters"), default=str),
                        "Last sampled": spec.get("sampled_duration"),
                    }
                )

            distribution_table = dash_table.DataTable(
                data=spec_rows,
                columns=[{"name": k, "id": k} for k in ["Type", "Parameters", "Last sampled"]],
                page_size=5,
                style_table={"overflowX": "auto"},
            ) if spec_rows else html.Div("No distribution metadata recorded for this activity name.")

            sample_rows = []
            for inst in activity_data.get("instances", []):
                if inst.get("sampled_duration") is None:
                    continue
                duration_info = inst.get("duration_info") or {}
                sample_rows.append(
                    {
                        "Entity": inst.get("entity_id"),
                        "Activity ID": inst.get("activity_id"),
                        "Sampled duration": inst.get("sampled_duration"),
                        "Distribution": duration_info.get("type", "-"),
                        "Parameters": json.dumps(duration_info.get("parameters"), default=str),
                    }
                )

            sampled_table = dash_table.DataTable(
                data=sample_rows,
                columns=[
                    {"name": "Entity", "id": "Entity"},
                    {"name": "Activity ID", "id": "Activity ID"},
                    {"name": "Sampled duration", "id": "Sampled duration"},
                    {"name": "Distribution", "id": "Distribution"},
                    {"name": "Parameters", "id": "Parameters"},
                ],
                page_size=10,
                style_table={"overflowX": "auto"},
            ) if sample_rows else html.Div("No sampled durations recorded for this activity name.")

            logs = activity_data.get("logs", [])
            log_table = dash_table.DataTable(
                data=logs,
                columns=[{"name": k, "id": k} for k in sorted(logs[0].keys())] if logs else [],
                page_size=10,
                style_table={"overflowX": "auto"},
            ) if logs else html.Div("No logs for this activity name.")

            summary = html.Div([
                html.H3(activity_name, className="section-title"),
                html.Div(f"Instances observed: {len(activity_data.get('instances', []))}", style={"marginBottom": "4px"}),
            ])
            return (
                html.Div(
                    [
                        summary,
                        duration_graph,
                        html.H4("Duration definitions", className="section-title"),
                        distribution_table,
                        html.H4("Sampled durations", className="section-title"),
                        sampled_table,
                    ],
                    className="panel-stack",
                ),
                log_table,
            )

        if selected.startswith("resource:"):
            res_id = int(selected.split(":")[1])
            resource = next((r for r in data.get("resources", []) if r.get("id") == res_id), None)
            if not resource:
                return html.Div("Resource not found."), html.Div()
            overview = html.Div([
                html.H3(resource.get("name", "Resource"), className="section-title"),
                html.Div(f"Type: {resource.get('type', '-')}", style={"marginBottom": "4px"}),
                html.Div(f"Capacity: {resource.get('capacity', '-')}", style={"marginBottom": "4px"}),
            ])
            return html.Div([overview, _resource_usage(resource)], className="panel-stack"), _resource_logs(resource)

        return html.Div("Select a node to inspect."), html.Div()

    return app


def run_post_dashboard(env, host: str = "127.0.0.1", port: int = 8050):
    app = build_app(env)
    runner, runner_name = _select_dash_runner(app)
    logger.info("Starting post-run dashboard with %s at http://%s:%s", runner_name, host, port)
    runner(host=host, port=port, debug=False)


def run_live_dashboard(env, host: str = "127.0.0.1", port: int = 8050):
    app = build_app(env, live=True)

    logger.info("Launching live dashboard thread at http://%s:%s", host, port)

    def _run_app():
        runner, runner_name = _select_dash_runner(app)
        logger.debug("Running live dashboard via %s()", runner_name)
        runner(host=host, port=port, debug=False)

    threading.Thread(target=_run_app, daemon=True).start()
    return app
