# D3E.2: vendor startup, one ephemeral runner, no clinical data or path disclosure.
param(
 [Parameter(Mandatory=$true)][string]$FacadExecutable,
 [Parameter(Mandatory=$true)][string]$DisposableRobert,
 [Parameter(Mandatory=$true)][string]$ProcessCounterScript,
 [Parameter(Mandatory=$true)][string]$ProcessCounterOutput,
 [Parameter(Mandatory=$true)][string]$OutputPath,
 [Parameter(Mandatory=$true)][string]$EventKeysPath,
 [Parameter(Mandatory=$true)][string]$TimelinePath,
 [Parameter(Mandatory=$true)][string]$PreLaunchPath,
 [Parameter(Mandatory=$true)][string]$SessionId
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$guid='{0CCE921D-69AE-11D9-BED3-505054503030}'
$root=$null;$oldAcl=$null;$enabled=$false;$wasEnabled=$null;$proc=$null
$rootPidEventKeys=@{}
$otherPidEventKeys=@{}
$sampledDescendantCount=0
$timelineOut=$null;$preLaunchOut=$null;$preLaunchEntries=$null
$checkpoints=New-Object 'System.Collections.Generic.List[object]'
function HashRelativeName([string]$relative){
  $digest=[Security.Cryptography.SHA256]::Create()
  try{
    $bytes=[Text.Encoding]::UTF8.GetBytes($relative.ToLowerInvariant())
    return [Convert]::ToHexString($digest.ComputeHash($bytes)).ToLowerInvariant()
  }finally{$digest.Dispose()}
}
function Get-PrivateIlexisSizeEntries {
  # Strictly metadata (size only), path identity used ONLY as ephemeral local digest.
  $files=@(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop)
  if($files.Count -gt 5000){throw 'TIMELINE_ENUMERATION_CAP'}
  $entries=@{}
  foreach($file in $files){
    if(($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'TIMELINE_REPARSE_POINT'}
    $relative=$file.FullName.Substring($root.Length).TrimStart('\','/')
    if([string]::IsNullOrWhiteSpace($relative) -or $relative.Contains('..') -or
       $relative.Length -gt 4096){throw 'TIMELINE_INVALID_RELATIVE_IDENTITY'}
    $key=HashRelativeName $relative
    if($entries.ContainsKey($key)){throw 'TIMELINE_DUPLICATE_KEY'}
    $entries[$key]=[long]$file.Length
  }
  return $entries
}
function Capture-PrivateIlexisCheckpoint([string]$stage){
  $entries=Get-PrivateIlexisSizeEntries
  [void]$checkpoints.Add([ordered]@{stage=$stage;entries=$entries})
}
$result=[ordered]@{
 schema='facad314_d3e_root_pid_write_v1'
 source='EPHEMERAL_OFFICIAL_ROBERT_STARTUP_ONLY'
 selected_scope='facad_ilexis_roaming_settings'
 windows_event_id=4663
 selected_scope_existed_before_start=$false
 audit_policy_success_enabled=$false
 scope_sacl_applied=$false
 scope_sacl_restored=$false
 audit_policy_restored=$false
 queried_event_count=0
 scoped_file_write_event_count=0
 facad_root_pid_write_event_count=0
 other_process_pid_write_event_count=0
 process_counter_samples=0
 process_root_alive_during_observation=$false
 complete_descendant_process_coverage=$false
 event_delivery_complete=$false
 configured_patient_data_root_verified=$false
 patient_files_or_settings_content_read=$false
 registry_values_read=$false
 license_content_read=$false
 same_landmark_parity_executed=$false
 shared_app_storage_isolation_verified=$false
 clinical_edit_allowed=$false
 verdict='BLOCKED_AUDIT_NOT_STARTED'
}
try {
 if($SessionId -notmatch '^[A-Za-z0-9_-]{1,128}$'){throw 'BAD_SESSION_ID'}
 if([string]::IsNullOrWhiteSpace($env:RUNNER_TEMP)){throw 'RUNNER_TEMP_REQUIRED'}
 $tempRoot=[IO.Path]::GetFullPath($env:RUNNER_TEMP).TrimEnd('\')
 $eventOut=[IO.Path]::GetFullPath($EventKeysPath)
 if(-not $eventOut.StartsWith($tempRoot+'\', [StringComparison]::OrdinalIgnoreCase) -or
    [IO.Path]::GetFileName($eventOut) -notmatch '^d3e3-event-keys-(cold|warm)\.json$' -or
    (Test-Path -LiteralPath $eventOut)) {throw 'EVENT_MANIFEST_MUST_BE_EPHEMERAL'}
 $timelineOut=[IO.Path]::GetFullPath($TimelinePath)
 if(-not $timelineOut.StartsWith($tempRoot+'\', [StringComparison]::OrdinalIgnoreCase) -or
    [IO.Path]::GetFileName($timelineOut) -cnotmatch '^d3e5-timeline-(cold|warm)\.json$' -or
    (Test-Path -LiteralPath $timelineOut) -or $timelineOut -eq $eventOut){
    throw 'TIMELINE_MANIFEST_MUST_BE_EPHEMERAL'
 }
 $preLaunchOut=[IO.Path]::GetFullPath($PreLaunchPath)
 if(-not $preLaunchOut.StartsWith($tempRoot+'\', [StringComparison]::OrdinalIgnoreCase) -or
    [IO.Path]::GetFileName($preLaunchOut) -cnotmatch '^d3e6-prelaunch-(cold|warm)\.json$' -or
    (Test-Path -LiteralPath $preLaunchOut) -or $preLaunchOut -eq $eventOut -or
    $preLaunchOut -eq $timelineOut){
    throw 'PRELAUNCH_MANIFEST_MUST_BE_EPHEMERAL'
 }
 if($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_OS -cne 'Windows' -or
    [string]::IsNullOrWhiteSpace($env:GITHUB_RUN_ID) -or
    [string]::IsNullOrWhiteSpace($env:APPDATA)) {throw 'RUNNER_ONLY'}
 if([IO.Path]::GetFileName($FacadExecutable) -cne 'Facad.exe' -or
    -not (Test-Path -LiteralPath $FacadExecutable -PathType Leaf)) {throw 'EXE_GUARD'}
 if([IO.Path]::GetFileName($DisposableRobert) -cne 'Robert-2.0.fcd' -or
    -not (Test-Path -LiteralPath $DisposableRobert -PathType Leaf)) {throw 'DEMO_GUARD'}
 $root=[IO.Path]::GetFullPath((Join-Path $env:APPDATA 'Ilexis')).TrimEnd('\')
 if(-not (Test-Path -LiteralPath $root -PathType Container)) {throw 'SCOPE_ABSENT'}
 if($root.Length -lt 4 -or $root[1] -cne ':' -or
    -not $root.EndsWith('\AppData\Roaming\Ilexis',[StringComparison]::OrdinalIgnoreCase)) {throw 'SCOPE_PATH_GUARD'}
 $rootInfo=Get-Item -LiteralPath $root -Force -ErrorAction Stop
 if(($rootInfo.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'SCOPE_REPARSE_POINT'}
 $result.selected_scope_existed_before_start=$true
 $oldAcl=Get-Acl -LiteralPath $root -Audit -ErrorAction Stop
 $saclBefore=$oldAcl.GetSecurityDescriptorSddlForm([Security.AccessControl.AccessControlSections]::Audit)
 $policy=@(& auditpol.exe /get "/subcategory:$guid" /r 2>$null)
 if($LASTEXITCODE -ne 0 -or $policy.Count -lt 2){throw 'POLICY_UNAVAILABLE'}
 $wasEnabled=([string]($policy | Select-Object -Last 1) -match 'Success')
 & auditpol.exe /set "/subcategory:$guid" '/success:enable' >$null 2>$null
 if($LASTEXITCODE -ne 0){throw 'POLICY_ENABLE_FAILED'}
 $enabled=$true;$result.audit_policy_success_enabled=$true
 $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User
 $rights=[Security.AccessControl.FileSystemRights]::WriteData -bor
         [Security.AccessControl.FileSystemRights]::AppendData -bor
         [Security.AccessControl.FileSystemRights]::WriteAttributes -bor
         [Security.AccessControl.FileSystemRights]::Delete
 $inherit=[Security.AccessControl.InheritanceFlags]::ContainerInherit -bor
          [Security.AccessControl.InheritanceFlags]::ObjectInherit
 $ace=[Security.AccessControl.FileSystemAuditRule]::new($sid,$rights,$inherit,
    [Security.AccessControl.PropagationFlags]::None,
    [Security.AccessControl.AuditFlags]::Success)
 $changed=Get-Acl -LiteralPath $root -Audit -ErrorAction Stop
 $changed.AddAuditRule($ace)
 Set-Acl -LiteralPath $root -AclObject $changed -ErrorAction Stop
 $result.scope_sacl_applied=$true
 $start=(Get-Date).AddSeconds(-1)
 # Capture size-only Ilexis snapshot before Facad root PID can exist.
 $preLaunchEntries=Get-PrivateIlexisSizeEntries
 $proc=Start-Process -FilePath $FacadExecutable -ArgumentList ('"'+$DisposableRobert+'"') -WorkingDirectory (Split-Path -Parent $FacadExecutable) -PassThru -ErrorAction Stop
 Capture-PrivateIlexisCheckpoint 'after_launch'
 Start-Sleep -Seconds 3
 if($proc.HasExited){throw 'EARLY_EXIT'}
 & $ProcessCounterScript -TargetPid $proc.Id -DurationSeconds 6 -OutputPath $ProcessCounterOutput
 $counter=Get-Content -LiteralPath $ProcessCounterOutput -Raw | ConvertFrom-Json
 if($counter.schema -cne 'facad314_d3_process_io_v1' -or $counter.sample_count -ne 12 -or
    $counter.path_attribution_available -ne $false -or $counter.clinical_edit_allowed -ne $false) {throw 'COUNTERS_INVALID'}
 if($counter.related_processes_observed -lt 1 -or $counter.related_processes_observed -gt 4001){throw 'UNSAFE_PROCESS_COUNTER'}
 $sampledDescendantCount=[int]$counter.related_processes_observed-1
 $result.process_counter_samples=[int]$counter.sample_count
 Start-Sleep -Seconds 6
 if($proc.HasExited){throw 'EARLY_EXIT_AFTER_OBSERVATION'}
 $result.process_root_alive_during_observation=$true
 Capture-PrivateIlexisCheckpoint 'pre_stop'
 if($proc.HasExited){throw 'EARLY_EXIT_DURING_CHECKPOINT'}
 Stop-Process -Id $proc.Id -Force -ErrorAction Stop
 Start-Sleep -Seconds 3
 Capture-PrivateIlexisCheckpoint 'post_stop'
 # Require full profile-relative Ilexis suffix. Never match bare Ilexis.
 $suffix=$root.Substring(2)
 $records=@(Get-WinEvent -FilterHashtable @{LogName='Security';Id=4663;StartTime=$start} -MaxEvents 4000 -ErrorAction Stop)
 if($records.Count -ge 4000){throw 'AUDIT_CAP'}
 $result.queried_event_count=$records.Count
 foreach($event in $records){
   [xml]$xml=$event.ToXml();$fields=@{}
   foreach($field in $xml.Event.EventData.Data){$fields[[string]$field.Name]=[string]$field.'#text'}
   if($fields['ObjectType'] -cne 'File' -or -not $fields['ObjectName'] -or
      -not $fields['ProcessId'] -or -not $fields['AccessMask']){continue}
   $pathText=[string]$fields['ObjectName']
   $inside=($pathText.EndsWith($suffix,[StringComparison]::OrdinalIgnoreCase) -or
            $pathText.IndexOf($suffix+'\', [StringComparison]::OrdinalIgnoreCase) -ge 0)
   if(-not $inside){continue}
   $mask=[Convert]::ToInt64(($fields['AccessMask'] -replace '^0x',''),16)
   if(($mask -band 0x10106) -eq 0){continue}
   $result.scoped_file_write_event_count++
   $id=[Convert]::ToInt32(($fields['ProcessId'] -replace '^0x',''),16)
   if($id -eq $proc.Id){$result.facad_root_pid_write_event_count++}
   else{$result.other_process_pid_write_event_count++}
   # Local identity only; other PID is NOT automatically a Facad descendant.
   $at=$pathText.IndexOf($suffix+'\', [StringComparison]::OrdinalIgnoreCase)
   if($at -ge 0){
     $relative=$pathText.Substring($at+$suffix.Length+1)
     $tokens=@($relative.Split('\'))
     if($relative -and $relative.Length -le 4096 -and
        -not @($tokens | Where-Object {$_ -eq '..' -or $_ -eq '.'}).Count){
       $key=HashRelativeName $relative
       if($id -eq $proc.Id){$rootPidEventKeys[$key]=$true}
       else{$otherPidEventKeys[$key]=$true}
     }
   }
 }
 $result.verdict=if($result.facad_root_pid_write_event_count -gt 0){
   'POSITIVE_FACAD_ROOT_PID_WRITE_USE_EVENTS_NOT_ISOLATION'
 } else {'BLOCKED_NO_FACAD_ROOT_PID_WRITE_EVENT'}
} catch {
 # Never print exception content, raw Security XML, paths, or PID.
 $result.verdict='BLOCKED_INCOMPLETE_OR_UNAVAILABLE_4663_EVIDENCE'
} finally {
 if($null -ne $proc -and -not $proc.HasExited){
   try{Stop-Process -Id $proc.Id -Force -ErrorAction Stop}catch{$result.verdict='BLOCKED_PROCESS_STOP_FAILED'}
 }
 if($null -ne $oldAcl -and $null -ne $root){
   try{
     Set-Acl -LiteralPath $root -AclObject $oldAcl -ErrorAction Stop
     $readback=Get-Acl -LiteralPath $root -Audit -ErrorAction Stop
     $saclAfter=$readback.GetSecurityDescriptorSddlForm([Security.AccessControl.AccessControlSections]::Audit)
     if($saclBefore -cne $saclAfter){throw 'SACL_RESTORATION_MISMATCH'}
     $result.scope_sacl_restored=$true
   }
   catch{$result.verdict='BLOCKED_SACL_RESTORE_FAILED'}
 }
 if($enabled){
   if($wasEnabled -eq $false){
     try{
       & auditpol.exe /set "/subcategory:$guid" '/success:disable' >$null 2>$null
       if($LASTEXITCODE -ne 0){throw 'RESTORE_FAILED'}
       $policyAfter=@(& auditpol.exe /get "/subcategory:$guid" /r 2>$null)
       if($LASTEXITCODE -ne 0 -or $policyAfter.Count -lt 2 -or
          ([string]($policyAfter | Select-Object -Last 1) -match 'Success')){throw 'POLICY_RESTORATION_MISMATCH'}
       $result.audit_policy_restored=$true
     }catch{$result.verdict='BLOCKED_AUDIT_POLICY_RESTORE_FAILED'}
   }elseif($wasEnabled -eq $true){$result.audit_policy_restored=$true}
   else{$result.verdict='BLOCKED_UNKNOWN_INITIAL_POLICY'}
 }
 if(-not $result.scope_sacl_restored -or -not $result.audit_policy_restored){
   $result.verdict='BLOCKED_RESTORATION_NOT_PROVEN'
 }
 if($result.verdict -ceq 'POSITIVE_FACAD_ROOT_PID_WRITE_USE_EVENTS_NOT_ISOLATION'){
   try{
     $ephemeral=[ordered]@{
       schema='facad314_d3e3_event_ids_v1'
       source='EPHEMERAL_FACAD_ROOT_PID_4663_KEYS_LOCAL_ONLY'
       selected_scope='facad_ilexis_roaming_settings'
       session_id=$SessionId
       root_pid_relative_key_hashes=@($rootPidEventKeys.Keys | Sort-Object)
       other_pid_relative_key_hashes=@($otherPidEventKeys.Keys | Sort-Object)
       observed_descendant_pid_count=$sampledDescendantCount
       clinical_edit_allowed=$false
       shared_app_storage_isolation_verified=$false
       complete_descendant_process_coverage=$false
       event_delivery_complete=$false
     }
     $ephemeral | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $eventOut -Encoding utf8
   }catch{$result.verdict='BLOCKED_EPHEMERAL_EVENT_KEYS_UNAVAILABLE'}
 }
 if($result.verdict -ceq 'POSITIVE_FACAD_ROOT_PID_WRITE_USE_EVENTS_NOT_ISOLATION'){
   if($checkpoints.Count -ne 3 -or [string]::IsNullOrWhiteSpace($timelineOut)){
     $result.verdict='BLOCKED_TIMELINE_CHECKPOINTS_INCOMPLETE'
   }else{
     try{
       $private=[ordered]@{
         schema='facad314_d3e5_timeline_local_v1'
         source='EPHEMERAL_ILEXIS_METADATA_ONLY'
         session_id=$SessionId
         selected_scope='facad_ilexis_roaming_settings'
         checkpoints=@($checkpoints.ToArray())
         shared_app_storage_isolation_verified=$false
         clinical_edit_allowed=$false
       }
       $private | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $timelineOut -Encoding utf8 -ErrorAction Stop
     }catch{$result.verdict='BLOCKED_EPHEMERAL_TIMELINE_UNAVAILABLE'}
   }
 }
 if($result.verdict -ceq 'POSITIVE_FACAD_ROOT_PID_WRITE_USE_EVENTS_NOT_ISOLATION'){
   if($null -eq $preLaunchEntries -or [string]::IsNullOrWhiteSpace($preLaunchOut)){
     $result.verdict='BLOCKED_PRIVATE_PRELAUNCH_CAPTURE_INCOMPLETE'
   }else{
     try{
       $privatePre=[ordered]@{
         schema='facad314_d3e6_prelaunch_local_v1'
         source='EPHEMERAL_ILEXIS_SIZE_ONLY_BEFORE_FACAD_START'
         session_id=$SessionId
         selected_scope='facad_ilexis_roaming_settings'
         capture_stage='immediately_before_start_process'
         entries=$preLaunchEntries
         shared_app_storage_isolation_verified=$false
         clinical_edit_allowed=$false
       }
       $privatePre | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $preLaunchOut -Encoding utf8 -ErrorAction Stop
     }catch{$result.verdict='BLOCKED_EPHEMERAL_PRELAUNCH_UNAVAILABLE'}
   }
 }
 $parent=Split-Path -Parent $OutputPath
 if($parent -and -not (Test-Path -LiteralPath $parent)){
   New-Item -ItemType Directory -Path $parent -Force | Out-Null
 }
 $result | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $OutputPath -Encoding utf8
 Write-Host ('D3E2_ROOT_PID_4663_VERDICT='+$result.verdict)
 Write-Host ('D3E2_SCOPED_WRITE_USE_EVENTS='+$result.scoped_file_write_event_count)
 Write-Host ('D3E2_FACAD_ROOT_PID_WRITE_USE_EVENTS='+$result.facad_root_pid_write_event_count)
 Write-Host ('D3E2_OTHER_PID_WRITE_USE_EVENTS='+$result.other_process_pid_write_event_count)
 Write-Host 'D3E2_DESCENDANT_COVERAGE_COMPLETE=false'
 Write-Host 'D3E2_SHARED_APP_STORAGE_ISOLATION=UNVERIFIED'
 Write-Host 'D3E2_CLINICAL_EDIT_ALLOWED=false'
 Write-Host 'D3E3_ROOT_PID_EVENT_KEY_IDS_UPLOADED=false'
 Write-Host 'D3E4_OTHER_PID_EVENT_KEY_IDS_UPLOADED=false'
 Write-Host ('D3E4_SAMPLED_DESCENDANT_PIDS='+$sampledDescendantCount)
}
if($result.verdict -cne 'POSITIVE_FACAD_ROOT_PID_WRITE_USE_EVENTS_NOT_ISOLATION'){exit 2}
