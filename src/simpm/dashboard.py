"""Plotly Dash dashboard for SimPM runs."""
from __future__ import annotations

import json
import threading
from queue import Queue
from typing import Any

try:
    import dash
    from dash import Dash, Input, Output, State, callback_context, dash_table, dcc, html
    import plotly.express as px
except ImportError as exc:  # pragma: no cover - handled at runtime
    raise ImportError(
        "Plotly Dash is required for dashboard mode. Install with `pip install dash plotly`."
    ) from exc


CONTENT_STYLE = {"width": "100%", "padding": "12px"}

BUTTON_BASE_STYLE = {
    "borderRadius": "12px",
    "border": "1px solid transparent",
    "padding": "10px 14px",
    "margin": "6px",
    "cursor": "pointer",
    "boxShadow": "0 1px 3px rgba(0, 0, 0, 0.15)",
}

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
            activity_entry = activities.setdefault(name, {"durations": [], "logs": [], "instances": []})
            activity_entry["instances"].append({"entity_id": entity.get("id"), **act})
            if act.get("duration") is not None:
                activity_entry["durations"].append(act["duration"])
            name_to_ids.setdefault(name, set()).add(act.get("activity_id"))

        for log in entity.get("logs", []):
            act_name = log.get("activity_name")
            if act_name:
                activities.setdefault(act_name, {"durations": [], "logs": [], "instances": []})["logs"].append(log)
                continue
            if log.get("source_type") == "activity":
                for candidate_name, activity_ids in name_to_ids.items():
                    if log.get("source_id") in activity_ids:
                        activities.setdefault(candidate_name, {"durations": [], "logs": [], "instances": []})["logs"].append(log)
                        break
    for log in run_data.get("logs", []):
        if log.get("activity_name"):
            activities.setdefault(log["activity_name"], {"durations": [], "logs": [], "instances": []})["logs"].append(log)
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


def _section(title: str, children):
    return html.Div(
        [
            html.Div(title, style={"fontWeight": "bold", "marginTop": "4px"}),
            html.Div(children, style={"display": "flex", "flexWrap": "wrap", "marginTop": "4px"}),
        ]
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
            children=[dcc.Tab(label=tab["label"], value=tab["value"]) for tab in tabs],
        )
    # Fallback for environments where dcc.Tabs is unavailable. RadioItems still provides
    # a "value" property, keeping existing callbacks functional even without tab
    # components.
    return dcc.RadioItems(
        id="section-tabs",
        options=tabs,
        value="environment",
        inline=True,
        labelStyle={"marginRight": "12px"},
    )


def _build_overview_cards(run_data: dict[str, Any]):
    env = run_data.get("environment", {})
    end_time = env.get("time", {}).get("end")
    return html.Div(
        [
            html.H3(env.get("name", "Environment")),
            html.Div(f"Run ID: {env.get('run_id', '-')}", style={"marginBottom": "4px"}),
            html.Div(f"Simulation time: 0 → {end_time if end_time is not None else '-'}"),
        ]
    )


def _global_activity_plot(run_data: dict[str, Any]):
    durations = []
    names = []
    for ent in run_data.get("entities", []):
        for act in ent.get("activities", []):
            if act.get("duration") is not None:
                durations.append(act["duration"])
                names.append(act["activity_name"])
    if not durations:
        return html.Div("No activity data available.")
    fig = px.histogram(x=durations, labels={"x": "Duration"}, nbins=20, title="Activity durations")
    fig.update_layout(height=300)
    return dcc.Graph(figure=fig)


def _environment_logs(run_data: dict[str, Any]):
    logs = _collect_logs(run_data)
    if not logs:
        return html.Div("No logs collected for this run.")
    columns = [
        {"name": col, "id": col}
        for col in sorted({k for row in logs for k in row.keys()})
    ]
    return dash_table.DataTable(
        data=logs,
        columns=columns,
        page_size=10,
        page_action="native",
        page_current=0,
        style_table={"overflowX": "auto"},
    )


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
    logs = entity.get("logs", [])
    if not logs:
        return html.Div("No logs collected for this entity.")
    return dash_table.DataTable(
        data=logs,
        columns=[{"name": k, "id": k} for k in sorted(logs[0].keys())],
        page_size=10,
        page_action="native",
        page_current=0,
        style_table={"overflowX": "auto"},
    )


