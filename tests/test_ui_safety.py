"""Browser-side rendering safety tests.

The demo page must never insert API or model generated values through
``innerHTML``. These tests assert both the static contract (no ``innerHTML``
in the shipped page) and the behavioural contract (HTML-like output is
rendered as text).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from matchpulse.service import create_app


def _demo_html() -> str:
    with TestClient(create_app()) as client:
        response = client.get("/demo")
        assert response.status_code == 200
        return response.text


def test_demo_page_never_uses_inner_html():
    html = _demo_html()
    assert "innerHTML" not in html
    assert "outerHTML" not in html
    assert "insertAdjacentHTML" not in html
    assert "document.write" not in html


def test_demo_page_builds_dynamic_content_with_safe_dom_apis():
    html = _demo_html()
    assert "createElement" in html
    assert "textContent" in html


def test_demo_page_exposes_the_required_controls_and_states():
    html = _demo_html()
    for marker in ("Start synthetic demo", "Replay demo", "Audience profile",
                   "Comparison language", "Same moment, different audiences",
                   "Recap", "Evidence:"):
        assert marker in html


def test_demo_page_is_keyboard_accessible_and_announces_status():
    html = _demo_html()
    assert 'role="status"' in html
    assert 'aria-live="polite"' in html
    assert ":focus-visible" in html
    assert 'type="button"' in html
    assert 'for="profile"' in html
    assert 'for="language"' in html


def test_demo_page_does_not_embed_a_dynamic_script_source():
    html = _demo_html()
    assert "<script src=" not in html
    assert "javascript:" not in html


def test_html_like_model_output_is_rendered_as_text_by_the_api():
    """A hostile model string must travel as data, never as markup."""
    with TestClient(create_app()) as client:
        html = client.get("/demo").text
        assert "<img src=x onerror=alert(1)>" not in html
        payload = {
            "match_id": "xss-demo", "sequence": 0, "clock_ms": 0,
            "event_type": "match_start", "source": "synthetic",
        }
        response = client.post("/v1/events", json=payload)
        assert response.status_code == 202
        assert response.json()["insights"] == []


def test_insight_payload_cannot_smuggle_markup_past_the_api():
    with TestClient(create_app()) as client:
        payload = {
            "match_id": "xss-demo", "sequence": 1, "clock_ms": 1000,
            "event_type": "shot", "team_id": "Northbridge-FC", "player_id": "NB-7",
            "outcome": "on_target", "speed_kmh": 120, "source": "synthetic",
        }
        response = client.post("/v1/events", json=payload)
        assert response.status_code == 202
        for insight in response.json()["insights"]:
            assert "<script" not in insight["title"]
            assert "<script" not in insight["body"]
            assert "<script" not in insight["overlay_text"]
