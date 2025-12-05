import importlib
import logging
import sys
import types

import pytest


@pytest.fixture
def dashboard_module(monkeypatch):
    """Import ``simpm.dashboard`` with lightweight stubs for Streamlit dependencies."""

    class DummyFigure(dict):
        def update_traces(self, **kwargs):  # pragma: no cover - trivial
            self["traces"] = kwargs

    def _figure_factory(name):
        def _factory(*args, **kwargs):
            return DummyFigure(name=name, args=args, kwargs=kwargs)

        return _factory

    fake_px = types.SimpleNamespace(
        histogram=_figure_factory("histogram"),
        line=_figure_factory("line"),
        ecdf=_figure_factory("ecdf"),
    )

    class DummyBootstrap:
        def __init__(self):
            self.calls = []

        def run(self, file, command_line=None, args=None, flag_options=None):  # pragma: no cover - trivial
            self.calls.append((file, command_line, args, flag_options))

    bootstrap = DummyBootstrap()

    fake_streamlit = types.SimpleNamespace(
        autorefresh=lambda **kwargs: None,
        set_page_config=lambda **kwargs: None,
        markdown=lambda *args, **kwargs: None,
        caption=lambda *args, **kwargs: None,
        title=lambda *args, **kwargs: None,
        warning=lambda *args, **kwargs: None,
        info=lambda *args, **kwargs: None,
        dataframe=lambda *args, **kwargs: None,
        download_button=lambda *args, **kwargs: None,
        plotly_chart=lambda *args, **kwargs: None,
        tabs=lambda labels: [types.SimpleNamespace(__enter__=lambda self: None, __exit__=lambda *e: False) for _ in labels],
        columns=lambda n: [types.SimpleNamespace(metric=lambda *a, **k: None, image=lambda *a, **k: None, markdown=lambda *a, **k: None, caption=lambda *a, **k: None) for _ in range(n)],
        selectbox=lambda label, options: options[0],
        image=lambda *args, **kwargs: None,
        button=lambda *args, **kwargs: None,
        dataframe_section=None,
        container=lambda: None,
        tabs_section=None,
        plotly=None,
        page_config=None,
        columns_section=None,
        subheader=lambda *args, **kwargs: None,
        metric=lambda *args, **kwargs: None,
        caption_section=None,
        set_option=lambda *args, **kwargs: None,
        slider=lambda *args, **kwargs: None,
        write=lambda *args, **kwargs: None,
        info_section=None,
        image_section=None,
        markdown_section=None,
        tab_section=None,
        title_section=None,
        warning_section=None,
        header=lambda *args, **kwargs: None,
        experimental_memo=lambda *args, **kwargs: None,
        experimental_singleton=lambda *args, **kwargs: None,
        experimental_rerun=lambda *args, **kwargs: None,
    )

    fake_st_web = types.SimpleNamespace(bootstrap=bootstrap)
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "streamlit.web", fake_st_web)
    monkeypatch.setitem(sys.modules, "streamlit.web.bootstrap", bootstrap)

    monkeypatch.setitem(sys.modules, "plotly", types.SimpleNamespace(express=fake_px))
    monkeypatch.setitem(sys.modules, "plotly.express", fake_px)

    sys.modules.pop("simpm.dashboard", None)
    module = importlib.import_module("simpm.dashboard")
    module._ACTIVE_DASHBOARD = None
    yield module
    sys.modules.pop("simpm.dashboard", None)


def test_build_app_creates_dashboard(monkeypatch, dashboard_module):
    registered = []

    class DummyEnv:
        def register_observer(self, observer):
            registered.append(observer)

    monkeypatch.setattr(dashboard_module, "collect_run_data", lambda env: types.SimpleNamespace(entities=[]))

    app = dashboard_module.build_app(DummyEnv())

    assert isinstance(app, dashboard_module.StreamlitDashboard)
    assert registered  # observer registered


def test_dashboard_launch_logging(monkeypatch, caplog, dashboard_module):
    class DummyDashboard:
        def __init__(self):
            self.called = []

        def run(self, host, port, async_mode=True):
            self.called.append((host, port, async_mode))

    dash_instance = DummyDashboard()

    def _build_app(env):
        return dash_instance

    monkeypatch.setattr(dashboard_module, "build_app", _build_app)

    with caplog.at_level(logging.INFO):
        dashboard_module.run_post_dashboard(env=object(), host="0.0.0.0", port=9100, start_async=False)

    assert dash_instance.called == [("0.0.0.0", 9100, False)]
    assert "Starting Streamlit dashboard" in caplog.text


def test_dashboard_launch_uses_args_when_command_line_missing(monkeypatch, dashboard_module):
    calls = []

    class MinimalBootstrap:
        def run(self, file, args=None, flag_options=None):  # pragma: no cover - trivial
            calls.append((file, args, flag_options))

    bootstrap = MinimalBootstrap()
    fake_web = types.SimpleNamespace(bootstrap=bootstrap)

    # Patch the bootstrap module to mimic newer Streamlit versions that omit command_line
    monkeypatch.setitem(sys.modules, "streamlit.web", fake_web)
    monkeypatch.setitem(sys.modules, "streamlit.web.bootstrap", bootstrap)

    env = types.SimpleNamespace(
        name="env",
        register_observer=lambda *a, **k: None,
        resources=[],
        entities=[],
    )

    dashboard = dashboard_module.StreamlitDashboard(env)
    dashboard.run(host="0.0.0.0", port=8600, async_mode=False)

    assert calls == [
        (
            dashboard_module.__file__,
            [],
            {"server.address": "0.0.0.0", "server.port": 8600, "server.headless": True},
        )
    ]
