import asyncio
import json

import httpx

from matchpulse.foundry import FoundryNarrativeClient, FoundrySettings
from matchpulse.models import Evidence, Persona, PersonalizedInsight


def item():
    return PersonalizedInsight(
        insight_id="i",
        match_id="m",
        profile_id="fan",
        locale="en",
        persona=Persona.FAN,
        priority=0.8,
        title="Shot",
        body="A shot reached 101 km/h.",
        overlay_text="101 km/h shot",
        clock_ms=1,
        sequence=1,
        severity="notable",
        evidence=Evidence(
            event_ids=["e1"],
            inputs={"speed": 101},
            formula="measured speed",
            confidence=0.9,
        ),
        stats={"speed_kmh": 101},
        expires_in_ms=12000,
    )


def test_foundry_guard_rejects_new_numeric_claim():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "title": "Shot",
                                    "body": "A 130 km/h shot",
                                    "overlay_text": "130 km/h",
                                }
                            )
                        }
                    }
                ]
            },
        )

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = FoundryNarrativeClient(
        FoundrySettings("https://example.test", "model", "secret"),
        http_client=http,
    )
    source = item()
    try:
        output, warning = asyncio.run(client.rewrite(source))
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning is not None
    assert "unsupported-number" in warning
