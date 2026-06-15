@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo Wan2GP Resolve AI - DaVinci Resolve Plugin Installer (Windows)
echo ========================================================
echo.

:: 0. Configuration
echo [1/4] Configuration...
set /p "WAN2GP_DIR=Please enter the full path to your Wan2GP installation (e.g., F:\Wan2GPmain): "

:: Strip wrapping quotes if user pasted them
set "WAN2GP_DIR=%WAN2GP_DIR:"=%"

:: Strip trailing backslash if present
if "%WAN2GP_DIR:~-1%"=="\" set "WAN2GP_DIR=%WAN2GP_DIR:~0,-1%"

if not exist "%WAN2GP_DIR%\wgp.py" (
    echo [ERROR] Could not find wgp.py in %WAN2GP_DIR%. 
    echo Please make sure you pointed to the root Wan2GP directory.
    pause
    exit /b 1
)

if not exist "src\orchestrator" mkdir "src\orchestrator"
echo {"wan2gp_dir": "%WAN2GP_DIR:\=\\%"} > src\orchestrator\config.json
echo Configuration saved!
echo.

:: 1. Copy Plugin to DaVinci Resolve Workflow Integrations Directory
set "PLUGINS_DIR=%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Workflow Integration Plugins"
set "RESOLVE_DIR=%PLUGINS_DIR%\com.antigravity.wangp"

echo [2/4] Installing UI Plugin into DaVinci Resolve...
echo Cleaning up old plugin versions...
if exist "%PLUGINS_DIR%\com.antigravity.wangp_backup" (
    rmdir /S /Q "%PLUGINS_DIR%\com.antigravity.wangp_backup" 2>nul
)
if exist "%RESOLVE_DIR%" (
    rmdir /S /Q "%RESOLVE_DIR%" 2>nul
)

timeout /t 1 >nul
mkdir "%RESOLVE_DIR%"
copy /Y "src\resolve_plugin\ui\*.*" "%RESOLVE_DIR%" >nul
echo Configuring paths...
powershell -Command "(Get-Content '%RESOLVE_DIR%\app.js') -replace 'F:\\progetti antigravity\\wan2gp Davinci', '%CD:\=\\%' | Set-Content '%RESOLVE_DIR%\app.js'"

echo Plugin copied successfully.
echo.

:: 2. Set up Python Environment
echo [3/4] Setting up Python Environment for Orchestrator...
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Installing requirements...
call .venv\Scripts\activate.bat
pip install -r src\orchestrator\requirements.txt >nul
echo Python environment ready.
echo.

:: 3. Create Desktop Shortcut
echo [4/4] Creating Desktop Shortcut for background services...
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\Start WanGP Services.lnk"
set "TARGET_PATH=%~dp0start_wangp_services.bat"
set "WORKING_DIR=%~dp0"

powershell -Command "$wshell = New-Object -ComObject WScript.Shell; $s = $wshell.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = '%TARGET_PATH%'; $s.WorkingDirectory = '%WORKING_DIR%'; $s.WindowStyle = 7; $s.Save()"

echo.
echo ========================================================
echo INSTALLATION COMPLETE!
echo.
echo A shortcut "Start Wan2GP Services" has been placed on your Desktop.
echo Double-click it before opening DaVinci Resolve to start the AI Orchestrator.
echo ========================================================
pause
