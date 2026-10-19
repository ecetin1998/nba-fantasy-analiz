"""Smoke-test the no-statistics roster entry page in a real Streamlit script run."""

from streamlit.testing.v1 import AppTest


def test_roster_input_is_visible_without_stat_download():
    app = AppTest.from_file("app.py", default_timeout=40).run()
    assert not app.exception, [str(error.message) for error in app.exception]
    labels = [item.label for item in app.get("multiselect")]
    assert any("Oyuncularım" in label for label in labels)
    assert any("IL / sakat" in label for label in labels)
