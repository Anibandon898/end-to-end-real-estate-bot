@echo off
cd /d C:\Users\HomePC\Projects\end-to-end-real-estate-bot
call .venv\Scripts\activate
start "PropertyPilot Backend" cmd /k "uvicorn backend.main:app --host 127.0.0.1 --port 8000"
timeout /t 2 /nobreak >nul
start "PropertyPilot Frontend" cmd /k "python -m http.server 5500 --directory frontend"
