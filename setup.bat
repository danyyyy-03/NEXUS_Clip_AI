@echo off
setlocal
cd /d "%~dp0"
title NEXUS Clip AI - Setup
where py >nul 2>&1
if errorlevel 1 (
 echo ERROR: Python launcher not found. Install Python 3.12 from python.org.
 pause
 exit /b 1
)
py -3.12 --version
if errorlevel 1 (
 echo ERROR: Python 3.12 is required. Install Python 3.12 for Windows.
 pause
 exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
 echo Creating a separate environment for NEXUS Clip AI...
 py -3.12 -m venv .venv
 if errorlevel 1 goto error
)
echo Installing local AI packages. Internet required for first installation...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error
echo.
echo SETUP COMPLETE. Double-click run.bat.
pause
exit /b 0
:error
echo.
echo SETUP FAILED. Send a screenshot of the error above.
pause
exit /b 1
