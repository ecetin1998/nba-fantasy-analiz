"""Smoke-test the no-statistics roster entry page in a real Streamlit script run."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_roster_input_is_visible_without_stat_download(monkeypatch):
    monkeypatch.setenv("FANTASY_OFFLINE_TEST", "1")
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(app_path, default_timeout=40).run()
    assert not app.exception, [str(error.message) for error in app.exception]
    labels = [item.label for item in app.get("multiselect")]
    assert any("Oyuncularım" in label for label in labels)
    assert any("IL / sakat" in label for label in labels)
