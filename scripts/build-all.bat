@echo off
chcp 65001 >nul
title CantioDAW Build Pipeline
echo ============================================
echo  CantioDAW Build Pipeline
echo ============================================
echo.

REM ---- Step 1: Install Python deps if needed ----
echo [1/5] Checking Python dependencies...
python -m pip install -e ".[all]" 2>nul || echo   [SKIP] pip install failed, continuing...

REM ---- Step 2: Install TS deps ----
echo [2/5] Installing TypeScript dependencies...
cd /d "%~dp0..\ts-orchestrator"
call npm install --omit=dev
if %errorlevel% neq 0 (
    echo   [WARN] npm install had issues, continuing...
)

REM ---- Step 3: Build TS release (obfuscated exe) ----
echo [3/5] Building TS release (obfuscated ^+ standalone exe)...
call node scripts\build-release.mjs
if %errorlevel% neq 0 (
    echo   [ERROR] TS release build failed!
    pause
    exit /b 1
)

REM ---- Step 4: Bundle Python with PyInstaller ----
echo [4/5] Building Python standalone executable (PyInstaller)...
cd /d "%~dp0.."
REM Check if pyinstaller is available
where pyinstaller >nul 2>nul
if %errorlevel% equ 0 (
    pyinstaller cantiodaw.spec --clean --noconfirm
    if %errorlevel% equ 0 (
        REM Copy Python exe to release folder
        if exist "dist\CantioDAW" (
            mkdir "%~dp0..\release\python" 2>nul
            xcopy /E /I /Y "dist\CantioDAW" "%~dp0..\release\python\"
            echo   Copied Python bundle to release\python\
        )
    ) else (
        echo   [WARN] PyInstaller build failed, continuing with TS-only release...
    )
) else (
    echo   [SKIP] PyInstaller not found. Install with: pip install pyinstaller
)

REM ---- Step 5: Finalize ----
echo [5/5] Finalizing release folder...
cd /d "%~dp0.."
if exist "release" (
    dir /b release\
    echo.
    echo ============================================
    echo  Build complete! Release folder: %~dp0..\release
    echo ============================================
) else (
    echo   [ERROR] Release folder not found!
)

pause
