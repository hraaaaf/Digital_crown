#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Configure HTTPS local pour le runtime cabinet immuable Digital Crown.
    Le hostname mDNS digitalcrown.local reste stable même si l'adresse DHCP change.
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

# 3. Détecter l'IP LAN sur l'interface réellement routée vers le réseau local.
# Préférer l'interface avec passerelle par défaut évite de sélectionner une IPv4 WSL/VPN/Hyper-V.
$lanConfig = Get-NetIPConfiguration |
    Where-Object { $_.IPv4DefaultGateway -and $_.IPv4Address } |
    Select-Object -First 1
$lanIP = if ($lanConfig) { $lanConfig.IPv4Address.IPAddress } else { $null }

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
Write-Host "  1. Envoyer ce certificat racine à l'iPhone :"
Write-Host "     $caRoot\rootCA.pem" -ForegroundColor Cyan
Write-Host ""
Write-Host "  2. Sur iPhone : Réglages > Général > VPN et gestion de l'appareil"
Write-Host "     > Installer le profil/certificat"
Write-Host ""
Write-Host "  3. Sur iPhone : Réglages > Général > Informations"
Write-Host "     > Réglages de confiance des certificats"
Write-Host "     > Activer la confiance pour la CA mkcert"
Write-Host ""
Write-Host "  4. Relancer le runtime cabinet immuable puis re-scanner le QR Code"
Write-Host ""
Write-Host "  Accès mobile stable : https://digitalcrown.local:8005" -ForegroundColor Green
Write-Host "  Diagnostic IP TLS   : https://$($lanIP):8005" -ForegroundColor DarkGray
Write-Host ""
Write-Host "IMPORTANT : ne pas utiliser Start_DigitalCrown.bat pour le cabinet réel." -ForegroundColor Yellow
Write-Host "Relancez via backend\scripts\run_real_backend.ps1 avec une release immuable." -ForegroundColor Green
