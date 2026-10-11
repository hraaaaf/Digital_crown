# D3E27: native FACAD persistence trial. All identities and hashes remain private.
param([Parameter(Mandatory=$true)][string]$FacadExecutable,
      [Parameter(Mandatory=$true)][string]$DisposableRobert,
      [Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'facad_314_d3e27_private_oracle.ps1')
$private=[ordered]@{
 event=Join-Path $env:RUNNER_TEMP 'd3e3-event-keys-cold.json'
 timeline=Join-Path $env:RUNNER_TEMP 'd3e5-timeline-cold.json'
 prelaunch=Join-Path $env:RUNNER_TEMP 'd3e6-prelaunch-cold.json'
 preflight=Join-Path $env:RUNNER_TEMP 'd3e7-preflight-cold.json'
 passive=Join-Path $env:RUNNER_TEMP 'd3e8-passive-control-cold.json'
 process=Join-Path $env:RUNNER_TEMP 'd3e27-process-io-private.json'
 observer=Join-Path $env:RUNNER_TEMP 'd3e27-root-observer-private.json'
}
$scope=Join-Path $env:APPDATA 'Ilexis'
if($env:RUNNER_ENVIRONMENT -cne 'github-hosted' -or $env:RUNNER_OS -cne 'Windows' -or
   $env:GITHUB_ACTIONS -cne 'true'){throw 'D3E27_RUNNER_ONLY'}
if([IO.Path]::GetFileName($FacadExecutable) -cne 'Facad.exe' -or
   [IO.Path]::GetFileName($DisposableRobert) -cne 'Robert-2.0.fcd' -or
   -not (Test-Path -LiteralPath $FacadExecutable -PathType Leaf) -or
   -not (Test-Path -LiteralPath $DisposableRobert -PathType Leaf)){
   throw 'D3E27_VENDOR_AND_ROBERT_GUARD'
}
if($OutputPath -notlike "$env:GITHUB_WORKSPACE\*" -or
   [IO.Path]::GetFileName($OutputPath) -cne 'd3e27-content-aggregate.json' -or
   (Test-Path -LiteralPath $OutputPath)){throw 'D3E27_OUTPUT_INVALID'}
foreach($file in $private.Values){
 if(Test-Path -LiteralPath $file){throw 'D3E27_PRIVATE_FILE_COLLISION'}
}
try{
  $controlBefore=Get-D3E27Snapshot -Root $scope
  Start-Sleep -Seconds 12
  $controlAfter=Get-D3E27Snapshot -Root $scope
  $activeBefore=Get-D3E27Snapshot -Root $scope
  $params=@{
    FacadExecutable=$FacadExecutable
    DisposableRobert=$DisposableRobert
    ProcessCounterScript=(Join-Path $PSScriptRoot 'facad_314_d3_process_io_observer.ps1')
    ProcessCounterOutput=$private.process
    OutputPath=$private.observer
    EventKeysPath=$private.event
    TimelinePath=$private.timeline
    PreLaunchPath=$private.prelaunch
    PreflightPath=$private.preflight
    PassiveControlPath=$private.passive
    SessionId="d3e27-$env:GITHUB_RUN_ID"
  }
  Write-Host 'D3E27_REAL_FACAD_STARTUP_OBSERVER_INVOKED=true'
  & (Join-Path $PSScriptRoot 'facad_314_d3e27_root_pid_diagnostic.ps1') @params
  $status=$LASTEXITCODE
  $afterStopped=Get-D3E27Snapshot -Root $scope
  Start-Sleep -Seconds 7
  $afterSettled=Get-D3E27Snapshot -Root $scope
  $keys=@()
  $sacl=$false;$policy=$false;$rootCount=0;$otherCount=0
  $rootAlive=$false;$verdict='BLOCKED_NO_OBSERVER'
  $diagnosticPhase='no_observer';$exceptionClass='none'
  $eventQueryCount=0;$scopedCount=0;$writeAccessCount=0
  if(Test-Path -LiteralPath $private.observer -PathType Leaf){
    $o=Get-Content -LiteralPath $private.observer -Raw | ConvertFrom-Json -ErrorAction Stop
    $sacl=($o.scope_sacl_restored -eq $true)
    $policy=($o.audit_policy_restored -eq $true)
    $rootCount=[int]$o.facad_root_pid_write_event_count
    $otherCount=[int]$o.other_process_pid_write_event_count
    $rootAlive=($o.process_root_alive_during_observation -eq $true)
    $verdict=[string]$o.verdict
    $diagnosticPhase=[string]$o.diagnostic_failure_phase
    $exceptionClass=[string]$o.diagnostic_exception_class
    $eventQueryCount=[int]$o.queried_event_count
    $scopedCount=[int]$o.diagnostic_4663_scoped_count
    $writeAccessCount=[int]$o.diagnostic_4663_write_access_count
  }
  if(Test-Path -LiteralPath $private.event -PathType Leaf){
    $ev=Get-Content -LiteralPath $private.event -Raw | ConvertFrom-Json -ErrorAction Stop
    if($ev.source -cne 'EPHEMERAL_FACAD_ROOT_PID_4663_KEYS_LOCAL_ONLY' -or
       $ev.schema -cne 'facad314_d3e3_event_ids_v1'){
       throw 'D3E27_EVENT_KEY_SOURCE_INVALID'
    }
    $keys=@($ev.root_pid_relative_key_hashes)
  }
  $result=Get-D3E27StableResult -ControlBefore $controlBefore -ControlAfter $controlAfter -ActiveBefore $activeBefore -AfterStopped $afterStopped -AfterSettled $afterSettled -RootEventKeys $keys
  $result['root_pid_write_use_count']=$rootCount
  $result['other_pid_write_use_count']=$otherCount
  $result['root_pid_alive_during_observation']=$rootAlive
  $result['observer_exit_code']=$status
  $result['observer_verdict']=$verdict
  $result['observer_failure_phase']=$diagnosticPhase
  $result['observer_exception_class']=$exceptionClass
  $result['observer_event_query_count']=$eventQueryCount
  $result['observer_scoped_event_count']=$scopedCount
  $result['observer_scoped_write_access_count']=$writeAccessCount
  $result['sacl_restored']=$sacl
  $result['audit_policy_restored']=$policy
  $result['negative_control_seconds']=12
  $result['settle_seconds']=7
  $result['persisted_content_change_causally_proven']=$false
  if(-not $sacl -or -not $policy){
    $result['verdict']='BLOCKED_AUDIT_OR_SACL_NOT_RESTORED'
  }elseif($status -ne 0){
    $result['verdict']='BLOCKED_ROOT_PID_EVIDENCE'
  }
  $result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputPath -Encoding utf8 -ErrorAction Stop
  Write-Host "D3E27_NEGATIVE_CONTROL_CHANGED_COUNT=$($result.negative_control_changed_count)"
  Write-Host "D3E27_AFTER_STOP_CHANGED_COUNT=$($result.after_facad_stop_changed_count)"
  Write-Host "D3E27_STABLE_CONTENT_CHANGED_COUNT=$($result.stable_existing_file_content_changed_count)"
  Write-Host "D3E27_STABLE_ROOT_PID_OVERLAP_NO_CONTROL_COUNT=$($result.stable_root_pid_overlap_without_control_count)"
  Write-Host "D3E27_SHARING_LOCKED_FILE_OBSERVATIONS=$($result.sharing_locked_file_observations)"
  Write-Host "D3E27_HASH_COVERAGE_COMPLETE=$($result.hash_coverage_complete)"
  Write-Host "D3E27_ROOT_PID_WRITE_USE_COUNT=$rootCount"
  Write-Host "D3E27_ORACLE_VERDICT=$($result.verdict)"
  Write-Host 'D3E27_FILE_NAMES_CONTENTS_AND_HASHES_EXPORTED=false'
  Write-Host 'D3E27_CONTENT_HASHED_IN_MEMORY=true'
  Write-Host 'D3E27_COMPLETE_CAUSALITY_PROVEN=false'
  Write-Host 'D3E27_SHARED_APP_STORAGE_ISOLATION=UNVERIFIED'
  Write-Host 'CLINICAL_EDIT_ALLOWED=false'
  if(-not $sacl -or -not $policy){throw 'D3E27_RESTORATION_PROOF_INCOMPLETE'}
  if($status -ne 0){throw 'D3E27_NATIVE_PROCESS_EVIDENCE_INCOMPLETE'}
}finally{
  $cleaned=$true
  foreach($path in $private.Values){
    if(Test-Path -LiteralPath $path){
      try{Remove-Item -LiteralPath $path -Force -ErrorAction Stop}catch{$cleaned=$false}
    }
  }
  Write-Host "D3E27_PRIVATE_MANIFESTS_CLEANED=$cleaned"
  if(-not $cleaned){throw 'D3E27_PRIVATE_CLEANUP_INCOMPLETE'}
}
