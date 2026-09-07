@echo off
title SchoolGuard Platform Launcher
echo ====================================================
echo   SchoolGuard Attendance & Notification Platform
echo ====================================================
cd /d "%~dp0"

echo [1/3] Starting Backend API on http://localhost:8000 ...
start "SchoolGuard API" cmd /k "py -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [2/3] Starting Telegram Assistant Bot ...
start "SchoolGuard Telegram Bot" cmd /k "py -u -m backend.bot.main"

timeout /t 2 /nobreak >nul

echo [3/3] Starting Frontend Dashboard on http://localhost:5173 ...
start "SchoolGuard Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo All services launched! You can minimize this window.
echo.
