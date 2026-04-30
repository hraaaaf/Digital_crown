# adopt_beads.ps1
# Ce script initialise Beads pour le projet Digital Crown.

$doltPath = "C:\Program Files\Dolt\bin"
if ($env:PATH -notlike "*$doltPath*") {
    $env:PATH += ";$doltPath"
}

Write-Host "--- Initialisation de Beads (Agency Protocol) ---" -ForegroundColor Cyan

# Initialisation de la base de données de tâches (Beads)
if (-not (Test-Path ".beads")) {
    bd init --quiet
    Write-Host "[+] Base Beads initialisée." -ForegroundColor Green
} else {
    Write-Host "[!] Base Beads déjà présente." -ForegroundColor Yellow
}

# Configuration initiale (Optionnel - à adapter selon les besoins)
# bd config set project.name "Digital Crown"

# Création de la première tâche "Molecule" : Intégration Beads
bd add task "Intégration du protocole Agency via Beads" --body "Mise en place de Dolt + Beads pour le suivi des tâches et de la mémoire de l'agent Antigravity." --tag "infrastructure" --tag "agency"

Write-Host "--- Adoption terminée ---" -ForegroundColor Cyan
Write-Host "Utilisez 'bd list' pour voir les tâches."
