$Action = New-ScheduledTaskAction -Execute "python" -Argument "$(Get-Location)\backend\scripts\backup_db.py" -WorkingDirectory "$(Get-Location)"
$Trigger = New-ScheduledTaskTrigger -Daily -At 3am
$Principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName "DigitalCrown_DailyBackup" -Action $Action -Trigger $Trigger -Principal $Principal -Description "Sauvegarde chiffree quotidienne de DigitalCrown"

Write-Host "✅ Tâche planifiée 'DigitalCrown_DailyBackup' créée avec succès."
Write-Host "La sauvegarde s'exécutera tous les jours à 03:00 du matin."
