@echo off
setlocal
cd /d "%~dp0"
title NEXUS Clip AI
if not exist ".venv\Scripts\python.exe" (
 echo SETUP REQUIRED: Double-click setup.bat first.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" app.py
if errorlevel 1 (
 echo.
 echo NEXUS Clip AI stopped with an error. Send a screenshot of the error.
 pause
)
