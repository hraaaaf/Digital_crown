# EXPLICITLY SYNTHETIC ONLY. Windows Security event 4663 includes raw paths,
# process names and SIDs. NEVER export raw events or execute against clinical paths.
param([Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
$guid='{0CCE921D-69AE-11D9-BED3-505054503030}' # Windows Audit File System
$verdict='BLOCKED_AUDIT_UNAVAILABLE'
$root=$null
$policyWasEnabled=$null
$result=[ordered]@{
  schema='facad314_d3e_audit_canary_v1'
  source='EPHEMERAL_WINDOWS_RUNNER_SYNTHETIC_CANARY_ONLY'
  audit_event_id=4663
  scoped_sacl_configuration_proven=$false
  audit_policy_enabled_during_observation=$false
  matching_4663_write_event_count=0
  queried_4663_event_count=0
  scoped_4663_event_count=0
  scoped_write_mask_event_count=0
  scoped_expected_pid_event_count=0
  expected_process_pid_matched=$false
  event_path_scope_matched=$false
  unexpected_pid_count=0
  event_completeness_verified=$false
  clinical_data_accessed=$false
  facad_application_launched=$false
  process_file_write_attribution_proven_for_facad=$false
  shared_app_storage_isolation_verified=$false
  clinical_edit_allowed=$false
  verdict=$verdict
}
try {
  if($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_OS -cne 'Windows' -or -not $env:RUNNER_TEMP -or -not $env:GITHUB_RUN_ID) {
    throw 'EPHEMERAL_RUNNER_REQUIRED'
  }
  $runnerTemp=[IO.Path]::GetFullPath($env:RUNNER_TEMP).TrimEnd('\')
  $root=Join-Path $runnerTemp ('facad-d3e-synthetic-'+[guid]::NewGuid().ToString('N'))
  if(-not ([IO.Path]::GetFullPath($root).StartsWith($runnerTemp+'\',[StringComparison]::OrdinalIgnoreCase))){
    throw 'PATH_GUARD'
  }
  New-Item -ItemType Directory -Path $root -ErrorAction Stop | Out-Null
  # Observe the existing system-wide audit policy before making a bounded change.
  $oldPolicy=@(& auditpol.exe /get "/subcategory:$guid" /r 2>$null)
  if($LASTEXITCODE -ne 0 -or $oldPolicy.Count -lt 2){throw 'AUDIT_POLICY_UNAVAILABLE'}
  $policyLine=($oldPolicy | Select-Object -Last 1)
  $policyFields=$policyLine | ConvertFrom-Csv -Header 'Machine','PolicyTarget','Subcategory','SubcategoryGUID','InclusionSetting','ExclusionSetting' -ErrorAction Stop
  # This retrieval is advisory only; never claim successful restoration if unable to parse.
  $policyWasEnabled=($policyLine -match 'Success')
  & auditpol.exe /set "/subcategory:$guid" '/success:enable' >$null 2>$null
  if($LASTEXITCODE -ne 0){throw 'AUDIT_POLICY_ENABLE_FAILED'}
  $result.audit_policy_enabled_during_observation=$true

  $sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User
  $auditRights=[System.Security.AccessControl.FileSystemRights]::WriteData -bor
    [System.Security.AccessControl.FileSystemRights]::AppendData -bor
    [System.Security.AccessControl.FileSystemRights]::WriteAttributes -bor
    [System.Security.AccessControl.FileSystemRights]::Delete
  $inherit=[System.Security.AccessControl.InheritanceFlags]::ContainerInherit -bor
    [System.Security.AccessControl.InheritanceFlags]::ObjectInherit
  $ace=[System.Security.AccessControl.FileSystemAuditRule]::new(
    $sid,$auditRights,$inherit,
    [System.Security.AccessControl.PropagationFlags]::None,
    [System.Security.AccessControl.AuditFlags]::Success)
  $acl=Get-Acl -LiteralPath $root -Audit
  $acl.AddAuditRule($ace)
  Set-Acl -LiteralPath $root -AclObject $acl -ErrorAction Stop
  $result.scoped_sacl_configuration_proven=$true
  $start=(Get-Date).AddSeconds(-1)
  $canary=Join-Path $root 'ephemeral-canary.txt'
  [IO.File]::WriteAllText($canary,'D3E synthetic only',[Text.Encoding]::UTF8)
  [IO.File]::AppendAllText($canary,'-write',[Text.Encoding]::UTF8)
  Start-Sleep -Seconds 2
  # Never serialize EventRecord.ToXml(), its ObjectName/ProcessName or any SID.
  $records=Get-WinEvent -FilterHashtable @{LogName='Security';Id=4663;StartTime=$start} -MaxEvents 500 -ErrorAction Stop
  $result.queried_4663_event_count=@($records).Count
  $matched=0
  $scoped=0
  $scopedWrites=0
  $scopedExpectedPid=0
  $unexpected=[System.Collections.Generic.HashSet[int]]::new()
  foreach($event in $records){
    [xml]$xml=$event.ToXml()
    $fields=@{}
    foreach($field in $xml.Event.EventData.Data){$fields[[string]$field.Name]=[string]$field.'#text'}
    if($fields['ObjectType'] -cne 'File' -or -not $fields['ObjectName']){continue}
    $inside=($fields['ObjectName'].Equals($root,[StringComparison]::OrdinalIgnoreCase) -or
             $fields['ObjectName'].StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase))
    if(-not $inside){continue}
    $scoped++
    if(-not $fields['ProcessId']){continue}
    $pidNumber=[Convert]::ToInt32(($fields['ProcessId'] -replace '^0x',''),16)
    if($pidNumber -eq $PID){$scopedExpectedPid++}
    if(-not $fields['AccessMask']){continue}
    $accessMask=[Convert]::ToInt64(($fields['AccessMask'] -replace '^0x',''),16)
    if(($accessMask -band 0x10106) -eq 0){continue}
    $scopedWrites++
    if($pidNumber -eq $PID){$matched++}else{[void]$unexpected.Add($pidNumber)}
  }
  $result.scoped_4663_event_count=$scoped
  $result.scoped_write_mask_event_count=$scopedWrites
  $result.scoped_expected_pid_event_count=$scopedExpectedPid
  $result.matching_4663_write_event_count=$matched
  $result.expected_process_pid_matched=($matched -gt 0)
  $result.event_path_scope_matched=($matched -gt 0)
  $result.unexpected_pid_count=$unexpected.Count
  # A positive canary is proof of functional instrumentation IN THIS ROOT ONLY.
  # Event loss detection and absence of writes remain completely unproven.
  $result.event_completeness_verified=$false
  $result.verdict=if($matched -gt 0){'SYNTHETIC_CANARY_4663_PID_MATCH_ONLY'}else{'BLOCKED_NO_MATCHING_CANARY_EVENT'}
} catch {
  # Intentionally hide exception strings, paths, SID and other personal identifiers.
  $result.verdict='BLOCKED_AUDIT_UNAVAILABLE_OR_INCOMPLETE'
} finally {
  if($root -and (Test-Path -LiteralPath $root)) {
    try {Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction Stop}catch{$result.verdict='BLOCKED_CLEANUP_FAILED'}
  }
  if($policyWasEnabled -eq $false -and $result.audit_policy_enabled_during_observation){
    try {
      & auditpol.exe /set "/subcategory:$guid" '/success:disable' >$null 2>$null
      if($LASTEXITCODE -ne 0){$result.verdict='BLOCKED_POLICY_RESTORE_FAILED'}
    } catch {$result.verdict='BLOCKED_POLICY_RESTORE_FAILED'}
  }
  $parent=Split-Path -Parent $OutputPath
  if($parent -and -not (Test-Path -LiteralPath $parent)){New-Item -ItemType Directory -Path $parent -Force | Out-Null}
  $result | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $OutputPath -Encoding utf8
  Write-Host ('D3E_CANARY_VERDICT='+$result.verdict)
  Write-Host ('D3E_4663_EVENTS_QUERIED='+$result.queried_4663_event_count)
  Write-Host ('D3E_SCOPED_4663_EVENTS='+$result.scoped_4663_event_count)
  Write-Host ('D3E_SCOPED_WRITE_EVENTS='+$result.scoped_write_mask_event_count)
  Write-Host ('D3E_SCOPED_EXPECTED_PID_EVENTS='+$result.scoped_expected_pid_event_count)
  Write-Host ('D3E_CANARY_MATCHED_WRITE_EVENT_COUNT='+$result.matching_4663_write_event_count)
  Write-Host 'D3E_FACAD_WRITE_ATTRIBUTION=false'
  Write-Host 'D3E_CLINICAL_EDIT_ALLOWED=false'
}
if($result.verdict -cne 'SYNTHETIC_CANARY_4663_PID_MATCH_ONLY'){exit 2}
