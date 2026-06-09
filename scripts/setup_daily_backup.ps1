$Action = New-ScheduledTaskAction -Execute "python" -Argument "$(Get-Location)\backend\scripts\backup_db.py" -WorkingDirectory "$(Get-Location)"
$Trigger = New-ScheduledTaskTrigger -Daily -At 3am

# Enregistre la tâche pour l'utilisateur courant (pas besoin de droits Administrateur)
Register-ScheduledTask -TaskName "DigitalCrown_DailyBackup" -Action $Action -Trigger $Trigger -Description "Sauvegarde chiffree quotidienne de DigitalCrown"

Write-Host "✅ Tâche planifiée 'DigitalCrown_DailyBackup' créée avec succès pour l'utilisateur courant."
Write-Host "La sauvegarde s'exécutera tous les jours à 03:00 du matin."
