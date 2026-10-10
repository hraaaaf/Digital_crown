# FAC-03 D3E16 read-only current-user auditpol diagnosis.
# Never print or export raw account inventories, SIDs or native error text.
param([Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$guid='{0cce921d-69ae-11d9-bed3-505054503030}'
$listResult='unavailable';$userListed='undetermined'
$getSubcategoryResult='unavailable';$getCategoryResult='unavailable'
$completed=$false

function Invoke-ReadOnlyAuditpol {
  param([Parameter(Mandatory=$true)][string[]]$CliArgs)
  try {
    # Native output contains potentially sensitive account context. RAM only.
    $null=@(& auditpol.exe @CliArgs 2>$null)
    if($LASTEXITCODE -eq 0){return 'zero'}
    return 'nonzero'
  }catch {return 'unavailable'}
}
try {
  if($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_OS -cne 'Windows' -or
     -not $env:GITHUB_WORKSPACE -or -not $env:GITHUB_RUN_ID){
    throw 'DISPOSABLE_WINDOWS_RUNNER_REQUIRED'
  }
  $ws=[IO.Path]::GetFullPath($env:GITHUB_WORKSPACE).TrimEnd('\')
  $target=[IO.Path]::GetFullPath($OutputPath)
  if(-not $target.StartsWith($ws+'\',[StringComparison]::OrdinalIgnoreCase) -or
     [IO.Path]::GetFileName($target) -cne 'd3e16-current-user-readonly.json' -or
     (Test-Path -LiteralPath $target)){throw 'PUBLIC_OUTPUT_BOUNDARY_INVALID'}
  $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
  if($sid -notmatch '^S-1-[0-9]+(-[0-9]+){1,15}$'){throw 'CURRENT_USER_SID_UNAVAILABLE'}
  $userArg="/user:{$sid}"
  # auditpol /list /user /v /r may contain other identities. Process in RAM.
  try {
    $rawList=@(& auditpol.exe /list /user /v /r 2>$null)
    if($LASTEXITCODE -eq 0){
      $listResult='zero'
      if($rawList.Count -gt 10000){throw 'READONLY_LIST_UNBOUNDED'}
      $inMemoryOutput=$rawList -join [Environment]::NewLine
      if($inMemoryOutput.Length -gt 500000){throw 'READONLY_LIST_UNBOUNDED'}
      $escaped=[regex]::Escape($sid)
      $matchingRegex='(?i)(?<![A-Z0-9-])'+$escaped+'(?![A-Z0-9-])'
      $userListed=if([regex]::IsMatch($inMemoryOutput,$matchingRegex)){
        'exact_current_sid_seen'
      }else{
        'not_seen_in_successful_listing'
      }
    }else{$listResult='nonzero'}
  }catch {
    $listResult='unavailable';$userListed='undetermined'
  }finally{
    $rawList=$null;$inMemoryOutput=$null;$escaped=$null;$matchingRegex=$null
  }
  # Two GET forms on current user only. No auditpol /set or global mutations.
  $getSubcategoryResult=Invoke-ReadOnlyAuditpol -CliArgs @('/get',$userArg,"/subcategory:$guid",'/r')
  $getCategoryResult=Invoke-ReadOnlyAuditpol -CliArgs @('/get',$userArg,'/category:*','/r')
  $completed=$true
}catch{
  $completed=$false
}
if(-not $completed){Write-Host 'D3E16_READONLY_DIAGNOSTIC_BLOCKED=true';exit 2}
$payload=[ordered]@{
  schema='facad314_d3e16_user_auditpol_presence_diagnostic_v1'
  source='EPHEMERAL_RUNNER_CURRENT_SID_READ_ONLY'
  previous_get_user_unavailable_observed=$true
  get_user_sid_syntax='braced_current_sid'
  policy_list_users_verbose_csv_query_result=$listResult
  current_sid_in_policy_listing=$userListed
  current_sid_subcategory_get_result=$getSubcategoryResult
  current_sid_category_all_get_result=$getCategoryResult
  used_only_current_sid_for_get_queries=$true
  raw_user_policy_inventory_kept_in_memory_only=$true
  auditpol_system_policy_modified=$false
  auditpol_per_user_policy_modified=$false
  user_accounts_or_sid_exported=$false
  auditpol_stdout_stderr_exported=$false
  security_events_or_files_read=$false
  registry_or_clinical_resources_read=$false
  global_kernel_file_etw_used=$false
  file_scoped_policy_proven=$false
  user_policy_configurable_proven=$false
  actual_ilexis_writer_proven=$false
  shared_app_storage_isolation_verified=$false
  clinical_edit_allowed=$false
  verdict='PER_USER_POLICY_READONLY_DIAGNOSTIC_NOT_CAPTURE_AUTHORIZATION'
}
$payload | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $target -Encoding utf8 -ErrorAction Stop
Write-Host "D3E16_POLICY_USER_LIST_QUERY=$listResult"
Write-Host "D3E16_CURRENT_SID_POLICY_LIST_MATCH=$userListed"
Write-Host "D3E16_USER_GET_SUBCATEGORY=$getSubcategoryResult"
Write-Host "D3E16_USER_GET_ALL_CATEGORY=$getCategoryResult"
Write-Host 'D3E16_POLICY_MODIFIED=false'
Write-Host 'D3E16_USER_POLICY_CONFIGURABLE_PROVEN=false'
Write-Host 'D3E16_ILEXIS_WRITER_PROVEN=false'
Write-Host 'CLINICAL_EDIT_ALLOWED=false'
Write-Host 'FAC03_D3=OPEN_RED'