def _activity_distribution(entity: dict[str, Any], activity_id: int):
    durations = [act["duration"] for act in entity.get("activities", []) if act.get("activity_id") == activity_id and act.get("duration") is not None]
    if not durations:
        return html.Div("No duration data available for this activity.")
    fig = px.histogram(x=durations, labels={"x": "Duration"}, nbins=10, title="Activity duration distribution")
    fig.update_layout(height=300)
    return dcc.Graph(figure=fig)


def _resource_usage(resource: dict[str, Any]):
    events = sorted(resource.get("usage", []), key=lambda x: x["time"])
    if not events:
        return html.Div("No usage events recorded for this resource.")
    cumulative = []
    total = 0
    times = []
    for event in events:
        total += event.get("delta", 0)
        times.append(event.get("time", 0))
        cumulative.append(total)
    fig = px.line(x=times, y=cumulative, labels={"x": "Time", "y": "Units in use"}, title="Resource utilization over time")
    fig.update_layout(height=300)
    return dcc.Graph(figure=fig)


def build_app(run_data: dict[str, Any], live_queue: Queue | None = None) -> Dash:
    app = Dash(__name__)
    app.layout = html.Div(
        [
            dcc.Store(id="run-data", data=run_data),
            dcc.Store(id="selected-node", data="environment"),
            dcc.Interval(id="live-interval", interval=500, n_intervals=0, disabled=live_queue is None),
            html.Div(
                [
                    _build_tabs(),
                    html.Div(id="selection-list", style={"marginBottom": "16px"}),
                    html.Div(id="detail-overview"),
                    html.H4("Logs"),
                    html.Div(id="detail-logs"),
                ],
                style=CONTENT_STYLE,
            ),
        ],
        style={"height": "100vh", "overflowY": "auto"},
    )

    @app.callback(Output("run-data", "data"), Input("live-interval", "n_intervals"), State("run-data", "data"))
    def _update_live_data(_, current_data):
        if live_queue is None:
            return current_data
        updated = dict(current_data)
        changed = False
        while not live_queue.empty():
            event = live_queue.get()
            updated = _apply_event(updated, event)
            changed = True
        return updated if changed else current_data

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
            return html.Div([
                _build_overview_cards(data),
                html.H4("Global activity overview"),
                _global_activity_plot(data),
            ]), _environment_logs(data)

        if selected == "entities":
            return html.Div("Select an entity to inspect."), html.Div()

        if selected.startswith("entity:"):
            ent_id = int(selected.split(":")[1])
            entity = next((e for e in data.get("entities", []) if e.get("id") == ent_id), None)
            if not entity:
                return html.Div("Entity not found."), html.Div()
            return html.Div([
                html.H3(f"Entity {entity['id']}"),
                html.Div(f"Type: {entity.get('type', '-')}", style={"marginBottom": "4px"}),
                _entity_timeline(entity),
            ]), _entity_logs(entity)

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
                html.H3(activity.get("activity_name", "Activity")),
                html.Div(f"Entity {entity['id']}"),
            ])
            logs = [log for log in entity.get("logs", []) if log.get("source_type") == "activity" and log.get("source_id") == int(act_id)]
            log_table = dash_table.DataTable(
                data=logs,
                columns=[{"name": k, "id": k} for k in sorted(logs[0].keys())] if logs else [],
                page_size=10,
                page_action="native",
                page_current=0,
            ) if logs else html.Div("No logs for this activity.")
            return html.Div([overview, _activity_distribution(entity, int(act_id))]), log_table

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

            logs = activity_data.get("logs", [])
            log_table = dash_table.DataTable(
                data=logs,
                columns=[{"name": k, "id": k} for k in sorted(logs[0].keys())] if logs else [],
                page_size=10,
                page_action="native",
                page_current=0,
                style_table={"overflowX": "auto"},
            ) if logs else html.Div("No logs for this activity name.")

            summary = html.Div([
                html.H3(activity_name),
                html.Div(f"Instances observed: {len(activity_data.get('instances', []))}", style={"marginBottom": "4px"}),
            ])
            return html.Div([summary, duration_graph]), log_table

        if selected.startswith("resource:"):
            res_id = int(selected.split(":")[1])
            resource = next((r for r in data.get("resources", []) if r.get("id") == res_id), None)
            if not resource:
                return html.Div("Resource not found."), html.Div()
            logs = resource.get("logs", [])
            log_table = dash_table.DataTable(
                data=logs,
                columns=[{"name": k, "id": k} for k in sorted(logs[0].keys())] if logs else [],
                page_size=10,
                page_action="native",
                page_current=0,
            ) if logs else html.Div("No logs for this resource.")
            overview = html.Div([
                html.H3(resource.get("name", "Resource")),
                html.Div(f"Type: {resource.get('type', '-')}", style={"marginBottom": "4px"}),
                html.Div(f"Capacity: {resource.get('capacity', '-')}", style={"marginBottom": "4px"}),
            ])
            return html.Div([overview, _resource_usage(resource)]), log_table

        return html.Div("Select a node to inspect."), html.Div()

    return app


