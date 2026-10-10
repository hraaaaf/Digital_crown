# FAC-03 D3E14 object-scoped SACL calibration, synthetic-only Windows runner.
# Never touches Ilexis, clinical records, Facad, licence, or global audit policy.
param([Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root=$null;$originalAcl=$null;$file=$null;$saclApplied=$false
$restored=$false;$cleanupOk=$false;$readBack=$false;$workerWrite=$false
$preAuditCount=0;$matchedCount=0;$writerCount=0;$otherCount=0
$policyQueryOk=$false;$auditSuccessSetting='undetermined';$outcome='not_attempted';$success=$false
$eventReadError=$false;$securityReadCount=0
$policyChanged=$false
try{
 if($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_OS -cne 'Windows' -or
    -not $env:RUNNER_TEMP -or -not $env:GITHUB_WORKSPACE -or -not $env:GITHUB_RUN_ID){
   throw 'RUNNER_ONLY'
 }
 $ws=[IO.Path]::GetFullPath($env:GITHUB_WORKSPACE).TrimEnd('\')
 $dest=[IO.Path]::GetFullPath($OutputPath)
 if(-not $dest.StartsWith($ws+'\',[StringComparison]::OrdinalIgnoreCase) -or
    [IO.Path]::GetFileName($dest) -cne 'd3e14-audit-calibration.json' -or
    (Test-Path -LiteralPath $dest)){throw 'PUBLIC_BOUNDARY_INVALID'}
 $tmp=[IO.Path]::GetFullPath($env:RUNNER_TEMP).TrimEnd('\')
 $root=Join-Path $tmp ('D3E14-'+[Guid]::NewGuid().ToString('N'))
 [void](New-Item -Path $root -ItemType Directory -ErrorAction Stop)
 $file=Join-Path $root ('synthetic-'+[Guid]::NewGuid().ToString('N')+'.txt')
 $worker=Join-Path $root 'synthetic-worker.ps1'
 [IO.File]::WriteAllText($file,'D3E14_SYNTHETIC_BEFORE')
 [IO.File]::WriteAllText($worker,@'
param([Parameter(Mandatory=$true)][string]$Target)
[IO.File]::WriteAllText($Target, 'D3E14_SYNTHETIC_AFTER')
'@)
 # Read policy ONLY. Never use auditpol /set, /backup, /restore, or /clear.
 # Query by stable subcategory GUID to avoid localized subcategory names.
 try{
   $policyText=@(& auditpol.exe /get /subcategory:'{0cce921d-69ae-11d9-bed3-505054503030}' /r 2>$null)
   $policyQueryOk=($LASTEXITCODE -eq 0 -and $policyText.Count -gt 0)
   if($policyQueryOk){
     try{
       $csv=@($policyText | ConvertFrom-Csv -ErrorAction Stop)
       foreach($row in $csv){
         $rowGuid=([string]$row.'Subcategory GUID').Trim('{} ').ToLowerInvariant()
         if($rowGuid -cne '0cce921d-69ae-11d9-bed3-505054503030'){continue}
         $setting=([string]$row.'Inclusion Setting').Trim()
         if($setting -match '(?i)\bsuccess\b'){
           $auditSuccessSetting='success_configured'
         }elseif($setting -match '(?i)\b(no auditing|failure)\b'){
           $auditSuccessSetting='success_not_configured'
         }
         break
       }
     }catch{$auditSuccessSetting='undetermined'}
   }
 }catch{$policyQueryOk=$false;$auditSuccessSetting='undetermined'}
 # SACL is added only to the synthetic file; original ACL is preserved locally.
 $identity=[Security.Principal.WindowsIdentity]::GetCurrent().User
 $currentSid=$identity.Value
 $originalAcl=Get-Acl -LiteralPath $file -Audit -ErrorAction Stop
 $newAcl=Get-Acl -LiteralPath $file -Audit -ErrorAction Stop
 $rule=[System.Security.AccessControl.FileSystemAuditRule]::new(
     $identity,
     ([System.Security.AccessControl.FileSystemRights]::WriteData -bor
      [System.Security.AccessControl.FileSystemRights]::AppendData),
     [System.Security.AccessControl.AuditFlags]::Success)
 $newAcl.AddAuditRule($rule)
 Set-Acl -LiteralPath $file -AclObject $newAcl -ErrorAction Stop
 $saclApplied=$true
 $effective=Get-Acl -LiteralPath $file -Audit -ErrorAction Stop
 foreach($audit in $effective.Audit){
   try{
     $sid=$audit.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
     if($sid -ceq $currentSid -and
        ([long]$audit.FileSystemRights -band 0x6) -ne 0 -and
        ([int]$audit.AuditFlags -band [int][Security.AccessControl.AuditFlags]::Success) -ne 0){
       $readBack=$true
     }
   }catch{}
 }
 if(-not $readBack){throw 'SACL_NOT_EFFECTIVE'}
 $start=[DateTime]::UtcNow.AddSeconds(-1)
 $exe=(Get-Command pwsh -ErrorAction Stop).Source
 $arguments='-NoLogo -NoProfile -NonInteractive -File "'+$worker+'" -Target "'+$file+'"'
 $child=Start-Process -FilePath $exe -ArgumentList $arguments -Wait -PassThru -ErrorAction Stop
 $workerWrite=($child.ExitCode -eq 0 -and [IO.File]::ReadAllText($file) -ceq 'D3E14_SYNTHETIC_AFTER')
 if(-not $workerWrite){throw 'SYNTHETIC_WORKER_FAILED'}
 Start-Sleep -Milliseconds 500
 $end=[DateTime]::UtcNow.AddSeconds(1)
 $records=@()
 try{
   $records=@(Get-WinEvent -FilterHashtable @{
     LogName='Security';Id=4663;StartTime=$start;EndTime=$end
   } -MaxEvents 10000 -ErrorAction Stop)
   if($records.Count -ge 10000){throw 'EVENT_LIMIT_REACHED'}
   $outcome=if($records.Count -eq 0){'no_matching_events'}else{'records_returned'}
 }catch{
   $id=[string]$_.FullyQualifiedErrorId
   $outcome=if($id -like 'NoMatchingEventsFound*'){'no_matching_events'}else{'query_error'}
   $records=@()
   if($outcome -eq 'query_error'){$eventReadError=$true}
 }
 if($outcome -eq 'records_returned'){
   $securityReadCount=$records.Count
   foreach($r in $records){
     try{
       if($r.Id -ne 4663 -or $r.ProviderName -cne 'Microsoft-Windows-Security-Auditing'){continue}
       [xml]$doc=$r.ToXml()
       $data=@{}
       foreach($node in $doc.Event.EventData.Data){
         $data[[string]$node.Name]=[string]$node.'#text'
       }
       if(-not $data.ContainsKey('ObjectName') -or
          -not ([string]$data.ObjectName).Equals($file,[StringComparison]::OrdinalIgnoreCase) -or
          -not $data.ContainsKey('AccessMask')){continue}
       $mask=[Convert]::ToInt64(([string]$data.AccessMask).Replace('0x',''),16)
       if(($mask -band 0x6) -eq 0){continue}
       $matchedCount++
       $pidValue=[string]$data.ProcessId
       if($pidValue -match '^0x[0-9a-fA-F]+$' -and
          [Convert]::ToInt64($pidValue.Substring(2),16) -eq [long]$child.Id){
          $writerCount++
       }else{$otherCount++}
     }catch{
       $outcome='invalid_event';$eventReadError=$true
       $securityReadCount=0;$matchedCount=0;$writerCount=0;$otherCount=0
       break
     }
   }
 }
 $success=$true
}catch{
 # Never print exception details, file paths, native event XML or PIDs.
 $outcome='probe_error';$success=$false
 $matchedCount=0;$writerCount=0;$otherCount=0
}finally{
 if($saclApplied -and $null -ne $originalAcl -and $null -ne $file -and
    (Test-Path -LiteralPath $file)){
   try{
     Set-Acl -LiteralPath $file -AclObject $originalAcl -ErrorAction Stop
     $restored=$true
   }catch{$restored=$false}
 }
 if($null -ne $root -and (Test-Path -LiteralPath $root)){
   try{Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction Stop}catch{}
 }
 $cleanupOk=($null -ne $root -and -not (Test-Path -LiteralPath $root))
}
if(-not $cleanupOk -or ($saclApplied -and -not $restored)){
 Write-Host 'D3E14_PRIVATE_SYNTHETIC_CLEANUP_FAILED=true'
 exit 2
}
if($matchedCount -gt 5000 -or $writerCount -gt $matchedCount -or
   $writerCount+$otherCount -ne $matchedCount){exit 2}
$result=[ordered]@{
 schema='facad314_d3e14_synthetic_object_sacl_v1'
 source='SYNTHETIC_FILE_OBJECT_AUDIT_ONLY'
 audit_policy_queried=$policyQueryOk
 audit_file_system_success_policy=$auditSuccessSetting
 global_audit_policy_modified=$policyChanged
 object_sacl_applied=$saclApplied
 object_sacl_readback_confirmed=$readBack
 synthetic_child_write_verified=$workerWrite
 security_4663_query_outcome=$outcome
 security_4663_query_error=$eventReadError
 security_records_read_count=[int]$securityReadCount
 matching_synthetic_file_write_access_event_count=[int]$matchedCount
 matching_synthetic_child_pid_access_event_count=[int]$writerCount
 matching_unknown_or_other_pid_access_event_count=[int]$otherCount
 synthetic_sacl_restored=$restored
 private_synthetic_files_deleted=$cleanupOk
 used_global_kernel_etw_capture=$false
 raw_security_event_exported=$false
 private_filename_or_pid_exported=$false
 clinical_or_ilexis_file_touched=$false
 write_completion_proven=$false
 real_ilexis_writer_proven=$false
 shared_app_storage_isolation_verified=$false
 clinical_edit_allowed=$false
 verdict='SYNTHETIC_OBJECT_SCOPED_AUDIT_CALIBRATION_NOT_CLINICAL_CAUSALITY'
}
$result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $dest -Encoding utf8 -ErrorAction Stop
Write-Host "D3E14_AUDIT_POLICY_QUERY_OK=$($policyQueryOk.ToString().ToLowerInvariant())"
Write-Host "D3E14_FILE_SYSTEM_SUCCESS_POLICY=$auditSuccessSetting"
Write-Host "D3E14_SYNTHETIC_SACL_READBACK=$($readBack.ToString().ToLowerInvariant())"
Write-Host "D3E14_SYNTHETIC_CHILD_WRITE_VERIFIED=$($workerWrite.ToString().ToLowerInvariant())"
Write-Host "D3E14_4663_QUERY_OUTCOME=$outcome"
Write-Host "D3E14_SYNTHETIC_MATCHED_WRITE_ACCESS_EVENT_COUNT=$matchedCount"
Write-Host "D3E14_SYNTHETIC_CHILD_PID_MATCH_COUNT=$writerCount"
Write-Host "D3E14_PRIVATE_CLEANUP_OK=$($cleanupOk.ToString().ToLowerInvariant())"
Write-Host 'D3E14_REAL_ILEXIS_WRITER_PROVEN=false'
Write-Host 'SHARED_APP_STORAGE_ISOLATION=UNVERIFIED'
Write-Host 'CLINICAL_EDIT_ALLOWED=false'
