# LOT08.2-F: disposable Windows standard-user process, source-only activation FUE.
# NEVER the Digital Crown exe / installer / scheduled task / real cabinet data.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ($env:GITHUB_ACTIONS -ne 'true' -or $env:CI -ne 'true' -or $env:RUNNER_OS -ne 'Windows' -or $env:OS -ne 'Windows_NT') {
    throw 'DISPOSABLE_GITHUB_WINDOWS_ONLY'
}
$principal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'DISPOSABLE_RUNNER_ADMIN_REQUIRED' }
$nonce = [guid]::NewGuid().ToString('N').Substring(0, 10)
$owner = 'dc08fo' + $nonce
$guest = 'dc08fg' + $nonce
$ownerPassword = 'Aa!9-' + [guid]::NewGuid().ToString('N')
$guestPassword = 'Aa!9-' + [guid]::NewGuid().ToString('N')
$root = Join-Path $env:ProgramData ('dc08f-' + [guid]::NewGuid().ToString('N'))
$clone = Join-Path $env:RUNNER_TEMP ('dc08f-restore-' + [guid]::NewGuid().ToString('N'))
$evidence = Join-Path $env:RUNNER_TEMP 'lot08_2_f_windows_user_profile_evidence.json'
$ownerCreated = $false
$guestCreated = $false
$worker = $null
try {
    if (Test-Path -LiteralPath $root) { throw 'LAB_ROOT_NOT_FRESH' }
    New-LocalUser -Name $owner -Password (ConvertTo-SecureString $ownerPassword -AsPlainText -Force) -PasswordNeverExpires -AccountNeverExpires | Out-Null
    $ownerCreated = $true
    New-LocalUser -Name $guest -Password (ConvertTo-SecureString $guestPassword -AsPlainText -Force) -PasswordNeverExpires -AccountNeverExpires | Out-Null
    $guestCreated = $true
    $ownerSid = (Get-LocalUser -Name $owner).SID.Value
    $ownerGroup = Get-LocalGroupMember -Group 'Administrators' -ErrorAction SilentlyContinue | Where-Object { $_.SID.Value -eq $ownerSid }
    if ($ownerGroup) { throw 'OWNER_MUST_BE_NON_ADMIN' }
    New-Item -Path $root -ItemType Directory -Force | Out-Null

    & icacls.exe $root /inheritance:r | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'ROOT_INHERITANCE_FAILED' }
    & icacls.exe $root /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' ("*" + $ownerSid + ':(OI)(CI)M') | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'PER_USER_ROOT_GRANT_FAILED' }
    $source = Join-Path $env:GITHUB_WORKSPACE 'scripts\quality\lot08_2_f_user_process_probe.py'
    $workerPath = Join-Path $root 'user_probe.py'
    Copy-Item -LiteralPath $source -Destination $workerPath
    $python = (Get-Command python.exe -ErrorAction Stop).Source
    $secureOwnerPassword = ConvertTo-SecureString $ownerPassword -AsPlainText -Force
    $credential = [pscredential]::new((".\" + $owner), $secureOwnerPassword)
    $arguments = '"{0}" owner "{1}" "{2}"' -f $workerPath, $root, $ownerSid

    # REAL standard-user Python child process; never launches the product.
    $worker = Start-Process -FilePath $python -ArgumentList $arguments -Credential $credential -LoadUserProfile -WorkingDirectory $env:ProgramData -PassThru
    $deadline = [DateTime]::UtcNow.AddSeconds(45)
    $ready = Join-Path $root 'owner-ready.json'
    while (-not (Test-Path -LiteralPath $ready) -and [DateTime]::UtcNow -lt $deadline) {
        $worker.Refresh()
        if ($worker.HasExited) { throw ('REAL_STANDARD_USER_PROCESS_FAILED_EXIT_' + $worker.ExitCode) }
        Start-Sleep -Milliseconds 250
    }
    if (-not (Test-Path -LiteralPath $ready)) { throw 'USER_PROCESS_READY_TIMEOUT' }
    $ownerReport = Get-Content -LiteralPath $ready -Raw | ConvertFrom-Json
    if ($ownerReport.process_user_sid_verified -ne $true -or $ownerReport.synthetic_files_created_under_user_token -ne 3) {
        throw 'REAL_USER_TOKEN_OR_SQLITE_OWNERSHIP_FAILED'
    }
    # Do not change ACL on an OPEN SQLite file: it is owned by the active
    # standard-user process. The parent folder has an explicit owner/admin/SYSTEM
    # DACL. Actual access denial is probed with guest token + Win32 CreateFileW.
    foreach ($name in @('auth-synthetic.sqlite','devices-synthetic.sqlite','queue-synthetic.sqlite')) {
        $p = Join-Path $root $name
        if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { throw 'OWNER_CREATED_SQLITE_MISSING' }
    }
    & python.exe $source expect-refusal $root $clone COLD_SNAPSHOT_REQUIRES_STOPPED_OWNER
    if ($LASTEXITCODE -ne 0) { throw 'ACTIVE_OWNER_MUST_DENY_RESTORE' }
    $lockTest = @'
import sqlite3,sys
path = sys.argv[1]
try:
    with sqlite3.connect(path, timeout=.15, isolation_level=None) as c:
        c.execute("BEGIN IMMEDIATE")
except sqlite3.OperationalError as exc:
    if "locked" not in str(exc):
        raise
else:
    raise AssertionError("ACTIVE_WRITER_LOCK_WAS_NOT_REAL")
print("REAL_ACTIVE_USER_SQLITE_WRITER_LOCK=PASS")
'@
    $lockTest | & python.exe - (Join-Path $root 'queue-synthetic.sqlite')
    if ($LASTEXITCODE -ne 0) { throw 'SQLITE_EXCLUSIVE_WRITER_NOT_OBSERVED' }
    $env:DC08F_GUEST_PASSWORD = $guestPassword
    try {
        & python.exe $source guest $root $guest
        if ($LASTEXITCODE -ne 0) { throw 'GUEST_NTFS_READ_WRITE_DENIAL_FAILED' }
    } finally {
        Remove-Item Env:DC08F_GUEST_PASSWORD -ErrorAction SilentlyContinue
    }
    Set-Content -LiteralPath (Join-Path $root 'owner-stop.request') -Value 'SYNTHETIC_STOP' -Encoding ASCII
    $worker.WaitForExit(15000) | Out-Null
    $worker.Refresh()
    if (-not $worker.HasExited -or $worker.ExitCode -ne 0) { throw 'CONTROLLED_USER_PROCESS_STOP_FAILED' }
    if (-not (Test-Path -LiteralPath (Join-Path $root 'owner-stopped.json'))) { throw 'OWNER_STOP_PROOF_MISSING' }
    & python.exe $source cold $root $clone
    if ($LASTEXITCODE -ne 0) { throw 'COLD_CLONE_FAILED' }
    & python.exe $source expect-refusal $root $clone RESTORE_NEVER_OVERWRITE
    if ($LASTEXITCODE -ne 0) { throw 'EXISTING_RESTORE_DESTINATION_OVERWRITTEN' }
    & python.exe -c 'import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute("UPDATE lab_epoch SET epoch=7 WHERE id=1"); c.commit(); c.close()' (Join-Path $root 'auth-synthetic.sqlite')
    if ($LASTEXITCODE -ne 0) { throw 'EPOCH_NEGATIVE_FIXTURE_FAILED' }
    $rejectTarget = Join-Path $env:RUNNER_TEMP ('dc08f-refused-' + [guid]::NewGuid().ToString('N'))
    & python.exe $source expect-refusal $root $rejectTarget CROSS_STORE_EPOCH_MISMATCH
    if ($LASTEXITCODE -ne 0) { throw 'DIVERGENT_EPOCH_WAS_NOT_REJECTED' }
    if (Test-Path -LiteralPath $rejectTarget) { throw 'REJECTED_RESTORE_CREATED_FILES' }

    [ordered]@{
        lot = '08.2-F'
        environment = 'disposable-github-windows-server-2022'
        actual_standard_user_child_process_verified = $true
        actual_user_sid_verified_in_child = $true
        actual_three_synthetic_sqlite_created_by_user = $true
        ntfs_untrusted_other_user_read_and_write_denied = $true
        active_writer_and_restore_denial_observed = $true
        stopped_owner_then_offline_clone_verified = $true
        existing_destination_and_epoch_divergence_refused = $true
        no_certified_installer_run = $true
        no_product_activation = $true
        no_patient_data = $true
        clinical_go = $false
    } | ConvertTo-Json | Set-Content -LiteralPath $evidence -Encoding UTF8
    Write-Output 'LOT08F_REAL_STANDARD_USER_TOKEN_AND_COLD_RESTORE_LAB_PASS'
} finally {
    if ($null -ne $worker) {
        try {
            $worker.Refresh()
            if (-not $worker.HasExited) { $worker.Kill(); $worker.WaitForExit(10000) | Out-Null }
        } catch {}
        $worker.Dispose()
    }
    Remove-Item Env:DC08F_GUEST_PASSWORD -ErrorAction SilentlyContinue
    if ($guestCreated) { Remove-LocalUser -Name $guest -ErrorAction SilentlyContinue }
    if ($ownerCreated) { Remove-LocalUser -Name $owner -ErrorAction SilentlyContinue }
    # The ephemeral owner created SQLite files under a restrictive DACL.
    # Reclaim rights solely inside the random ProgramData fixture after
    # stopping its process; never apply these commands to product paths.
    if (Test-Path -LiteralPath $root) {
        & takeown.exe /F $root /R /D Y | Out-Null
        & icacls.exe $root /grant '*S-1-5-32-544:(OI)(CI)F' /T /C | Out-Null
    }
    foreach ($p in @($root,$clone)) {
        for ($retry = 0; $retry -lt 8 -and (Test-Path -LiteralPath $p); $retry++) {
            Remove-Item -LiteralPath $p -Recurse -Force -ErrorAction SilentlyContinue
            if (Test-Path -LiteralPath $p) { Start-Sleep -Milliseconds 250 }
        }
        if (Test-Path -LiteralPath $p) { throw 'DISPOSABLE_WINDOWS_LAB_CLEANUP_FAILED' }
    }
}
