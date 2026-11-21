@echo off
setlocal
cd /d "%~dp0"
title NEXUS Clip AI - Windows EXE Builder
if not exist ".venv\Scripts\python.exe" (
 echo Run setup.bat first.
 pause
 exit /b 1
)
echo Installing PyInstaller into local environment...
".venv\Scripts\python.exe" -m pip install "pyinstaller>=6,<7"
if errorlevel 1 goto failed
echo Building executable. Speech model downloads on first run, NOT embedded in EXE.
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name NEXUS_Clip_AI --collect-all faster_whisper --collect-all ctranslate2 --collect-all av --collect-all imageio_ffmpeg --collect-all tokenizers --collect-all huggingface_hub app.py
if errorlevel 1 goto failed
echo.
echo EXE GENERATED: dist\NEXUS_Clip_AI.exe
echo Test on Windows before releasing; build has not been verified on clean machines.
pause
exit /b 0
:failed
echo BUILD FAILED. Keep the error and ask for help.
pause
exit /b 1
