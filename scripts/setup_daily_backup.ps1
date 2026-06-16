$ErrorActionPreference = "Stop"

$Root = Split-Path $PSScriptRoot -Parent
$Python = Join-Path $Root "venv\Scripts\python.exe"
$BackupScript = Join-Path $Root "backend\scripts\backup_db.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

if (-not (Test-Path $BackupScript)) {
    throw "Script de backup introuvable: $BackupScript"
}

$Action = New-ScheduledTaskAction -Execute $Python -Argument "`"$BackupScript`"" -WorkingDirectory $Root
$Trigger = New-ScheduledTaskTrigger -Daily -At 3am
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)

Register-ScheduledTask `
    -TaskName "DigitalCrown_DailyBackup" `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Sauvegarde chiffree quotidienne de DigitalCrown" `
    -Force | Out-Null

Write-Host "Tache planifiee 'DigitalCrown_DailyBackup' creee ou mise a jour."
Write-Host "La sauvegarde s'executera tous les jours a 03:00."
Write-Host "Commande: $Python `"$BackupScript`""
