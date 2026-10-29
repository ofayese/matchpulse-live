# cspell:ignore sanitised
"""Optional, allowlist-only telemetry for MatchPulse Live.

Telemetry is strictly opt-in. When no exporter configuration is supplied the
module is inert: every ``record_*`` call is a no-op and the application
behaves exactly as it did before telemetry existed.

Only aggregate, low-cardinality signals are recorded. The module never accepts
and never exports request bodies, response bodies, prompts, model output,
evidence text, authorization data, cookies, client IPs, tokens, connection
strings, or arbitrary match/event identifiers as metric dimensions.
"""

from __future__ import annotations

import logging
import os
import re
import threading
from dataclasses import dataclass
from typing import Any

log = logging.getLogger(__name__)

CONNECTION_STRING_ENV = "APPLICATIONINSIGHTS_CONNECTION_STRING"
OTLP_ENDPOINT_ENV = "OTEL_EXPORTER_OTLP_ENDPOINT"

MAX_ROUTE_TEMPLATE_LENGTH = 120
MAX_DIMENSION_LENGTH = 64

# A route template may only contain route syntax. Anything that looks like a
# concrete identifier (UUID, long hex, long digit run) is rejected so that
# per-match or per-event values can never become metric dimensions.
_ROUTE_TEMPLATE_RE = re.compile(r"^[A-Za-z0-9_{}/.:-]{1,120}$")
_IDENTIFIER_LIKE_RE = re.compile(
    r"[0-9a-fA-F]{8,}|\d{6,}|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}"
)

ALLOWED_HTTP_FIELDS = frozenset(
    {"route_template", "method", "status", "duration_ms"}
)
ALLOWED_EVENT_FIELDS = frozenset({"accepted", "rejected", "duplicate"})
ALLOWED_FOUNDRY_FIELDS = frozenset(
    {"attempt", "success", "fallback", "rejection", "latency_ms"}
)
ALLOWED_WEBSOCKET_FIELDS = frozenset({"connect", "disconnect", "send", "drop"})

