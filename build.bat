@echo off
setlocal

echo === Whisper Prepis Build Script ===
echo.

REM Activate venv
call .venv\Scripts\activate.bat

REM Confirm PyInstaller is available
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: PyInstaller not found in venv. Install with:
    echo   .venv\Scripts\pip install pyinstaller==6.19.0
    exit /b 1
)

REM Check ffmpeg binaries exist
if not exist bin\ffmpeg.exe (
    echo ERROR: bin\ffmpeg.exe not found.
    echo   Download from https://github.com/BtbN/FFmpeg-Builds/releases
    echo   Extract ffmpeg.exe and ffprobe.exe to bin\
    exit /b 1
)
if not exist bin\ffprobe.exe (
    echo ERROR: bin\ffprobe.exe not found.
    exit /b 1
)

REM Security scan -- fail fast on potential hardcoded secrets
echo Scanning for hardcoded secrets...
findstr /r /s /i "sk-ant- sk-proj- api_key.*=.*['\"]" src\*.py main.py 2>nul
if %errorlevel% equ 0 (
    echo.
    echo WARNING: Potential hardcoded secrets found above. Review before continuing.
    pause
)

REM Remove previous build artifacts
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Running PyInstaller...
pyinstaller whisperai.spec

if errorlevel 1 (
    echo.
    echo BUILD FAILED
    exit /b 1
)

echo.
echo === Build complete: dist\WhisperPrepis\ ===

REM Create release zip
echo Creating release zip...
cd dist
powershell -Command "Compress-Archive -Path 'WhisperPrepis' -DestinationPath 'WhisperPrepis-v1.0-windows.zip' -Force"
cd ..
echo Release zip: dist\WhisperPrepis-v1.0-windows.zip

endlocal
