@echo off
cd /d "%~dp0"
echo Starting Wan2GP Native Web UI...

:: Find Wan2GP Directory
set WAN2GP_DIR=
for /f "delims=" %%A in ('.venv\Scripts\python.exe -c "import json, os; print(json.load(open('src/orchestrator/config.json'))['wan2gp_dir']) if os.path.exists('src/orchestrator/config.json') else print('')"') do set WAN2GP_DIR=%%A

if "%WAN2GP_DIR%"=="" (
    echo [ERROR] Wan2GP directory not found in config.json. Please run install_windows.bat again.
    pause
    exit /b 1
)

:: Find Wan2GP Python Executable
set WAN2GP_PYTHON="%WAN2GP_DIR%\venv\Scripts\python.exe"
if not exist %WAN2GP_PYTHON% set WAN2GP_PYTHON="%WAN2GP_DIR%\.venv\Scripts\python.exe"
if not exist %WAN2GP_PYTHON% set WAN2GP_PYTHON="%WAN2GP_DIR%\wan2gp\Scripts\python.exe"
if not exist %WAN2GP_PYTHON% set WAN2GP_PYTHON=python

echo Launching Wan2GP from: %WAN2GP_DIR%
cd /d "%WAN2GP_DIR%"

if "%1"=="--hidden" (
    start /B "Wan2GP Web UI" %WAN2GP_PYTHON% wgp.py
    echo Wan2GP started silently in background!
    exit /b 0
) else (
    start "Wan2GP Web UI" cmd /k "%WAN2GP_PYTHON% wgp.py"
    echo Wan2GP started in a separate window! 
)
echo You can now use the Wan2GP UI inside DaVinci Resolve.
pause
