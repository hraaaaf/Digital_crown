# LOT08.2-E actual Windows SCM service token / per-service SID ACL, disposable LAB.
# GitHub-hosted Windows only, three synthetic SQLite files; no clinic runtime.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($env:OS -ne 'Windows_NT' -or -not $env:RUNNER_TEMP -or -not $env:GITHUB_ACTIONS) { throw 'GITHUB_WINDOWS_RUNNER_REQUIRED' }
$identity = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $identity.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'ADMIN_RUNNER_REQUIRED' }
$svcName = 'dc08e' + [guid]::NewGuid().ToString('N').Substring(0, 8)
$guest = 'dc08eg' + [guid]::NewGuid().ToString('N').Substring(0, 8)
$guestPassword = 'Aa!9-' + [guid]::NewGuid().ToString('N')
$root = Join-Path $env:RUNNER_TEMP ('dc08e-svc-' + [guid]::NewGuid().ToString('N'))
$reportPath = Join-Path $env:RUNNER_TEMP 'lot08_2_e_windows_real_service_evidence.json'
$serviceCreated = $false
$guestCreated = $false
$probeEnvSet = $false
try {
    New-Item -ItemType Directory -Path $root -Force | Out-Null
    $source = Join-Path (Get-Location).Path 'scripts/quality/lot08_2_e_service_probe.py'
    $servicePy = Join-Path $root 'windows_scm_service_probe.py'
    Copy-Item -LiteralPath $source -Destination $servicePy
    $python = (Get-Command python.exe -ErrorAction Stop).Source
    $binary = '"{0}" "{1}" "{2}" "{3}" "{4}" "service-result.json"' -f $python, $servicePy, $svcName, $root, 'SID_PENDING'
    & sc.exe create $svcName binPath= $binary obj= 'NT AUTHORITY\LocalService' type= own start= demand | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'SC_CREATE_FAILED' }
    $serviceCreated = $true
    & sc.exe sidtype $svcName unrestricted | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'SC_SIDTYPE_FAILED' }
    $sidText = & sc.exe showsid $svcName
    if ($LASTEXITCODE -ne 0) { throw 'SC_SHOWSID_FAILED' }
    $match = [regex]::Match(($sidText -join ' '), 'S-1-5-80-(?:\d+-){4}\d+')
    if (-not $match.Success) { throw 'SC_PER_SERVICE_SID_MISSING' }
    $serviceSid = $match.Value
    $binary = '"{0}" "{1}" "{2}" "{3}" "{4}" "service-result.json"' -f $python, $servicePy, $svcName, $root, $serviceSid
    & sc.exe config $svcName binPath= $binary | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'SC_CONFIG_FAILED' }
    $serviceConfig = Get-CimInstance Win32_Service -Filter ("Name='" + $svcName + "'")
    if (-not $serviceConfig -or $serviceConfig.StartName -notmatch 'LocalService') { throw 'SC_SERVICE_ACCOUNT_MISMATCH' }
    & icacls.exe $root /inheritance:r | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'ROOT_INHERITANCE_FAILED' }
    & icacls.exe $root /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' ('*' + $serviceSid + ':(OI)(CI)M') | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'SERVICE_SID_ACL_FAILED' }
    & icacls.exe $servicePy /inheritance:r | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'SERVICE_SCRIPT_INHERITANCE_FAILED' }
    & icacls.exe $servicePy /grant:r '*S-1-5-18:F' '*S-1-5-32-544:F' ('*' + $serviceSid + ':RX') | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'SERVICE_SCRIPT_ACL_FAILED' }

    & python.exe -c 'import sys; from pathlib import Path; from scripts.quality.lot08_2_e_snapshot_lab import create_synthetic_fixture; create_synthetic_fixture(Path(sys.argv[1]))' $root
    if ($LASTEXITCODE -ne 0) { throw 'THREE_SYNTHETIC_DB_INIT_FAILED' }
    foreach ($name in @('auth-synthetic.sqlite','devices-synthetic.sqlite','queue-synthetic.sqlite')) {
        $p = Join-Path $root $name
        & icacls.exe $p /inheritance:r | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'SQLITE_INHERITANCE_FAILED' }
        & icacls.exe $p /grant:r '*S-1-5-18:F' '*S-1-5-32-544:F' ('*' + $serviceSid + ':M') | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'SQLITE_GRANT_FAILED' }
    }
    $serviceResult = Join-Path $root 'service-result.json'
    & sc.exe start $svcName | Out-Null
    $startExit = $LASTEXITCODE
    $deadline = [DateTime]::UtcNow.AddSeconds(45)
    while (-not (Test-Path -LiteralPath $serviceResult) -and [DateTime]::UtcNow -lt $deadline) {
        Start-Sleep -Milliseconds 300
    }
    if (-not (Test-Path -LiteralPath $serviceResult)) { throw ("SC_SERVICE_RESULT_TIMEOUT_START_EXIT_" + $startExit) }
    $result = Get-Content -LiteralPath $serviceResult -Raw | ConvertFrom-Json
    if ($result.status -ne 'success' -or $result.account_sid_is_local_service -ne $true -or $result.per_service_sid_visible_in_actual_service_token -ne $true -or $result.sqlite_three_files_opened_written_by_real_service_token -ne $true) {
        throw ('SC_SERVICE_TOKEN_PROOF_FAILED_' + $result.failure_type)
    }
    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    do {
        $status = Get-CimInstance Win32_Service -Filter ("Name='" + $svcName + "'")
        if ($status.State -eq 'Stopped') { break }
        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $deadline)
    if (-not $status -or $status.State -ne 'Stopped') { throw 'SC_SERVICE_DID_NOT_STOP' }

    New-LocalUser -Name $guest -Password (ConvertTo-SecureString $guestPassword -AsPlainText -Force) -PasswordNeverExpires -AccountNeverExpires | Out-Null
    $guestCreated = $true
    $env:DC8E_GUEST = $guest
    $env:DC8E_PASS = $guestPassword
    $env:DC8E_ROOT = $root
    $probeEnvSet = $true
    @'
