"""Pure subtitle/transcript formatting and safe export helpers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import re


@dataclass(frozen=True)
class Caption:
    start: float
    end: float
    text: str

    def __post_init__(self) -> None:
        if not all(math.isfinite(x) for x in (self.start, self.end)):
            raise ValueError("Caption timestamps must be finite numbers")
        if self.start < 0 or self.end <= self.start:
            raise ValueError("Caption end must be after start (and start >= 0)")
        if not self.text.strip():
            raise ValueError("Caption text cannot be empty")


_VALID_STEM = re.compile(r'[^\w .()-]+', flags=re.UNICODE)


def clean_stem(stem: str) -> str:
    name = _VALID_STEM.sub("_", stem).strip(" ._")
    return name[:90] or "clip"


def timecode(seconds: float, *, srt: bool = True) -> str:
    if not math.isfinite(seconds) or seconds < 0:
        raise ValueError("Seconds must be nonnegative and finite")
    millis = int(round(seconds * 1000))
    hours, remain = divmod(millis, 3_600_000)
    minutes, remain = divmod(remain, 60_000)
    sec, fraction = divmod(remain, 1000)
    return f"{hours:02d}:{minutes:02d}:{sec:02d}{',' if srt else '.'}{fraction:03d}"


def parse_timecode(text: str) -> float:
    match = re.fullmatch(r"\s*(\d+):(\d{2}):(\d{2})[,.](\d{3})\s*", text)
    if not match:
        raise ValueError("Use the format HH:MM:SS.mmm (e.g. 00:00:02.500)")
    h, m, s, ms = map(int, match.groups())
    if m >= 60 or s >= 60:
        raise ValueError("Minutes and seconds must be below 60")
    return h * 3600 + m * 60 + s + ms / 1000


def srt_text(captions: list[Caption]) -> str:
    return "".join(
        f"{i}\n{timecode(c.start)} --> {timecode(c.end)}\n{c.text.strip()}\n\n"
        for i, c in enumerate(captions, 1)
    )


def vtt_text(captions: list[Caption]) -> str:
    return "WEBVTT\n\n" + "".join(
        f"{timecode(c.start, srt=False)} --> {timecode(c.end, srt=False)}\n{c.text.strip()}\n\n"
        for c in captions
    )


def transcript_text(captions: list[Caption], *, timestamps: bool = True) -> str:
    return "\n".join(
        f"[{timecode(c.start, srt=False)}] {c.text.strip()}" if timestamps else c.text.strip()
        for c in captions
    ) + ("\n" if captions else "")


def allocate_path(directory: Path, stem: str, suffix: str) -> Path:
    """Choose a filename, never an existing file. Callers must still use exclusive writes."""
    directory = Path(directory)
    base = clean_stem(stem)
    candidate = directory / f"{base}{suffix}"
    idx = 1
    while candidate.exists():
        candidate = directory / f"{base} ({idx}){suffix}"
        idx += 1
        if idx > 50_000:
            raise RuntimeError("Too many output files with the same name")
    return candidate


def export_text(directory: Path, stem: str, suffix: str, content: str) -> Path:
    """Create output exclusively to avoid overwriting existing work."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for _ in range(5):
        destination = allocate_path(directory, stem, suffix)
        try:
            with destination.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
            return destination
        except FileExistsError:
            continue
    raise FileExistsError("Could not reserve a free output filename")
