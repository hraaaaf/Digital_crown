# D3E30: synthetic Windows Security 4663 query/parser tests. Fake Get-WinEvent
# shadows the real command. No Security log read, SACL change, FACAD, or patient.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if($env:RUNNER_OS -cne 'Windows' -or $env:GITHUB_ACTIONS -cne 'true' -or
   [string]::IsNullOrWhiteSpace($env:GITHUB_WORKSPACE)){throw 'D3E30_WINDOWS_GITHUB_ONLY'}
$root=[IO.Path]::GetFullPath($env:GITHUB_WORKSPACE).TrimEnd('\')
$summary=Join-Path $root 'd3e30-synthetic-audit-safe.json'
if(Test-Path -LiteralPath $summary){throw 'D3E30_AGGREGATE_EXISTS'}
$diagnostic=Get-Content -LiteralPath (Join-Path $root 'scripts/facad_314_d3e27_root_pid_diagnostic.ps1') -Raw
if(-not $diagnostic.Contains("facad_314_d3e30_4663_guard.ps1") -or
   -not $diagnostic.Contains('Get-D3E30Security4663Batch -StartTime $start') -or
    $diagnostic.Contains("Get-WinEvent -FilterHashtable")){
  throw 'D3E30_PRODUCTION_OBSERVER_NOT_WIRED'
}
. (Join-Path $root 'scripts/facad_314_d3e22_event_path_map.ps1')
. (Join-Path $root 'scripts/facad_314_d3e30_4663_guard.ps1')

$script:Mode='events'
$script:Batch=@()
$script:QueryCalls=0
function Get-WinEvent {
  [CmdletBinding()]
  param([hashtable]$FilterHashtable,[int]$MaxEvents)
  $script:QueryCalls++
  if($FilterHashtable['LogName'] -cne 'Security' -or
     $FilterHashtable['Id'] -ne 4663 -or
     $null -eq $FilterHashtable['StartTime'] -or
     $MaxEvents -ne 4000){throw 'SYNTHETIC_BAD_QUERY_CONTRACT'}
  if($script:Mode -ceq 'throw'){throw 'PRIVATE_NATIVE_ERROR_PATH_PID_DO_NOT_LOG'}
  return $script:Batch
}
function New-Event {
 param(
  [string]$SyntheticPid='0xABC',[string]$Mask='0x02',
  [string]$Path='C:\Users\Synthetic\AppData\Roaming\Ilexis\CASE_A.dat',
  [string]$Type='File',[string]$Provider='Microsoft-Windows-Security-Auditing',
  [int]$Id=4663,[string]$OverrideXml='', [bool]$DuplicatePid=$false
 )
 $xml='<Event><EventData>'
 $xml+='<Data Name="ObjectType">'+$Type+'</Data>'
 $xml+='<Data Name="ObjectName">'+$Path+'</Data>'
 $xml+='<Data Name="ProcessId">'+$SyntheticPid+'</Data>'
 $xml+='<Data Name="AccessMask">'+$Mask+'</Data>'
 if($DuplicatePid){$xml+='<Data Name="ProcessId">0x999</Data>'}
 $xml+='</EventData></Event>'
 if($OverrideXml.Length){$xml=$OverrideXml}
 $event=[pscustomobject]@{Id=$Id;ProviderName=$Provider;XmlPayload=$xml}
 $event|Add-Member -MemberType ScriptMethod -Name ToXml -Value {return [string]$this.XmlPayload}
 return $event
}
function Assert-Fails([string]$code){
 $raised=$false
 try{
   $null=Get-D3E30Security4663Batch -StartTime ([datetime]'2026-10-11T08:00:00')
 }catch{
   if($_.Exception.Message -cne $code){throw ('D3E30_WRONG_RESULT_FOR_'+$code)}
   $raised=$true
 }
 if(-not $raised){throw 'D3E30_AUDIT_FALSE_PASS'}
}
$passed=0
$valid=New-Event
$other=New-Event -SyntheticPid '0xBCD'
$script:Batch=@($valid,$other)
$batch=Get-D3E30Security4663Batch -StartTime ([datetime]'2026-10-11T08:00:00')
if($batch.queried_event_count -ne 2 -or @($batch.file_records).Count -ne 2 -or
   $batch.file_records[0] -isnot [System.Collections.IDictionary] -or
   $batch.file_records[0]['ObjectType'] -cne 'File' -or
   $batch.file_records[0].ProcessId -cne '0xABC' -or
   $batch.file_records[1].ProcessId -cne '0xBCD'){throw 'D3E30_VALID_BATCH_FAILED'}
$passed++
# Paths are pure strings; no filesystem access. Reuse the actual D3E22 source-lock.
$scoped=Resolve-ScopedEventRelative -ScopeRoot 'C:\Users\Synthetic\AppData\Roaming\Ilexis' -ObservedPath $batch.file_records[0].ObjectName
if($scoped -cne 'CASE_A.dat' -or
   -not (Test-ScopedWriteDataAccess -AccessMask $batch.file_records[0].AccessMask) -or
   (Test-ScopedWriteDataAccess -AccessMask '0x100') -or
   $null -ne (Resolve-ScopedEventRelative -ScopeRoot 'C:\Users\Synthetic\AppData\Roaming\Ilexis' -ObservedPath 'C:\Users\Other\AppData\Roaming\Ilexis\CASE_A.dat')){
  throw 'D3E30_PATH_SCOPE_OR_WRITE_BIT_SPOOF'
}
$passed++
foreach($item in @(
  (New-Event -Provider 'Forger-Not-Security-Auditing'),
  (New-Event -Id 1),
  (New-Event -Type 'Registry')
)){
 $script:Batch=@($item)
 $batch=Get-D3E30Security4663Batch -StartTime ([datetime]'2026-10-11T08:00:00')
 if($batch.queried_event_count -ne 1 -or @($batch.file_records).Count -ne 0){
   throw 'D3E30_SPOOFED_EVENT_WAS_ACCEPTED'
 }
 $passed++
}
$script:Mode='throw'
Assert-Fails 'D3E30_AUDIT_QUERY_UNAVAILABLE';$passed++
$script:Mode='events'
$script:Batch=@()
Assert-Fails 'D3E30_AUDIT_ZERO_EVENTS_INCONCLUSIVE';$passed++
$script:Batch=@($valid)*4000
Assert-Fails 'D3E30_AUDIT_EVENT_CAP';$passed++
$script:Batch=@(New-Event -OverrideXml '<<broken')
Assert-Fails 'D3E30_AUDIT_XML_INVALID';$passed++
$script:Batch=@(New-Event -DuplicatePid $true)
Assert-Fails 'D3E30_AUDIT_XML_INVALID';$passed++
$script:Batch=@(New-Event -SyntheticPid '')
Assert-Fails 'D3E30_AUDIT_FIELDS_MISSING';$passed++
$script:Batch=@(New-Event -SyntheticPid 'not-hex')
Assert-Fails 'D3E30_AUDIT_PID_INVALID';$passed++
$script:Batch=@(New-Event -Mask '0x-no')
Assert-Fails 'D3E30_AUDIT_MASK_INVALID';$passed++
$script:Batch=@(New-Event -Path ('C:\Users\Synthetic\AppData\Roaming\Ilexis\'+('Z'*8300)))
Assert-Fails 'D3E30_AUDIT_PATH_INVALID';$passed++
# The query-error redaction must never bypass a terminal failure despite benign masks.
$script:Batch=@(New-Event -Mask '0x100')
$batch=Get-D3E30Security4663Batch -StartTime ([datetime]'2026-10-11T08:00:00')
if(@($batch.file_records).Count -ne 1 -or
   (Test-ScopedWriteDataAccess -AccessMask $batch.file_records[0].AccessMask)){
   throw 'D3E30_NON_WRITE_MASK_MISCLASSIFIED'
}
$passed++
if($passed -ne 15){throw 'D3E30_TEST_COUNT_UNEXPECTED'}
$summaryData=[ordered]@{
 schema='facad_d3e30_synthetic_4663_gate_v1'
 synthetic_cases_passed=$passed
 query_mock_call_count=$script:QueryCalls
 production_observer_wired=$true
 query_failure_rejected=$true
 no_events_inconclusive=$true
 event_limit_rejected=$true
 malformed_xml_rejected=$true
 duplicate_xml_fields_rejected=$true
 missing_fields_rejected=$true
 invalid_pid_and_mask_rejected=$true
 wrong_id_provider_type_ignored=$true
 scoped_write_bits_checked=$true
 confidential_native_error_redacted=$true
 vendor_executed=$false
 windows_security_log_read=$false
 windows_sacl_modified=$false
 audit_4663_certified=$false
 shared_app_storage_isolation_verified=$false
 clinical_edit_allowed=$false
 verdict='SYNTHETIC_ONLY_D3_OPEN_RED'
}
$summaryData|ConvertTo-Json -Depth 4|Set-Content -LiteralPath $summary -Encoding utf8
Write-Host 'D3E30_SYNTHETIC_4663_CASES=15'
Write-Host 'D3E30_GET_WINEVENT=MOCK_ONLY'
Write-Host 'D3E30_VENDOR_EXECUTED=false'
Write-Host 'D3E30_D3=OPEN_RED'