import ctypes, os
from pathlib import Path
W, H = ctypes.c_wchar_p, ctypes.c_void_p
adv = ctypes.WinDLL('advapi32', use_last_error=True)
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
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
token = H()
if not adv.LogonUserW(os.environ['DC8E_GUEST'], '.', os.environ['DC8E_PASS'], 2, 0, ctypes.byref(token)):
    raise OSError(ctypes.get_last_error(), 'GUEST_LOGON_FAILED')
try:
    if not adv.ImpersonateLoggedOnUser(token):
        raise OSError(ctypes.get_last_error(), 'GUEST_IMPERSONATION_FAILED')
    try:
        for name in ('auth-synthetic.sqlite', 'devices-synthetic.sqlite', 'queue-synthetic.sqlite'):
            p = Path(os.environ['DC8E_ROOT']) / name
            for flags in (0x80000000, 0x40000000):
                handle = kernel.CreateFileW(str(p), flags, 7, None, 3, 128, None)
                if handle != H(-1).value:
                    kernel.CloseHandle(handle)
                    raise AssertionError('UNTRUSTED_USER_ACCESS_GRANTED')
                if ctypes.get_last_error() != 5:
                    raise OSError(ctypes.get_last_error(), 'UNEXPECTED_ACCESS_FAILURE')
    finally:
        if not adv.RevertToSelf():
            raise OSError(ctypes.get_last_error(), 'REVERT_FAILED')
finally:
    kernel.CloseHandle(token)
print('REAL_SCM_SERVICE_PER_SID_WRITE_AND_GUEST_DENY=PASS')
'@ | & python.exe -
    if ($LASTEXITCODE -ne 0) { throw 'UNTRUSTED_USER_ACL_PROBE_FAILED' }

    [ordered]@{
        lot = 'LOT08.2-E'
        environment = 'github-hosted-windows-server-2022-disposable-SCM'
        actual_scm_service_created_and_started = $true
        service_account_local_service = $true
        per_service_sid_token_verified = $true
        per_service_sid_ntfs_sqlite_write = $true
        untrusted_user_read_write_denied_for_three_files = $true
        synthetic_sqlite_files = 3
        installed_digital_crown_service_tested = $false
        production_machine_tested = $false
        patient_data_used = $false
        clinical_activation = $false
    } | ConvertTo-Json | Set-Content -LiteralPath $reportPath -Encoding UTF8
    Write-Output 'WINDOWS_REAL_SERVICE_IDENTITY_LAB_PASS'
}
finally {
    if ($probeEnvSet) {
        foreach ($key in @('DC8E_GUEST','DC8E_PASS','DC8E_ROOT')) { Remove-Item ('Env:' + $key) -ErrorAction SilentlyContinue }
    }
    if ($serviceCreated) {
        & sc.exe stop $svcName 2>$null | Out-Null
        & sc.exe delete $svcName | Out-Null
    }
    if ($guestCreated) { Remove-LocalUser -Name $guest -ErrorAction SilentlyContinue }
    if (Test-Path -LiteralPath $root) {
        for ($i = 0; $i -lt 12; $i++) {
            Remove-Item -LiteralPath $root -Force -Recurse -ErrorAction SilentlyContinue
            if (-not (Test-Path -LiteralPath $root)) { break }
            Start-Sleep -Milliseconds 300
        }
        if (Test-Path -LiteralPath $root) { throw 'DISPOSABLE_LAB_FILE_CLEANUP_FAILED' }
    }
}