_HTTP_METHODS = frozenset(
    {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
)


class MetricSink:
    """Minimal exporter contract.

    Implementations are called with an already-sanitised metric name, an
    aggregate value, and a dimension mapping whose keys are drawn from the
    allowlists above.
    """

    def emit(
        self, name: str, value: float, dimensions: dict[str, str]
    ) -> None:  # pragma: no cover - interface
        _ = name, value, dimensions
        raise NotImplementedError


@dataclass
class _Aggregate:
    count: int = 0
    total: float = 0.0

    def add(self, value: float) -> None:
        self.count += 1
        self.total += value


class Telemetry:
    """Allowlist-only telemetry facade.

    The facade is inert unless it was constructed with ``enabled=True``. It is
    deliberately incapable of recording free-form key/value data: every public
    ``record_*`` method takes a fixed set of typed arguments.
    """

    def __init__(
        self, sink: MetricSink | None = None, *, enabled: bool = False
    ) -> None:
        self._sink = sink
        self._enabled = bool(enabled or sink is not None)
        self._lock = threading.Lock()
        self._http: dict[tuple[str, str, int], _Aggregate] = {}
        self._events: dict[str, int] = {}
        self._foundry: dict[str, int] = {}
        self._websocket: dict[str, int] = {}

    # ------------------------------------------------------------------ setup

    @classmethod
    def from_env(cls) -> Telemetry:
        """Build telemetry from the environment.

        Returns a disabled instance when no exporter configuration is present,
        which is the default for local runs, tests and the challenge baseline.
        """
        connection_string = os.getenv(CONNECTION_STRING_ENV, "").strip()
        otlp_endpoint = os.getenv(OTLP_ENDPOINT_ENV, "").strip()
        if not connection_string and not otlp_endpoint:
            return cls(enabled=False)
        sink = _build_otel_sink(connection_string, otlp_endpoint)
        if sink is None:
            log.warning(
                "Telemetry configuration present but no exporter is installed; metrics stay local."
            )
        return cls(sink=sink, enabled=True)

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def state(self) -> str:
        return "configured" if self._enabled else "disabled"

    # ------------------------------------------------------------- recording

    def record_http(
        self, route_template: str, method: str, status: int, duration_ms: float
    ) -> None:
        if not self._enabled:
            return
        template = _sanitize_route_template(route_template)
        verb = method.upper() if method.upper() in _HTTP_METHODS else "OTHER"
        code = (
            int(status)
            if isinstance(status, int) and 100 <= status <= 599
            else 0
        )
        value = (
            float(duration_ms)
            if isinstance(duration_ms, (int, float)) and duration_ms >= 0
            else 0.0
        )
        with self._lock:
            key = (template, verb, code)
            aggregate = self._http.get(key)
            if aggregate is None:
                aggregate = _Aggregate()
                self._http[key] = aggregate
            aggregate.add(value)
        self._emit(
            "http.server.duration",
            value,
            {"route_template": template, "method": verb, "status": str(code)},
        )

    def record_events(
        self, accepted: int = 0, rejected: int = 0, duplicate: int = 0
    ) -> None:
        if not self._enabled:
            return
        counts = {
            "accepted": _non_negative(accepted),
            "rejected": _non_negative(rejected),
            "duplicate": _non_negative(duplicate),
        }
        with self._lock:
            for name, value in counts.items():
                self._events[name] = self._events.get(name, 0) + value
        for name, value in counts.items():
            if value:
                self._emit(f"matchpulse.events.{name}", float(value), {})

    def record_foundry(
        self,
        attempt: int = 0,
        success: int = 0,
        fallback: int = 0,
        rejection: int = 0,
        latency_ms: float = 0.0,
    ) -> None:
        if not self._enabled:
            return
        counts = {
            "attempt": _non_negative(attempt),
            "success": _non_negative(success),
            "fallback": _non_negative(fallback),
            "rejection": _non_negative(rejection),
        }
        latency = (
            float(latency_ms)
            if isinstance(latency_ms, (int, float)) and latency_ms >= 0
            else 0.0
        )
        with self._lock:
            for name, value in counts.items():
                self._foundry[name] = self._foundry.get(name, 0) + value
        for name, value in counts.items():
            if value:
                self._emit(f"matchpulse.foundry.{name}", float(value), {})
        if latency:
            self._emit("matchpulse.foundry.latency", latency, {})

    def record_websocket(
        self,
        connect: int = 0,
        disconnect: int = 0,
        send: int = 0,
        drop: int = 0,
    ) -> None:
        if not self._enabled:
            return
        counts = {
            "connect": _non_negative(connect),
            "disconnect": _non_negative(disconnect),
            "send": _non_negative(send),
            "drop": _non_negative(drop),
        }
        with self._lock:
            for name, value in counts.items():
                self._websocket[name] = self._websocket.get(name, 0) + value
        for name, value in counts.items():
            if value:
                self._emit(f"matchpulse.websocket.{name}", float(value), {})

    # --------------------------------------------------------------- reading

    def snapshot(self) -> dict[str, Any]:
        """Return the locally aggregated, allowlisted counters."""
        with self._lock:
            return {
                "enabled": self._enabled,
                "http": [
                    {
                        "route_template": template,
                        "method": verb,
                        "status": code,
                        "count": aggregate.count,
                        "total_duration_ms": round(aggregate.total, 3),
                    }
                    for (template, verb, code), aggregate in sorted(
                        self._http.items()
                    )
                ],
                "events": dict(self._events),
                "foundry": dict(self._foundry),
                "websocket": dict(self._websocket),
            }

    # --------------------------------------------------------------- exporting

    def export(self) -> None:
        """Push the aggregated counters to the exporter.

        Export failures are contained: telemetry must never break a request.
        """
        if not self._enabled or self._sink is None:
            return
        snapshot = self.snapshot()
        for entry in snapshot["http"]:
            self._emit(
                "http.server.duration",
                entry["total_duration_ms"],
                {
                    "route_template": entry["route_template"],
                    "method": entry["method"],
                    "status": str(entry["status"]),
                },
            )
        for name, value in snapshot["events"].items():
            self._emit(f"matchpulse.events.{name}", float(value), {})
        for name, value in snapshot["foundry"].items():
            self._emit(f"matchpulse.foundry.{name}", float(value), {})
        for name, value in snapshot["websocket"].items():
            self._emit(f"matchpulse.websocket.{name}", float(value), {})

    def _emit(
        self, name: str, value: float, dimensions: dict[str, str]
    ) -> None:
        if self._sink is None:
            return
        try:
            self._sink.emit(name, value, dimensions)
        except Exception as exc:  # telemetry must never break the request path
            log.warning("Telemetry export failed: %s", type(exc).__name__)


def _non_negative(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0
    return max(0, int(value))


def _sanitize_route_template(route_template: str) -> str:
    """Keep only safe route syntax so identifiers never become dimensions."""
    if not isinstance(route_template, str):
        return "unknown"
    candidate = route_template.strip()
    if not candidate or len(candidate) > MAX_ROUTE_TEMPLATE_LENGTH:
        return "unknown"
    if not _ROUTE_TEMPLATE_RE.match(candidate):
        return "unknown"
    if _IDENTIFIER_LIKE_RE.search(candidate):
        return "unknown"
    return candidate


def _build_otel_sink(
    connection_string: str, otlp_endpoint: str
) -> MetricSink | None:
    """Return an OpenTelemetry-backed sink when the SDK is installed."""
    try:
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.resources import Resource
    except ImportError:
        return None

    try:
        provider = MeterProvider(
            resource=Resource.create({"service.name": "matchpulse-live"})
        )
        meter = provider.get_meter("matchpulse.live")
    except Exception as exc:  # pragma: no cover - depends on optional SDK
        log.warning("Telemetry meter unavailable: %s", type(exc).__name__)
        return None

    class _OtelSink(MetricSink):
        def __init__(self) -> None:
            self._instruments: dict[str, Any] = {}

        def emit(
            self, name: str, value: float, dimensions: dict[str, str]
        ) -> None:
            instrument = self._instruments.get(name)
            if instrument is None:
                instrument = meter.create_counter(name)
                self._instruments[name] = instrument
            instrument.add(value, dict(dimensions))

    del connection_string, otlp_endpoint
    return _OtelSink()
