# FAC-03 D3E9: 4 independent disposable Windows trial arms before Facad startup.
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
function Get-Metadata {
  $files=@(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop)
  if($files.Count -gt 5000){throw 'FILE_CAP'}
  $entries=@{}
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
  }
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
  foreach($key in $pre.Keys){
    if(-not $post.ContainsKey($key)){$counts.removed++}
    elseif($pre[$key] -ne $post[$key]){$counts.modified_size_changed++}
  }
  foreach($key in $post.Keys){
    if(-not $pre.ContainsKey($key)){$counts.created++}
  }
  $complete=$true
}catch{
  # No file path, raw metadata, WinEvent, ACL, or caller error detail in logs.
  $complete=$false
}finally{
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
if(-not $complete -or -not $saclRestored -or -not $policyRestored){
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
