@echo off
title Build Panda PC Optimizer EXE
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (py -m pip install pyinstaller psutil) else (python -m pip install pyinstaller psutil)
if errorlevel 1 goto fail
where py >nul 2>nul
if %errorlevel%==0 (py -m PyInstaller --noconfirm --clean --onefile --windowed --name "Panda PC Optimizer" main.py) else (python -m PyInstaller --noconfirm --clean --onefile --windowed --name "Panda PC Optimizer" main.py)
if errorlevel 1 goto fail
echo Built dist\Panda PC Optimizer.exe
pause
exit /b 0
:fail
echo Build failed. Run install.bat and check Python installation.
pause
exit /b 1
