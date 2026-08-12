@echo off
title Уз Тонг Хонг Ко BIQS Telegram Bot
chcp 65001 > nul
echo ========================================================
echo   Запуск Telegram-бота и Mini App «Уз Тонг Хонг Ко»
echo ========================================================
echo.
echo Запуск сервера и Telegram-бота...
echo Для остановки нажмите CTRL+C.
echo.
cd /d "%~dp0"
python run.py
pause
