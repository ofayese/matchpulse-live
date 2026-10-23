from __future__ import annotations

import asyncio
import os
import time
from collections import defaultdict
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field

from .agents import SupervisorAgent
from .demo import DemoBusyError, DemoCooldownError, DemoRunManager, DemoRunPlan
from .foundry import (
    STATE_DISABLED,
    FoundryNarrativeClient,
    FoundrySettings,
)
from .models import (
    AudienceProfile,
    DemoRunRequest,
    DemoRunResponse,
    DemoRunStatusResponse,
    EventIngestResponse,
    MatchEvent,
    MatchRecap,
    MatchState,
    MomentComparison,
    MomentVariant,
    PersonalizedInsight,
    VariantsResponse,
)
from .telemetry import Telemetry

DEFAULT_PROFILES = {
    "fan-en": AudienceProfile(profile_id="fan-en", persona="fan", locale="en", favorite_club="Northbridge-FC", favorite_player="NB-9", metric_interests=["shooting", "pressing"]),
    "analyst-en": AudienceProfile(profile_id="analyst-en", persona="analyst", locale="en", detail="deep", metric_interests=["passing", "possession", "pressing"]),
    "broadcaster-es": AudienceProfile(profile_id="broadcaster-es", persona="broadcaster", locale="es", detail="compact"),
    "fan-fr": AudienceProfile(profile_id="fan-fr", persona="fan", locale="fr", favorite_club="Riverside-Athletic", metric_interests=["shooting", "defending"]),
}

SYNTHETIC_ONLY_DISABLED_MESSAGE = (
    "challenge safety gate CHALLENGE_SYNTHETIC_ONLY must remain enabled"
)

DEMO_SUBSCRIBER_WAIT_SECONDS = 10.0
DEMO_EMIT_DELAY_SECONDS = 0.30


class EventBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    events: list[MatchEvent] = Field(min_length=1, max_length=500)


@dataclass
class Subscriber:
    profile_id: str
    queue: asyncio.Queue[PersonalizedInsight]


class BroadcastHub:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Subscriber]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def subscribe(self, match_id: str, profile_id: str) -> Subscriber:
        subscriber = Subscriber(profile_id, asyncio.Queue(maxsize=64))
        async with self._lock:
            self._subscribers[match_id].append(subscriber)
        return subscriber

    async def unsubscribe(self, match_id: str, subscriber: Subscriber) -> None:
        async with self._lock:
            if subscriber in self._subscribers.get(match_id, []):
                self._subscribers[match_id].remove(subscriber)

    def subscriber_count(self, match_id: str) -> int:
        return len(self._subscribers.get(match_id, []))

    async def publish(self, items: list[PersonalizedInsight]) -> None:
        async with self._lock:
            for item in items:
                for subscriber in list(self._subscribers.get(item.match_id, [])):
                    if subscriber.profile_id != item.profile_id:
                        continue
                    if subscriber.queue.full():
                        try:
                            subscriber.queue.get_nowait()
                        except asyncio.QueueEmpty:
                            pass
                    subscriber.queue.put_nowait(item)


