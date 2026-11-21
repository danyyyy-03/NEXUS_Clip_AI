import tempfile
import unittest
from pathlib import Path

from nexus_clip.subtitles import (Caption, allocate_path, clean_stem,
                                  export_text, parse_timecode, srt_text,
                                  timecode, transcript_text, vtt_text)


class SubtitleTests(unittest.TestCase):
    def test_caption_valid(self):
        self.assertEqual(Caption(0, 1, " Hello ").text, " Hello ")

    def test_reject_empty_caption(self):
        with self.assertRaises(ValueError):
            Caption(0, 1, "  ")

    def test_reject_start_negative(self):
        with self.assertRaises(ValueError):
            Caption(-1, 2, "hi")

    def test_reject_end_before_start(self):
        with self.assertRaises(ValueError):
            Caption(2, 1, "hi")

    def test_reject_equal_end(self):
        with self.assertRaises(ValueError):
            Caption(1, 1, "hi")

    def test_reject_infinite(self):
        with self.assertRaises(ValueError):
            Caption(0, float("inf"), "hi")

    def test_reject_nan(self):
        with self.assertRaises(ValueError):
            Caption(float("nan"), 2, "hi")

    def test_srt_time(self):
        self.assertEqual(timecode(62.3456), "00:01:02,346")

    def test_vtt_time(self):
        self.assertEqual(timecode(62.3456, srt=False), "00:01:02.346")

    def test_hours(self):
        self.assertEqual(timecode(3600.003), "01:00:00,003")

    def test_timestamp_rollover(self):
        self.assertEqual(timecode(59.9999), "00:01:00,000")

    def test_negative_timestamp(self):
        with self.assertRaises(ValueError):
            timecode(-.5)

    def test_parse_srt_and_vtt(self):
        self.assertAlmostEqual(parse_timecode("01:02:03.456"), 3723.456)
        self.assertAlmostEqual(parse_timecode("01:02:03,456"), 3723.456)

    def test_parse_bad_timestamp(self):
        for value in ("1:23", "00:70:10.000", "00:00:70.000", "01:02:03.45"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_timecode(value)

    def test_srt_content(self):
        text = srt_text([Caption(0, 1.5, "hi"), Caption(2, 3.5, "bye")])
        self.assertIn("1\n00:00:00,000 --> 00:00:01,500\nhi", text)
        self.assertIn("2\n00:00:02,000 --> 00:00:03,500\nbye", text)

    def test_vtt_content(self):
        self.assertTrue(vtt_text([Caption(0, 1, "Hello")]).startswith("WEBVTT\n\n00:00:00.000 --> 00:00:01.000"))

    def test_transcript_with_time(self):
        self.assertIn("[00:00:05.000] Hello", transcript_text([Caption(5, 6, "Hello")]))

    def test_transcript_without_time(self):
        self.assertEqual(transcript_text([Caption(5, 6, "Hello")], timestamps=False), "Hello\n")

    def test_empty_exports(self):
        self.assertEqual(srt_text([]), "")
        self.assertEqual(vtt_text([]), "WEBVTT\n\n")

    def test_filename_cleaning(self):
        self.assertEqual(clean_stem('File:<>?/\\"*name'), "File_name")

    def test_unique_export(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            a = export_text(p, "video_subtitles", ".srt", "one")
            b = export_text(p, "video_subtitles", ".srt", "two")
            self.assertEqual(a.name, "video_subtitles.srt")
            self.assertEqual(b.name, "video_subtitles (1).srt")
            self.assertEqual(a.read_text(), "one")
            self.assertEqual(b.read_text(), "two")

    def test_export_folder_created(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "deeper"
            result = export_text(destination, "test", ".txt", "ok")
            self.assertTrue(result.exists())

    def test_candidate_skips_existing(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            (p / "a.txt").write_text("original")
            self.assertEqual(allocate_path(p, "a", ".txt").name, "a (1).txt")
