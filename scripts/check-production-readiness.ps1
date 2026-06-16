$ErrorActionPreference = "Stop"

$Root = Split-Path $PSScriptRoot -Parent
$BackendEnv = Join-Path $Root "backend\.env"
$FrontendEnv = Join-Path $Root "frontend\.env"
$CertFile = Join-Path $Root "certs\cert.pem"
$KeyFile = Join-Path $Root "certs\key.pem"

function Read-EnvFile($Path) {
    $values = @{}
    if (-not (Test-Path $Path)) {
        return $values
    }
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            return
        }
        $parts = $line.Split("=", 2)
        $values[$parts[0].Trim()] = $parts[1].Trim()
    }
    return $values
}

function Check($Name, $Ok, $Fix) {
    if ($Ok) {
        Write-Host "[OK]   $Name" -ForegroundColor Green
    } else {
        Write-Host "[MISS] $Name" -ForegroundColor Red
        Write-Host "       $Fix" -ForegroundColor Yellow
        $script:Missing += 1
    }
}

$script:Missing = 0
$Backend = Read-EnvFile $BackendEnv
$Frontend = Read-EnvFile $FrontendEnv

Write-Host ""
Write-Host "Digital Crown - Production readiness" -ForegroundColor Cyan
Write-Host ""

Check "backend/.env present" (Test-Path $BackendEnv) "Copiez backend/.env.example vers backend/.env et renseignez les valeurs."
Check "frontend/.env present" (Test-Path $FrontendEnv) "Copiez frontend/.env.example vers frontend/.env et renseignez les valeurs."
Check "SECRET_KEY fort" ($Backend["SECRET_KEY"] -and $Backend["SECRET_KEY"].Length -ge 32 -and $Backend["SECRET_KEY"] -notlike "CHANGE_ME*") "Generez une cle reelle avec python -c `"import secrets; print(secrets.token_hex(32))`"."
Check "ALLOWED_ORIGINS production" ($Backend["ALLOWED_ORIGINS"] -and $Backend["ALLOWED_ORIGINS"] -notmatch "localhost|127\.0\.0\.1") "Remplacez localhost par le domaine HTTPS de production."
Check "FRONTEND_URL production" ($Backend["FRONTEND_URL"] -and $Backend["FRONTEND_URL"].StartsWith("https://")) "Renseignez FRONTEND_URL=https://votre-domaine."
Check "VITE_API_URL production" ($Frontend["VITE_API_URL"] -and $Frontend["VITE_API_URL"].StartsWith("https://")) "Renseignez VITE_API_URL=https://votre-api-ou-domaine."
Check "Certificat HTTPS" ((Test-Path $CertFile) -and (Test-Path $KeyFile)) "Placez cert.pem et key.pem dans certs/ ou terminez TLS au reverse proxy."
Check "SMTP configure" ($Backend["SMTP_HOST"] -and $Backend["SMTP_FROM_EMAIL"] -and $Backend["SMTP_PASSWORD"] -and $Backend["SMTP_PASSWORD"] -ne "CHANGE_ME") "Configurez SMTP_HOST, SMTP_FROM_EMAIL et SMTP_PASSWORD."
Check "Email admin configure" ($Backend["ADMIN_NOTIFICATION_EMAIL"]) "Renseignez ADMIN_NOTIFICATION_EMAIL pour recevoir les nouvelles inscriptions."
Check "Sentry backend configure" ($Backend["SENTRY_DSN"]) "Renseignez SENTRY_DSN pour les erreurs backend."
Check "Sentry frontend configure" ($Frontend["VITE_SENTRY_DSN"]) "Renseignez VITE_SENTRY_DSN pour les erreurs frontend."

$Task = Get-ScheduledTask -TaskName "DigitalCrown_DailyBackup" -ErrorAction SilentlyContinue
Check "Backup quotidien planifie" ($null -ne $Task) "Lancez scripts\setup_daily_backup.ps1."

Write-Host ""
if ($Missing -eq 0) {
    Write-Host "Readiness OK: aucun point manquant detecte." -ForegroundColor Green
    exit 0
}

Write-Host "$Missing point(s) a corriger avant commercialisation." -ForegroundColor Yellow
exit 1
