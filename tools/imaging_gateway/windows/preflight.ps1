# LOT06-G — read-only Windows installation gate, NO ACL/key/driver mutation.
# Requires Windows PowerShell 5.1 or PowerShell 7 on Windows.
[CmdletBinding()]
param(
  [string]$WatchDir,
  [string]$StateDir,
  [switch]$SelfTest
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$unsafeSids = @(
  'S-1-1-0',       # Everyone
  'S-1-5-11',      # Authenticated Users
  'S-1-5-32-545',  # BUILTIN\Users
  'S-1-5-32-546',  # BUILTIN\Guests
  'S-1-5-7',       # Anonymous
  'S-1-5-4'        # Interactive
)
# WriteData, AppendData, WriteEA, WriteAttributes, Delete, DeleteSubdirectories,
# WriteDac, WriteOwner, and GenericWrite/GenericAll. Normal read/execute is OK.
$writeMask = [int64](
  [int][System.Security.AccessControl.FileSystemRights]::Write -bor
  [int][System.Security.AccessControl.FileSystemRights]::Delete -bor
  [int][System.Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles -bor
  [int][System.Security.AccessControl.FileSystemRights]::ChangePermissions -bor
  [int][System.Security.AccessControl.FileSystemRights]::TakeOwnership
)

function Test-BroadWriteRules {
  param([object[]]$Rules)
  foreach ($rule in $Rules) {
    if ($rule.Type -ne 'Allow') { continue }
    if (($unsafeSids -contains $rule.Sid) -and
        (([int64]$rule.Mask -band $writeMask) -ne 0)) {
      return $true
    }
  }
  return $false
}

function Convert-RulesToOpaque {
  param([System.Security.AccessControl.FileSystemSecurity]$Acl)
  $rules = @()
  foreach ($rule in $Acl.Access) {
    $sid = $rule.IdentityReference.Translate(
      [System.Security.Principal.SecurityIdentifier]
    ).Value
    $rules += [pscustomobject]@{
      Sid = $sid
      Type = $rule.AccessControlType.ToString()
      Mask = [int64]$rule.FileSystemRights
    }
  }
  return $rules
}

function Test-AncestorReparse {
  param([string]$FullPath)
  $current = [System.IO.DirectoryInfo]::new($FullPath)
  while ($null -ne $current) {
    if (([int]$current.Attributes -band [int][System.IO.FileAttributes]::ReparsePoint) -ne 0) {
      return $true
    }
    $current = $current.Parent
  }
  return $false
}

function Add-Check {
  param(
    [System.Collections.Generic.List[object]]$Checks,
    [string]$Code,
    [bool]$Ok
  )
  $Checks.Add([pscustomobject]@{ code = $Code; ok = $Ok })
}

if ($SelfTest) {
  $write = [int64][System.Security.AccessControl.FileSystemRights]::Write
  $read = [int64][System.Security.AccessControl.FileSystemRights]::Read
  $examples = @(
    [pscustomobject]@{ name='BROAD_ALLOW_WRITE'; rules=@([pscustomobject]@{Sid='S-1-1-0';Type='Allow';Mask=$write}); expected=$true },
    [pscustomobject]@{ name='BROAD_ALLOW_READ'; rules=@([pscustomobject]@{Sid='S-1-1-0';Type='Allow';Mask=$read}); expected=$false },
    [pscustomobject]@{ name='BROAD_DENY_WRITE'; rules=@([pscustomobject]@{Sid='S-1-5-32-545';Type='Deny';Mask=$write}); expected=$false },
    [pscustomobject]@{ name='OWNER_WRITE'; rules=@([pscustomobject]@{Sid='S-1-5-21-1-2-3-1001';Type='Allow';Mask=$write}); expected=$false },
    [pscustomobject]@{ name='AUTH_USERS_WRITE'; rules=@([pscustomobject]@{Sid='S-1-5-11';Type='Allow';Mask=$write}); expected=$true },
    [pscustomobject]@{ name='INTERACTIVE_WRITE'; rules=@([pscustomobject]@{Sid='S-1-5-4';Type='Allow';Mask=$write}); expected=$true }
  )
  $failed = @()
  foreach ($case in $examples) {
    if ([bool](Test-BroadWriteRules -Rules $case.rules) -ne [bool]$case.expected) {
      $failed += $case.name
    }
  }
  [pscustomobject]@{
    contract='DC06G-WINDOWS-PREFLIGHT-SELFTEST-V1'
    count=$examples.Count
    passed=($examples.Count - $failed.Count)
    ok=($failed.Count -eq 0)
    failed=$failed
  } | ConvertTo-Json -Compress -Depth 4
  if ($failed.Count) { exit 1 }
  exit 0
}

$checks = [System.Collections.Generic.List[object]]::new()
$report = [ordered]@{
  contract='DC06G-WINDOWS-PREFLIGHT-V1'
  status='BLOCKED'
  ready_for_install=$false
  clinical_activation_permitted=$false
  key_strategy='ENV_ONLY_UNCERTIFIED'
  checks=@()
}
# Fail closed even if ACL checks are clean: the current agent receives a raw
# 256-bit key via an environment variable; DPAPI binding, escrow, rotation and
# Windows service account ownership are NOT implemented/certified.
$phase = 'START'
try {
  if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
    Add-Check $checks 'WINDOWS_REQUIRED' $false
  } elseif ([string]::IsNullOrWhiteSpace($WatchDir) -or
            [string]::IsNullOrWhiteSpace($StateDir)) {
    Add-Check $checks 'REQUIRED_PATHS_MISSING' $false
  } else {
    $phase = 'PATHS'
    $watch = Get-Item -LiteralPath $WatchDir -Force -ErrorAction Stop
    $state = Get-Item -LiteralPath $StateDir -Force -ErrorAction Stop
    if (-not $watch.PSIsContainer -or -not $state.PSIsContainer) {
      Add-Check $checks 'DIRECTORY_TYPE_INVALID' $false
    } else {
      $wa = [System.IO.Path]::GetFullPath($watch.FullName).TrimEnd('\')
      $st = [System.IO.Path]::GetFullPath($state.FullName).TrimEnd('\')
      $sep = [System.IO.Path]::DirectorySeparatorChar
      $separate = ($wa -ne $st) -and
        (-not $wa.StartsWith($st + $sep, [System.StringComparison]::OrdinalIgnoreCase)) -and
        (-not $st.StartsWith($wa + $sep, [System.StringComparison]::OrdinalIgnoreCase))
      Add-Check $checks 'WATCH_STATE_DISJOINT' $separate

      foreach ($item in @($watch, $state)) {
        Add-Check $checks 'WATCH_OR_STATE_ANCESTORS_NO_REPARSE' (
          -not (Test-AncestorReparse -FullPath $item.FullName)
        )
        $isReparse = (([int]$item.Attributes -band [int][System.IO.FileAttributes]::ReparsePoint) -ne 0)
        Add-Check $checks 'WATCH_OR_STATE_NO_REPARSE' (-not $isReparse)
      }
      $spool = Join-Path $state.FullName 'spool'
      $spoolObj = Get-Item -LiteralPath $spool -Force -ErrorAction Stop
      Add-Check $checks 'SPOOL_IS_DIRECTORY' ([bool]$spoolObj.PSIsContainer)
      Add-Check $checks 'SPOOL_ANCESTORS_NO_REPARSE' (
        -not (Test-AncestorReparse -FullPath $spool)
      )
      Add-Check $checks 'SPOOL_NO_REPARSE' (
        ([int]$spoolObj.Attributes -band [int][System.IO.FileAttributes]::ReparsePoint) -eq 0
      )
      $phase = 'VOLUME'
      $volume = $state.PSDrive.Name
      if ($volume -match '^[A-Za-z]$') {
        $fsName = (Get-Volume -DriveLetter $volume -ErrorAction Stop).FileSystem
        Add-Check $checks 'STATE_VOLUME_NTFS' ($fsName -eq 'NTFS')
      } else {
        Add-Check $checks 'STATE_VOLUME_NTFS' $false
      }
      foreach ($path in @($state.FullName, $spool)) {
        $phase = 'STATE_SPOOL_ACL'
        $acl = Get-Acl -LiteralPath $path -ErrorAction Stop
        $rules = @(Convert-RulesToOpaque -Acl $acl)
        Add-Check $checks 'STATE_ACL_BROAD_WRITE_DENIED' (
          -not (Test-BroadWriteRules -Rules $rules)
        )
        $owner = $acl.Owner
        Add-Check $checks 'STATE_ACL_OWNER_PRESENT' (
          -not [string]::IsNullOrWhiteSpace($owner)
        )
      }
      $dbPath = Join-Path $state.FullName 'acquisitions.sqlite3'
      $phase = 'DATABASE_ACL'
      if (Test-Path -LiteralPath $dbPath -PathType Leaf) {
        $db = Get-Item -LiteralPath $dbPath -Force -ErrorAction Stop
        Add-Check $checks 'DATABASE_NO_REPARSE' (
          ([int]$db.Attributes -band [int][System.IO.FileAttributes]::ReparsePoint) -eq 0
        )
        $dbAcl = Get-Acl -LiteralPath $dbPath -ErrorAction Stop
        Add-Check $checks 'DATABASE_ACL_BROAD_WRITE_DENIED' (
          -not (Test-BroadWriteRules -Rules @(Convert-RulesToOpaque -Acl $dbAcl))
        )
      } else {
        Add-Check $checks 'DATABASE_NOT_INITIALIZED' $false
      }
    }
  }
} catch {
  # Avoid exception details; they may contain absolute paths, account names, etc.
  Add-Check $checks ('INSPECTION_FAILED_' + $phase) $false
}
Add-Check $checks 'DPAPI_DEVICE_KEY_AND_RECOVERY_VERIFIED' $false
Add-Check $checks 'PHYSICAL_NTFS_ACL_FIELD_CERTIFIED' $false
$report.checks=@($checks.ToArray())
$report | ConvertTo-Json -Compress -Depth 6
# Status BLOCKED is a valid read-only finding, not a script execution failure.
exit 0
