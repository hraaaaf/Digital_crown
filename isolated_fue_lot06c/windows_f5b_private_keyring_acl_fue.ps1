# Synthetic Windows ACL contract gate; no clinical secrets or activation.
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'WINDOWS_ONLY' }
$root = Join-Path $env:RUNNER_TEMP ('dc06-f5b-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root | Out-Null
$path = Join-Path $root 'synthetic-keyring.json'
try {
  '{"active_media_id":"m1"}' | Set-Content -LiteralPath $path -Encoding utf8
  $current = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
  $sidEveryone = New-Object System.Security.Principal.SecurityIdentifier('S-1-1-0')
  $sidUsers = New-Object System.Security.Principal.SecurityIdentifier('S-1-5-32-545')
  function Assert-PrivateAcl([string]$target) {
    $item = Get-Item -LiteralPath $target -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'KEYRING_REPARSE_DENIED' }
    $acl = Get-Acl -LiteralPath $target
    if ($acl.AreAccessRulesProtected -ne $true) { throw 'KEYRING_INHERITANCE_DENIED' }
    $owner = $acl.GetOwner([System.Security.Principal.SecurityIdentifier])
    if ($owner.Value -ne $current.Value) { throw 'KEYRING_OWNER_DENIED' }
    $rules = $acl.GetAccessRules($true,$true,[System.Security.Principal.SecurityIdentifier])
    foreach ($rule in $rules) {
      if ($rule.AccessControlType -ne [System.Security.AccessControl.AccessControlType]::Allow) { continue }
      if ($rule.IdentityReference.Value -in @($sidEveryone.Value, $sidUsers.Value, 'S-1-5-11', 'S-1-5-7')) {
        throw 'KEYRING_BROAD_ACCESS_DENIED'
      }
      if ($rule.IdentityReference.Value -notin @($current.Value, 'S-1-5-18', 'S-1-5-32-544')) {
        throw 'KEYRING_UNEXPECTED_PRINCIPAL_DENIED'
      }
    }
    return $true
  }
  $acl = Get-Acl -LiteralPath $path
  $acl.SetAccessRuleProtection($true,$false)
  $acl.SetOwner($current)
  $acl.SetAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($current,'FullControl','Allow')))
  Set-Acl -LiteralPath $path -AclObject $acl
  if (-not (Assert-PrivateAcl $path)) { throw 'PRIVATE_ACL_FAILED' }
  Write-Output 'DC06_F5B_PRIVATE_ACL_ACCEPT_PASS'
  $acl = Get-Acl -LiteralPath $path
  $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($sidEveryone,'Read','Allow')))
  Set-Acl -LiteralPath $path -AclObject $acl
  try { Assert-PrivateAcl $path | Out-Null; throw 'BROAD_ACL_ACCEPTED' } catch {
    if ($_.Exception.Message -ne 'KEYRING_BROAD_ACCESS_DENIED') { throw }
  }
  Write-Output 'DC06_F5B_BROAD_ACL_DENIED_PASS'
  $acl = Get-Acl -LiteralPath $path
  $acl.RemoveAccessRuleAll((New-Object System.Security.AccessControl.FileSystemAccessRule($sidEveryone,'Read','Allow')))
  $acl.SetAccessRuleProtection($false,$true)
  Set-Acl -LiteralPath $path -AclObject $acl
  try { Assert-PrivateAcl $path | Out-Null; throw 'INHERITANCE_ACCEPTED' } catch {
    if ($_.Exception.Message -ne 'KEYRING_INHERITANCE_DENIED') { throw }
  }
  Write-Output 'DC06_F5B_INHERITED_ACL_DENIED_PASS'
  $acl = Get-Acl -LiteralPath $path
  $acl.SetAccessRuleProtection($true,$false)
  Set-Acl -LiteralPath $path -AclObject $acl
  $link = Join-Path $root 'link.json'
  New-Item -ItemType SymbolicLink -Path $link -Target $path -ErrorAction SilentlyContinue | Out-Null
  if (Test-Path -LiteralPath $link) {
    try { Assert-PrivateAcl $link | Out-Null; throw 'SYMLINK_ACCEPTED' } catch {
      if ($_.Exception.Message -ne 'KEYRING_REPARSE_DENIED') { throw }
    }
    Write-Output 'DC06_F5B_SYMLINK_DENIED_PASS'
  } else { Write-Output 'DC06_F5B_SYMLINK_SKIPPED_NO_PRIVILEGE' }
  # The product loader remains fail-closed on Windows; ACL checks alone cannot prevent TOCTOU.
  $source = Get-Content -LiteralPath 'backend/services/clinical_media_crypto_v2.py' -Raw
  if (-not $source.Contains('KEYRING_FILE_PLATFORM_UNSUPPORTED')) { throw 'WINDOWS_PRODUCT_GUARD_MISSING' }
  Write-Output 'DC06_F5B_WINDOWS_PRODUCT_FAIL_CLOSED_PASS'
} finally {
  Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
