"""Optional MP4 export with selectable (soft) subtitles, without re-encoding video."""
from __future__ import annotations

from pathlib import Path
from typing import Callable
import subprocess
import tempfile
import threading
import time

from .subtitles import Caption, allocate_path, srt_text
from .transcribe import Cancelled, VIDEO_EXTENSIONS, validate_media


def ffmpeg_binary() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError, OSError) as exc:
        raise RuntimeError("FFmpeg not available. Run setup.bat again.") from exc


def mp4_command(ffmpeg_exe: str, media: Path, subtitle_file: Path, destination: Path) -> list[str]:
    return [
        ffmpeg_exe, "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
        "-i", str(media), "-i", str(subtitle_file),
        "-map", "0:v:0", "-map", "0:a?", "-map", "1:0",
        "-c:v", "copy", "-c:a", "copy", "-c:s", "mov_text",
        "-metadata:s:s:0", "language=eng", "-movflags", "+faststart",
        str(destination),
    ]


def embed_subtitles(
    media: Path,
    captions: list[Caption],
    output_dir: Path,
    cancelled: threading.Event,
    progress: Callable[[str], None] | None = None,
    executable: str | None = None,
) -> Path:
    """Mux selectable subtitle track into MP4; source remains untouched.

    Deliberately *not* hard-burned captions: viewers can toggle subtitles on/off.
    Some source codecs/containers cannot be stream-copied into MP4; fail safely.
    """
    media = validate_media(media)
    if media.suffix.lower() not in VIDEO_EXTENSIONS:
        raise ValueError("Embedding subtitles requires a video (not audio-only)")
    if not captions:
        raise ValueError("Generate captions before embedding")
    if cancelled.is_set():
        raise Cancelled("MP4 export cancelled")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = allocate_path(output_dir, f"{media.stem}_captioned", ".mp4")
    if destination.resolve() == media.resolve():
        raise ValueError("Output cannot replace original video")
    ffmpeg_exe = executable or ffmpeg_binary()
    notify = progress or (lambda message: None)
    with tempfile.TemporaryDirectory(prefix="nexus_clip_captions_") as workspace:
        subtitle_file = Path(workspace) / "captions.srt"
        subtitle_file.write_text(srt_text(captions), encoding="utf-8-sig", newline="\n")
        command = mp4_command(ffmpeg_exe, media, subtitle_file, destination)
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        notify("Embedding selectable subtitle track into MP4...")
        try:
            process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, creationflags=creationflags)
        except OSError as exc:
            raise RuntimeError(f"Could not start FFmpeg: {exc}") from exc
        try:
            while process.poll() is None:
                if cancelled.is_set():
                    process.terminate()
                    try:
                        process.wait(timeout=4)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    raise Cancelled("MP4 export cancelled")
                time.sleep(0.12)
            _, error = process.communicate()
            if process.returncode != 0:
                details = error.decode("utf-8", errors="replace")[-1500:].strip()
                raise RuntimeError(f"MP4 export failed: {details or 'unsupported media/codec'}")
            if not destination.is_file() or destination.stat().st_size == 0:
                raise RuntimeError("FFmpeg finished without producing a valid file")
            notify("MP4 with selectable subtitles is ready.")
            return destination
        except (Cancelled, RuntimeError):
            if destination.exists():
                destination.unlink()
            raise
