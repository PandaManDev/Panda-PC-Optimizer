@echo off
title Panda PC Optimizer Setup
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (py -m pip install -r requirements.txt) else (python -m pip install -r requirements.txt)
if errorlevel 1 (echo Setup failed. Install Python 3 from https://www.python.org/downloads/windows/ and check Add Python to PATH. & pause & exit /b 1)
echo Setup complete. Double-click run.bat to start the app.
pause
