from __future__ import annotations

import hashlib
import io
import json
import subprocess
import tempfile
import wave
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx


class LocalTTSError(RuntimeError):
    """Raised when local TTS cannot safely complete a requested operation."""


@dataclass(frozen=True)
class TTSContract:
    """Service contract knobs kept together until the local service is finalized."""

    health_path: str = "/health"
    voices_path: str = "/v1/voices"
    speech_path: str = "/v1/audio/speech"
    model_field: str = "model"
    input_field: str = "input"
    voice_field: str = "voice"
    speed_field: str = "speed"
    response_format_field: str = "response_format"
    language_field: str | None = None
    model: str = "kokoro-v1.0"
    response_format: str = "wav"


DEFAULT_CONTRACT = TTSContract()
SAMPLE_RATE = 48_000
CHANNELS = 2
SAMPLE_WIDTH = 2
MASTER_FILTER = "highpass=f=70,lowpass=f=15000,loudnorm=I=-16:TP=-1.5:LRA=9"


@dataclass(frozen=True)
class SegmentResult:
    path: Path
    duration: float
    sha256: str
    sample_rate: int
    channels: int
    voice: str
    speed: float
    attempts: int


@dataclass(frozen=True)
class SegmentWindow:
    cue_index: int
    start_ms: int
    end_ms: int
    speech_start_ms: int
    speech_end_ms: int

    @property
    def max_duration(self) -> float:
        return (self.speech_end_ms - self.speech_start_ms) / 1000.0


