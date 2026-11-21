import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace

from nexus_clip.subtitles import Caption
from nexus_clip.transcribe import (Cancelled, LANGUAGES, MEDIA_EXTENSIONS,
                                    MODEL_CHOICES, model_storage,
                                    transcribe_media, validate_media)


class WhisperStub:
    def __init__(self, parts):
        self.parts = parts
        self.calls = []

    def transcribe(self, path, **kwargs):
        self.calls.append((path, kwargs))
        return iter(self.parts), SimpleNamespace(duration=10.0, language="en")


class TranscriberTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.media = Path(self.temp.name) / "hello.wav"
        self.media.write_bytes(b"fake audio sample")

    def test_validate_media(self):
        self.assertEqual(validate_media(self.media), self.media.resolve())

    def test_missing(self):
        with self.assertRaises(FileNotFoundError):
            validate_media(self.media.with_name("missing.wav"))

    def test_empty_file(self):
        p = Path(self.temp.name) / "empty.wav"
        p.touch()
        with self.assertRaises(ValueError):
            validate_media(p)

    def test_extension(self):
        p = Path(self.temp.name) / "secret.exe"
        p.write_bytes(b"hello")
        with self.assertRaises(ValueError):
            validate_media(p)

    def test_models(self):
        self.assertIn("tiny", MODEL_CHOICES)
        self.assertIn("base", MODEL_CHOICES)
        self.assertIn("small", MODEL_CHOICES)

    def test_languages(self):
        self.assertEqual(LANGUAGES["English"], "en")
        self.assertEqual(LANGUAGES["Romanian"], "ro")
        self.assertIsNone(LANGUAGES["Auto detect"])

    def test_storage_path(self):
        self.assertEqual(model_storage().name, "models")

    def test_media_extensions(self):
        self.assertIn(".mp4", MEDIA_EXTENSIONS)
        self.assertIn(".wav", MEDIA_EXTENSIONS)

    def test_transcribe_stub(self):
        stub = WhisperStub([
            SimpleNamespace(start=0.0, end=1.0, text="  Hello   world  "),
            SimpleNamespace(start=2.0, end=3.2, text="Welcome"),
        ])
        logs = []
        captions, lang, duration = transcribe_media(self.media, "tiny", "en", threading.Event(),
            progress=lambda v, m: logs.append((v, m)), model_factory=lambda *_: stub)
        self.assertEqual(captions, [Caption(0, 1, "Hello world"), Caption(2, 3.2, "Welcome")])
        self.assertEqual(lang, "en")
        self.assertEqual(duration, 10)
        self.assertEqual(logs[-1][0], 1.0)
        self.assertEqual(stub.calls[0][1]["language"], "en")

    def test_empty_and_invalid_segments_skipped(self):
        stub = WhisperStub([
            SimpleNamespace(start=0.0, end=0.0, text="bad"),
            SimpleNamespace(start=1.0, end=2.0, text="  "),
            SimpleNamespace(start=3.0, end=4.0, text="good"),
        ])
        result, _, _ = transcribe_media(self.media, "tiny", None, threading.Event(), model_factory=lambda *_: stub)
        self.assertEqual([c.text for c in result], ["good"])

    def test_invalid_model(self):
        with self.assertRaises(ValueError):
            transcribe_media(self.media, "unknown", None, threading.Event(), model_factory=lambda *_: None)

    def test_invalid_language(self):
        with self.assertRaises(ValueError):
            transcribe_media(self.media, "tiny", "xx", threading.Event(), model_factory=lambda *_: None)

    def test_cancel_before(self):
        event = threading.Event()
        event.set()
        with self.assertRaises(Cancelled):
            transcribe_media(self.media, "tiny", None, event, model_factory=lambda *_: None)

    def test_cancel_on_progress(self):
        event = threading.Event()
        stub = WhisperStub([
            SimpleNamespace(start=0.0, end=1.0, text="hello"),
            SimpleNamespace(start=1.0, end=2.0, text="world"),
        ])
        def progress(pct, message):
            if pct > .03:
                event.set()
        with self.assertRaises(Cancelled):
            transcribe_media(self.media, "tiny", None, event, progress=progress, model_factory=lambda *_: stub)
