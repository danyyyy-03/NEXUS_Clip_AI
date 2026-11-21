import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from nexus_clip.subtitles import Caption
from nexus_clip.transcribe import Cancelled
from nexus_clip.video import embed_subtitles, mp4_command


class VideoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.video = self.root / "sample.mp4"
        self.video.write_bytes(b"fake mp4")
        self.captions = [Caption(0, 1, "hi")]
        self.output = self.root / "exports"

    def test_ffmpeg_command(self):
        command = mp4_command("ffmpeg", self.video, Path("caption.srt"), self.root / "out.mp4")
        self.assertEqual(command[0], "ffmpeg")
        self.assertIn("mov_text", command)
        self.assertIn("-n", command)
        self.assertIn("0:v:0", command)
        self.assertNotIn("shell=True", command)

    def test_audio_cannot_embed(self):
        self.video.rename(self.root / "sample.mp3")
        with self.assertRaises(FileNotFoundError):
            embed_subtitles(self.video, self.captions, self.output, threading.Event(), executable="ffmpeg")
        p = self.root / "new.mp3"
        p.write_bytes(b"audio")
        with self.assertRaises(ValueError):
            embed_subtitles(p, self.captions, self.output, threading.Event(), executable="ffmpeg")

    def test_no_caption(self):
        with self.assertRaises(ValueError):
            embed_subtitles(self.video, [], self.output, threading.Event(), executable="ffmpeg")

    def test_cancel_before_start(self):
        event = threading.Event()
        event.set()
        with self.assertRaises(Cancelled):
            embed_subtitles(self.video, self.captions, self.output, event, executable="ffmpeg")

    def test_invalid_ffmpeg_executable(self):
        with self.assertRaises(RuntimeError):
            embed_subtitles(self.video, self.captions, self.output, threading.Event(), executable="clearly_does_not_exist_nexus_exe_403")

    def test_ffmpeg_error_cleans_partial(self):
        # Reaches actual FFmpeg if installed, and confirms no partial MP4 is retained.
        import shutil
        executable = shutil.which("ffmpeg")
        if not executable:
            self.skipTest("FFmpeg unavailable in test environment")
        with self.assertRaises(RuntimeError):
            embed_subtitles(self.video, self.captions, self.output, threading.Event(), executable=executable)
        self.assertEqual(list(self.output.glob("*.mp4")), [])
