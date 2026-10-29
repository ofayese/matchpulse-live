# cspell:ignore Northbridge Segoe minmax Francais matchinfo onclose
from __future__ import annotations

import asyncio
import os
import time
from collections import defaultdict
from dataclasses import dataclass

from fastapi import (
    APIRouter,
    FastAPI,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
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
    DetailLevel,
    EventIngestResponse,
    MatchEvent,
    MatchRecap,
    MatchState,
    MomentComparison,
    MomentVariant,
    Persona,
    PersonalizedInsight,
    VariantsResponse,
)
from .telemetry import Telemetry

DEFAULT_PROFILES = {
    "fan-en": AudienceProfile(
        profile_id="fan-en",
        persona=Persona.FAN,
        locale="en",
        favorite_club="Northbridge-FC",
        favorite_player="NB-9",
        metric_interests=["shooting", "pressing"],
    ),
    "analyst-en": AudienceProfile(
        profile_id="analyst-en",
        persona=Persona.ANALYST,
        locale="en",
        detail=DetailLevel.DEEP,
        metric_interests=["passing", "possession", "pressing"],
    ),
    "broadcaster-es": AudienceProfile(
        profile_id="broadcaster-es",
        persona=Persona.BROADCASTER,
        locale="es",
        detail=DetailLevel.COMPACT,
    ),
    "fan-fr": AudienceProfile(
        profile_id="fan-fr",
        persona=Persona.FAN,
        locale="fr",
        favorite_club="Riverside-Athletic",
        metric_interests=["shooting", "defending"],
    ),
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
                for subscriber in self._subscribers.get(item.match_id, []):
                    if subscriber.profile_id != item.profile_id:
                        continue
                    if subscriber.queue.full():
                        try:
                            subscriber.queue.get_nowait()
                        except asyncio.QueueEmpty:
                            pass
                    subscriber.queue.put_nowait(item)


_DEMO_HTML = """<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">  # noqa: E501\n<title>MatchPulse Live</title><style>\n:root{--navy:#071a2b;--blue:#16b8f3;--lime:#c8f560;--ink:#edf7ff;--muted:#9eb4c7;--warn:#ffb347;--bad:#ff7a7a}  # noqa: E501\n*{box-sizing:border-box}\nbody{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;background:radial-gradient(circle at 80% 0,#123d56,var(--navy) 42%);color:var(--ink);min-height:100vh}  # noqa: E501\nheader{padding:28px 5vw 14px;display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}.brand{font-weight:800;letter-spacing:.04em}.live{color:var(--lime)}  # noqa: E501\nmain{display:grid;grid-template-columns:minmax(260px,1fr) minmax(360px,1.6fr);gap:22px;padding:16px 5vw 48px}.card{background:#0c2437dd;border:1px solid #2a4b61;border-radius:18px;padding:20px;box-shadow:0 16px 45px #0005}  # noqa: E501\nlabel{display:block;color:var(--muted);font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;margin:14px 0 6px}select,button{width:100%;padding:12px;border-radius:10px;border:1px solid #3b6177;background:#102f46;color:var(--ink)}button{margin-top:16px;background:var(--blue);color:#00131e;border:0;font-weight:800;cursor:pointer}  # noqa: E501\nbutton[disabled]{opacity:.55;cursor:not-allowed}\n:focus-visible{outline:3px solid var(--lime);outline-offset:2px}\n.score{font-size:2.5rem;font-weight:900;margin:12px 0}.overlay{min-height:155px;border-left:5px solid var(--lime);padding:18px;background:#061521;border-radius:10px}.overlay h2{margin:0 0 8px;font-size:1.3rem}.overlay p{color:#d5e7f2;line-height:1.5}.meta{font-family:ui-monospace,monospace;color:var(--blue);font-size:.78rem;word-break:break-word}  # noqa: E501\n.feed{margin-top:18px;display:grid;gap:10px}.feed article{padding:12px;border:1px solid #29465a;border-radius:10px;background:#0a1d2c}.pill{display:inline-block;padding:4px 8px;border-radius:99px;background:#173c51;color:var(--lime);font-size:.7rem}.status{color:var(--muted);font-size:.85rem}  # noqa: E501\n.status[data-state="running"]{color:var(--lime)}.status[data-state="connecting"]{color:var(--blue)}.status[data-state="completed"]{color:var(--lime)}.status[data-state="deterministic-fallback"]{color:var(--warn)}.status[data-state="error"]{color:var(--bad)}  # noqa: E501\n.moment{border:1px solid #29465a;border-radius:12px;padding:14px;margin-bottom:14px;background:#0a1d2c}.moment h3{margin:0 0 4px;font-size:1rem}.variant{border-top:1px dashed #29465a;padding-top:10px;margin-top:10px}.variant b{color:var(--lime)}  # noqa: E501\ntable{width:100%;border-collapse:collapse;font-size:.8rem}th,td{text-align:left;padding:6px 8px;border-bottom:1px solid #23404f;vertical-align:top}  # noqa: E501\n@media(max-width:800px){main{grid-template-columns:1fr}}\n</style></head><body>\n<header><div class="brand">MATCHPULSE <span class="live">LIVE</span></div>\n<div class="status" id="status" role="status" aria-live="polite" data-state="idle">Ready</div></header>  # noqa: E501\n<main>\n<section class="card">\n<span class="pill">SYNTHETIC DATA ONLY</span>\n<h1>Every match, made for every fan.</h1>\n<p>One evidence-backed football moment becomes a different experience for an analyst, broadcaster, or fan - in English, Spanish, or French.</p>  # noqa: E501\n<label for="profile">Audience profile</label>\n<select id="profile"><option value="fan-en">fan-en</option><option value="analyst-en">analyst-en</option><option value="broadcaster-es">broadcaster-es</option><option value="fan-fr">fan-fr</option></select>  # noqa: E501\n<label for="language">Comparison language</label>\n<select id="language"><option value="">Audience default</option><option value="en">English</option><option value="es">Espanol</option><option value="fr">Francais</option></select>  # noqa: E501\n<button id="start" type="button">Start synthetic demo</button>\n<button id="replay" type="button">Replay demo</button>\n<p class="meta" id="matchinfo">No demo run yet.</p>\n<p class="meta" id="foundry">Foundry: checking...</p>\n</section>\n<section class="card">\n<div class="score">LIVE INTELLIGENCE</div>\n<div class="overlay" id="overlay"><h2>Waiting for a meaningful moment</h2><p>Insights appear only after the explainability agent validates source event evidence.</p></div>  # noqa: E501\n<div class="feed" id="feed"></div>\n<h3 style="margin-top:26px">Same moment, different audiences</h3>\n<p class="status" id="compare-empty">Run the demo to compare audiences.</p>\n<div id="compare"></div>\n<h3 style="margin-top:26px">Recap</h3>\n<p class="status" id="recap-empty">No recap yet.</p>\n<div id="recap"></div>\n</section>\n</main>\n<script>\n(function () {\n  "use strict";\n  var statusEl = document.getElementById("status");\n  var overlayEl = document.getElementById("overlay");\n  var feedEl = document.getElementById("feed");\n  var compareEl = document.getElementById("compare");\n  var compareEmptyEl = document.getElementById("compare-empty");\n  var recapEl = document.getElementById("recap");\n  var recapEmptyEl = document.getElementById("recap-empty");\n  var matchInfoEl = document.getElementById("matchinfo");\n  var foundryEl = document.getElementById("foundry");\n  var profileEl = document.getElementById("profile");\n  var languageEl = document.getElementById("language");\n  var startBtn = document.getElementById("start");\n  var replayBtn = document.getElementById("replay");\n  var ws = null;\n  var currentMatch = null;\n\n  function el(tag, className, text) {\n    var node = document.createElement(tag);\n    if (className) { node.className = className; }\n    if (text !== undefined && text !== null) { node.textContent = String(text); }  # noqa: E501\n    return node;\n  }\n\n  function setStatus(text, kind) {\n    statusEl.textContent = text;\n    statusEl.setAttribute("data-state", kind);\n  }\n\n  function clear(node) {\n    while (node.firstChild) { node.removeChild(node.firstChild); }\n  }\n\n  function setBusy(busy) {\n    startBtn.disabled = busy;\n    replayBtn.disabled = busy;\n  }\n\n  function renderOverlay(item) {\n    clear(overlayEl);\n    var meta = el("div", "meta", item.locale.toUpperCase() + " \\u00b7 " + item.persona + " \\u00b7 " + Math.floor(item.clock_ms / 60000) + ":" + String(Math.floor((item.clock_ms % 60000) / 1000)).padStart(2, "0"));  # noqa: E501\n    var title = el("h2", null, item.title);\n    var body = el("p", null, item.body);\n    var evidence = el("div", "meta", "Evidence: " + item.evidence.event_ids.join(", ") + " | formula: " + item.evidence.formula + " | confidence " + item.evidence.confidence);  # noqa: E501\n    overlayEl.appendChild(meta);\n    overlayEl.appendChild(title);\n    overlayEl.appendChild(body);\n    overlayEl.appendChild(evidence);\n  }\n\n  function renderFeedItem(item) {\n    var article = el("article");\n    article.appendChild(el("strong", null, item.overlay_text));\n    article.appendChild(el("div", "meta", "priority " + item.priority + " \\u00b7 insight " + item.insight_id));  # noqa: E501\n    feedEl.insertBefore(article, feedEl.firstChild);\n    while (feedEl.children.length > 5) { feedEl.removeChild(feedEl.lastChild); }  # noqa: E501\n  }\n\n  function renderComparison(data) {\n    clear(compareEl);\n    if (!data.moments.length) {\n      compareEmptyEl.textContent = "No comparable moments yet.";\n      return;\n    }\n    compareEmptyEl.textContent = "Shared insight " + data.moments.length + " moment(s), one authoritative basis each.";  # noqa: E501\n    data.moments.forEach(function (moment) {\n      var box = el("div", "moment");\n      box.appendChild(el("h3", null, "Moment " + moment.insight_id));\n      var shared = el("div", "meta", "kind " + moment.kind + " \\u00b7 sequence " + moment.sequence + " \\u00b7 evidence " + moment.evidence_event_ids.join(", "));  # noqa: E501\n      box.appendChild(shared);\n      var table = el("table");\n      var head = el("tr");\n      ["Audience", "Title", "Overlay", "Priority"].forEach(function (label) { head.appendChild(el("th", null, label)); });  # noqa: E501\n      table.appendChild(head);\n      moment.variants.forEach(function (variant) {\n        var row = el("tr");\n        row.appendChild(el("td", null, variant.profile_id + " (" + variant.locale + ")"));  # noqa: E501\n        row.appendChild(el("td", null, variant.title));\n        row.appendChild(el("td", null, variant.overlay_text));\n        row.appendChild(el("td", null, variant.priority));\n        table.appendChild(row);\n      });\n      box.appendChild(table);\n      var stats = el("div", "meta", "authoritative stats: " + JSON.stringify(moment.stats));  # noqa: E501\n      box.appendChild(stats);\n      compareEl.appendChild(box);\n    });\n  }\n\n  function renderRecap(recap) {\n    clear(recapEl);\n    recapEmptyEl.textContent = "";\n    recapEl.appendChild(el("h3", null, recap.headline));\n    var list = el("ul");\n    recap.bullets.forEach(function (bullet) {\n      var item = el("li", null, bullet);\n      list.appendChild(item);\n    });\n    recapEl.appendChild(list);\n    recapEl.appendChild(el("div", "meta", "evidence " + recap.evidence_event_ids.join(", ")));  # noqa: E501\n  }\n\n  function openSocket(matchId, profileId) {\n    if (ws) { ws.close(); ws = null; }\n    var proto = window.location.protocol === "https:" ? "wss" : "ws";\n    ws = new WebSocket(proto + "://" + window.location.host + "/ws/matches/" + encodeURIComponent(matchId) + "?profile_id=" + encodeURIComponent(profileId));  # noqa: E501\n    ws.onopen = function () { setStatus("Running synthetic demo", "running"); };  # noqa: E501\n    ws.onmessage = function (event) {\n      var payload = JSON.parse(event.data);\n      if (payload.type === "welcome") { return; }\n      renderOverlay(payload);\n      renderFeedItem(payload);\n    };\n    ws.onerror = function () { setStatus("WebSocket error", "error"); };\n    ws.onclose = function () { if (statusEl.getAttribute("data-state") === "running") { setStatus("Demo connection closed", "idle"); } };  # noqa: E501\n  }\n\n  function refreshFoundry() {\n    fetch("/health/ready").then(function (response) { return response.json(); }).then(function (data) {  # noqa: E501\n      var mode = data.foundry_mode || "disabled";\n      foundryEl.textContent = "Foundry: " + mode;\n      if (mode === "configured-unverified") {\n        foundryEl.textContent = "Foundry: configured but unverified - deterministic output until a call succeeds";  # noqa: E501\n      }\n      if (mode === "degraded-fallback") {\n        foundryEl.textContent = "Foundry: degraded - deterministic output only";  # noqa: E501\n      }\n    }).catch(function () { foundryEl.textContent = "Foundry: unknown"; });\n  }\n\n  function refreshComparison(matchId) {\n    var url = "/v1/matches/" + encodeURIComponent(matchId) + "/variants";\n    var locale = languageEl.value;\n    if (locale) { url += "?locale=" + encodeURIComponent(locale); }\n    fetch(url).then(function (response) { return response.json(); }).then(renderComparison).catch(function () { });  # noqa: E501\n  }\n\n  function refreshRecap(matchId) {\n    var url = "/v1/matches/" + encodeURIComponent(matchId) + "/recap?profile_id=" + encodeURIComponent(profileEl.value);  # noqa: E501\n    var locale = languageEl.value;\n    if (locale) { url += "&locale=" + encodeURIComponent(locale); }\n    fetch(url).then(function (response) { return response.json(); }).then(renderRecap).catch(function () { });  # noqa: E501\n  }\n\n  function pollRun(runId, matchId) {\n    var attempts = 0;\n    function tick() {\n      attempts += 1;\n      fetch("/v1/demo/runs/" + encodeURIComponent(runId)).then(function (response) { return response.json(); }).then(function (status) {  # noqa: E501\n        if (status.status === "completed") {\n          setStatus("Demo completed", "completed");\n          setBusy(false);\n          refreshComparison(matchId);\n          refreshRecap(matchId);\n          return;\n        }\n        if (status.status === "failed") {\n          setStatus("Demo failed", "error");\n          setBusy(false);\n          return;\n        }\n        if (attempts < 200) { window.setTimeout(tick, 500); }\n      }).catch(function () {\n        if (attempts < 200) { window.setTimeout(tick, 1000); } else { setBusy(false); }  # noqa: E501\n      });\n    }\n    window.setTimeout(tick, 400);\n  }\n\n  function startDemo() {\n    setBusy(true);\n    setStatus("Connecting", "connecting");\n    fetch("/v1/demo/runs", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" })  # noqa: E501\n      .then(function (response) {\n        if (!response.ok) { throw new Error("run rejected"); }\n        return response.json();\n      })\n      .then(function (run) {\n        currentMatch = run.match_id;\n        matchInfoEl.textContent = "Match " + run.match_id + " (run " + run.run_id + ")";  # noqa: E501\n        openSocket(run.match_id, profileEl.value);\n        pollRun(run.run_id, run.match_id);\n      })\n      .catch(function () {\n        setStatus("Could not start the demo", "error");\n        setBusy(false);\n      });\n  }\n\n  startBtn.addEventListener("click", startDemo);\n  replayBtn.addEventListener("click", startDemo);\n  profileEl.addEventListener("change", function () { if (currentMatch) { refreshComparison(currentMatch); refreshRecap(currentMatch); } });  # noqa: E501\n  languageEl.addEventListener("change", function () { if (currentMatch) { refreshComparison(currentMatch); refreshRecap(currentMatch); } });  # noqa: E501\n  refreshFoundry();\n})();\n</script></body></html>"""


def _synthetic_only_enabled() -> bool:
    return os.getenv("CHALLENGE_SYNTHETIC_ONLY", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _locale_override(
    profile: AudienceProfile, locale: str | None
) -> AudienceProfile:
    """Return a copy of the profile using a requested locale, if it is valid."""
    if not locale or locale == profile.locale:
        return profile
    if locale not in {"en", "es", "fr"}:
        return profile
    return profile.model_copy(update={"locale": locale})


router = APIRouter()


def get_profile(
    app: FastAPI, profile_id: str, locale: str | None = None
) -> AudienceProfile:
    item = app.state.profiles.get(profile_id)
    if item is None:
        raise HTTPException(404, "profile not found")
    return _locale_override(item, locale)


async def _ingest_event(
    app: FastAPI, event: MatchEvent
) -> EventIngestResponse:
    started = time.perf_counter()
    if not _synthetic_only_enabled():
        raise HTTPException(503, SYNTHETIC_ONLY_DISABLED_MESSAGE)
    try:
        applied, outputs, warnings, _ = app.state.pipeline.process(
            event, app.state.profiles.values()
        )
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    if app.state.foundry and outputs:
        before = app.state.foundry.counters
        attempt_started = time.perf_counter()
        try:
            enriched, f_warnings = await app.state.foundry.rewrite_many(
                outputs
            )
            outputs = enriched
            warnings.extend(f_warnings)
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
    app.state.telemetry.record_events(
        accepted=1, duplicate=1 if applied.duplicate else 0
    )
    return EventIngestResponse(
        accepted=True,
        duplicate=applied.duplicate,
        latency_ms=round((time.perf_counter() - started) * 1000, 3),
        state=applied.state,
        insights=outputs,
        warnings=warnings,
    )


@router.get("/health/live")
async def health_live() -> dict:
    return {"status": "ok"}


@router.get("/health/ready")
async def health_ready(request: Request) -> dict:
    app = request.app
    if app.state.foundry is None:
        foundry_mode = STATE_DISABLED
    else:
        foundry_mode = app.state.foundry.state
    return {
        "status": "ready",
        "synthetic_only": True,
        "foundry_mode": foundry_mode,
        "telemetry_mode": app.state.telemetry.state,
        "profiles": len(app.state.profiles),
    }


@router.get("/demo", response_class=HTMLResponse)
async def demo() -> str:
    return _DEMO_HTML


@router.get("/v1/profiles")
async def list_profiles(request: Request) -> list[AudienceProfile]:
    return list(request.app.state.profiles.values())


@router.put(
    "/v1/profiles/{profile_id}",
    responses={400: {"description": "Bad Request"}},
)
async def put_profile(
    request: Request, profile_id: str, body: AudienceProfile
) -> AudienceProfile:
    if profile_id != body.profile_id:
        raise HTTPException(400, "path and body profile_id must match")
    request.app.state.profiles[profile_id] = body
    return body


@router.post(
    "/v1/events",
    status_code=202,
    responses={
        503: {"description": "Service Unavailable"},
        409: {"description": "Conflict"},
    },
)
async def post_event(
    request: Request, event: MatchEvent
) -> EventIngestResponse:
    return await _ingest_event(request.app, event)


@router.post(
    "/v1/events/batch",
    status_code=202,
    responses={
        503: {"description": "Service Unavailable"},
        409: {"description": "Conflict"},
    },
)
async def post_batch(
    request: Request, batch: EventBatch
) -> list[EventIngestResponse]:
    responses = []
    for event in batch.events:
        responses.append(await _ingest_event(request.app, event))
    return responses


@router.get(
    "/v1/matches/{match_id}/state",
    responses={404: {"description": "Not Found"}},
)
async def get_state(request: Request, match_id: str) -> MatchState:
    state = request.app.state.pipeline.state.get(match_id)
    if state is None:
        raise HTTPException(404, "match not found")
    return state


@router.post("/v1/matches/{match_id}/reset")
async def reset_match(request: Request, match_id: str) -> dict[str, object]:
    existed = request.app.state.pipeline.state.reset(match_id)
    return {"match_id": match_id, "reset": True, "existed": existed}


@router.get(
    "/v1/matches/{match_id}/recap",
    responses={404: {"description": "Not Found"}},
)
async def recap(
    request: Request,
    match_id: str,
    profile_id: str = Query("fan-en"),
    locale: str | None = Query(None),
) -> MatchRecap:
    try:
        return request.app.state.pipeline.recap(
            match_id, get_profile(request.app, profile_id, locale)
        )
    except KeyError as exc:
        raise HTTPException(404, "match not found") from exc


@router.get("/v1/matches/{match_id}/variants")
async def variants(
    request: Request, match_id: str, locale: str | None = Query(None)
) -> VariantsResponse:
    app = request.app
    insights = app.state.pipeline.state.insights(match_id)
    moments: list[MomentComparison] = []
    for insight in insights:
        variants_for_moment: list[MomentVariant] = []
        for audience in app.state.profiles.values():
            effective = _locale_override(audience, locale)
            rendered = app.state.pipeline.personalize.run(insight, effective)
            variants_for_moment.append(
                MomentVariant(
                    profile_id=rendered.profile_id,
                    locale=rendered.locale,
                    persona=rendered.persona,
                    priority=rendered.priority,
                    title=rendered.title,
                    body=rendered.body,
                    overlay_text=rendered.overlay_text,
                    evidence_event_ids=list(rendered.evidence.event_ids),
                    stats=dict(rendered.stats),
                )
            )
        moments.append(
            MomentComparison(
                insight_id=insight.insight_id,
                sequence=insight.sequence,
                clock_ms=insight.clock_ms,
                kind=insight.kind,
                evidence_event_ids=list(insight.evidence.event_ids),
                stats=dict(insight.stats),
                variants=variants_for_moment,
            )
        )
    return VariantsResponse(match_id=match_id, moments=moments)


@router.post(
    "/v1/demo/runs",
    status_code=202,
    responses={
        503: {"description": "Service Unavailable"},
        409: {"description": "Conflict"},
        429: {"description": "Too Many Requests"},
    },
)
async def start_demo_run(
    request: Request, body: DemoRunRequest | None = None
) -> DemoRunResponse:
    app = request.app
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
        plan = app.state.demo.plan(
            seed=request_body.seed, event_cap=request_body.event_cap
        )
    except Exception:
        app.state.demo.release()
        raise
    app.state.demo.register(plan)
    task = asyncio.create_task(_execute_demo_run(app, plan))
    app.state.demo_tasks.add(task)
    task.add_done_callback(app.state.demo_tasks.discard)
    return DemoRunResponse(
        run_id=plan.run_id,
        match_id=plan.match_id,
        seed=plan.seed,
        status="awaiting-client",
        event_count=plan.event_count,
        websocket_path=f"/ws/matches/{plan.match_id}",
    )


@router.get(
    "/v1/demo/runs/{run_id}", responses={404: {"description": "Not Found"}}
)
async def demo_run_status(
    request: Request, run_id: str
) -> DemoRunStatusResponse:
    status = request.app.state.demo.status(run_id)
    if status is None:
        raise HTTPException(404, "demo run not found")
    return DemoRunStatusResponse(
        run_id=status.run_id,
        match_id=status.match_id,
        seed=status.seed,
        status=status.status,
        event_count=status.event_count,
        insight_count=status.insight_count,
        duplicate_count=status.duplicate_count,
        error=status.error,
    )


@router.websocket("/ws/matches/{match_id}")
async def websocket_match(
    websocket: WebSocket, match_id: str, profile_id: str = Query("fan-en")
) -> None:
    app = websocket.app
    if profile_id not in app.state.profiles:
        await websocket.close(code=4404, reason="profile not found")
        return
    await websocket.accept()
    subscriber = await app.state.hub.subscribe(match_id, profile_id)
    app.state.telemetry.record_websocket(connect=1)
    await websocket.send_json(
        {"type": "welcome", "match_id": match_id, "profile_id": profile_id}
    )
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


def create_app() -> FastAPI:
    app = FastAPI(
        title="MatchPulse Live",
        version="0.1.0",
        description="Real-time, multilingual, personalized football intelligence from synthetic events",
    )
    app.state.pipeline = SupervisorAgent()
    app.state.profiles = dict(DEFAULT_PROFILES)
    app.state.hub = BroadcastHub()
    app.state.telemetry = Telemetry.from_env()
    app.state.demo = DemoRunManager()
    app.state.demo_tasks = set()
    app.state.demo_subscriber_wait_seconds = DEMO_SUBSCRIBER_WAIT_SECONDS
    app.state.demo_emit_delay_seconds = DEMO_EMIT_DELAY_SECONDS
    foundry_settings = FoundrySettings.from_env()
    app.state.foundry = (
        FoundryNarrativeClient(foundry_settings) if foundry_settings else None
    )

    async def ingest_wrapper(event: MatchEvent) -> EventIngestResponse:
        return await _ingest_event(app, event)

    app.state.ingest = ingest_wrapper

    @app.middleware("http")
    async def telemetry_middleware(request: Request, call_next):
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
        finally:
            route = request.scope.get("route")
            template = getattr(route, "path", None) or "unmatched"
            app.state.telemetry.record_http(
                template,
                request.method,
                status_code,
                (time.perf_counter() - started) * 1000,
            )
        return response

    app.include_router(router)
    return app


async def _wait_for_subscribers(app: FastAPI, match_id: str) -> None:
    deadline = time.monotonic() + app.state.demo_subscriber_wait_seconds
    while time.monotonic() < deadline:
        if app.state.hub.subscriber_count(match_id) > 0:
            break
        await asyncio.sleep(0.05)


async def _execute_demo_run(app: FastAPI, plan: DemoRunPlan) -> None:
    """Drive one demo run: wait for the browser, then emit bounded events."""
    status = app.state.demo.status(plan.run_id)
    if status is not None:
        status.status = "running"
    try:
        await _wait_for_subscribers(app, plan.match_id)
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
