"""Real FFmpeg integration test: generated MP4 must contain video + subtitle streams."""
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

from nexus_clip.subtitles import Caption
from nexus_clip.video import embed_subtitles


class IntegrationTests(unittest.TestCase):
    def test_embed_srt_in_real_mp4(self):
        ffmpeg = shutil.which("ffmpeg")
        ffprobe = shutil.which("ffprobe")
        if not ffmpeg or not ffprobe:
            self.skipTest("System ffmpeg/ffprobe not installed in test environment")
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            video = folder / "sample.mp4"
            cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=blue:s=320x240:r=25:d=2",
                   "-f", "lavfi", "-i", "sine=frequency=440:duration=2", "-shortest", "-c:v", "mpeg4", "-c:a", "aac", "-y", str(video)]
            p = subprocess.run(cmd, capture_output=True, text=True)
            if p.returncode != 0:
                self.skipTest("System FFmpeg cannot generate sample media")
            output = embed_subtitles(video, [Caption(0.1, 1.5, "NEXUS Clip AI works")], folder / "out", threading.Event(), executable=ffmpeg)
            self.assertTrue(output.is_file())
            self.assertNotEqual(video.resolve(), output.resolve())
            probe = subprocess.run([ffprobe, "-v", "error", "-show_entries", "stream=codec_type,codec_name", "-of", "csv=p=0", str(output)], capture_output=True, text=True)
            self.assertEqual(probe.returncode, 0)
            self.assertIn("mov_text", probe.stdout)
            self.assertIn("video", probe.stdout)
            self.assertTrue(video.exists())
