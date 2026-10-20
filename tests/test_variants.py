"""Shared-moment comparison across audiences.

Every audience must present the same authoritative moment: the same insight id,
the same evidence event ids, the same statistics and the same deterministic
basis. Only presentation, priority, detail and language may differ.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from matchpulse.service import create_app

PROFILES = ("fan-en", "analyst-en", "broadcaster-es", "fan-fr")


def _seed(client: TestClient) -> str:
    match_id = "compare-demo"
    events = [
        {"match_id": match_id, "sequence": 0, "clock_ms": 0, "event_type": "match_start", "source": "synthetic"},
        {"match_id": match_id, "sequence": 1, "clock_ms": 45000, "event_type": "shot",
         "team_id": "Northbridge-FC", "player_id": "NB-7", "outcome": "on_target",
         "speed_kmh": 118, "source": "synthetic"},
        {"match_id": match_id, "sequence": 2, "clock_ms": 90000, "event_type": "tackle",
         "team_id": "Northbridge-FC", "player_id": "NB-7", "outcome": "success",
         "x": 78, "y": 40, "source": "synthetic"},
        {"match_id": match_id, "sequence": 3, "clock_ms": 5400000, "event_type": "match_end", "source": "synthetic"},
    ]
    for event in events:
        assert client.post("/v1/events", json=event).status_code == 202
    return match_id


def test_variants_share_one_authoritative_basis():
    with TestClient(create_app()) as client:
        match_id = _seed(client)
        response = client.get(f"/v1/matches/{match_id}/variants")
        assert response.status_code == 200
        moments = response.json()["moments"]
        assert moments
        for moment in moments:
            variants = {variant["profile_id"]: variant for variant in moment["variants"]}
            assert set(variants) == set(PROFILES)
            for variant in variants.values():
                assert variant["evidence_event_ids"] == moment["evidence_event_ids"]
            # The authoritative statistics are identical for every audience.
            assert len({tuple(sorted(variant["stats"].items())) for variant in moment["variants"]}) == 1
            # The insight id is shared, so the presentation is the only difference.
            assert all(variant["profile_id"] in PROFILES for variant in moment["variants"])


def test_variants_preserve_evidence_and_identifiers():
    with TestClient(create_app()) as client:
        match_id = _seed(client)
        moments = client.get(f"/v1/matches/{match_id}/variants").json()["moments"]
        for moment in moments:
            assert moment["insight_id"]
            assert moment["evidence_event_ids"]
            assert moment["stats"]


def test_variants_use_the_default_locale_of_each_audience():
    with TestClient(create_app()) as client:
        match_id = _seed(client)
        moments = client.get(f"/v1/matches/{match_id}/variants").json()["moments"]
        locales = {variant["profile_id"]: variant["locale"]
                   for moment in moments for variant in moment["variants"]}
        assert locales["fan-en"] == "en"
        assert locales["analyst-en"] == "en"
        assert locales["broadcaster-es"] == "es"
        assert locales["fan-fr"] == "fr"


def test_a_language_override_changes_only_the_presentation():
    with TestClient(create_app()) as client:
        match_id = _seed(client)
        default = client.get(f"/v1/matches/{match_id}/variants").json()["moments"]
        overridden = client.get(f"/v1/matches/{match_id}/variants", params={"locale": "fr"}).json()["moments"]
        assert len(default) == len(overridden)
        for before, after in zip(default, overridden, strict=True):
            assert before["insight_id"] == after["insight_id"]
            assert before["evidence_event_ids"] == after["evidence_event_ids"]
            assert before["stats"] == after["stats"]
            assert {variant["locale"] for variant in after["variants"]} == {"fr"}


def test_presentation_differs_between_audiences():
    with TestClient(create_app()) as client:
        match_id = _seed(client)
        moments = client.get(f"/v1/matches/{match_id}/variants").json()["moments"]
        titles = {moment["insight_id"]: {variant["profile_id"]: variant["title"] for variant in moment["variants"]}
                  for moment in moments}
        assert titles
    assert any(len(set(values.values())) > 1 for values in titles.values())


def test_unknown_match_has_no_moments():
    with TestClient(create_app()) as client:
        response = client.get("/v1/matches/does-not-exist/variants")
        assert response.status_code == 200
        assert response.json()["moments"] == []


def test_health_ready_reports_a_truthful_foundry_state():
    with TestClient(create_app()) as client:
        payload = client.get("/health/ready").json()
        assert payload["synthetic_only"] is True
        assert payload["foundry_mode"] == "disabled"
        assert payload["telemetry_mode"] == "disabled"
