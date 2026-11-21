"""Faster-Whisper adapter. Speech inference runs on the user's computer."""
from __future__ import annotations

from pathlib import Path
from typing import Callable
import os
import threading

from .subtitles import Caption

MODEL_CHOICES = ("tiny", "base", "small")
LANGUAGES = {"Auto detect": None, "English": "en", "Romanian": "ro", "Spanish": "es", "French": "fr", "German": "de", "Italian": "it", "Portuguese": "pt"}
MEDIA_EXTENSIONS = {".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg", ".wma", ".mp4", ".mov", ".mkv", ".webm", ".avi"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}


class Cancelled(Exception):
    """User cancelled work between decoded speech segments."""


def model_storage() -> Path:
    root = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_CACHE_HOME")
    if not root:
        root = str(Path.home() / ".cache")
    return Path(root) / "NEXUS_Clip_AI" / "models"


def validate_media(path: Path) -> Path:
    path = Path(path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Media file not found: {path}")
    if path.suffix.lower() not in MEDIA_EXTENSIONS:
        raise ValueError("Unsupported format. Choose a common audio or video file.")
    if path.stat().st_size == 0:
        raise ValueError("The selected media file is empty.")
    return path.resolve()


def _load_whisper(model_name: str, download_dir: Path):
    # Imported only after clicking Transcribe so the GUI starts even if packages are missing.
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("faster-whisper is missing. Run setup.bat, then run.bat.") from exc
    download_dir.mkdir(parents=True, exist_ok=True)
    return WhisperModel(
        model_name, device="cpu", compute_type="int8", download_root=str(download_dir),
        cpu_threads=min(max(2, os.cpu_count() or 4), 6),
    )


def transcribe_media(
    path: Path,
    model_name: str,
    language: str | None,
    cancelled: threading.Event,
    progress: Callable[[float, str], None] | None = None,
    model_factory: Callable | None = None,
) -> tuple[list[Caption], str | None, float]:
    media = validate_media(path)
    if model_name not in MODEL_CHOICES:
        raise ValueError("Unsupported AI model")
    if language not in LANGUAGES.values():
        raise ValueError("Unsupported language")
    if cancelled.is_set():
        raise Cancelled("Transcription cancelled")
    report = progress or (lambda fraction, message: None)
    report(0, "Loading local speech model (first use may download files)...")
    factory = model_factory or _load_whisper
    model = factory(model_name, model_storage())
    if cancelled.is_set():
        raise Cancelled("Transcription cancelled")
    report(0.02, "Analyzing audio and transcribing locally...")
    raw_segments, info = model.transcribe(
        str(media), language=language, beam_size=3, vad_filter=True,
        condition_on_previous_text=False,
    )
    duration = max(0.0, float(getattr(info, "duration", 0.0) or 0.0))
    recognized = getattr(info, "language", None)
    captions: list[Caption] = []
    for segment in raw_segments:
        if cancelled.is_set():
            raise Cancelled("Transcription cancelled")
        text = " ".join(str(segment.text).split())
        start = max(0.0, float(segment.start))
        end = max(0.0, float(segment.end))
        if text and end > start:
            captions.append(Caption(start, end, text))
        portion = (end / duration) if duration else 0.0
        report(min(0.97, max(0.02, portion)), f"Transcribed {end:.1f}s / {duration:.1f}s")
    if cancelled.is_set():
        raise Cancelled("Transcription cancelled")
    report(1.0, f"Done. {len(captions)} captions generated.")
    return captions, recognized, duration
