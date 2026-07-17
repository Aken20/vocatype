@echo off
:: VocaType — One-Click Launcher
:: Starts the Python backend and Tauri frontend together

setlocal

:: ── Paths (relative to this script's location) ──────────
set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%python-backend"
set "FRONTEND_DIR=%PROJECT_DIR%tauri-app"

:: ── Ensure Rust/Cargo is in PATH ───────────────────────
if exist "%USERPROFILE%\.cargo\bin\cargo.exe" (
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
)

echo ========================================
echo   🎙️  VocaType — Starting...
echo ========================================
echo.

:: ── Start Python backend in background ──────────────────
echo [1/2] Starting Python backend...
start "VocaType Backend" /MIN cmd /c "cd /d "%BACKEND_DIR%" && .venv\Scripts\python.exe main.py"
echo        Backend launching on http://127.0.0.1:9877

:: ── Wait for backend to be ready ────────────────────────
echo        Waiting for backend to be ready...
:wait_loop
timeout /t 2 /nobreak >nul
curl -s http://127.0.0.1:9877/api/health >nul 2>&1
if %errorlevel% neq 0 goto wait_loop
echo        Backend is ready!

:: ── Start Tauri frontend ────────────────────────────────
echo.
echo [2/2] Starting Tauri frontend...
cd /d "%FRONTEND_DIR%"
call npm run tauri dev

echo.
echo VocaType closed. Press any key to exit...
pause >nul
