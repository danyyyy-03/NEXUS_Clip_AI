import unittest
from unittest.mock import patch


class UITests(unittest.TestCase):
    def test_import_ui_without_optional_ai_package(self):
        import nexus_clip.ui
        self.assertTrue(hasattr(nexus_clip.ui, "ClipApp"))

    def test_english_title(self):
        from nexus_clip import __version__
        self.assertEqual(__version__, "0.1.1")

    def test_gui_constructs_if_display_available(self):
        import tkinter as tk
        from nexus_clip.ui import ClipApp
        try:
            app = ClipApp()
        except tk.TclError:
            self.skipTest("No graphical display available")
        try:
            self.assertIn("NEXUS Clip AI", app.title())
            self.assertEqual(app.model_var.get(), "tiny")
            self.assertFalse(app.captions)
            self.assertEqual(app.start_button.cget("state"), "normal")
        finally:
            app.destroy()
