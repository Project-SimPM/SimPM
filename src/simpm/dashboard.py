"""Plotly Dash dashboard for SimPM runs."""
from __future__ import annotations

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


NAV_STYLE = {"width": "25%", "borderRight": "1px solid #ddd", "padding": "8px", "overflowY": "auto", "height": "100vh"}
CONTENT_STYLE = {"width": "75%", "padding": "12px"}


def _nav_button(label: str, path: str, level: int = 0):
    return html.Div(
        html.Button(label, id={"type": "nav-node", "path": path}, n_clicks=0, style={"width": "100%", "textAlign": "left", "marginLeft": f"{level * 12}px"}),
    )


def build_nav_tree(run_data: dict[str, Any]):
    entities = run_data.get("entities", [])
    resources = run_data.get("resources", [])
    env_name = run_data.get("environment", {}).get("name", "Environment")

    items = [_nav_button(env_name, "environment")]
    items.append(html.Div("Entities", style={"fontWeight": "bold", "marginTop": "8px"}))
    for ent in entities:
        ent_path = f"entity:{ent['id']}"
        items.append(_nav_button(f"{ent['name']} (Entity {ent['id']})", ent_path, level=1))
        for act in ent.get("activities", []):
            act_path = f"activity:{ent['id']}:{act['activity_id']}"
            items.append(_nav_button(f"{act['activity_name']} (Activity)", act_path, level=2))
    items.append(html.Div("Resources", style={"fontWeight": "bold", "marginTop": "8px"}))
    for res in resources:
        res_path = f"resource:{res['id']}"
        items.append(_nav_button(f"{res['name']} (Resource {res['id']})", res_path, level=1))
    return items


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
    logs = run_data.get("logs", [])
    if not logs:
        return html.Div("No logs collected for this run.")
    return dash_table.DataTable(
        data=logs,
        columns=[{"name": k, "id": k} for k in sorted(logs[0].keys())],
        page_size=10,
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
                    html.Div(id="nav-tree", style=NAV_STYLE),
                    html.Div(
                        [
                            html.Div(id="detail-overview"),
                            html.H4("Logs"),
                            html.Div(id="detail-logs"),
                        ],
                        style=CONTENT_STYLE,
                    ),
                ],
                style={"display": "flex", "height": "100vh"},
            ),
        ]
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

    @app.callback(Output("nav-tree", "children"), Input("run-data", "data"))
    def _render_tree(data):
        return build_nav_tree(data)

    @app.callback(
        Output("selected-node", "data"),
        Input({"type": "nav-node", "path": dash.ALL}, "n_clicks"),
        State("selected-node", "data"),
        prevent_initial_call=True,
    )
    def _select_node(clicks, current):
        ctx = callback_context
        if not ctx.triggered:
            return current
        trig = ctx.triggered_id
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
            ) if logs else html.Div("No logs for this activity.")
            return html.Div([overview, _activity_distribution(entity, int(act_id))]), log_table

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
    app.run_server(host=host, port=port, debug=False)


def run_live_dashboard(run_data: dict[str, Any], event_queue: Queue, host: str = "127.0.0.1", port: int = 8050):
    app = build_app(run_data, live_queue=event_queue)
    threading.Thread(target=lambda: app.run_server(host=host, port=port, debug=False), daemon=True).start()
    return app
