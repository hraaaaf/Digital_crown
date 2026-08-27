#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Configure HTTPS local pour DigitalCrown (Vite + FastAPI).
    A relancer si vous changez de réseau WiFi.
#>

$ErrorActionPreference = "Stop"
$ROOT = Split-Path $PSScriptRoot -Parent

Write-Host ""
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "  Digital Crown - Setup HTTPS Local" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# 1. Vérifier mkcert
if (-not (Get-Command mkcert -ErrorAction SilentlyContinue)) {
    Write-Host "[!] mkcert non trouvé. Installation via winget..." -ForegroundColor Yellow
    winget install FiloSottile.mkcert --silent --accept-package-agreements --accept-source-agreements
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
}

# 2. Installer la CA mkcert dans le store Windows
Write-Host "[1/3] Installation de la CA locale mkcert..." -ForegroundColor Green
& mkcert -install

# 3. Détecter l'IP LAN
$lanIP = (Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*" -and $_.PrefixOrigin -ne "WellKnown" } |
    Select-Object -First 1).IPAddress

if (-not $lanIP) {
    Write-Host "[!] Impossible de détecter l'IP LAN. Utilisation de localhost uniquement." -ForegroundColor Yellow
    $lanIP = "localhost"
}

Write-Host "[2/3] IP LAN détectée : $lanIP" -ForegroundColor Green

# 4. Générer le certificat. Le hostname .local reste stable quand le DHCP change l'IP.
$certsDir = Join-Path $ROOT "certs"
New-Item -ItemType Directory -Force -Path $certsDir | Out-Null

Push-Location $certsDir
& mkcert -cert-file cert.pem -key-file key.pem localhost 127.0.0.1 digitalcrown.local $lanIP
Pop-Location

Write-Host "[3/3] Certificats générés dans certs/" -ForegroundColor Green

# 5. Afficher les instructions iPhone
$caRoot = & mkcert -CAROOT
Write-Host ""
Write-Host "=======================================" -ForegroundColor Yellow
Write-Host "  IMPORTANT : Installation sur iPhone" -ForegroundColor Yellow
Write-Host "=======================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Envoyer ce fichier par mail ou AirDrop a l'iPhone :"
Write-Host "     $caRoot\rootCA.pem" -ForegroundColor Cyan
Write-Host ""
Write-Host "  2. Sur iPhone : Reglages > General > VPN et gestion"
Write-Host "     > Installer le profil (rootCA.pem)"
Write-Host ""
Write-Host "  3. Sur iPhone : Reglages > General > A propos"
Write-Host "     > Certificats racines de confiance"
Write-Host "     > Activer 'mkcert ...'"
Write-Host ""
Write-Host "  4. Relancer Digital Crown puis re-scanner le QR Code"
Write-Host ""
Write-Host "  Acces mobile stable : https://digitalcrown.local:5173" -ForegroundColor Green
Write-Host "  IP LAN actuelle     : https://$($lanIP):5173" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Terminé ! Relancez Start_DigitalCrown.bat" -ForegroundColor Green
