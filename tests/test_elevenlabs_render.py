from __future__ import annotations

import json

import pytest

from scripts import matchpulse_elevenlabs_render as render


def test_unit_windows_keep_clearance_and_final_silence() -> None:
    script = json.loads(render.SCRIPT_PATH.read_text(encoding="utf-8"))
    previous_end = 0.0
    for unit in script["units"]:
        start, end = render.unit_window(unit)
        assert start >= previous_end
        assert end <= unit["visual_end_seconds"] - 0.1 + 1e-9
        previous_end = unit["visual_end_seconds"]
    assert render.unit_window(script["units"][-1])[1] <= 114.5


def test_aliases_are_synthesis_only() -> None:
    assert render.apply_aliases("Foundry is off", {"Foundry": "Foundree"}) == "Foundree is off"
    assert render.apply_aliases("Foundry is off", {}) == "Foundry is off"


def test_identity_check_rejects_missing_or_changed_file(tmp_path) -> None:
    target = tmp_path / "x.bin"
    target.write_bytes(b"abc")
    with pytest.raises(render.RenderError):
        render.require_identity(target, "0" * 64)
    with pytest.raises(render.RenderError):
        render.require_identity(tmp_path / "missing.bin", "0" * 64)
    render.require_identity(target, render.sha256_file(target))


def test_clip_count_detects_full_scale() -> None:
    import array

    samples = array.array("h", [0, 32767, -32768, 100])
    assert render.clip_count(samples.tobytes()) == 2
