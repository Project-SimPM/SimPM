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
        sidebar=types.SimpleNamespace(
            selectbox=lambda *args, **kwargs: (args[1][0] if len(args) > 1 and args[1] else None),
            radio=lambda label, options, index=0: options[index],
        ),
    )
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    monkeypatch.setitem(sys.modules, "plotly", types.SimpleNamespace(express=fake_px))
    monkeypatch.setitem(sys.modules, "plotly.express", fake_px)

    sys.modules.pop("simpm.dashboard", None)
    module = importlib.import_module("simpm.dashboard")
    module._ACTIVE_DASHBOARD = None
    yield module
    sys.modules.pop("simpm.dashboard", None)


def test_build_app_creates_dashboard(monkeypatch, dashboard_module):
    registered = []

    monkeypatch.setattr(
        dashboard_module,
        "collect_run_data",
        lambda env: dashboard_module.RunSnapshot(environment={}, entities=[], resources=[], logs=[]),
    )

    app = dashboard_module.build_app(object())

    assert isinstance(app, dashboard_module.StreamlitDashboard)
    assert app.snapshot.entities == []


def test_dashboard_launch_logging(monkeypatch, caplog, dashboard_module):
    calls = []

    class DummyProcess:
        pass

    def fake_popen(cmd):
        calls.append(("popen", cmd))
        return DummyProcess()

    def fake_run(cmd, check=False):
        calls.append(("run", cmd, check))

    monkeypatch.setattr(dashboard_module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(dashboard_module.subprocess, "run", fake_run)

    snapshot = dashboard_module.RunSnapshot(environment={}, entities=[], resources=[], logs=[])

    with caplog.at_level(logging.INFO):
        dashboard_module.run_post_dashboard(snapshot, host="0.0.0.0", port=9100, start_async=False)

    assert calls and calls[0][0] == "run"
    assert "Starting Streamlit dashboard" in caplog.text