def _apply_event(run_data: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    updated = dict(run_data)
    evt_type = event.get("event")
    if isinstance(evt_type, dict):
        updated_logs = list(updated.get("logs", []))
        updated_logs.append(evt_type)
        updated["logs"] = updated_logs
        return updated
    if evt_type == "entity_created":
        updated_entities = list(updated.get("entities", []))
        updated_entities.append(event["entity"])
        updated["entities"] = updated_entities
    elif evt_type == "resource_created":
        updated_resources = list(updated.get("resources", []))
        updated_resources.append(event["resource"])
        updated["resources"] = updated_resources
    elif evt_type in {"activity_started", "activity_finished"}:
        ent_id = event.get("entity_id")
        entities = list(updated.get("entities", []))
        for ent in entities:
            if ent.get("id") == ent_id:
                if evt_type == "activity_started":
                    ent.setdefault("activities", []).append(event.get("activity", {}))
                else:
                    for act in ent.get("activities", []):
                        if act.get("activity_id") == event.get("activity_id") and act.get("end") is None:
                            act["end"] = event.get("end_time")
                            if act.get("start") is not None and act.get("end") is not None:
                                act["duration"] = act["end"] - act["start"]
                            break
                break
        updated["entities"] = entities
    elif evt_type in {"resource_acquired", "resource_released"}:
        res_id = event.get("resource_id")
        resources = list(updated.get("resources", []))
        for res in resources:
            if res.get("id") == res_id:
                res.setdefault("usage", []).append(
                    {
                        "time": event.get("time"),
                        "delta": event.get("amount") if evt_type == "resource_acquired" else -event.get("amount"),
                        "entity_id": event.get("entity_id"),
                        "action": "acquired" if evt_type == "resource_acquired" else "released",
                    }
                )
                break
        updated["resources"] = resources
    elif evt_type == "log":
        log_event = event.get("payload") or event.get("log_event") or event.get("event", {})
        updated_logs = list(updated.get("logs", []))
        updated_logs.append(log_event)
        updated["logs"] = updated_logs
    return updated


def run_post_dashboard(run_data: dict[str, Any], host: str = "127.0.0.1", port: int = 8050):
    app = build_app(run_data)
    app.run(host=host, port=port, debug=False)


def run_live_dashboard(run_data: dict[str, Any], event_queue: Queue, host: str = "127.0.0.1", port: int = 8050):
    app = build_app(run_data, live_queue=event_queue)
    def _run_app():
        if hasattr(app, "run"):
            app.run(host=host, port=port, debug=False)
        else:
            app.run_server(host=host, port=port, debug=False)

    threading.Thread(target=_run_app, daemon=True).start()
    return app
