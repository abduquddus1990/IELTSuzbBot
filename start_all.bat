@echo off
cd /d "%~dp0"
echo ====================================================================
echo   IELTS ^& CEFR Mock AI — FastAPI Server + Telegram Bot Launcher
echo   Papka: %CD%
echo ====================================================================
echo.
echo [1/2] FastAPI va WebApp serveri ishga tushirilmoqda (http://localhost:8080/webapp)...
start "IELTS-CEFR FastAPI Server" cmd /k "cd /d "%~dp0" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8080"

echo [2/2] Telegram bot lokal ishga tushirilmaydi: production bot Render webhook orqali ishlaydi.
echo       Lokal test uchun alohida test-bot tokeni bilan: python -m app.bot.run_polling

echo.
echo Tayyor! Brauzerda http://localhost:8080/webapp ochilmoqda...
timeout /t 2 >nul
start http://localhost:8080/webapp
