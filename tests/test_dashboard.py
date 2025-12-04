import importlib
import logging
import sys
import types
from queue import Queue

import pytest


@pytest.fixture
def dashboard_module(monkeypatch):
    """Import ``simpm.dashboard`` with lightweight stubs for Dash dependencies."""

    def _component(name):
        def _build(*args, **kwargs):
            return {"component": name, "args": args, "kwargs": kwargs}

        return _build

    class DummyFigure(dict):
        def update_layout(self, **kwargs):
            self["layout"] = kwargs

        def update_yaxes(self, **kwargs):
            self["yaxes"] = kwargs

    def _figure_factory(name):
        def _factory(*args, **kwargs):
            return DummyFigure(name=name, args=args, kwargs=kwargs)

        return _factory

    class DummyDash:
        def __init__(self, name):
            self.name = name
            self.layout = None
            self.callbacks = []

        def callback(self, *args, **kwargs):
            def decorator(func):
                self.callbacks.append((args, kwargs, func))
                return func

            return decorator

        def run_server(self, host, port, debug=False):
            self.server_args = (host, port, debug)

    class DummyParam:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    fake_dash = types.SimpleNamespace(
        Dash=DummyDash,
        Input=DummyParam,
        Output=DummyParam,
        State=DummyParam,
        ALL="ALL",
        callback_context=types.SimpleNamespace(triggered=[], triggered_id=None),
    )

    fake_html = types.SimpleNamespace(Div=_component("Div"), Button=_component("Button"), H3=_component("H3"), H4=_component("H4"))
    fake_dcc = types.SimpleNamespace(Store=_component("Store"), Interval=_component("Interval"), Graph=_component("Graph"))
    fake_dash_table = types.SimpleNamespace(DataTable=_component("DataTable"))
    fake_px = types.SimpleNamespace(histogram=_figure_factory("histogram"), timeline=_figure_factory("timeline"), line=_figure_factory("line"))

    fake_dash.html = fake_html
    fake_dash.dcc = fake_dcc
    fake_dash.dash_table = fake_dash_table

    monkeypatch.setitem(sys.modules, "dash", fake_dash)
    monkeypatch.setitem(sys.modules, "dash.html", fake_html)
    monkeypatch.setitem(sys.modules, "dash.dcc", fake_dcc)
    monkeypatch.setitem(sys.modules, "dash.dash_table", fake_dash_table)

    monkeypatch.setitem(sys.modules, "plotly", types.SimpleNamespace(express=fake_px))
    monkeypatch.setitem(sys.modules, "plotly.express", fake_px)

    sys.modules.pop("simpm.dashboard", None)
    module = importlib.import_module("simpm.dashboard")
    yield module
    sys.modules.pop("simpm.dashboard", None)


def test_apply_event_updates_run_data(dashboard_module):
    run_data = {"entities": [], "resources": [], "logs": []}

    updated = dashboard_module._apply_event(run_data, {"event": "entity_created", "entity": {"id": 1, "activities": []}})
    updated = dashboard_module._apply_event(updated, {"event": "resource_created", "resource": {"id": 10, "usage": []}})
    updated = dashboard_module._apply_event(
        updated,
        {"event": "activity_started", "entity_id": 1, "activity": {"activity_id": 5, "start": 0}},
    )
    updated = dashboard_module._apply_event(
        updated,
        {"event": "activity_finished", "entity_id": 1, "activity_id": 5, "end_time": 3},
    )
    updated = dashboard_module._apply_event(
        updated,
        {"event": "resource_acquired", "resource_id": 10, "entity_id": 1, "time": 0, "amount": 1},
    )
    updated = dashboard_module._apply_event(
        updated,
        {"event": "resource_released", "resource_id": 10, "entity_id": 1, "time": 2, "amount": 1},
    )
    updated = dashboard_module._apply_event(updated, {"event": "log", "event": {"message": "hello"}})

    entity = updated["entities"][0]
    resource = updated["resources"][0]

    assert len(entity["activities"]) == 1
    assert entity["activities"][0]["duration"] == 3
    assert [entry["action"] for entry in resource["usage"]] == ["acquired", "released"]
    assert updated["logs"] == [{"message": "hello"}]


def test_run_live_dashboard_starts_thread(monkeypatch, dashboard_module):
    threads = []

    class DummyThread:
        def __init__(self, target=None, daemon=None):
            self.target = target
            self.daemon = daemon
            self.started = False

        def start(self):
            self.started = True
            if self.target:
                self.target()

    def _thread_factory(target=None, daemon=None):
        thread = DummyThread(target=target, daemon=daemon)
        threads.append(thread)
        return thread

    monkeypatch.setattr(dashboard_module.threading, "Thread", _thread_factory)

    run_data = {"entities": [], "resources": [], "logs": []}
    queue = Queue()

    app = dashboard_module.run_live_dashboard(run_data, queue, host="0.0.0.0", port=9000)

    assert threads and threads[0].daemon is True
    assert threads[0].started is True
    assert getattr(app, "server_args", None) == ("0.0.0.0", 9000, False)


def test_dashboard_launch_logging(monkeypatch, caplog, dashboard_module):
    calls: dict[str, tuple[str, tuple[str, int, bool]]] = {}

    class DummyApp:
        def run_server(self, host, port, debug=False):
            calls["method"] = ("run_server", (host, port, debug))

        def run(self, host, port, debug=False):
            calls["method"] = ("run", (host, port, debug))

    def _build_app(run_data, live_queue=None):
        return DummyApp()

    monkeypatch.setattr(dashboard_module, "build_app", _build_app)

    with caplog.at_level(logging.INFO):
        dashboard_module.run_post_dashboard({"logs": []}, host="0.0.0.0", port=9100)

    assert calls.get("method") == ("run_server", ("0.0.0.0", 9100, False))
    assert "Starting post-run dashboard" in caplog.text
