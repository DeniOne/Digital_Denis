@echo off
setlocal
title Digital Denis Launcher
cd /d "%~dp0"

echo ===================================================
echo   DIGITAL DENIS - DEVELOPMENT LAUNCHER
echo ===================================================

:: 1. BACKEND
echo.
echo [1/3] Checking Backend...
if not exist "backend\.venv" (
    echo    - Creating Python virtual environment...
    python -m venv backend\.venv
)

:: Install deps in isolated shell
echo    - Installing/Checking dependencies...
cmd /c "cd backend && .venv\Scripts\activate && pip install -r requirements.txt > nul"

echo    - Starting Backend Server...
start "DD Backend" /D "%~dp0backend" cmd /k ".venv\Scripts\activate && uvicorn main:app --reload --port 8000"


:: 2. TELEGRAM BOT
echo.
echo [2/3] Checking Telegram Bot...
if not exist "telegram\.venv" (
    echo    - Creating Bot virtual environment...
    python -m venv telegram\.venv
)

echo    - Installing/Checking dependencies...
cmd /c "cd telegram && .venv\Scripts\activate && pip install -r requirements.txt > nul"

echo    - Starting Bot...
start "DD Telegram Bot" /D "%~dp0telegram" cmd /k ".venv\Scripts\activate && python bot.py"


:: 3. FRONTEND
echo.
echo [3/3] Checking Frontend...
cd frontend
if not exist "node_modules" (
    echo    - Installing Node dependencies...
    call npm install
)

echo    - Starting Frontend Server...
:: Using /D path to ensure correct context
start "DD Frontend" /D "%~dp0frontend" cmd /k "npm run dev"

cd ..
echo.
echo ===================================================
echo   ALL SERVICES STARTED!
echo ===================================================
echo   Backend:  http://localhost:8000/docs
echo   Frontend: http://localhost:3000
echo ===================================================
echo.
echo   Press any key to close this launcher...
pause > nul
