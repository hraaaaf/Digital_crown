# FAC-03 D3E9/D3E10/D3E11: independent disposable Windows arms and metadata-only provenance.
# Read metadata only. Never persist file identities/paths/sizes or profile content.
param(
 [Parameter(Mandatory=$true)][ValidateSet('passive_1','passive_2','sacl_1','sacl_2')][string]$Arm,
 [Parameter(Mandatory=$true)][string]$OutputPath
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$guid='{0CCE921D-69AE-11D9-BED3-505054503030}'
$root=$null;$oldAcl=$null;$sddlBefore=$null;$wasEnabled=$null
$policyEnabled=$false;$saclMutated=$false;$policyRestored=$false;$saclRestored=$false
$complete=$false
$counts=@{modified_size_changed=0;created=0;removed=0}
$script:privateTimes=@{}
$preTimes=@{};$postTimes=@{};$eventStart=$null;$eventEnd=$null
$timeCounters=@{size_and_timestamp_changed=0;size_without_timestamp_changed=0;same_size_timestamp_changed=0}
$eventQueryAttempted=$false;$eventQueryAvailable=$false;$eventQueryOutcome='not_attempted'
$matchedOwn=@{};$matchedOther=@{};$matchedAuditWriteUseCount=0
$d3e10Completed=$false
$watcher=$null;$watchRegistered=$false;$watchErrorsRegistered=$false
$watchEventsOk=$false;$watcherStarted=$false;$watcherReportedError=$false
$watchEventCount=0;$watchMatches=@{}
$watchChangedSource='D3E11-Changed-'+$Arm
$watchErrorSource='D3E11-Error-'+$Arm
$script:privatePaths=@{}
$matchedSacl=0;$matchedInheritedSacl=0;$saclChecked=0;$saclFailed=0
$d3e11Completed=$false
function Get-Metadata {
  $files=@(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop)
  if($files.Count -gt 5000){throw 'FILE_CAP'}
  $entries=@{}
  $times=@{}
  $privatePaths=@{}
  foreach($file in $files){
    if(($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'REPARSE_POINT'}
    $relative=$file.FullName.Substring($root.Length).TrimStart('\','/')
    if(-not $relative -or $relative.Length -gt 4096 -or
       @($relative.Split('\') | Where-Object {$_ -eq '.' -or $_ -eq '..'}).Count){
      throw 'INVALID_RELATIVE_ENTRY'
    }
    $digest=[Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($relative.ToLowerInvariant()))
    $key=[Convert]::ToHexString($digest).ToLowerInvariant()
    if($entries.ContainsKey($key)){throw 'DUPLICATE_ENTRY'}
    $entries[$key]=[long]$file.Length
    $times[$key]=[long]$file.LastWriteTimeUtc.Ticks
    $privatePaths[$key]=$file.FullName
  }
  $script:privatePaths=$privatePaths
  $script:privateTimes=$times
  return $entries
}
try{
  if($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_OS -cne 'Windows' -or
     -not $env:GITHUB_RUN_ID -or -not $env:GITHUB_WORKSPACE -or -not $env:APPDATA){
    throw 'RUNNER_ONLY'
  }
  $workspace=[IO.Path]::GetFullPath($env:GITHUB_WORKSPACE).TrimEnd('\')
  $dest=[IO.Path]::GetFullPath($OutputPath)
  if(-not $dest.StartsWith($workspace+'\', [StringComparison]::OrdinalIgnoreCase) -or
     [IO.Path]::GetFileName($dest) -cne "d3e9-arm-$Arm.json" -or
     -not $dest.Contains('\facad-quick-demo\') -or
     (Test-Path -LiteralPath $dest)){throw 'PUBLIC_OUTPUT_GUARD'}
  $root=[IO.Path]::GetFullPath((Join-Path $env:APPDATA 'Ilexis')).TrimEnd('\')
  if(-not $root.EndsWith('\AppData\Roaming\Ilexis',[StringComparison]::OrdinalIgnoreCase) -or
     -not (Test-Path -LiteralPath $root -PathType Container)){throw 'SCOPE_GUARD'}
  $rootInfo=Get-Item -LiteralPath $root -Force -ErrorAction Stop
  if(($rootInfo.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'SCOPE_REPARSE'}
  $oldAcl=Get-Acl -LiteralPath $root -Audit -ErrorAction Stop
  $sddlBefore=$oldAcl.GetSecurityDescriptorSddlForm([Security.AccessControl.AccessControlSections]::Audit)
  $before=Get-Metadata
  # Match audit-policy setup between trial arms; treatment differs ONLY by Set-Acl.
  $policy=@(& auditpol.exe /get "/subcategory:$guid" /r 2>$null)
  if($LASTEXITCODE -ne 0 -or $policy.Count -lt 2){throw 'POLICY_UNAVAILABLE'}
  $wasEnabled=([string]($policy | Select-Object -Last 1) -match 'Success')
  & auditpol.exe /set "/subcategory:$guid" '/success:enable' >$null 2>$null
  if($LASTEXITCODE -ne 0){throw 'POLICY_ENABLE_FAILED'}
  $policyEnabled=$true
  $pre=Get-Metadata
  $preTimes=$script:privateTimes
  # Native Windows change notification is independent of Security event 4663.
  # All paths remain in memory; NEVER output event args or raw paths.
  $watcher=[IO.FileSystemWatcher]::new($root)
  $watcher.IncludeSubdirectories=$true
  $watcher.Filter='*'
  $watcher.NotifyFilter=[IO.NotifyFilters]::Size -bor [IO.NotifyFilters]::LastWrite
  $watcher.InternalBufferSize=16384
  Register-ObjectEvent -InputObject $watcher -EventName Changed -SourceIdentifier $watchChangedSource -ErrorAction Stop | Out-Null
  $watchRegistered=$true
  Register-ObjectEvent -InputObject $watcher -EventName Error -SourceIdentifier $watchErrorSource -ErrorAction Stop | Out-Null
  $watchErrorsRegistered=$true
  $watcher.EnableRaisingEvents=$true
  $watcherStarted=$true
  $eventStart=(Get-Date).AddSeconds(-1)
  if($Arm.StartsWith('sacl_',[StringComparison]::Ordinal)){
    $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User
    $rights=[Security.AccessControl.FileSystemRights]::WriteData -bor
            [Security.AccessControl.FileSystemRights]::AppendData -bor
            [Security.AccessControl.FileSystemRights]::WriteAttributes -bor
            [Security.AccessControl.FileSystemRights]::Delete
    $inherit=[Security.AccessControl.InheritanceFlags]::ContainerInherit -bor
             [Security.AccessControl.InheritanceFlags]::ObjectInherit
    $ace=[Security.AccessControl.FileSystemAuditRule]::new(
      $sid,$rights,$inherit,[Security.AccessControl.PropagationFlags]::None,
      [Security.AccessControl.AuditFlags]::Success)
    $changed=Get-Acl -LiteralPath $root -Audit -ErrorAction Stop
    $changed.AddAuditRule($ace)
    $saclMutated=$true # Even if Set-Acl partially fails, attempt restoration.
    Set-Acl -LiteralPath $root -AclObject $changed -ErrorAction Stop
  }
  # Identical bounded passive wait after the optional SACL mutation, no Facad root process.
  Start-Sleep -Seconds 2
  $post=Get-Metadata
  $postTimes=$script:privateTimes
  $postPaths=$script:privatePaths
  if($watcherStarted){$watcher.EnableRaisingEvents=$false}
  $changeEvents=@(Get-Event -SourceIdentifier $watchChangedSource -ErrorAction SilentlyContinue)
  $errorEvents=@(Get-Event -SourceIdentifier $watchErrorSource -ErrorAction SilentlyContinue)
  $watchEventCount=$changeEvents.Count
  $watcherReportedError=($errorEvents.Count -gt 0 -or $watchEventCount -ge 4000)
  $eventEnd=(Get-Date)
  $changedSizeKeys=@{}
  foreach($key in $pre.Keys){
    if(-not $post.ContainsKey($key)){$counts.removed++}
    elseif($pre[$key] -ne $post[$key]){
      $counts.modified_size_changed++
      $changedSizeKeys[$key]=$true
      if($preTimes[$key] -ne $postTimes[$key]){$timeCounters.size_and_timestamp_changed++}
      else{$timeCounters.size_without_timestamp_changed++}
    }elseif($preTimes[$key] -ne $postTimes[$key]){
      $timeCounters.same_size_timestamp_changed++
    }
  }
  foreach($key in $post.Keys){
    if(-not $pre.ContainsKey($key)){$counts.created++}
  }
  # Match OS notifications to changed-size files without exporting identities.
  if($watcherStarted -and -not $watcherReportedError){
    $prefix=$root+'\'
    foreach($queued in $changeEvents){
      try{
        $candidate=[string]$queued.SourceEventArgs.FullPath
        if(-not $candidate.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){continue}
        $relative=$candidate.Substring($prefix.Length)
        if(-not $relative -or $relative.Length -gt 4096 -or
           @($relative.Split('\') | Where-Object {$_ -eq '.' -or $_ -eq '..'}).Count){continue}
        $hash=[Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($relative.ToLowerInvariant()))
        $key=[Convert]::ToHexString($hash).ToLowerInvariant()
        if($changedSizeKeys.ContainsKey($key)){$watchMatches[$key]=$true}
      }catch{
        $watcherReportedError=$true
        $watchMatches=@{}
        break
      }
    }
  }
  $watchEventsOk=($watcherStarted -and -not $watcherReportedError)
  # Read only SACL metadata for size-changing files; never file content.
  # Count current-runner-SID Success write-audit ACEs, including inheritance.
  $currentSid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
  foreach($key in $changedSizeKeys.Keys){
    if(-not $postPaths.ContainsKey($key)){$saclFailed++;continue}
    try{
      $fileAcl=Get-Acl -LiteralPath $postPaths[$key] -Audit -ErrorAction Stop
      $saclChecked++
      $hasRule=$false;$hasInheritedRule=$false
      foreach($rule in $fileAcl.Audit){
        $ruleSid=$rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
        $rightsBits=[long]$rule.FileSystemRights
        $auditBits=[int]$rule.AuditFlags
        if($ruleSid -ceq $currentSid -and ($rightsBits -band 0x06) -ne 0 -and
           ($auditBits -band [int][Security.AccessControl.AuditFlags]::Success) -ne 0){
          $hasRule=$true
          if($rule.IsInherited){$hasInheritedRule=$true}
        }
      }
      if($hasRule){$matchedSacl++}
      if($hasInheritedRule){$matchedInheritedSacl++}
    }catch{$saclFailed++}
  }
  $d3e11Completed=$true
  # Query Windows Security 4663 only within the bounded prelaunch interval.
  # 4663 records ACCESS USE, not proof that file content changed or who wrote it.
  # We compare temporary relative-file SHA identities entirely in memory.
  $eventQueryAttempted=$true
  try{
    $auditEvents=@(Get-WinEvent -FilterHashtable @{
      LogName='Security';Id=4663;StartTime=$eventStart;EndTime=$eventEnd
    } -MaxEvents 4000 -ErrorAction Stop)
    if($auditEvents.Count -ge 4000){throw 'AUDIT_EVENT_CAP'}
    $eventQueryAvailable=$true
    $eventQueryOutcome='records_returned'
    $rootPrefix=$root+'\'
    foreach($record in $auditEvents){
      try{
        [xml]$xml=$record.ToXml()
        $fields=@{}
        foreach($value in $xml.Event.EventData.Data){
          $fields[[string]$value.Name]=[string]$value.'#text'
        }
        if($fields['ObjectType'] -cne 'File' -or
           -not $fields['ObjectName'] -or -not $fields['ProcessId'] -or
           -not $fields['AccessMask']){continue}
        $fullName=[string]$fields['ObjectName']
        if(-not $fullName.StartsWith($rootPrefix,[StringComparison]::OrdinalIgnoreCase)){continue}
        $relative=$fullName.Substring($rootPrefix.Length)
        if(-not $relative -or $relative.Length -gt 4096 -or
           @($relative.Split('\') | Where-Object {$_ -eq '.' -or $_ -eq '..'}).Count){continue}
        $hash=[Security.Cryptography.SHA256]::HashData(
          [Text.Encoding]::UTF8.GetBytes($relative.ToLowerInvariant()))
        $key=[Convert]::ToHexString($hash).ToLowerInvariant()
        if(-not $changedSizeKeys.ContainsKey($key)){continue}
        # File WriteData/AppendData access use, not mere WriteAttributes.
        $maskText=([string]$fields['AccessMask'] -replace '^0x','')
        $mask=[Convert]::ToInt64($maskText,16)
        if(($mask -band 0x06) -eq 0){continue}
        $matchedAuditWriteUseCount++
        $pidText=([string]$fields['ProcessId'] -replace '^0x','')
        $eventPid=[Convert]::ToInt64($pidText,16)
        if($eventPid -eq $PID){$matchedOwn[$key]=$true}
        else{$matchedOther[$key]=$true}
      }catch{
        # One malformed 4663 event cannot create positive attribution.
        $eventQueryAvailable=$false
        $eventQueryOutcome='invalid_event'
        $matchedOwn=@{};$matchedOther=@{};$matchedAuditWriteUseCount=0
        break
      }
    }
  }catch{
    # Get-WinEvent raises NoMatchingEventsFound on a valid empty result.
    # Distinguish an empty bounded query from an unavailable/failed query.
    # Neither proves the absence of a writer or complete event delivery.
    $errorId=[string]$_.FullyQualifiedErrorId
    if($errorId -like 'NoMatchingEventsFound*'){
      $eventQueryOutcome='no_matching_events'
    }else{
      $eventQueryOutcome='query_error'
    }
    $eventQueryAvailable=$false
    $matchedOwn=@{};$matchedOther=@{};$matchedAuditWriteUseCount=0
  }
  $d3e10Completed=$true
  $complete=$true
}catch{
  # No file path, raw metadata, WinEvent, ACL, or caller error detail in logs.
  $complete=$false
}finally{
  if($watcherStarted){try{$watcher.EnableRaisingEvents=$false}catch{$complete=$false}}
  if($watchRegistered){try{Unregister-Event -SourceIdentifier $watchChangedSource -ErrorAction Stop}catch{$complete=$false}}
  if($watchErrorsRegistered){try{Unregister-Event -SourceIdentifier $watchErrorSource -ErrorAction Stop}catch{$complete=$false}}
  foreach($eventSource in @($watchChangedSource,$watchErrorSource)){
    try{Get-Event -SourceIdentifier $eventSource -ErrorAction SilentlyContinue | Remove-Event -ErrorAction Stop}catch{}
  }
  if($null -ne $watcher){try{$watcher.Dispose()}catch{$complete=$false}}
  if($saclMutated -and $null -ne $oldAcl){
    try{
      Set-Acl -LiteralPath $root -AclObject $oldAcl -ErrorAction Stop
      $check=Get-Acl -LiteralPath $root -Audit -ErrorAction Stop
      $afterSddl=$check.GetSecurityDescriptorSddlForm([Security.AccessControl.AccessControlSections]::Audit)
      if($afterSddl -cne $sddlBefore){throw 'RESTORE_MISMATCH'}
      $saclRestored=$true
    }catch{$complete=$false}
  }elseif(-not $saclMutated -and $null -ne $oldAcl){$saclRestored=$true}
  if($policyEnabled){
    if($wasEnabled -eq $false){
      try{
        & auditpol.exe /set "/subcategory:$guid" '/success:disable' >$null 2>$null
        if($LASTEXITCODE -ne 0){throw 'RESTORE_FAIL'}
        $verify=@(& auditpol.exe /get "/subcategory:$guid" /r 2>$null)
        if($LASTEXITCODE -ne 0 -or $verify.Count -lt 2 -or
           ([string]($verify | Select-Object -Last 1) -match 'Success')){
          throw 'POLICY_RESTORE_MISMATCH'
        }
        $policyRestored=$true
      }catch{$complete=$false}
    }elseif($wasEnabled -eq $true){$policyRestored=$true}
  }
}
if(-not $complete -or -not $d3e10Completed -or -not $d3e11Completed -or -not $saclRestored -or -not $policyRestored){
  Write-Host 'D3E9_ARM_VERDICT=BLOCKED_INCOMPLETE_OR_UNRESTORED_TRIAL'
  Write-Host 'SHARED_APP_STORAGE_ISOLATION=UNVERIFIED'
  Write-Host 'CLINICAL_EDIT_ALLOWED=false'
  exit 2
}
$aggregate=[ordered]@{
  schema='facad314_d3e9_independent_arm_v1'
  source='BOUNDED_INDEPENDENT_WINDOWS_RUNNER_METADATA_ONLY'
  arm=$Arm
  intervention=if($saclMutated){'sacl_applied'}else{'passive_no_sacl'}
  pre_intervention_file_count=$pre.Count
  post_intervention_file_count=$post.Count
  changed_size_count=$counts.modified_size_changed
  created_count=$counts.created
  removed_count=$counts.removed
  passive_wait_seconds=2
  sacl_restored=$saclRestored
  audit_policy_restored=$policyRestored
  separate_ephemeral_windows_runner=$true
  facad_root_launched_during_trial=$false
  raw_file_metadata_exported=$false
  file_identity_or_path_exported=$false
  matched_counterfactual_proven=$false
  writer_causality_proven=$false
  complete_audit_event_delivery=$false
  shared_app_storage_isolation_verified=$false
  clinical_edit_allowed=$false
  verdict='BOUNDED_CONTROLLED_ARM_NOT_CAUSALITY'
}

$d3e10=[ordered]@{
  schema='facad314_d3e10_prelaunch_metadata_audit_v1'
  source='EPHEMERAL_D3E9_ARM_SIZE_TIMESTAMP_AND_4663_MATCH_AGGREGATE'
  arm=$Arm
  changed_size_count=[int]$counts.modified_size_changed
  changed_size_and_last_write_timestamp_count=[int]$timeCounters.size_and_timestamp_changed
  changed_size_without_timestamp_change_count=[int]$timeCounters.size_without_timestamp_changed
  unchanged_size_changed_timestamp_count=[int]$timeCounters.same_size_timestamp_changed
  security_4663_query_attempted=$eventQueryAttempted
  security_4663_records_available=$eventQueryAvailable
  security_4663_query_outcome=$eventQueryOutcome
  matching_write_data_or_append_access_event_count=[int]$matchedAuditWriteUseCount
  same_powershell_pid_matching_file_count=[int]$matchedOwn.Count
  other_pid_matching_file_count=[int]$matchedOther.Count
  process_identity_exported=$false
  file_identity_or_size_or_timestamp_exported=$false
  file_content_read=$false
  full_event_delivery_proven=$false
  file_write_causality_proven=$false
  clinical_edit_allowed=$false
  shared_app_storage_isolation_verified=$false
  verdict='METADATA_4663_BOUNDED_NOT_WRITER_CAUSALITY'
}
$extraPath=[IO.Path]::GetFullPath((Join-Path (Split-Path $dest -Parent) ("d3e10-provenance-$Arm.json")))
if((Test-Path -LiteralPath $extraPath) -or
   -not $extraPath.StartsWith($workspace+'\', [StringComparison]::OrdinalIgnoreCase)){
  Write-Host 'D3E10_PRIVATE_OUTPUT_BOUNDARY_INVALID'
  exit 2
}
$d3e10 | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $extraPath -Encoding utf8 -ErrorAction Stop
Write-Host "D3E10_SIZE_AND_TIMESTAMP_CHANGED_COUNT=$($timeCounters.size_and_timestamp_changed)"
Write-Host "D3E10_SIZE_ONLY_CHANGED_COUNT=$($timeCounters.size_without_timestamp_changed)"
Write-Host "D3E10_MATCHING_4663_WRITE_USE_COUNT=$matchedAuditWriteUseCount"
Write-Host "D3E10_MATCHING_4663_OTHER_PROCESS_FILE_COUNT=$($matchedOther.Count)"
Write-Host "D3E10_SECURITY_EVENT_RECORDS_AVAILABLE=$($eventQueryAvailable.ToString().ToLowerInvariant())"
Write-Host "D3E10_SECURITY_QUERY_OUTCOME=$eventQueryOutcome"
Write-Host 'D3E10_FILE_CONTENT_READ=false'
Write-Host 'D3E10_WRITER_CAUSALITY_PROVEN=false'


$d3e11=[ordered]@{
  schema='facad314_d3e11_fsw_sacl_aggregate_v1'
  source='NATIVE_CHANGE_NOTIFICATION_AND_FILE_AUDIT_RULE_METADATA_ONLY'
  arm=$Arm
  changed_size_file_count=[int]$counts.modified_size_changed
  filesystem_watcher_started=$watcherStarted
  filesystem_watcher_error_reported=$watcherReportedError
  filesystem_watcher_received_event_count=[int]$watchEventCount
  changed_size_files_with_notification_count=[int]$watchMatches.Count
  file_sacl_checked_changed_file_count=[int]$saclChecked
  file_sacl_unchecked_changed_file_count=[int]$saclFailed
  changed_files_with_current_sid_write_audit_count=[int]$matchedSacl
  changed_files_with_inherited_current_sid_write_audit_count=[int]$matchedInheritedSacl
  file_content_read=$false
  file_identifiers_or_paths_or_sizes_exported=$false
  notification_delivery_complete_proven=$false
  writer_pid_proven=$false
  change_caused_by_set_acl_proven=$false
  shared_app_storage_isolation_verified=$false
  clinical_edit_allowed=$false
  verdict='FSW_SACL_COVERAGE_OBSERVATION_NOT_CAUSALITY'
}
$d3e11Path=[IO.Path]::GetFullPath((Join-Path (Split-Path $dest -Parent) ("d3e11-observation-$Arm.json")))
if((Test-Path -LiteralPath $d3e11Path) -or
   -not $d3e11Path.StartsWith($workspace+'\', [StringComparison]::OrdinalIgnoreCase)){
  Write-Host 'D3E11_AGGREGATE_OUTPUT_BOUNDARY_INVALID'
  exit 2
}
$d3e11 | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $d3e11Path -Encoding utf8 -ErrorAction Stop
Write-Host "D3E11_FSW_MATCHED_CHANGED_SIZE_COUNT=$($watchMatches.Count)"
Write-Host "D3E11_FSW_ERROR_REPORTED=$($watcherReportedError.ToString().ToLowerInvariant())"
Write-Host "D3E11_SACL_CHANGED_FILES_AUDITED_COUNT=$matchedSacl"
Write-Host "D3E11_SACL_CHANGED_FILES_INHERITED_AUDITED_COUNT=$matchedInheritedSacl"
Write-Host "D3E11_SACL_INSPECTION_FAILED_COUNT=$saclFailed"
Write-Host 'D3E11_WRITER_PID_PROVEN=false'
Write-Host 'D3E11_CLINICAL_EDIT_ALLOWED=false'

$aggregate | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $dest -Encoding utf8 -ErrorAction Stop
Write-Host "D3E9_TRIAL_ARM=$Arm"
Write-Host "D3E9_MODIFIED_SIZE_COUNT=$($counts.modified_size_changed)"
Write-Host "D3E9_CREATED_COUNT=$($counts.created)"
Write-Host "D3E9_REMOVED_COUNT=$($counts.removed)"
Write-Host 'D3E9_SACL_RESTORED=true'
Write-Host 'D3E9_AUDIT_POLICY_RESTORED=true'
Write-Host 'D3E9_FILE_IDENTITIES_EXPORTED=false'
Write-Host 'SHARED_APP_STORAGE_ISOLATION=UNVERIFIED'
Write-Host 'CLINICAL_EDIT_ALLOWED=false'
