@echo off
title OUR OCR ENGINE - Local Network Mode
echo ========================================================
echo        OUR OCR ENGINE - LOCAL NETWORK LAUNCHER
echo ========================================================
echo.

:: Detect local IP Address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set LOCAL_IP=%%a
)
:: Trim leading space
set LOCAL_IP=%LOCAL_IP:~1%

echo Local Machine IP Address detected: %LOCAL_IP%
echo.
echo Launching Backend (Port 8000) & Frontend (Port 5173)...
echo.
echo --------------------------------------------------------
echo ACCESS THE APP ON ANY DEVICE CONNECTED TO THE SAME WI-FI:
echo.
echo   👉 App UI:   http://%LOCAL_IP%:5173
echo   👉 API Docs: http://%LOCAL_IP%:8000/docs
echo --------------------------------------------------------
echo.

:: Start Backend in new window
start "OCR Engine Backend (FastAPI)" cmd /k "cd /d "%~dp0" && set PYTHONPATH=%~dp0backend && .\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

:: Start Frontend in new window
start "OCR Engine Frontend (React)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo Both servers started in background windows!
pause
