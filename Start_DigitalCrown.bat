@echo off
title Digital Crown - Launch Manager
color 0B

REM ========================================================
REM        DIGITAL CROWN - DEMARRAGE RAPIDE
REM ========================================================
echo.

REM 1. Demarrage du Backend (FastAPI) depuis la racine
echo [1/2] Allumage du Moteur Backend...
start "" cmd /k "title SERVEUR BACKEND && if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat && uvicorn backend.main:app --reload --reload-delay 2 --port 8000"

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