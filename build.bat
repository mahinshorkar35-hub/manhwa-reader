@echo off
REM MangaRecap Build Script for Windows
REM Creates a standalone .exe using PyInstaller

echo ==========================================
echo MangaRecap Build Script
echo ==========================================

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Check/Install PyInstaller
echo Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Build the application
echo ==========================================
echo Building MangaRecap.exe...
echo This may take several minutes...
echo ==========================================

pyinstaller manga_recap.spec --clean --noconfirm

if errorlevel 1 (
    echo ==========================================
    echo Build FAILED!
    echo ==========================================
    pause
    exit /b 1
)

echo ==========================================
echo Build SUCCESSFUL!
echo ==========================================
echo Output: dist\MangaRecap\MangaRecap.exe
echo.
echo To create a single file, check the spec file settings.
echo.
pause
