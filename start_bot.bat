@echo off
title SchoolGuard Telegram Bot
echo ====================================================
echo   SchoolGuard Telegram Assistant Bot (Polling)
echo ====================================================
cd /d "%~dp0"
py -u -m backend.bot.main
pause
