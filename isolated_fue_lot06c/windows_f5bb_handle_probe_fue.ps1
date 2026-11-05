$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'WINDOWS_ONLY' }
$root = Join-Path $env:RUNNER_TEMP ('dc06-f5bb-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root | Out-Null
$current = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
$everyone = New-Object System.Security.Principal.SecurityIdentifier('S-1-1-0')
function Set-PrivateAcl([string]$path) {
  $acl = Get-Acl -LiteralPath $path
  $acl.SetAccessRuleProtection($true,$false)
  $acl.SetOwner($current)
  $acl.RemoveAccessRuleAll((New-Object System.Security.AccessControl.FileSystemAccessRule($everyone,'Read','Allow')))
  $acl.SetAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($current,'FullControl','Allow')))
  Set-Acl -LiteralPath $path -AclObject $acl
}
function RunProbe([string]$case, [string]$path) {
  $env:DC06_F5BB_CASE = $case
  $env:DC06_F5BB_TEST_FILE = $path
  @'
import importlib.util
import os
from pathlib import Path
spec = importlib.util.spec_from_file_location(
    "dc06_f5bb_handle", Path("backend/services/windows_keyring_handle_probe.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
case = os.environ["DC06_F5BB_CASE"]
path = os.environ["DC06_F5BB_TEST_FILE"]
if case == "read":
    result = module.read_no_reparse_file(path)
    assert result.decode("utf-8-sig") == '{"synthetic":true}', result
else:
    expected = {
        "oversize": {"KEYRING_FILE_TOO_LARGE"},
        "relative": {"KEYRING_PATH_UNSUPPORTED"},
        "reparse": {"KEYRING_REPARSE_DENIED", "KEYRING_OPEN_DENIED"},
        "parent_reparse": {"KEYRING_REPARSE_DENIED", "KEYRING_OPEN_DENIED"},
        "broad_acl": {"KEYRING_BROAD_ACL_DENIED"},
        "inherited_acl": {"KEYRING_ACL_NOT_PRIVATE"},
    }[case]
    try:
        module.read_no_reparse_file(path)
    except module.WindowsKeyringHandleDenied as exc:
        assert str(exc) in expected, (case, str(exc))
    else:
        raise AssertionError(f"INSECURE_CASE_ACCEPTED:{case}")
print("DC06_F5BB_" + case.upper() + "_PASS")
'@ | python -
  if ($LASTEXITCODE -ne 0) { throw "DC06_F5BB_CASE_FAILED:$case" }
}
try {
  $file = Join-Path $root 'synthetic.json'
  Set-Content -LiteralPath $file -Value '{"synthetic":true}' -NoNewline -Encoding utf8
  Set-PrivateAcl $file
  RunProbe 'read' $file
  Set-Content -LiteralPath $file -Value ('x' * 16385) -NoNewline -Encoding utf8
  RunProbe 'oversize' $file
  RunProbe 'relative' 'relative.json'
  Set-Content -LiteralPath $file -Value '{"synthetic":true}' -NoNewline -Encoding utf8

  $acl = Get-Acl -LiteralPath $file
  $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($everyone,'Read','Allow')))
  Set-Acl -LiteralPath $file -AclObject $acl
  RunProbe 'broad_acl' $file
  Set-PrivateAcl $file

  $acl = Get-Acl -LiteralPath $file
  $acl.SetAccessRuleProtection($false,$true)
  Set-Acl -LiteralPath $file -AclObject $acl
  RunProbe 'inherited_acl' $file
  Set-PrivateAcl $file

  $link = Join-Path $root 'link.json'
  New-Item -ItemType SymbolicLink -Path $link -Target $file -ErrorAction SilentlyContinue | Out-Null
  if (-not (Test-Path -LiteralPath $link)) { throw 'F5BB_FINAL_SYMLINK_FUE_UNAVAILABLE' }
  RunProbe 'reparse' $link

  $parent = Join-Path $root 'realparent'
  New-Item -ItemType Directory -Path $parent | Out-Null
  $nested = Join-Path $parent 'keyring.json'
  Set-Content -LiteralPath $nested -Value '{"synthetic":true}' -NoNewline -Encoding utf8
  Set-PrivateAcl $nested
  $junction = Join-Path $root 'junctionparent'
  New-Item -ItemType Junction -Path $junction -Target $parent -ErrorAction SilentlyContinue | Out-Null
  if (-not (Test-Path -LiteralPath $junction)) { throw 'F5BB_PARENT_JUNCTION_FUE_UNAVAILABLE' }
  RunProbe 'parent_reparse' (Join-Path $junction 'keyring.json')

  $source = Get-Content -LiteralPath 'backend/services/clinical_media_crypto_v2.py' -Raw
  if (-not $source.Contains('KEYRING_FILE_PLATFORM_UNSUPPORTED')) { throw 'WINDOWS_FAIL_CLOSED_MISSING' }
  if (-not $source.Contains('windows_keyring_handle_probe')) { throw 'F5BC_PRODUCT_INTEGRATION_MISSING' }
  Write-Output 'DC06_F5BB_PRODUCT_INTEGRATION_GUARD_PASS'
  Write-Output 'DC06_F5BB_NATIVE_ACL_PARENT_REPARSE_FUE_PASS'
} finally {
  Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
