# LOT08.2-D: real disposable Windows NTFS ACL enforcement in a GitHub-hosted runner.
# Uses only random synthetic SQLite. No access to workstation/cabinet or PHI.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if (-not $IsWindows -and -not $env:OS.StartsWith('Windows')) { throw 'WINDOWS_REQUIRED' }
$principal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'WINDOWS_ADMIN_RUNNER_REQUIRED'
}
$root = Join-Path $env:RUNNER_TEMP ('dc8-ntfs-' + [guid]::NewGuid().ToString('N'))
$suffix = [guid]::NewGuid().ToString('N').Substring(0,8)
$serviceName = 'dc8s' + $suffix
$guestName = 'dc8g' + $suffix
$servicePassword = 'Aa!9-' + [guid]::NewGuid().ToString('N')
$guestPassword = 'Aa!9-' + [guid]::NewGuid().ToString('N')
$serviceCreated = $false
$guestCreated = $false
$evidence = Join-Path $env:RUNNER_TEMP 'lot08_2_d_windows_acl_evidence.json'
try {
    New-LocalUser -Name $serviceName -Password (ConvertTo-SecureString $servicePassword -AsPlainText -Force) -PasswordNeverExpires -AccountNeverExpires | Out-Null
    $serviceCreated = $true
    New-LocalUser -Name $guestName -Password (ConvertTo-SecureString $guestPassword -AsPlainText -Force) -PasswordNeverExpires -AccountNeverExpires | Out-Null
    $guestCreated = $true
    $serviceSid = (Get-LocalUser -Name $serviceName).SID.Value
    New-Item -ItemType Directory -Path $root -Force | Out-Null

    & icacls.exe $root /inheritance:r | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'ACL_INHERITANCE_FAILED' }
    & icacls.exe $root /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' ("*" + $serviceSid + ':(OI)(CI)M') | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'ACL_GRANT_FAILED' }

    $env:DC8_ACL_ROOT = $root
    @'
import os, pathlib, sqlite3
root = pathlib.Path(os.environ["DC8_ACL_ROOT"])
for filename in ("auth-synthetic.sqlite", "devices-synthetic.sqlite", "queue-synthetic.sqlite"):
    with sqlite3.connect(root / filename) as db:
        db.execute("CREATE TABLE synthetic_marker(id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        db.execute("INSERT INTO synthetic_marker(value) VALUES (?)", ("NO_PATIENT_DATA",))
'@ | & python -
    if ($LASTEXITCODE -ne 0) { throw 'SYNTHETIC_SQLITE_INIT_FAILED' }

    # Explicit ACL on each SQLite file: no access for untrusted local user.
    Get-ChildItem -LiteralPath $root -Filter '*-synthetic.sqlite' | ForEach-Object {
        & icacls.exe $_.FullName /inheritance:r | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'SQLITE_ACL_INHERITANCE_FAILED' }
        & icacls.exe $_.FullName /grant:r '*S-1-5-18:F' '*S-1-5-32-544:F' ("*" + $serviceSid + ':M') | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'SQLITE_ACL_GRANT_FAILED' }
    }

    $env:DC8_SVC_NAME = $serviceName
    $env:DC8_SVC_PASS = $servicePassword
    $env:DC8_GUEST_NAME = $guestName
    $env:DC8_GUEST_PASS = $guestPassword
    $probe = @'
import ctypes
import os
from pathlib import Path

adv = ctypes.WinDLL("advapi32", use_last_error=True)
kernel = ctypes.WinDLL("kernel32", use_last_error=True)
W = ctypes.c_wchar_p
H = ctypes.c_void_p
adv.LogonUserW.argtypes = [W, W, W, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(H)]
adv.LogonUserW.restype = ctypes.c_int
adv.ImpersonateLoggedOnUser.argtypes = [H]
adv.ImpersonateLoggedOnUser.restype = ctypes.c_int
adv.RevertToSelf.argtypes = []
adv.RevertToSelf.restype = ctypes.c_int
kernel.CreateFileW.argtypes = [W, ctypes.c_uint32, ctypes.c_uint32, H, ctypes.c_uint32, ctypes.c_uint32, H]
kernel.CreateFileW.restype = H
kernel.CloseHandle.argtypes = [H]
kernel.CloseHandle.restype = ctypes.c_int

