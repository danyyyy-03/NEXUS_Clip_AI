"""Tkinter user interface (English) for NEXUS Clip AI."""
from __future__ import annotations

from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .subtitles import Caption, export_text, parse_timecode, srt_text, timecode, transcript_text, vtt_text
from .transcribe import LANGUAGES, MODEL_CHOICES, Cancelled, VIDEO_EXTENSIONS, transcribe_media
from .video import embed_subtitles

BG = "#10121B"
PANEL = "#1A1D2A"
ENTRY = "#23283A"
EDGE = "#303648"
FG = "#F1F2FA"
MUTED = "#9CA5BC"
PURPLE = "#9A70F4"
GREEN = "#74E5B3"


class ClipApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"NEXUS Clip AI  •  v{__version__}")
        self.geometry("1130x730")
        self.minsize(830, 600)
        self.configure(bg=BG)
        self.media: Path | None = None
        self.captions: list[Caption] = []
        self.detected_language: str | None = None
        self.duration = 0.0
        self.jobs: queue.Queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.busy = False

        self.media_var = tk.StringVar(value="No media selected")
        self.output_var = tk.StringVar(value="Select a video/audio file to choose export directory")
        self.model_var = tk.StringVar(value="tiny")
        self.lang_var = tk.StringVar(value="Auto detect")
        self.status_var = tk.StringVar(value="Ready. Choose an audio or video file to begin.")
        self.info_var = tk.StringVar(value="No transcript loaded")
        self.progress_var = tk.DoubleVar(value=0)
        self._init_style()
        self._build()
        self.bind("<Control-o>", lambda e: self._choose_media())
        self.bind("<Control-s>", lambda e: self._export_srt())
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.after(100, self._drain_jobs)

    def _init_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=FG, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Panel.TLabel", background=PANEL, foreground=FG, font=("Segoe UI", 10))
        style.configure("SmallPanel.TLabel", background=PANEL, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Heading.TLabel", background=BG, foreground=FG, font=("Segoe UI Semibold", 23))
        style.configure("Subheading.TLabel", background=PANEL, foreground=PURPLE, font=("Segoe UI Semibold", 10))
        style.configure("TCombobox", foreground=FG, fieldbackground=ENTRY, background=ENTRY, arrowcolor=FG, padding=7)
        style.map("TCombobox", fieldbackground=[("readonly", ENTRY)], foreground=[("readonly", FG)])
        style.configure("TProgressbar", troughcolor=EDGE, background=PURPLE, bordercolor=EDGE, thickness=10)
        style.configure("Treeview", background=PANEL, foreground=FG, fieldbackground=PANEL, rowheight=31, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=ENTRY, foreground=FG, font=("Segoe UI Semibold", 10), padding=9)
        style.map("Treeview", background=[("selected", "#514182")], foreground=[("selected", FG)])
        style.configure("Vertical.TScrollbar", background=ENTRY, troughcolor=BG)

    def _button(self, master, text, command, *, primary=False, width=None):
        color = PURPLE if primary else ENTRY
        fg = "#140C28" if primary else FG
        btn = tk.Button(master, text=text, command=command, width=width, bg=color, fg=fg,
                        activebackground="#B79AF8" if primary else "#353E57",
                        activeforeground=fg, relief="flat", bd=0, cursor="hand2",
                        font=("Segoe UI Semibold", 10), padx=14, pady=10)
        return btn

    def _panel(self, parent, title: str):
        box = tk.Frame(parent, bg=PANEL, highlightbackground=EDGE, highlightthickness=1)
        tk.Label(box, text=title.upper(), bg=PANEL, fg=PURPLE, anchor="w",
                 font=("Segoe UI Semibold", 10)).pack(fill="x", padx=17, pady=(13, 7))
        return box

    def _build(self) -> None:
        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=25, pady=(19, 11))
        tk.Label(head, text="NEXUS", bg=BG, fg=PURPLE, font=("Segoe UI Black", 25)).pack(side="left")
        tk.Label(head, text="  CLIP AI", bg=BG, fg=FG, font=("Segoe UI Semibold", 24)).pack(side="left")
        tk.Label(head, text="OFFLINE SPEECH · WINDOWS · v0.1", bg=BG, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="right", pady=13)
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=23, pady=(0, 10))
        sidebar = tk.Frame(main, bg=BG, width=340)
        sidebar.pack(side="left", fill="y", padx=(0, 15))
        sidebar.pack_propagate(False)
        content = tk.Frame(main, bg=BG)
        content.pack(side="left", fill="both", expand=True)

        source = self._panel(sidebar, "01 / Media source")
        source.pack(fill="x", pady=(0, 12))
        tk.Label(source, textvariable=self.media_var, bg=PANEL, fg=FG, font=("Segoe UI", 9),
                 wraplength=296, justify="left", anchor="w").pack(fill="x", padx=17, pady=(2, 9))
        self.choose_button = self._button(source, "Open video or audio  (Ctrl+O)", self._choose_media, primary=True)
        self.choose_button.pack(fill="x", padx=17, pady=(0, 12))
        tk.Label(source, text="MP4 · MOV · MKV · WEBM · MP3 · WAV and more", bg=PANEL,
                 fg=MUTED, font=("Segoe UI", 8)).pack(fill="x", padx=17, pady=(0, 12))

        settings = self._panel(sidebar, "02 / AI settings")
        settings.pack(fill="x", pady=(0, 12))
        tk.Label(settings, text="Whisper model", bg=PANEL, fg=MUTED, anchor="w").pack(fill="x", padx=17)
        self.model_selector = ttk.Combobox(settings, values=MODEL_CHOICES, textvariable=self.model_var, state="readonly")
        self.model_selector.pack(fill="x", padx=17, pady=(4, 11))
        tk.Label(settings, text="Language", bg=PANEL, fg=MUTED, anchor="w").pack(fill="x", padx=17)
        self.lang_selector = ttk.Combobox(settings, values=list(LANGUAGES), textvariable=self.lang_var, state="readonly")
        self.lang_selector.pack(fill="x", padx=17, pady=(4, 9))
        tk.Label(settings, text="tiny = fastest  |  base = balanced  |  small = slower",
                 bg=PANEL, fg=MUTED, font=("Segoe UI", 8)).pack(fill="x", padx=17, pady=(0, 13))

        process = self._panel(sidebar, "03 / Transcription")
        process.pack(fill="x", pady=(0, 12))
        self.start_button = self._button(process, "Transcribe locally", self._start_transcribe, primary=True)
        self.start_button.pack(fill="x", padx=17, pady=(0, 7))
        self.cancel_button = self._button(process, "Cancel current task", self._cancel)
        self.cancel_button.pack(fill="x", padx=17, pady=(0, 13))
        self.cancel_button.configure(state="disabled")
        ttk.Progressbar(process, maximum=100, variable=self.progress_var).pack(fill="x", padx=17, pady=(0, 15))

        output = self._panel(sidebar, "04 / Export folder")
        output.pack(fill="x")
        tk.Label(output, textvariable=self.output_var, bg=PANEL, fg=MUTED, wraplength=300,
                 justify="left", anchor="w", font=("Segoe UI", 9)).pack(fill="x", padx=17, pady=(0, 8))
        self.output_button = self._button(output, "Change output folder", self._choose_output)
        self.output_button.pack(fill="x", padx=17, pady=(0, 12))

        tk.Label(content, text="Caption workspace", bg=BG, fg=FG,
                 font=("Segoe UI Semibold", 18)).pack(anchor="w", pady=(2, 2))
        tk.Label(content, text="Review and edit captions before exporting. Double-click any row to edit.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 10))
        preview = tk.Frame(content, bg=PANEL, highlightbackground=EDGE, highlightthickness=1)
        preview.pack(fill="both", expand=True)
        cols = ("start", "end", "text")
        self.tree = ttk.Treeview(preview, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("start", text="START")
        self.tree.heading("end", text="END")
        self.tree.heading("text", text="TRANSCRIPTION / CAPTION")
        self.tree.column("start", width=115, minwidth=95, stretch=False)
        self.tree.column("end", width=115, minwidth=95, stretch=False)
        self.tree.column("text", width=380, stretch=True)
        sb = ttk.Scrollbar(preview, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True, padx=(7, 0), pady=7)
        self.tree.bind("<Double-1>", self._edit_caption)
        tk.Label(content, textvariable=self.info_var, bg=BG, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(9, 9))
        actions = tk.Frame(content, bg=BG)
        actions.pack(fill="x")
        self.export_buttons = []
        for label, command in (("Save SRT", self._export_srt), ("Save VTT", self._export_vtt),
                               ("Save TXT", self._export_txt), ("Embed in MP4", self._start_embed)):
            button = self._button(actions, label, command)
            button.pack(side="left", padx=(0, 8))
            self.export_buttons.append(button)
        tk.Label(content, text="MP4 export adds a selectable subtitle track, not hardcoded/burned-in text.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(9, 0))
        footer = tk.Frame(self, bg=PANEL)
        footer.pack(fill="x")
        tk.Label(footer, textvariable=self.status_var, bg=PANEL, fg=GREEN, anchor="w",
                 font=("Segoe UI", 9)).pack(fill="x", padx=23, pady=9)
        self._update_actions()

    def _choose_media(self) -> None:
        if self.busy:
            return
        selected = filedialog.askopenfilename(
            title="Select media", filetypes=[("Audio and video", "*.mp4 *.mov *.mkv *.webm *.avi *.mp3 *.wav *.m4a *.aac *.ogg *.flac *.wma"), ("All files", "*.*")],
        )
        if not selected:
            return
        from .transcribe import validate_media
        try:
            path = validate_media(Path(selected))
        except (ValueError, OSError) as exc:
            messagebox.showerror("Unsupported media", str(exc))
            return
        self.media = path
        self.media_var.set(path.name)
        self.output_dir = path.parent / "NEXUS_Clip_Exports"
        self.output_var.set(str(self.output_dir))
        self.captions = []
        self.detected_language = None
        self.duration = 0.0
        self.progress_var.set(0)
        self._refresh_rows()
        self.status_var.set("Media ready. Select a model and click Transcribe locally.")
        self._update_actions()

    def _choose_output(self) -> None:
        start = str(getattr(self, "output_dir", Path.home()))
        path = filedialog.askdirectory(initialdir=start, title="Choose folder for exports")
        if path:
            self.output_dir = Path(path)
            self.output_var.set(str(self.output_dir))

    def _set_busy(self, state: bool) -> None:
        self.busy = state
        self.choose_button.configure(state="disabled" if state else "normal")
        self.start_button.configure(state="disabled" if state else "normal")
        self.output_button.configure(state="disabled" if state else "normal")
        self.model_selector.configure(state="disabled" if state else "readonly")
        self.lang_selector.configure(state="disabled" if state else "readonly")
        self.cancel_button.configure(state="normal" if state else "disabled")
        self._update_actions()

    def _update_actions(self) -> None:
        has_captions = bool(self.captions) and not self.busy
        for button in self.export_buttons:
            button.configure(state="normal" if has_captions else "disabled")
        if has_captions and self.media and self.media.suffix.lower() not in VIDEO_EXTENSIONS:
            self.export_buttons[-1].configure(state="disabled")

    def _start_transcribe(self) -> None:
        if self.busy:
            return
        if self.media is None:
            messagebox.showinfo("Choose media", "Choose a video or audio file first.")
            return
        if self.captions and not messagebox.askyesno("Replace transcript?", "This will replace your edited captions. Continue?"):
            return
        self.captions = []
        self.detected_language = None
        self.duration = 0.0
        self._refresh_rows()
        self.cancel_event = threading.Event()
        self.progress_var.set(0)
        self.status_var.set("Preparing local speech recognition...")
        self._set_busy(True)
        media = self.media
        model = self.model_var.get()
        language = LANGUAGES[self.lang_var.get()]

        def work():
            try:
                segments, lang, duration = transcribe_media(
                    media, model, language, self.cancel_event,
                    progress=lambda percent, message: self.jobs.put(("progress", percent, message)),
                )
                self.jobs.put(("transcribed", segments, lang, duration))
            except Cancelled as exc:
                self.jobs.put(("cancelled", str(exc)))
            except Exception as exc:
                self.jobs.put(("error", str(exc)))

        threading.Thread(target=work, daemon=True).start()

    def _start_embed(self) -> None:
        if self.busy or self.media is None or not self.captions:
            return
        self.cancel_event = threading.Event()
        self._set_busy(True)
        media = self.media
        captions = list(self.captions)
        directory = self.output_dir
        self.status_var.set("Preparing MP4 with selectable subtitles...")

        def work():
            try:
                result = embed_subtitles(media, captions, directory, self.cancel_event,
                                         progress=lambda msg: self.jobs.put(("status", msg)))
                self.jobs.put(("embedded", result))
            except Cancelled as exc:
                self.jobs.put(("cancelled", str(exc)))
            except Exception as exc:
                self.jobs.put(("error", str(exc)))

        threading.Thread(target=work, daemon=True).start()

    def _cancel(self) -> None:
        self.cancel_event.set()
        self.status_var.set("Cancellation requested. Finishing the current step...")
        self.cancel_button.configure(state="disabled")

    def _drain_jobs(self) -> None:
        try:
            while True:
                item = self.jobs.get_nowait()
                kind = item[0]
                if kind == "progress":
                    _, fraction, message = item
                    self.progress_var.set(round(fraction * 100, 1))
                    self.status_var.set(message)
                elif kind == "status":
                    self.status_var.set(item[1])
                elif kind == "transcribed":
                    _, self.captions, self.detected_language, self.duration = item
                    self._set_busy(False)
                    self.progress_var.set(100)
                    self._refresh_rows()
                    self.status_var.set(f"Ready! {len(self.captions)} captions. Review and export.")
                    if not self.captions:
                        messagebox.showinfo("No speech found", "No speech detected. Try a clearer clip or another model.")
                elif kind == "embedded":
                    self._set_busy(False)
                    self.progress_var.set(100)
                    self.status_var.set(f"MP4 saved: {item[1]}")
                    messagebox.showinfo("MP4 exported", f"Saved video with selectable subtitle track:\n{item[1]}")
                elif kind == "cancelled":
                    self._set_busy(False)
                    self.status_var.set(item[1])
                    self.progress_var.set(0)
                elif kind == "error":
                    self._set_busy(False)
                    self.status_var.set("Error: " + item[1])
                    messagebox.showerror("NEXUS Clip AI", item[1])
        except queue.Empty:
            pass
        self.after(100, self._drain_jobs)

    def _refresh_rows(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for index, caption in enumerate(self.captions):
            self.tree.insert("", "end", iid=str(index), values=(timecode(caption.start, srt=False), timecode(caption.end, srt=False), caption.text))
        self.info_var.set(f"{len(self.captions)} captions  ·  Duration: {self.duration:.1f}s  ·  Detected language: {self.detected_language or '—'}")
        self._update_actions()

    def _edit_caption(self, event=None) -> None:
        if self.busy:
            return
        selection = self.tree.selection()
        if not selection:
            return
        index = int(selection[0])
        caption = self.captions[index]
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit caption #{index + 1}")
        dialog.geometry("510x280")
        dialog.resizable(False, False)
        dialog.configure(bg=PANEL)
        dialog.transient(self)
        dialog.grab_set()
        tk.Label(dialog, text="Edit caption times (HH:MM:SS.mmm) and text", bg=PANEL, fg=FG,
                 font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=20, pady=(16, 10))
        timing = tk.Frame(dialog, bg=PANEL)
        timing.pack(fill="x", padx=20)
        start_entry = tk.Entry(timing, bg=ENTRY, fg=FG, relief="flat", insertbackground=FG, font=("Consolas", 11))
        start_entry.insert(0, timecode(caption.start, srt=False))
        start_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=8)
        end_entry = tk.Entry(timing, bg=ENTRY, fg=FG, relief="flat", insertbackground=FG, font=("Consolas", 11))
        end_entry.insert(0, timecode(caption.end, srt=False))
        end_entry.pack(side="left", fill="x", expand=True, ipady=8)
        text_field = tk.Text(dialog, height=4, wrap="word", bg=ENTRY, fg=FG, insertbackground=FG,
                             relief="flat", padx=9, pady=8, font=("Segoe UI", 10))
        text_field.insert("1.0", caption.text)
        text_field.pack(fill="both", expand=True, padx=20, pady=(12, 9))

        def save():
            try:
                self.captions[index] = Caption(parse_timecode(start_entry.get()), parse_timecode(end_entry.get()),
                                               text_field.get("1.0", "end-1c").strip())
            except ValueError as exc:
                messagebox.showerror("Invalid caption", str(exc), parent=dialog)
                return
            self._refresh_rows()
            dialog.destroy()
            self.status_var.set("Caption edited. Export to save your changes.")

        self._button(dialog, "Save caption", save, primary=True).pack(anchor="e", padx=20, pady=(0, 15))
        dialog.bind("<Escape>", lambda e: dialog.destroy())
        text_field.focus_set()

    def _export(self, suffix: str, content: str) -> None:
        if self.busy or not self.media or not self.captions:
            return
        try:
            destination = export_text(self.output_dir, self.media.stem + "_subtitles" if suffix != ".txt" else self.media.stem + "_transcript", suffix, content)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Export failed", str(exc))
            return
        self.status_var.set(f"Saved {destination.name} to {destination.parent}")
        messagebox.showinfo("Export complete", f"Saved:\n{destination}")

    def _export_srt(self) -> None:
        self._export(".srt", srt_text(self.captions))

    def _export_vtt(self) -> None:
        self._export(".vtt", vtt_text(self.captions))

    def _export_txt(self) -> None:
        self._export(".txt", transcript_text(self.captions))

    def _close(self) -> None:
        if self.busy and not messagebox.askyesno("Exit NEXUS Clip AI?", "A task is running. Request cancellation and exit?"):
            return
        self.cancel_event.set()
        self.destroy()


def main() -> None:
    ClipApp().mainloop()
