import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import comparison as cmp
from streamlit.testing.v1 import AppTest
from test_core import A, B, GOOD

import ui


def _result():
    return cmp.verify_evidence(cmp.validate_result(GOOD), A, B)


def _run_app():
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()


def test_initial_render_and_missing_files_warning():
    at = _run_app()
    assert not at.exception
    next(b for b in at.button if b.label == "Compare Documents").click().run()
    assert any("both Document A and Document B" in w.value for w in at.warning)


def test_sample_flow_shows_results(monkeypatch):
    monkeypatch.setattr(cmp, "compare_documents", lambda a, b, **k: _result())
    at = _run_app()
    next(b for b in at.sidebar.button if "sample" in b.label.lower()).click().run()
    next(b for b in at.button if b.label == "Compare Documents").click().run()
    assert not at.exception
    assert at.session_state["result"] is not None
    assert [t.label for t in at.tabs] == ["Summary A", "Summary B", "Similarities", "Differences",
                                           "Key Details", "Overall Conclusion"]


def test_api_error_is_shown(monkeypatch):
    def boom(a, b, **k):
        raise cmp.ComparisonError("The API rate limit or quota was reached.")
    monkeypatch.setattr(cmp, "compare_documents", boom)
    at = _run_app()
    next(b for b in at.sidebar.button if "sample" in b.label.lower()).click().run()
    next(b for b in at.button if b.label == "Compare Documents").click().run()
    assert not at.exception
    assert at.session_state["result"] is None


def test_metrics_and_html_escaping(monkeypatch):
    m = dict((l, v) for l, v, _ in ui.compute_metrics(_result()))
    assert m["Differences"] == "1" and m["Detail match"] == "0%"
    assert ui.e("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"


def test_metric_html_counts_up_and_has_ring():
    out = ui.metric_html("Match", "40%", "hint", "#fff", 2)
    assert 'style="--n:40"' in out and "ring" in out and 'aria-label="40%"' in out
    plain = ui.metric_html("Differences", "4", "hint", "#fff")
    assert 'style="--n:4"' in plain and "ring" not in plain
    assert "—" in ui.metric_html("Match", "—", "hint", "#fff")


def test_css_respects_reduced_motion_and_loader_present():
    assert "prefers-reduced-motion" in ui.CSS
    assert "Neural scan" in ui.LOADER_HTML