_DEMO_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MatchPulse Live</title><style>
:root{--navy:#071a2b;--blue:#16b8f3;--lime:#c8f560;--ink:#edf7ff;--muted:#9eb4c7;--warn:#ffb347;--bad:#ff7a7a}
*{box-sizing:border-box}
body{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;background:radial-gradient(circle at 80% 0,#123d56,var(--navy) 42%);color:var(--ink);min-height:100vh}
header{padding:28px 5vw 14px;display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}.brand{font-weight:800;letter-spacing:.04em}.live{color:var(--lime)}
main{display:grid;grid-template-columns:minmax(260px,1fr) minmax(360px,1.6fr);gap:22px;padding:16px 5vw 48px}.card{background:#0c2437dd;border:1px solid #2a4b61;border-radius:18px;padding:20px;box-shadow:0 16px 45px #0005}
label{display:block;color:var(--muted);font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;margin:14px 0 6px}select,button{width:100%;padding:12px;border-radius:10px;border:1px solid #3b6177;background:#102f46;color:var(--ink)}button{margin-top:16px;background:var(--blue);color:#00131e;border:0;font-weight:800;cursor:pointer}
button[disabled]{opacity:.55;cursor:not-allowed}
:focus-visible{outline:3px solid var(--lime);outline-offset:2px}
.score{font-size:2.5rem;font-weight:900;margin:12px 0}.overlay{min-height:155px;border-left:5px solid var(--lime);padding:18px;background:#061521;border-radius:10px}.overlay h2{margin:0 0 8px;font-size:1.3rem}.overlay p{color:#d5e7f2;line-height:1.5}.meta{font-family:ui-monospace,monospace;color:var(--blue);font-size:.78rem;word-break:break-word}
.feed{margin-top:18px;display:grid;gap:10px}.feed article{padding:12px;border:1px solid #29465a;border-radius:10px;background:#0a1d2c}.pill{display:inline-block;padding:4px 8px;border-radius:99px;background:#173c51;color:var(--lime);font-size:.7rem}.status{color:var(--muted);font-size:.85rem}
.status[data-state="running"]{color:var(--lime)}.status[data-state="connecting"]{color:var(--blue)}.status[data-state="completed"]{color:var(--lime)}.status[data-state="deterministic-fallback"]{color:var(--warn)}.status[data-state="error"]{color:var(--bad)}
.moment{border:1px solid #29465a;border-radius:12px;padding:14px;margin-bottom:14px;background:#0a1d2c}.moment h3{margin:0 0 4px;font-size:1rem}.variant{border-top:1px dashed #29465a;padding-top:10px;margin-top:10px}.variant b{color:var(--lime)}
table{width:100%;border-collapse:collapse;font-size:.8rem}th,td{text-align:left;padding:6px 8px;border-bottom:1px solid #23404f;vertical-align:top}
@media(max-width:800px){main{grid-template-columns:1fr}}
</style></head><body>
<header><div class="brand">MATCHPULSE <span class="live">LIVE</span></div>
<div class="status" id="status" role="status" aria-live="polite" data-state="idle">Ready</div></header>
<main>
<section class="card">
<span class="pill">SYNTHETIC DATA ONLY</span>
<h1>Every match, made for every fan.</h1>
<p>One evidence-backed football moment becomes a different experience for an analyst, broadcaster, or fan - in English, Spanish, or French.</p>
<label for="profile">Audience profile</label>
<select id="profile"><option value="fan-en">fan-en</option><option value="analyst-en">analyst-en</option><option value="broadcaster-es">broadcaster-es</option><option value="fan-fr">fan-fr</option></select>
<label for="language">Comparison language</label>
<select id="language"><option value="">Audience default</option><option value="en">English</option><option value="es">Espanol</option><option value="fr">Francais</option></select>
<button id="start" type="button">Start synthetic demo</button>
<button id="replay" type="button">Replay demo</button>
<p class="meta" id="matchinfo">No demo run yet.</p>
<p class="meta" id="foundry">Foundry: checking...</p>
</section>
<section class="card">
<div class="score">LIVE INTELLIGENCE</div>
<div class="overlay" id="overlay"><h2>Waiting for a meaningful moment</h2><p>Insights appear only after the explainability agent validates source event evidence.</p></div>
<div class="feed" id="feed"></div>
<h3 style="margin-top:26px">Same moment, different audiences</h3>
<p class="status" id="compare-empty">Run the demo to compare audiences.</p>
<div id="compare"></div>
<h3 style="margin-top:26px">Recap</h3>
<p class="status" id="recap-empty">No recap yet.</p>
<div id="recap"></div>
</section>
</main>
<script>
(function () {
  "use strict";
  var statusEl = document.getElementById("status");
  var overlayEl = document.getElementById("overlay");
  var feedEl = document.getElementById("feed");
  var compareEl = document.getElementById("compare");
  var compareEmptyEl = document.getElementById("compare-empty");
  var recapEl = document.getElementById("recap");
  var recapEmptyEl = document.getElementById("recap-empty");
  var matchInfoEl = document.getElementById("matchinfo");
  var foundryEl = document.getElementById("foundry");
  var profileEl = document.getElementById("profile");
  var languageEl = document.getElementById("language");
  var startBtn = document.getElementById("start");
  var replayBtn = document.getElementById("replay");
  var ws = null;
  var currentMatch = null;

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text !== undefined && text !== null) { node.textContent = String(text); }
    return node;
  }

  function setStatus(text, kind) {
    statusEl.textContent = text;
    statusEl.setAttribute("data-state", kind);
  }

  function clear(node) {
    while (node.firstChild) { node.removeChild(node.firstChild); }
  }

  function setBusy(busy) {
    startBtn.disabled = busy;
    replayBtn.disabled = busy;
  }

  function renderOverlay(item) {
    clear(overlayEl);
    var meta = el("div", "meta", item.locale.toUpperCase() + " \\u00b7 " + item.persona + " \\u00b7 " + Math.floor(item.clock_ms / 60000) + ":" + String(Math.floor((item.clock_ms % 60000) / 1000)).padStart(2, "0"));
    var title = el("h2", null, item.title);
    var body = el("p", null, item.body);
    var evidence = el("div", "meta", "Evidence: " + item.evidence.event_ids.join(", ") + " | formula: " + item.evidence.formula + " | confidence " + item.evidence.confidence);
    overlayEl.appendChild(meta);
    overlayEl.appendChild(title);
    overlayEl.appendChild(body);
    overlayEl.appendChild(evidence);
  }

  function renderFeedItem(item) {
    var article = el("article");
    article.appendChild(el("strong", null, item.overlay_text));
    article.appendChild(el("div", "meta", "priority " + item.priority + " \\u00b7 insight " + item.insight_id));
    feedEl.insertBefore(article, feedEl.firstChild);
    while (feedEl.children.length > 5) { feedEl.removeChild(feedEl.lastChild); }
  }

  function renderComparison(data) {
    clear(compareEl);
    if (!data.moments.length) {
      compareEmptyEl.textContent = "No comparable moments yet.";
      return;
    }
    compareEmptyEl.textContent = "Shared insight " + data.moments.length + " moment(s), one authoritative basis each.";
    data.moments.forEach(function (moment) {
      var box = el("div", "moment");
      box.appendChild(el("h3", null, "Moment " + moment.insight_id));
      var shared = el("div", "meta", "kind " + moment.kind + " \\u00b7 sequence " + moment.sequence + " \\u00b7 evidence " + moment.evidence_event_ids.join(", "));
      box.appendChild(shared);
      var table = el("table");
      var head = el("tr");
      ["Audience", "Title", "Overlay", "Priority"].forEach(function (label) { head.appendChild(el("th", null, label)); });
      table.appendChild(head);
      moment.variants.forEach(function (variant) {
        var row = el("tr");
        row.appendChild(el("td", null, variant.profile_id + " (" + variant.locale + ")"));
        row.appendChild(el("td", null, variant.title));
        row.appendChild(el("td", null, variant.overlay_text));
        row.appendChild(el("td", null, variant.priority));
        table.appendChild(row);
      });
      box.appendChild(table);
      var stats = el("div", "meta", "authoritative stats: " + JSON.stringify(moment.stats));
      box.appendChild(stats);
      compareEl.appendChild(box);
    });
  }

  function renderRecap(recap) {
    clear(recapEl);
    recapEmptyEl.textContent = "";
    recapEl.appendChild(el("h3", null, recap.headline));
    var list = el("ul");
    recap.bullets.forEach(function (bullet) {
      var item = el("li", null, bullet);
      list.appendChild(item);
    });
    recapEl.appendChild(list);
    recapEl.appendChild(el("div", "meta", "evidence " + recap.evidence_event_ids.join(", ")));
  }

  function openSocket(matchId, profileId) {
    if (ws) { ws.close(); ws = null; }
    var proto = window.location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(proto + "://" + window.location.host + "/ws/matches/" + encodeURIComponent(matchId) + "?profile_id=" + encodeURIComponent(profileId));
    ws.onopen = function () { setStatus("Running synthetic demo", "running"); };
    ws.onmessage = function (event) {
      var payload = JSON.parse(event.data);
      if (payload.type === "welcome") { return; }
      renderOverlay(payload);
      renderFeedItem(payload);
    };
    ws.onerror = function () { setStatus("WebSocket error", "error"); };
    ws.onclose = function () { if (statusEl.getAttribute("data-state") === "running") { setStatus("Demo connection closed", "idle"); } };
  }

  function refreshFoundry() {
    fetch("/health/ready").then(function (response) { return response.json(); }).then(function (data) {
      var mode = data.foundry_mode || "disabled";
      foundryEl.textContent = "Foundry: " + mode;
      if (mode === "configured-unverified") {
        foundryEl.textContent = "Foundry: configured but unverified - deterministic output until a call succeeds";
      }
      if (mode === "degraded-fallback") {
        foundryEl.textContent = "Foundry: degraded - deterministic output only";
      }
    }).catch(function () { foundryEl.textContent = "Foundry: unknown"; });
  }

  function refreshComparison(matchId) {
    var url = "/v1/matches/" + encodeURIComponent(matchId) + "/variants";
    var locale = languageEl.value;
    if (locale) { url += "?locale=" + encodeURIComponent(locale); }
    fetch(url).then(function (response) { return response.json(); }).then(renderComparison).catch(function () { });
  }

  function refreshRecap(matchId) {
    var url = "/v1/matches/" + encodeURIComponent(matchId) + "/recap?profile_id=" + encodeURIComponent(profileEl.value);
    var locale = languageEl.value;
    if (locale) { url += "&locale=" + encodeURIComponent(locale); }
    fetch(url).then(function (response) { return response.json(); }).then(renderRecap).catch(function () { });
  }

  function pollRun(runId, matchId) {
    var attempts = 0;
    function tick() {
      attempts += 1;
      fetch("/v1/demo/runs/" + encodeURIComponent(runId)).then(function (response) { return response.json(); }).then(function (status) {
        if (status.status === "completed") {
          setStatus("Demo completed", "completed");
          setBusy(false);
          refreshComparison(matchId);
          refreshRecap(matchId);
          return;
        }
        if (status.status === "failed") {
          setStatus("Demo failed", "error");
          setBusy(false);
          return;
        }
        if (attempts < 200) { window.setTimeout(tick, 500); }
      }).catch(function () {
        if (attempts < 200) { window.setTimeout(tick, 1000); } else { setBusy(false); }
      });
    }
    window.setTimeout(tick, 400);
  }

  function startDemo() {
    setBusy(true);
    setStatus("Connecting", "connecting");
    fetch("/v1/demo/runs", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" })
      .then(function (response) {
        if (!response.ok) { throw new Error("run rejected"); }
        return response.json();
      })
      .then(function (run) {
        currentMatch = run.match_id;
        matchInfoEl.textContent = "Match " + run.match_id + " (run " + run.run_id + ")";
        openSocket(run.match_id, profileEl.value);
        pollRun(run.run_id, run.match_id);
      })
      .catch(function () {
        setStatus("Could not start the demo", "error");
        setBusy(false);
      });
  }

  startBtn.addEventListener("click", startDemo);
  replayBtn.addEventListener("click", startDemo);
  profileEl.addEventListener("change", function () { if (currentMatch) { refreshComparison(currentMatch); refreshRecap(currentMatch); } });
  languageEl.addEventListener("change", function () { if (currentMatch) { refreshComparison(currentMatch); refreshRecap(currentMatch); } });
  refreshFoundry();
})();
</script></body></html>"""


def _synthetic_only_enabled() -> bool:
    return os.getenv("CHALLENGE_SYNTHETIC_ONLY", "true").strip().lower() in {"1", "true", "yes", "on"}


def _locale_override(profile: AudienceProfile, locale: str | None) -> AudienceProfile:
    """Return a copy of the profile using a requested locale, if it is valid."""
    if not locale or locale == profile.locale:
        return profile
    if locale not in {"en", "es", "fr"}:
        return profile
    return profile.model_copy(update={"locale": locale})


def create_app() -> FastAPI:
    app = FastAPI(title="MatchPulse Live", version="0.1.0", description="Real-time, multilingual, personalized football intelligence from synthetic events")
    app.state.pipeline = SupervisorAgent()
    app.state.profiles = dict(DEFAULT_PROFILES)
    app.state.hub = BroadcastHub()
    app.state.telemetry = Telemetry.from_env()
    app.state.demo = DemoRunManager()
    app.state.demo_tasks = set()
    app.state.demo_subscriber_wait_seconds = DEMO_SUBSCRIBER_WAIT_SECONDS
    app.state.demo_emit_delay_seconds = DEMO_EMIT_DELAY_SECONDS
    foundry_settings = FoundrySettings.from_env()
    app.state.foundry = FoundryNarrativeClient(foundry_settings) if foundry_settings else None

    def profile(profile_id: str, locale: str | None = None) -> AudienceProfile:
        item = app.state.profiles.get(profile_id)
        if item is None:
            raise HTTPException(404, "profile not found")
        return _locale_override(item, locale)

    async def ingest(event: MatchEvent) -> EventIngestResponse:
        started = time.perf_counter()
        if not _synthetic_only_enabled():
            raise HTTPException(503, SYNTHETIC_ONLY_DISABLED_MESSAGE)
        try:
            applied, outputs, warnings, _handoffs = app.state.pipeline.process(event, app.state.profiles.values())
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        if app.state.foundry and outputs:
            before = app.state.foundry.counters
            attempt_started = time.perf_counter()
            try:
                enriched, foundry_warnings = await app.state.foundry.rewrite_many(outputs)
                outputs = enriched
                warnings.extend(foundry_warnings)
            except Exception:
                outputs = list(outputs)
            after = app.state.foundry.counters
            app.state.telemetry.record_foundry(
                attempt=after["attempted"] - before["attempted"],
                success=after["succeeded"] - before["succeeded"],
                fallback=after["fallbacks"] - before["fallbacks"],
                rejection=after["rejections"] - before["rejections"],
                latency_ms=(time.perf_counter() - attempt_started) * 1000,
            )
        await app.state.hub.publish(outputs)
        app.state.telemetry.record_events(accepted=1, duplicate=1 if applied.duplicate else 0)
        return EventIngestResponse(accepted=True, duplicate=applied.duplicate,
            latency_ms=round((time.perf_counter() - started) * 1000, 3), state=applied.state,
            insights=outputs, warnings=warnings)

    app.state.ingest = ingest

    @app.middleware("http")
    async def telemetry_middleware(request, call_next):
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
        finally:
            route = request.scope.get("route")
            template = getattr(route, "path", None) or "unmatched"
            app.state.telemetry.record_http(template, request.method, status_code,
                                            (time.perf_counter() - started) * 1000)
        return response

    @app.get("/health/live")
    async def health_live() -> dict:
        return {"status": "ok"}

    @app.get("/health/ready")
    async def health_ready() -> dict:
        if app.state.foundry is None:
            foundry_mode = STATE_DISABLED
        else:
            foundry_mode = app.state.foundry.state
        return {"status": "ready", "synthetic_only": True,
                "foundry_mode": foundry_mode,
                "telemetry_mode": app.state.telemetry.state,
                "profiles": len(app.state.profiles)}

    @app.get("/demo", response_class=HTMLResponse)
    async def demo() -> str:
        return _DEMO_HTML

    @app.get("/v1/profiles", response_model=list[AudienceProfile])
    async def list_profiles() -> list[AudienceProfile]:
        return list(app.state.profiles.values())

    @app.put("/v1/profiles/{profile_id}", response_model=AudienceProfile)
    async def put_profile(profile_id: str, body: AudienceProfile) -> AudienceProfile:
        if profile_id != body.profile_id:
            raise HTTPException(400, "path and body profile_id must match")
        app.state.profiles[profile_id] = body
        return body

    @app.post("/v1/events", response_model=EventIngestResponse, status_code=202)
    async def post_event(event: MatchEvent) -> EventIngestResponse:
        return await ingest(event)

    @app.post("/v1/events/batch", response_model=list[EventIngestResponse], status_code=202)
    async def post_batch(batch: EventBatch) -> list[EventIngestResponse]:
        responses = []
        for event in batch.events:
            responses.append(await ingest(event))
        return responses

    @app.get("/v1/matches/{match_id}/state", response_model=MatchState)
    async def get_state(match_id: str) -> MatchState:
        state = app.state.pipeline.state.get(match_id)
        if state is None:
            raise HTTPException(404, "match not found")
        return state

    @app.post("/v1/matches/{match_id}/reset")
    async def reset_match(match_id: str) -> dict[str, object]:
        existed = app.state.pipeline.state.reset(match_id)
        return {"match_id": match_id, "reset": True, "existed": existed}

    @app.get("/v1/matches/{match_id}/recap", response_model=MatchRecap)
    async def recap(match_id: str, profile_id: str = Query("fan-en"),
                    locale: str | None = Query(None)) -> MatchRecap:
        try:
            return app.state.pipeline.recap(match_id, profile(profile_id, locale))
        except KeyError as exc:
            raise HTTPException(404, "match not found") from exc

    @app.get("/v1/matches/{match_id}/variants", response_model=VariantsResponse)
    async def variants(match_id: str, locale: str | None = Query(None)) -> VariantsResponse:
        """Return every shared moment with each audience's presentation.

        Every variant of a moment shares the same insight id, the same evidence
        event ids and the same authoritative statistics; only presentation,
        priority, detail and language may differ.
        """
        insights = app.state.pipeline.state.insights(match_id)
        moments: list[MomentComparison] = []
        for insight in insights:
            variants_for_moment: list[MomentVariant] = []
            for audience in app.state.profiles.values():
                effective = _locale_override(audience, locale)
                rendered = app.state.pipeline.personalize.run(insight, effective)
                variants_for_moment.append(MomentVariant(
                    profile_id=rendered.profile_id,
                    locale=rendered.locale,
                    persona=rendered.persona,
                    priority=rendered.priority,
                    title=rendered.title,
                    body=rendered.body,
                    overlay_text=rendered.overlay_text,
                    evidence_event_ids=list(rendered.evidence.event_ids),
                    stats=dict(rendered.stats),
                ))
            moments.append(MomentComparison(
                insight_id=insight.insight_id,
                sequence=insight.sequence,
                clock_ms=insight.clock_ms,
                kind=insight.kind,
                evidence_event_ids=list(insight.evidence.event_ids),
                stats=dict(insight.stats),
                variants=variants_for_moment,
            ))
        return VariantsResponse(match_id=match_id, moments=moments)

    @app.post("/v1/demo/runs", response_model=DemoRunResponse, status_code=202)
    async def start_demo_run(body: DemoRunRequest | None = None) -> DemoRunResponse:
        """Start a bounded, seeded, synthetic-only demo run."""
        if not _synthetic_only_enabled():
            raise HTTPException(503, SYNTHETIC_ONLY_DISABLED_MESSAGE)
        request_body = body or DemoRunRequest()
        try:
            app.state.demo.reserve()
        except DemoBusyError as exc:
            raise HTTPException(409, "a demo run is already in progress") from exc
        except DemoCooldownError as exc:
            raise HTTPException(429, str(exc)) from exc
        try:
            plan = app.state.demo.plan(seed=request_body.seed, event_cap=request_body.event_cap)
        except Exception:
            app.state.demo.release()
            raise
        app.state.demo.register(plan)
        task = asyncio.create_task(_execute_demo_run(app, plan))
        app.state.demo_tasks.add(task)
        task.add_done_callback(app.state.demo_tasks.discard)
        return DemoRunResponse(run_id=plan.run_id, match_id=plan.match_id, seed=plan.seed,
                               status="awaiting-client", event_count=plan.event_count,
                               websocket_path=f"/ws/matches/{plan.match_id}")

    @app.get("/v1/demo/runs/{run_id}", response_model=DemoRunStatusResponse)
    async def demo_run_status(run_id: str) -> DemoRunStatusResponse:
        status = app.state.demo.status(run_id)
        if status is None:
            raise HTTPException(404, "demo run not found")
        return DemoRunStatusResponse(run_id=status.run_id, match_id=status.match_id, seed=status.seed,
                                     status=status.status, event_count=status.event_count,
                                     insight_count=status.insight_count,
                                     duplicate_count=status.duplicate_count, error=status.error)

    @app.websocket("/ws/matches/{match_id}")
    async def websocket_match(websocket: WebSocket, match_id: str, profile_id: str = Query("fan-en")) -> None:
        if profile_id not in app.state.profiles:
            await websocket.close(code=4404, reason="profile not found")
            return
        await websocket.accept()
        subscriber = await app.state.hub.subscribe(match_id, profile_id)
        app.state.telemetry.record_websocket(connect=1)
        await websocket.send_json({"type": "welcome", "match_id": match_id, "profile_id": profile_id})
        try:
            while True:
                item = await subscriber.queue.get()
                await websocket.send_json(item.model_dump(mode="json"))
                app.state.telemetry.record_websocket(send=1)
        except WebSocketDisconnect:
            pass
        finally:
            app.state.telemetry.record_websocket(disconnect=1)
            await app.state.hub.unsubscribe(match_id, subscriber)

    return app


async def _execute_demo_run(app: FastAPI, plan: DemoRunPlan) -> None:
    """Drive one demo run: wait for the browser, then emit bounded events."""
    status = app.state.demo.status(plan.run_id)
    if status is not None:
        status.status = "running"
    try:
        deadline = time.monotonic() + app.state.demo_subscriber_wait_seconds
        while time.monotonic() < deadline:
            if app.state.hub.subscriber_count(plan.match_id) > 0:
                break
            await asyncio.sleep(0.05)
        for event in plan.events:
            try:
                response = await app.state.ingest(event)
            except HTTPException as exc:
                if status is not None:
                    status.status = "failed"
                    status.error = str(exc.detail)
                return
            if status is not None:
                status.event_count += 1
                status.insight_count += len(response.insights)
                status.duplicate_count += 1 if response.duplicate else 0
            await asyncio.sleep(app.state.demo_emit_delay_seconds)
        if status is not None:
            status.status = "completed"
    except Exception as exc:  # pragma: no cover - defensive
        if status is not None:
            status.status = "failed"
            status.error = type(exc).__name__
    finally:
        app.state.demo.release()


app = create_app()
