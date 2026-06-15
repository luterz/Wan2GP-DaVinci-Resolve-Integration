@echo off
cd /d "%~dp0"
echo Starting Wan2GP Resolve AI Orchestrator and DaVinci Resolve Bridge...

:: Set DaVinci Resolve Python Scripting Environment Variables
set RESOLVE_SCRIPT_API=%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting
set RESOLVE_SCRIPT_LIB=C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll
set PYTHONPATH=%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules;%PYTHONPATH%
set PATH=C:\Program Files\Blackmagic Design\DaVinci Resolve;%PATH%

cd src\orchestrator
start "WanGP Orchestrator API" ..\..\.venv\Scripts\uvicorn.exe main:app --host 127.0.0.1 --port 8000
start "WanGP Job Processor" ..\..\.venv\Scripts\python.exe job_processor.py

echo All services started in separate windows! 
echo You can now open DaVinci Resolve and use the WanGP AI Workflow Integration.
echo (Close the black terminal windows when you want to stop the servers)
pause
