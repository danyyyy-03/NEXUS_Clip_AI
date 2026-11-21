# NEXUS Clip AI — v0.1.1

**Local Windows video/audio transcription, editable captions, and subtitle exports.**

NEXUS Clip AI is an open-source Python 3.12 desktop application that transcribes video and audio locally using **Faster-Whisper**. No subscription, cloud transcription API, user account, or Ollama service is needed. Installing dependencies and downloading a Whisper model for the first time require internet; after that, transcription can run locally with a cached model.

## Features

- English-language dark-themed Tkinter interface
- Import MP4, MOV, MKV, WebM, AVI, MP3, WAV, M4A, AAC, FLAC, OGG and WMA
- Faster-Whisper CPU `int8` transcription, no dedicated GPU required
- Choose Whisper `tiny`, `base`, or `small`; automatic language detection or manual selection
- Review captions with timestamps; double-click a row to edit text and timing
- Export SRT subtitles, WebVTT subtitles, or a plain text transcript
- Optionally embed *selectable* (soft) subtitles in a new MP4 without re-encoding compatible video streams
- Preserve original files and choose unique output filenames
- Cancel ongoing processing between segments; automated tests included

## Windows installation

**Requirements:** Windows 10/11 64-bit, Python 3.12 64-bit, internet for the first setup and model download.

1. Download the source ZIP or clone this repository.
2. Open the folder containing `setup.bat`, `run.bat`, and `app.py`.
3. Double-click **setup.bat**. This creates a local `.venv` and installs dependencies.
4. Double-click **run.bat**.
5. Click **Open video or audio**, choose a short clip with clear speech, select **tiny**, and click **Transcribe locally**.
6. Correct any transcript mistakes by double-clicking a caption row.
7. Use **Save SRT**, **Save VTT**, **Save TXT**, or **Embed in MP4**.
8. Exports appear in a `NEXUS_Clip_Exports` folder beside the source video by default.

The first use of each Whisper model downloads weights to `%LOCALAPPDATA%\NEXUS_Clip_AI\models`, not into the repository. They can be reused offline.

See [START_HERE_RO.md](START_HERE_RO.md) for Romanian-language instructions.

## Fix in v0.1.1

This version pins `av==17.1.0` to avoid the PyAV 19 / Faster-Whisper `metadata_errors` compatibility failure encountered in v0.1.0.

If updating an existing installation:

```bat
.venv\Scripts\python.exe -m pip install --force-reinstall --no-deps av==17.1.0
```

## Automated tests

```bat
py -3.12 -m unittest discover -s tests -v
```

Or double-click `test.bat`.

Unit tests simulate AI inference rather than downloading a model. Some FFmpeg or GUI integration tests may be skipped when dependencies or graphical display are unavailable. Real transcription was also manually tested with a short clip on Windows.

## Experimental Windows EXE

After testing the normal Python version, double-click `build.bat` to attempt a build using PyInstaller. The result should be `dist\NEXUS_Clip_AI.exe`.

The packaged EXE has **not** been verified on a clean Windows installation. Do not publish an EXE release until you test it. Whisper models remain external downloads.

## Important limitations

- MP4 subtitle embedding creates a **selectable subtitle track**, not captions burned into the video image; TikTok/Reels may not display these automatically.
- Some source codecs cannot be copied into MP4. If embedding fails, export an SRT instead.
- No automatic short-form clip selection, speaker diarization, batch processing, translation or karaoke effects.
- Speech recognition quality varies; always review captions.
- Do not transcribe recordings without appropriate rights or consent.
- Never disables your Windows security protections; unsigned builds may prompt SmartScreen.

## Structure

```text
app.py
nexus_clip/
  __init__.py
  subtitles.py
  transcribe.py
  video.py
  ui.py
tests/
  __init__.py
  test_subtitles.py
  test_transcribe.py
  test_video.py
  test_integration.py
  test_ui.py
  test_ui_integration.py
setup.bat
run.bat
build.bat
test.bat
requirements.txt
START_HERE_RO.md
README.md
LICENSE
.gitignore
```

## License

MIT — see [LICENSE](LICENSE).
