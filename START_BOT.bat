@echo off
title Uz Tong Hong Ko BIQS Telegram Bot Launcher
chcp 65001 > nul
echo ========================================================
echo   Uz Tong Hong Ko BIQS Telegram Bot & Mini App Launcher
echo ========================================================
echo.
echo Server & Telegram Bot is starting...
echo Press CTRL+C to stop the bot.
echo.
cd /d "%~dp0"
python run.py
pause
