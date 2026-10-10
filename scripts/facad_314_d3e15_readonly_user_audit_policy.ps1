# FAC-03 D3E15: inspect per-user File System audit policy on Windows (READ ONLY).
# No SACL, no auditpol /set, no Security log reads, no ETW, no Facad/Ilexis.
param([Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$guid='{0cce921d-69ae-11d9-bed3-505054503030}'
function Inspect-AuditPolicyCsv {
 param([string[]]$Text,[string]$PolicyField)
 # Never print data: auditpol rows may contain machine and user identities.
 try {
   if($Text.Count -eq 0){return 'unavailable'}
   $rows=@($Text | ConvertFrom-Csv -ErrorAction Stop)
   foreach($row in $rows){
     $actual=[string]$row.'Subcategory GUID'
     if($actual.Trim('{} ').ToLowerInvariant() -cne '0cce921d-69ae-11d9-bed3-505054503030'){continue}
     $setting=[string]$row.$PolicyField
     if($setting -match '(?i)\bsuccess\b'){return 'success_configured'}
     if($setting -match '(?i)\b(no auditing|failure)\b'){return 'success_not_configured'}
     return 'undetermined'
   }
   return 'undetermined'
 }catch{return 'parse_error'}
}
$rootOk=$false
$systemStatus='unavailable';$userStatus='unavailable'
$systemQueryOk=$false;$userQueryOk=$false
$adminMembershipKnown=$false;$runnerIsAdmin=$false
$perUserPolicyChanged=$false;$globalPolicyChanged=$false
$policyQueryOnly=$true
try {
 if($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_OS -cne 'Windows' -or
    -not $env:GITHUB_WORKSPACE -or -not $env:GITHUB_RUN_ID){
   throw 'RUNNER_NOT_AUTHORIZED'
 }
 $ws=[IO.Path]::GetFullPath($env:GITHUB_WORKSPACE).TrimEnd('\')
 $out=[IO.Path]::GetFullPath($OutputPath)
 if(-not $out.StartsWith($ws+'\',[StringComparison]::OrdinalIgnoreCase) -or
    [IO.Path]::GetFileName($out) -cne 'd3e15-audit-policy-readonly.json' -or
    (Test-Path -LiteralPath $out)){throw 'OUTPUT_BOUNDARY_INVALID'}
 $identity=[Security.Principal.WindowsIdentity]::GetCurrent()
 $principal=[Security.Principal.WindowsPrincipal]::new($identity)
 $runnerIsAdmin=$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
 $adminMembershipKnown=$true
 # File System audit subcategory stable GUID, independent of translated display label.
 try{
   $rawSystem=@(& auditpol.exe /get "/subcategory:$guid" /r 2>$null)
   $systemQueryOk=($LASTEXITCODE -eq 0)
   if($systemQueryOk){$systemStatus=Inspect-AuditPolicyCsv -Text $rawSystem -PolicyField 'Inclusion Setting'}
 }catch{$systemStatus='unavailable'}
 # Query *only the invoking disposable runner principal*, in memory.
 # Never emit its SID, machine name, or unredacted auditpol CSV.
 try{
   $userArg="/user:{$($identity.User.Value)}"
   $rawUser=@(& auditpol.exe /get $userArg "/subcategory:$guid" /r 2>$null)
   $userQueryOk=($LASTEXITCODE -eq 0)
   if($userQueryOk){$userStatus=Inspect-AuditPolicyCsv -Text $rawUser -PolicyField 'Inclusion Setting'}
 }catch{$userStatus='unavailable'}
 $rootOk=$true
}catch{
 # Never serialize exception, SID, paths or any native command output.
 $rootOk=$false
}
if(-not $rootOk){
 Write-Host 'D3E15_READONLY_POLICY_PROBE_BLOCKED=true'
 exit 2
}
$result=[ordered]@{
 schema='facad314_d3e15_readonly_per_user_policy_v1'
 source='CURRENT_EPHEMERAL_WINDOWS_RUNNER_READ_ONLY'
 file_system_audit_subcategory='FILE_SYSTEM'
 auditpol_system_query_succeeded=$systemQueryOk
 auditpol_user_query_succeeded=$userQueryOk
 system_success_audit_status=$systemStatus
 per_user_inclusion_success_audit_status=$userStatus
 runner_admin_membership_check_succeeded=$adminMembershipKnown
 runner_is_local_administrator=$runnerIsAdmin
 global_policy_modified=$globalPolicyChanged
 per_user_policy_modified=$perUserPolicyChanged
 security_events_queried=$false
 global_kernel_etw_capture_used=$false
 synthetic_or_clinical_files_touched=$false
 raw_auditpol_output_exported=$false
 sid_or_username_exported=$false
 private_paths_or_process_ids_exported=$false
 per_user_audit_is_exclusive_to_one_file_proven=$false
 real_ilexis_writer_proven=$false
 shared_app_storage_isolation_verified=$false
 clinical_edit_allowed=$false
 verdict='READ_ONLY_PER_USER_AUDIT_POLICY_OBSERVATION_NOT_CAPTURE_AUTHORIZATION'
}
$result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $out -Encoding utf8 -ErrorAction Stop
Write-Host "D3E15_SYSTEM_POLICY=$systemStatus"
Write-Host "D3E15_PER_USER_POLICY=$userStatus"
Write-Host "D3E15_PER_USER_QUERY_SUCCEEDED=$($userQueryOk.ToString().ToLowerInvariant())"
Write-Host "D3E15_RUNNER_ADMIN=$($runnerIsAdmin.ToString().ToLowerInvariant())"
Write-Host 'D3E15_POLICY_MODIFIED=false'
Write-Host 'D3E15_CAPTURE_AUTHORIZED=false'
Write-Host 'FAC03_D3=OPEN_RED'
Write-Host 'SHARED_APP_STORAGE_ISOLATION=UNVERIFIED'
Write-Host 'CLINICAL_EDIT_ALLOWED=false'
