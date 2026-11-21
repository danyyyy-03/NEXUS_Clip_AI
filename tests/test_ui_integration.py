"""GUI workflow smoke test with stubbed speech inference (doesn't download a model)."""
import tempfile
import threading
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from nexus_clip.subtitles import Caption
from nexus_clip.ui import ClipApp


class GUIWorkflowTests(unittest.TestCase):
    def test_choose_transcribe_and_export(self):
        with tempfile.TemporaryDirectory() as folder:
            media = Path(folder) / "my video.mp4"
            media.write_bytes(b"synthetic input")
            try:
                app = ClipApp()
            except tk.TclError:
                self.skipTest("No graphical display available")
            try:
                with patch("nexus_clip.ui.filedialog.askopenfilename", return_value=str(media)):
                    app._choose_media()
                self.assertEqual(app.media, media.resolve())

                def fake_transcriber(path, model, language, stop_event, progress=None):
                    if progress:
                        progress(0.4, "Testing")
                    return ([Caption(0.1, 1.2, "Hello!"), Caption(1.4, 2.1, "NEXUS AI")], "en", 2.2)

                with patch("nexus_clip.ui.transcribe_media", side_effect=fake_transcriber), \
                     patch("nexus_clip.ui.messagebox.showinfo"):
                    app._start_transcribe()
                    deadline = time.monotonic() + 2
                    while app.busy and time.monotonic() < deadline:
                        app.update()
                        time.sleep(.02)
                    self.assertFalse(app.busy)
                    self.assertEqual(len(app.captions), 2)
                    self.assertEqual(len(app.tree.get_children()), 2)
                    app._export_srt()
                    app._export_vtt()
                    app._export_txt()

                self.assertEqual(len(list(app.output_dir.glob("*.srt"))), 1)
                self.assertEqual(len(list(app.output_dir.glob("*.vtt"))), 1)
                self.assertEqual(len(list(app.output_dir.glob("*.txt"))), 1)
                self.assertIn("Hello!", next(app.output_dir.glob("*.srt")).read_text(encoding="utf-8"))
            finally:
                app.destroy()