def allowed(path, mode):
    handle = kernel.CreateFileW(str(path), mode, 7, None, 3, 128, None)
    if handle == H(-1).value:
        err = ctypes.get_last_error()
        if err == 5:
            return False
        raise OSError(err, "Unexpected CreateFileW failure")
    kernel.CloseHandle(handle)
    return True

def check_user(user, password, expected):
    token = H()
    if not adv.LogonUserW(user, ".", password, 2, 0, ctypes.byref(token)):
        raise OSError(ctypes.get_last_error(), "LAB_USER_LOGON_FAILED")
    try:
        if not adv.ImpersonateLoggedOnUser(token):
            raise OSError(ctypes.get_last_error(), "LAB_IMPERSONATION_FAILED")
        try:
            for path in sorted(Path(os.environ["DC8_ACL_ROOT"]).glob("*-synthetic.sqlite")):
                for mode in (0x80000000, 0x40000000):  # GENERIC_READ / GENERIC_WRITE
                    result = allowed(path, mode)
                    if result is not expected:
                        raise AssertionError("WINDOWS_NTFS_ACCESS_MISMATCH: " + path.name)
        finally:
            if not adv.RevertToSelf():
                raise OSError(ctypes.get_last_error(), "REVERT_TOKEN_FAILED")
    finally:
        kernel.CloseHandle(token)

root = Path(os.environ["DC8_ACL_ROOT"])
files = sorted(root.glob("*-synthetic.sqlite"))
assert len(files) == 3
for p in files:
    assert p.read_bytes().startswith(b"SQLite format 3")
    assert allowed(p, 0x80000000) and allowed(p, 0x40000000)
check_user(os.environ["DC8_SVC_NAME"], os.environ["DC8_SVC_PASS"], True)
check_user(os.environ["DC8_GUEST_NAME"], os.environ["DC8_GUEST_PASS"], False)
print("NTFS_3_FILES_ADMIN_AND_SERVICE_RW_GUEST_DENIED=PASS")
'@
    $probePath = Join-Path $root 'acl_impersonation_probe.py'
    Set-Content -LiteralPath $probePath -Value $probe -Encoding UTF8
    & python $probePath
    if ($LASTEXITCODE -ne 0) { throw 'ACL_IMPERSONATION_PROBE_FAILED' }
    # No IDs, passwords, ACL paths or credentials are archived.
    [ordered]@{
        lot = 'LOT08.2-D'
        environment = 'github-hosted-windows-synthetic'
        files_tested = 3
        ntfs_admin_access = $true
        ntfs_service_identity_read_write = $true
        ntfs_untrusted_identity_read_write_denied = $true
        physical_machine_or_cabinet_tested = $false
        clinical_activation = $false
    } | ConvertTo-Json | Set-Content -LiteralPath $evidence -Encoding UTF8
    Write-Output 'WINDOWS_ACL_LAB_PASS'
}
finally {
    foreach ($var in @('DC8_SVC_PASS','DC8_GUEST_PASS','DC8_SVC_NAME','DC8_GUEST_NAME','DC8_ACL_ROOT')) {
        Remove-Item ("Env:" + $var) -ErrorAction SilentlyContinue
    }
    if ($guestCreated) { Remove-LocalUser -Name $guestName -ErrorAction SilentlyContinue }
    if ($serviceCreated) { Remove-LocalUser -Name $serviceName -ErrorAction SilentlyContinue }
    if (Test-Path -LiteralPath $root) {
        Remove-Item -LiteralPath $root -Force -Recurse -ErrorAction SilentlyContinue
    }
}
