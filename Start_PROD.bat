@echo off
chcp 65001 >nul
echo ==========================================
echo  DIGITAL CROWN - PRODUCTION
echo ==========================================
echo.

set ROOT=%~dp0
set BACKEND_PORT=8000
set FRONTEND_PORT=5173
set CERT_FILE=%ROOT%certs\cert.pem
set KEY_FILE=%ROOT%certs\key.pem

set BACKEND_SSL=
set FRONTEND_HTTPS=
set BACKEND_SCHEME=http
set FRONTEND_SCHEME=http

if exist "%CERT_FILE%" if exist "%KEY_FILE%" (
  set BACKEND_SSL=--ssl-certfile "%CERT_FILE%" --ssl-keyfile "%KEY_FILE%"
  set FRONTEND_HTTPS=true
  set BACKEND_SCHEME=https
  set FRONTEND_SCHEME=https
)

:: Backend production
start "Backend PROD - %BACKEND_PORT%" cmd /k "cd /d %ROOT% && venv\Scripts\activate && uvicorn backend.main:app --host 0.0.0.0 --port %BACKEND_PORT% --workers 4 %BACKEND_SSL%"

timeout /t 3 /nobreak >nul

:: Frontend production preview/dev host with optional HTTPS certs
start "Frontend PROD - %FRONTEND_PORT%" cmd /k "cd /d %ROOT%frontend && set VITE_ENABLE_HTTPS=%FRONTEND_HTTPS%&& npm run dev"

echo.
echo Demarrage production en cours...
echo Backend : %BACKEND_SCHEME%://127.0.0.1:%BACKEND_PORT%
echo Frontend: %FRONTEND_SCHEME%://localhost:%FRONTEND_PORT%
if "%FRONTEND_HTTPS%"=="" (
  echo HTTPS non actif: lancez scripts\setup-https.ps1 ou installez vos certificats dans certs\.
) else (
  echo HTTPS actif via certs\cert.pem et certs\key.pem.
)
echo.
pause