def validate_loopback_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower()
        port = parsed.port
    except ValueError as exc:
        raise LocalTTSError("TTS URL is invalid") from exc
    is_loopback = host == "localhost" or host in {"127.0.0.1", "::1"}
    if (
        parsed.scheme.lower() != "http"
        or not is_loopback
        or port is None
        or not 1 <= port <= 65535
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise LocalTTSError("TTS URL must be plain HTTP on localhost, 127.0.0.1, or ::1 with an explicit port")
    authority_host = f"[{host}]" if ":" in host else host
    return f"http://{authority_host}:{port}"


def _wav_metadata(data: bytes) -> tuple[float, int, int]:
    if len(data) < 44 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise LocalTTSError("Local TTS returned an invalid or empty WAV file")
    try:
        with wave.open(io.BytesIO(data), "rb") as wav_file:
            frames = wav_file.getnframes()
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            if frames <= 0 or sample_rate <= 0 or channels <= 0 or wav_file.getsampwidth() <= 0:
                raise LocalTTSError("Local TTS returned an invalid or empty WAV file")
            duration = frames / sample_rate
    except (wave.Error, EOFError) as exc:
        raise LocalTTSError("Local TTS returned an unparseable WAV file") from exc
    return duration, sample_rate, channels


def _approved_path(path: Path, approved_dirs: Iterable[Path]) -> Path:
    resolved = path.expanduser().resolve()
    for directory in approved_dirs:
        root = Path(directory).expanduser().resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        return resolved
    raise LocalTTSError("Output path is outside approved temporary or submission directories")


class LocalDockerTTS:
    def __init__(
        self,
        base_url: str,
        *,
        approved_output_dirs: Iterable[Path],
        timeout_seconds: float = 15.0,
        retries: int = 2,
        contract: TTSContract = DEFAULT_CONTRACT,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = validate_loopback_url(base_url)
        self.approved_output_dirs = tuple(Path(path) for path in approved_output_dirs)
        if not self.approved_output_dirs:
            raise LocalTTSError("At least one approved output directory is required")
        if not 0 < timeout_seconds <= 30:
            raise LocalTTSError("TTS timeout must be greater than 0 and at most 30 seconds")
        if not 0 <= retries <= 3:
            raise LocalTTSError("TTS retries must be between 0 and 3")
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.contract = contract
        self._client = httpx.Client(transport=transport, timeout=timeout_seconds, follow_redirects=False)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> LocalDockerTTS:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def health_check(self) -> dict[str, Any]:
        try:
            response = self._client.get(self._url(self.contract.health_path))
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LocalTTSError("Local TTS health check failed") from exc
        return {"status": "ok", "http_status": response.status_code}

    def discover_voices(self) -> list[str]:
        try:
            response = self._client.get(self._url(self.contract.voices_path))
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise LocalTTSError("Local TTS voice discovery failed") from exc
        entries = payload.get("voices", payload.get("data", [])) if isinstance(payload, dict) else payload
        if not isinstance(entries, list):
            raise LocalTTSError("Local TTS voice discovery returned an invalid response")
        names = []
        for entry in entries:
            name = entry if isinstance(entry, str) else entry.get("voice_id", entry.get("id", entry.get("name", entry.get("voice")))) if isinstance(entry, dict) else None
            if isinstance(name, str) and name:
                names.append(name)
        return names

    def synthesize_segment(
        self,
        *,
        text: str,
        output_path: Path,
        voice: str = "bf_emma",
        speed: float = 0.95,
        language: str = "b",
    ) -> SegmentResult:
        if not text.strip():
            raise LocalTTSError("Narration segment text must not be empty")
        if not 0.90 <= speed <= 1.05:
            raise LocalTTSError("TTS speed must be between 0.90 and 1.05")
        if not voice or not language:
            raise LocalTTSError("Voice and language must be specified")
        path = _approved_path(Path(output_path), self.approved_output_dirs)
        if path.exists():
            raise LocalTTSError("TTS output already exists; refusing to overwrite")
        payload = {
            self.contract.model_field: self.contract.model,
            self.contract.input_field: text,
            self.contract.voice_field: voice,
            self.contract.speed_field: speed,
            self.contract.response_format_field: self.contract.response_format,
        }
        if self.contract.language_field is not None:
            payload[self.contract.language_field] = language
        response: httpx.Response | None = None
        attempts = 0
        for attempts in range(1, self.retries + 2):
            try:
                response = self._client.post(self._url(self.contract.speech_path), json=payload)
                if response.status_code >= 500 and attempts <= self.retries:
                    continue
                response.raise_for_status()
                break
            except httpx.HTTPError as exc:
                if attempts > self.retries:
                    raise LocalTTSError("Local TTS synthesis request failed") from exc
        if response is None:
            raise LocalTTSError("Local TTS service did not return a response")
        content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if content_type not in {"audio/wav", "audio/x-wav", "audio/wave", "application/wav"}:
            raise LocalTTSError("Local TTS returned an unexpected Content-Type")
        data = response.content
        duration, sample_rate, channels = _wav_metadata(data)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("xb") as output:
                output.write(data)
        except FileExistsError as exc:
            raise LocalTTSError("TTS output already exists; refusing to overwrite") from exc
        return SegmentResult(
            path=path,
            duration=duration,
            sha256=hashlib.sha256(data).hexdigest(),
            sample_rate=sample_rate,
            channels=channels,
            voice=voice,
            speed=speed,
            attempts=attempts,
        )


def cue_text(cue: Any) -> str:
    lines = getattr(cue, "lines", None)
    if lines is not None:
        return " ".join(lines)
    text = getattr(cue, "text", None)
    if isinstance(text, str):
        return text
    raise LocalTTSError("Caption cue has no readable text")


def plan_segment_window(cue: Any, *, lead_in_ms: int = 100, trailing_ms: int = 100) -> SegmentWindow:
    if not 50 <= lead_in_ms <= 150:
        raise LocalTTSError("Narration lead-in must be between 50 and 150 ms")
    start_ms, end_ms = int(cue.start_ms), int(cue.end_ms)
    window = SegmentWindow(
        cue_index=int(cue.index),
        start_ms=start_ms,
        end_ms=end_ms,
        speech_start_ms=start_ms + lead_in_ms,
        speech_end_ms=end_ms - trailing_ms,
    )
    if window.speech_end_ms <= window.speech_start_ms:
        raise LocalTTSError(f"Caption segment {window.cue_index} has no usable speech window")
    return window


def _probe_wav(path: Path) -> tuple[int, int, int, bytes]:
    try:
        with wave.open(str(path), "rb") as wav_file:
            channels, sample_width, sample_rate = wav_file.getnchannels(), wav_file.getsampwidth(), wav_file.getframerate()
            frames = wav_file.getnframes()
            pcm = wav_file.readframes(frames)
    except (wave.Error, EOFError) as exc:
        raise LocalTTSError("Mastered narration segment is not a valid WAV file") from exc
    if frames <= 0 or sample_width != SAMPLE_WIDTH or sample_rate != SAMPLE_RATE or channels != CHANNELS:
        raise LocalTTSError("Mastered narration segment has an unexpected audio format")
    return frames, sample_rate, channels, pcm


def _run_ffmpeg(ffmpeg_bin: str, source: Path, destination: Path) -> None:
    command = [
        ffmpeg_bin,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-i",
        str(source),
        "-af",
        MASTER_FILTER,
        "-ar",
        str(SAMPLE_RATE),
        "-ac",
        str(CHANNELS),
        "-c:a",
        "pcm_s16le",
        "-f",
        "wav",
        "-n",
        str(destination),
    ]
    try:
        subprocess.run(command, capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise LocalTTSError("FFmpeg could not master a narration segment") from exc


def _write_exclusive(path: Path, data: bytes, approved_dirs: Iterable[Path]) -> Path:
    target = _approved_path(path, approved_dirs)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("xb") as output:
            output.write(data)
    except FileExistsError as exc:
        raise LocalTTSError(f"Output already exists; refusing to overwrite: {target.name}") from exc
    return target


def synthesize_timeline(
    *,
    adapter: LocalDockerTTS,
    cues: list[Any],
    total_duration_seconds: float,
    output_path: Path,
    manifest_path: Path,
    ffmpeg_bin: str = "ffmpeg",
    voice: str = "bf_emma",
    speed: float = 0.95,
    language: str = "b",
) -> dict[str, Any]:
    if total_duration_seconds <= 0:
        raise LocalTTSError("Timeline duration must be positive")
    if not 0.90 <= speed <= 1.05:
        raise LocalTTSError("TTS speed must be between 0.90 and 1.05")
    allowed = adapter.approved_output_dirs
    final_path = _approved_path(Path(output_path), allowed)
    final_manifest = _approved_path(Path(manifest_path), allowed)
    if final_path.exists() or final_manifest.exists():
        raise LocalTTSError("Narration output or manifest already exists; refusing to overwrite")
    total_frames = round(total_duration_seconds * SAMPLE_RATE)
    timeline = bytearray(total_frames * CHANNELS * SAMPLE_WIDTH)
    previous_cue_end = 0
    manifest_segments: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="matchpulse-local-tts-") as work_dir:
        work = Path(work_dir)
        for cue in cues:
            window = plan_segment_window(cue)
            text = cue_text(cue)
            if window.start_ms < previous_cue_end:
                raise LocalTTSError(f"Caption segment {window.cue_index} overlaps the previous cue")
            previous_cue_end = window.end_ms
            cue_end_frame = round(window.speech_end_ms * SAMPLE_RATE / 1000)
            cue_start_frame = round(window.speech_start_ms * SAMPLE_RATE / 1000)
            if cue_end_frame > total_frames:
                raise LocalTTSError(f"Caption segment {window.cue_index} exceeds the {total_duration_seconds:g}-second timeline")
            attempt_speed = speed
            total_attempts = 0
            result: SegmentResult | None = None
            mastered_path: Path | None = None
            for retry in range(4):
                raw_path = work / f"cue-{window.cue_index}-try-{retry + 1}.wav"
                result = adapter.synthesize_segment(
                    text=text,
                    output_path=raw_path,
                    voice=voice,
                    speed=attempt_speed,
                    language=language,
                )
                total_attempts += result.attempts
                mastered_path = work / f"cue-{window.cue_index}-mastered-{retry + 1}.wav"
                _run_ffmpeg(ffmpeg_bin, raw_path, mastered_path)
                frames, _, _, pcm = _probe_wav(mastered_path)
                duration = frames / SAMPLE_RATE
                if duration <= window.max_duration:
                    break
                if retry >= 3 or attempt_speed >= 1.05:
                    raise LocalTTSError(
                        f"Caption segment {window.cue_index} exceeds its speech window at speed {attempt_speed:.2f}; shorten its wording"
                    )
                attempt_speed = min(1.05, max(attempt_speed + 0.01, attempt_speed * duration / window.max_duration))
                attempt_speed = round(attempt_speed, 4)
            assert result is not None and mastered_path is not None
            frames, _, _, pcm = _probe_wav(mastered_path)
            if frames > cue_end_frame - cue_start_frame:
                raise LocalTTSError(f"Caption segment {window.cue_index} overlaps its cue end; shorten its wording")
            byte_start = cue_start_frame * CHANNELS * SAMPLE_WIDTH
            byte_end = byte_start + len(pcm)
            timeline[byte_start:byte_end] = pcm
            manifest_segments.append(
                {
                    "cue_index": window.cue_index,
                    "start_ms": window.start_ms,
                    "end_ms": window.end_ms,
                    "speech_start_ms": window.speech_start_ms,
                    "speech_end_ms": window.speech_end_ms,
                    "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    "voice": voice,
                    "speed": attempt_speed,
                    "duration": round(frames / SAMPLE_RATE, 6),
                    "sha256": hashlib.sha256(pcm).hexdigest(),
                    "attempts": total_attempts,
                }
            )
        assembled = work / "timeline.wav"
        with wave.open(str(assembled), "wb") as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(SAMPLE_WIDTH)
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(timeline)
        timeline_bytes = assembled.read_bytes()
        manifest = {
            "format": "wav",
            "sample_rate": SAMPLE_RATE,
            "channels": CHANNELS,
            "duration_seconds": total_duration_seconds,
            "segments": manifest_segments,
        }
        manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
        _write_exclusive(final_path, timeline_bytes, allowed)
        try:
            _write_exclusive(final_manifest, manifest_bytes, allowed)
        except Exception:
            final_path.unlink(missing_ok=True)
            raise
    return manifest


def estimated_cue_duration(text: str) -> float:
    words = len(text.split())
    return max(0.25, words / 2.8)
