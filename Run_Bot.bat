@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
    python bot.py
) else (
    py -3 bot.py
)
echo.
pause
