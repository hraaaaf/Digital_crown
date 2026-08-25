@echo off
title Digital Crown - Launch Manager
color 0B

REM ========================================================
REM        DIGITAL CROWN - DEMARRAGE RAPIDE
REM ========================================================
echo.

REM M6-D2a : si setup-https.ps1 a créé les certificats, tout le LAN mobile
REM démarre sur le même schéma HTTPS (frontend + API). Sinon on conserve HTTP.
set "DIGITALCROWN_ENABLE_HTTPS=false"
set "VITE_ENABLE_HTTPS=false"
set "DC_SSL_ARGS="
if exist "certs\cert.pem" if exist "certs\key.pem" (
    set "DIGITALCROWN_ENABLE_HTTPS=true"
    set "VITE_ENABLE_HTTPS=true"
    set "DC_SSL_ARGS=--ssl-certfile certs\cert.pem --ssl-keyfile certs\key.pem"
    echo [SECURE] HTTPS LAN active.
) else (
    echo [INFO] HTTPS LAN non configure. Lancez scripts\setup-https.ps1 pour camera/PWA/Push OS.
)

REM 1. Demarrage du Backend (FastAPI) depuis la racine
echo [1/2] Allumage du Moteur Backend...
start "" cmd /k "title SERVEUR BACKEND && if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat && uvicorn backend.main:app --host 0.0.0.0 --reload --reload-delay 2 --port 8005 %DC_SSL_ARGS%"

REM 2. Demarrage du Frontend (React)
echo [2/2] Lancement de l'Interface Utilisateur...
start "" cmd /k "title SERVEUR FRONTEND && cd frontend && npm run dev"

echo.
echo ========================================================
echo   SYSTEME OPERATIONNEL !
echo   Ne fermez pas les deux nouvelles fenetres noires.
echo ========================================================
echo.
pause
