import importlib
import logging
import sys
import types

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


def test_build_app_populates_initial_snapshot(monkeypatch, dashboard_module):
    snapshot_data = {"environment": {}, "entities": ["ent"], "resources": ["res"], "logs": []}

    class DummySnapshot:
        def as_dict(self):
            return snapshot_data

    monkeypatch.setattr(dashboard_module, "collect_run_data", lambda env: DummySnapshot())

    app = dashboard_module.build_app(env=object(), live=False)
    layout_children = app.layout["args"][0]
    run_store = next(child for child in layout_children if child["kwargs"].get("id") == "run-data")

    assert run_store["kwargs"]["data"] == snapshot_data


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

    app = dashboard_module.run_live_dashboard(env=object(), host="0.0.0.0", port=9000)

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

    def _build_app(env, live=False, refresh_ms=500):
        return DummyApp()

    monkeypatch.setattr(dashboard_module, "build_app", _build_app)

    with caplog.at_level(logging.INFO):
        dashboard_module.run_post_dashboard(env=object(), host="0.0.0.0", port=9100)

    assert calls.get("method") == ("run_server", ("0.0.0.0", 9100, False))
    assert "Starting post-run dashboard" in caplog.text
