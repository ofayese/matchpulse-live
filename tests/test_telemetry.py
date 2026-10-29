# cspell:ignore delenv
"""Optional telemetry tests.

Telemetry must stay inert without configuration, must only ever record
allowlisted aggregate signals, and must never break the request path.
"""

from __future__ import annotations

import pytest

from matchpulse.telemetry import (
    CONNECTION_STRING_ENV,
    OTLP_ENDPOINT_ENV,
    MetricSink,
    Telemetry,
)


class _RecordingSink(MetricSink):
    def __init__(self) -> None:
        self.emitted: list[tuple[str, float, dict[str, str]]] = []

    def emit(self, name: str, value: float, dimensions: dict[str, str]) -> None:
        self.emitted.append((name, value, dimensions))


class _FailingSink(MetricSink):
    def emit(self, _name: str, _value: float, _dimensions: dict[str, str]) -> None:
        raise RuntimeError("exporter unavailable")


def test_telemetry_is_disabled_without_configuration(monkeypatch):
    monkeypatch.delenv(CONNECTION_STRING_ENV, raising=False)
    monkeypatch.delenv(OTLP_ENDPOINT_ENV, raising=False)
    telemetry = Telemetry.from_env()
    assert telemetry.enabled is False
    assert telemetry.state == "disabled"


def test_disabled_telemetry_records_nothing():
    telemetry = Telemetry()
    telemetry.record_http("/v1/events", "POST", 202, 1.0)
    telemetry.record_events(accepted=3)
    telemetry.record_foundry(attempt=1)
    telemetry.record_websocket(connect=1)
    snapshot = telemetry.snapshot()
    assert snapshot["http"] == []
    assert snapshot["events"] == {}
    assert snapshot["foundry"] == {}
    assert snapshot["websocket"] == {}


def test_telemetry_is_enabled_when_a_connection_string_is_supplied(monkeypatch):
    monkeypatch.setenv(CONNECTION_STRING_ENV, "InstrumentationKey=00000000-0000-0000-0000-000000000000")
    telemetry = Telemetry.from_env()
    assert telemetry.enabled is True
    assert telemetry.state == "configured"


def test_only_allowlisted_http_signals_are_recorded():
    sink = _RecordingSink()
    telemetry = Telemetry(sink=sink)
    telemetry.record_http("/v1/matches/{match_id}/state", "GET", 200, 12.5)
    assert sink.emitted
    name, value, dimensions = sink.emitted[0]
    assert name == "http.server.duration"
    assert value == 12.5
    assert set(dimensions) == {"route_template", "method", "status"}
    assert dimensions["route_template"] == "/v1/matches/{match_id}/state"


def test_identifiers_never_become_metric_dimensions():
    sink = _RecordingSink()
    telemetry = Telemetry(sink=sink)
    telemetry.record_http("/v1/matches/59dccafac618d9d2f3f0c1dc1d491ddec4ae537b/state", "GET", 200, 1.0)
    telemetry.record_http("/v1/matches/demo-abc123def456/state", "GET", 200, 1.0)
    for _, _, dimensions in sink.emitted:
        assert dimensions["route_template"] == "unknown"


def test_recorded_dimensions_carry_no_payloads_or_secrets():
    sink = _RecordingSink()
    telemetry = Telemetry(sink=sink)
    telemetry.record_events(accepted=1, rejected=0, duplicate=0)
    telemetry.record_foundry(attempt=1, success=0, fallback=1, rejection=0, latency_ms=4.0)
    telemetry.record_websocket(connect=1, disconnect=0, send=2, drop=0)
    for name, value, dimensions in sink.emitted:
        assert isinstance(name, str)
        assert isinstance(value, float)
        for key, text in dimensions.items():
            assert key in {"route_template", "method", "status"}
            assert "Bearer" not in text
            assert "api-key" not in text


def test_telemetry_failure_is_non_fatal():
    sink = _FailingSink()
    telemetry = Telemetry(sink=sink)
    telemetry.record_http("/v1/events", "POST", 202, 1.0)
    telemetry.export()
    assert telemetry.snapshot()["http"]


def test_aggregate_counters_are_exposed():
    telemetry = Telemetry(sink=_RecordingSink())
    telemetry.record_events(accepted=2, rejected=1, duplicate=1)
    telemetry.record_foundry(attempt=2, success=1, fallback=1)
    telemetry.record_websocket(connect=1, send=3)
    snapshot = telemetry.snapshot()
    assert snapshot["events"] == {"accepted": 2, "rejected": 1, "duplicate": 1}
    assert snapshot["foundry"]["attempt"] == 2
    assert snapshot["foundry"]["fallback"] == 1
    assert snapshot["websocket"] == {
        "connect": 1,
        "disconnect": 0,
        "send": 3,
        "drop": 0,
    }


def test_negative_and_non_numeric_values_are_ignored():
    sink = _RecordingSink()
    telemetry = Telemetry(sink=sink)
    telemetry.record_events(accepted=-5, rejected=True)
    telemetry.record_http("/v1/events", "post", 202, -1.0)
    snapshot = telemetry.snapshot()
    assert snapshot["events"]["accepted"] == 0
    assert snapshot["events"]["rejected"] == 0
    assert snapshot["http"][0]["method"] == "POST"
    assert snapshot["http"][0]["total_duration_ms"] == 0.0


@pytest.mark.parametrize("template", ["", "x" * 200, "/v1/matches/123456789012/state", "/v1/events?body=x"])
def test_unsafe_route_templates_are_replaced(template):
    sink = _RecordingSink()
    telemetry = Telemetry(sink=sink)
    telemetry.record_http(template, "GET", 200, 1.0)
    assert sink.emitted[0][2]["route_template"] == "unknown"
