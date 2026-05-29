@echo off
REM MangaRecap Single-File Build Script
REM Creates a single standalone .exe (slower startup, more portable)

echo ==========================================
echo MangaRecap Single-File Build
echo ==========================================

python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

echo Installing dependencies...
pip install -r requirements.txt

echo Building single-file executable...
pyinstaller build_onefile.spec --clean --noconfirm

if errorlevel 1 (
    echo Build FAILED!
    pause
    exit /b 1
)

echo ==========================================
echo Build SUCCESSFUL!
echo Output: dist\MangaRecap.exe
echo ==========================================
pause
