"""Bounded, server-side seeded demo runs.

A demo run lets a judge see MatchPulse Live work without a terminal. It is
deliberately constrained:

* every run gets its own unique fictional match identifier, so replay runs
  never share sequence numbers or state;
* events come from the existing deterministic synthetic generator only;
* the number of ingested events is capped;
* at most one demo run may be in flight at a time;
* a cooldown prevents a demo run from being started repeatedly in a row;
* the synthetic-only safety gate still applies to every ingested event.

The demo never invents data, never contacts an external service and never
requires terminal or CLI access from the judge.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass

from .models import MatchEvent
from .synthetic import generate_match

DEFAULT_EVENT_CAP = 24
DEFAULT_COOLDOWN_SECONDS = 20.0
DEFAULT_MAX_CONCURRENT_RUNS = 1
DEFAULT_SUBSCRIBER_WAIT_SECONDS = 10.0
DEFAULT_EMIT_DELAY_SECONDS = 0.30
DEFAULT_SEED = 27
DEFAULT_BODY_EVENTS = 60


class DemoRunError(RuntimeError):
    """Base error for demo run admission control."""


class DemoBusyError(DemoRunError):
    """Raised when a demo run is already in flight."""


class DemoCooldownError(DemoRunError):
    """Raised when a demo run is requested during the cooldown window."""


@dataclass(frozen=True)
class DemoRunPlan:
    """The deterministic plan for a single demo run."""

    run_id: str
    match_id: str
    seed: int
    events: tuple[MatchEvent, ...]

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def first_sequence(self) -> int:
        return self.events[0].sequence if self.events else 0

    @property
    def last_sequence(self) -> int:
        return self.events[-1].sequence if self.events else 0


@dataclass
class DemoRunStatus:
    """Mutable lifecycle state for a demo run."""

    run_id: str
    match_id: str
    seed: int
    status: str = "pending"
    event_count: int = 0
    insight_count: int = 0
    duplicate_count: int = 0
    error: str | None = None


class DemoRunManager:
    """Admission control and planning for server-side seeded demo runs."""

    def __init__(
        self,
        *,
        event_cap: int = DEFAULT_EVENT_CAP,
        cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS,
        max_concurrent_runs: int = DEFAULT_MAX_CONCURRENT_RUNS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.event_cap = max(1, int(event_cap))
        self.cooldown_seconds = max(0.0, float(cooldown_seconds))
        self.max_concurrent_runs = max(1, int(max_concurrent_runs))
        self._clock = clock
        self._active = 0
        self._last_started_at: float | None = None
        self._runs: dict[str, DemoRunStatus] = {}

    # ------------------------------------------------------------- admission

    def check_admission(self) -> None:
        """Raise when a new demo run must not start right now."""
        if self._active >= self.max_concurrent_runs:
            raise DemoBusyError("a demo run is already in progress")
        if self._last_started_at is not None:
            elapsed = self._clock() - self._last_started_at
            if elapsed < self.cooldown_seconds:
                raise DemoCooldownError(
                    f"demo cooldown active, retry in {self.cooldown_seconds - elapsed:.1f}s"
                )

    def reserve(self) -> None:
        self.check_admission()
        self._active += 1
        self._last_started_at = self._clock()

    def release(self) -> None:
        if self._active > 0:
            self._active -= 1

    @property
    def active_runs(self) -> int:
        return self._active

    # ---------------------------------------------------------------- planning

    def plan(self, seed: int | None = None, event_cap: int | None = None) -> DemoRunPlan:
        """Build the deterministic event plan for one demo run."""
        cap = self.event_cap if event_cap is None else max(1, int(event_cap))
        effective_seed = DEFAULT_SEED if seed is None else int(seed)
        run_id = uuid.uuid4().hex
        match_id = f"demo-{run_id[:12]}"
        events = self._bounded_events(match_id, effective_seed, cap)
        return DemoRunPlan(run_id=run_id, match_id=match_id, seed=effective_seed, events=events)

    @staticmethod
    def _bounded_events(match_id: str, seed: int, cap: int) -> tuple[MatchEvent, ...]:
        generated = list(generate_match(match_id=match_id, seed=seed, events=DEFAULT_BODY_EVENTS))
        if len(generated) <= cap:
            return tuple(generated)
        # Keep the opening event, the bounded body, and the closing event so the
        # match still reads as a complete synthetic match.
        body = generated[1:-1][: max(0, cap - 2)]
        return tuple([generated[0], *body, generated[-1]])

    # ----------------------------------------------------------------- status

    def register(self, plan: DemoRunPlan) -> DemoRunStatus:
        status = DemoRunStatus(run_id=plan.run_id, match_id=plan.match_id, seed=plan.seed,
                               status="running", event_count=0)
        self._runs[plan.run_id] = status
        return status

    def update(self, run_id: str, **fields: object) -> DemoRunStatus | None:
        status = self._runs.get(run_id)
        if status is None:
            return None
        for name, value in fields.items():
            setattr(status, name, value)
        return status

    def status(self, run_id: str) -> DemoRunStatus | None:
        return self._runs.get(run_id)

    def recent(self, limit: int = 20) -> list[DemoRunStatus]:
        return list(self._runs.values())[-limit:]
