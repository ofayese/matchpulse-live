"""Bounded server-side seeded demo run tests."""

from __future__ import annotations

import time

from fastapi.testclient import TestClient

from matchpulse.demo import DemoCooldownError, DemoRunManager
from matchpulse.service import create_app


def _client(app):
    app.state.demo_subscriber_wait_seconds = 0.2
    app.state.demo_emit_delay_seconds = 0.0
    return TestClient(app)


def test_demo_run_returns_a_synthetic_only_descriptor():
    with _client(create_app()) as client:
        response = client.post("/v1/demo/runs", json={})
        assert response.status_code == 202, response.text
        payload = response.json()
        assert payload["synthetic_only"] is True
        assert payload["match_id"].startswith("demo-")
        assert payload["run_id"]
        assert payload["event_count"] > 0
        assert payload["websocket_path"].endswith(payload["match_id"])


def test_demo_run_ingests_bounded_synthetic_events_and_completes():
    with _client(create_app()) as client:
        run = client.post("/v1/demo/runs", json={}).json()
        status = {}
        for _ in range(100):
            status = client.get(f"/v1/demo/runs/{run['run_id']}").json()
            if status["status"] in {"completed", "failed"}:
                break
            time.sleep(0.05)
        assert status["status"] == "completed", status
        assert status["event_count"] <= 24
        assert status["duplicate_count"] == 0
        state = client.get(f"/v1/matches/{run['match_id']}/state").json()
        assert state["status"] == "finished"
        assert state["event_count"] == status["event_count"]


def test_each_demo_run_uses_a_unique_match_id():
    app = create_app()
    app.state.demo = DemoRunManager(cooldown_seconds=0.0)
    with _client(app) as client:
        first = client.post("/v1/demo/runs", json={}).json()
        for _ in range(100):
            status = client.get(f"/v1/demo/runs/{first['run_id']}").json()
            if status["status"] in {"completed", "failed"}:
                break
            time.sleep(0.05)
        second = client.post("/v1/demo/runs", json={}).json()
        assert first["match_id"] != second["match_id"]
        assert first["run_id"] != second["run_id"]


def test_second_concurrent_demo_run_is_rejected():
    app = create_app()
    app.state.demo_subscriber_wait_seconds = 5.0
    app.state.demo_emit_delay_seconds = 0.0
    with TestClient(app) as client:
        first = client.post("/v1/demo/runs", json={})
        assert first.status_code == 202
        second = client.post("/v1/demo/runs", json={})
        assert second.status_code == 409
        assert "already in progress" in second.json()["detail"]


def test_demo_cooldown_is_enforced():
    app = create_app()
    app.state.demo_subscriber_wait_seconds = 0.0
    app.state.demo_emit_delay_seconds = 0.0
    app.state.demo = DemoRunManager(cooldown_seconds=30.0)
    with TestClient(app) as client:
        first_run = client.post("/v1/demo/runs", json={})
        assert first_run.status_code == 202
        # Wait for the run to complete to release the lock
        for _ in range(100):
            status = client.get(f"/v1/demo/runs/{first_run.json()['run_id']}").json()
            if status["status"] in {"completed", "failed"}:
                break
            time.sleep(0.05)

        second = client.post("/v1/demo/runs", json={})
        assert second.status_code == 429
        assert "cooldown" in second.json()["detail"]


def test_demo_run_is_rejected_when_the_synthetic_only_gate_is_disabled(monkeypatch):
    monkeypatch.setenv("CHALLENGE_SYNTHETIC_ONLY", "false")
    with _client(create_app()) as client:
        response = client.post("/v1/demo/runs", json={})
        assert response.status_code == 503
        assert "CHALLENGE_SYNTHETIC_ONLY" in response.json()["detail"]


def test_unknown_demo_run_is_reported_as_not_found():
    with _client(create_app()) as client:
        assert client.get("/v1/demo/runs/does-not-exist").status_code == 404


def test_demo_run_plans_are_bounded_and_deterministic():
    manager = DemoRunManager(event_cap=10)
    plan = manager.plan(seed=27)
    assert len(plan.events) <= 10
    assert plan.events[0].event_type.value == "match_start"
    assert plan.events[-1].event_type.value == "match_end"
    sequences = [event.sequence for event in plan.events]
    assert sequences == sorted(sequences)
    assert len(set(sequences)) == len(sequences)


def test_demo_manager_reports_the_cooldown_error_type():
    manager = DemoRunManager(cooldown_seconds=60.0)
    manager.reserve()
    manager.release()
    try:
        manager.check_admission()
    except DemoCooldownError as exc:
        assert "cooldown" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected a cooldown error")
