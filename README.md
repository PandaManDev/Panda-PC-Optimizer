# Panda PC Optimizer 🐼

A lightweight Windows 10/11 desktop app for monitoring CPU, memory and disk usage, viewing processes, and opening useful Windows settings.

## Features
- Live CPU, RAM and system-drive usage
- Top 100 processes with CPU and memory estimates
- Confirm-before-ending selected processes
- Quick links to Startup Apps, Task Manager and Power settings
- Game Mode reduces how often the app refreshes
- Local-only; no telemetry or background services

## Run on Windows
1. Install Python 3 from https://www.python.org/downloads/windows/ (check **Add Python to PATH**).
2. Download this repository as a ZIP and extract it.
3. Double-click `install.bat`.
4. Double-click `run.bat`.

## Build an EXE
Run `build_exe.bat`. The standalone app will be in `dist/Panda PC Optimizer.exe`.

## Important
This app helps you identify resource-heavy processes; it cannot magically reduce CPU use by itself. Ending tasks can lose unsaved work. Do not terminate Windows/system processes. Game Mode only slows this monitor's refresh rate; it does not kill tasks or modify system settings.
