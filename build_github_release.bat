@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo Building GitHub Release for WanGP AI DaVinci
echo ========================================================

set "SOURCE_DIR=%~dp0"
set "RELEASE_DIR=%~dp0github_release"

echo Source: %SOURCE_DIR%
echo Target: %RELEASE_DIR%

if exist "%RELEASE_DIR%" (
    echo Cleaning existing release folder...
    rmdir /S /Q "%RELEASE_DIR%"
)

timeout /t 1 >nul
mkdir "%RELEASE_DIR%"

echo Copying required files...
xcopy "%SOURCE_DIR%install_windows.bat" "%RELEASE_DIR%\" /Y /Q >nul
xcopy "%SOURCE_DIR%install_mac.sh" "%RELEASE_DIR%\" /Y /Q >nul
xcopy "%SOURCE_DIR%start_wangp_services.bat" "%RELEASE_DIR%\" /Y /Q >nul
xcopy "%SOURCE_DIR%start_wangp_services.sh" "%RELEASE_DIR%\" /Y /Q >nul
xcopy "%SOURCE_DIR%requirements.txt" "%RELEASE_DIR%\" /Y /Q >nul
xcopy "%SOURCE_DIR%README.md" "%RELEASE_DIR%\" /Y /Q >nul

echo Copying src folder...
mkdir "%RELEASE_DIR%\src"
xcopy "%SOURCE_DIR%src" "%RELEASE_DIR%\src" /E /I /Y /Q /EXCLUDE:%SOURCE_DIR%exclude.txt >nul

echo Release built successfully at %RELEASE_DIR%
