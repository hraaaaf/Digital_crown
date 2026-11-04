#Requires -Version 7.0
# LOT06-R one-shot phase-1 fixture. Only ephemeral GitHub-hosted Windows VM.
# Builds test executable at runtime, creates/stops/deletes SCM service and users.
# No patient data, no clinic PC, no permanent service or repo binaries.
$ErrorActionPreference='Stop'
if (-not $IsWindows -or $env:ENVIRONMENT -ne 'test' -or
    $env:DIGITALCROWN_ISOLATED_RUNTIME -ne 'true' -or
    $env:DC06C05B03R_TEST_ONLY -ne '1' -or
    $env:GITHUB_ACTIONS -ne 'true' -or
    $env:RUNNER_OS -ne 'Windows') {
    throw 'C05B03R_HOSTED_WINDOWS_LAB_ONLY'
}
if ($env:DC06B04_RESTART_KEY_TEST -eq '1' -and
    $env:DC06B03_SERVICE_SPOOL -ne '1') {
    throw 'DC06B04_REQUIRES_B03_REAL_SERVICE_SPOOL'
}
if ($env:DC06B06_NATIVE_INVENTORY -eq '1' -and $env:DC06B03_SERVICE_SPOOL -ne '1') {
    throw 'DC06_B06_REQUIRES_B03_ENCRYPTED_SPOOL'
}
if ($env:DC06B06_NATIVE_MEDIA -eq '1' -and
    ($env:DC06B03_SERVICE_SPOOL -ne '1' -or
     $env:DC06B06_NATIVE_INVENTORY -ne '1' -or
     $env:DC06B04_RESTART_KEY_TEST -ne '1')) {
    throw 'DC06_B06_MEDIA_REQUIRES_SERVICE_SPOOL_INVENTORY_AND_RESTART_FUE'
}
if ($env:DC06B05_PACKAGE_ACL_TEST -eq '1' -and
    ($env:DC06B03_SERVICE_SPOOL -ne '1' -or $env:DC06B04_RESTART_KEY_TEST -ne '1')) {
    throw 'DC06B05_REQUIRES_B04_SCOPED_WINDOWS_LAB'
}
$guid=[Guid]::NewGuid().ToString('N')
$serviceName='DC06R' + $guid.Substring(0,11)
$allowedUser='dc06ra' + $guid.Substring(0,8)
$deniedUser='dc06rb' + $guid.Substring(0,8)
$pipeName='\\.\pipe\DigitalCrown-LAB-R-' + $guid
$root=Join-Path $env:ProgramData ('DC06R-LAB-' + $guid)
$bin=Join-Path $root 'bin'
$project=Join-Path $PSScriptRoot 'scm_fixture_c05b03r/ScmPipeFixture.csproj'
$client=Join-Path $PSScriptRoot 'windows_scm_client_c05b03r.ps1'
$createdService=$false
$createdUsers=@()
$createdDir=$false
$b05Phase='PRE_CONFIG'
function Invoke-ScChecked([string[]]$Params) {
    $result=@(& sc.exe @Params)
    if ($LASTEXITCODE -ne 0) {
        throw ('C05B03R_SC_FAIL_' + $Params[0] + '_' + $LASTEXITCODE)
    }
    return ($result -join [Environment]::NewLine)
}
function Wait-ServiceState([string]$Service, [string]$Expected, [int]$LimitSeconds) {
    $until=[DateTime]::UtcNow.AddSeconds($LimitSeconds)
    do {
        $q=@(& sc.exe query $Service) -join [Environment]::NewLine
        if ($LASTEXITCODE -eq 0 -and $q -match ('STATE\s*:\s*\d+\s+' + $Expected)) {
            return
        }
        Start-Sleep -Milliseconds 350
    } while ([DateTime]::UtcNow -lt $until)
    throw ('C05B03R_SCM_STATE_NOT_' + $Expected)
}
function Invoke-Child([string]$Username, [string]$Password,
                       [string]$ExpectedSid, [int]$ExpectedOpen,
                       [int]$ExpectedCreate, [switch]$ProbeQueueReadOnly,
                       [ValidateSet('None','Valid','Tampered','WrongKey')][string]$B03Status='None',
                       [switch]$ProbeB05Package,
                       [ValidateSet('None','Valid','Tampered','WrongKey','Unauthorized')][string]$B06InventoryStatus='None',
                       [ValidateSet('None','Valid','Tampered','WrongKey','Unauthorized')][string]$B06MediaStatus='None') {
    $cred=[System.Management.Automation.PSCredential]::new(
        ('.' + [char]92 + $Username), (ConvertTo-SecureString $Password -AsPlainText -Force)
    )
    $exe=(Get-Command pwsh -ErrorAction Stop).Source
    $arguments='-NoProfile -NonInteractive -File "' + $client +
        '" -PipeName "' + $pipeName + '" -ExpectedSid "' + $ExpectedSid +
        '" -ParentPid ' + $PID + ' -ExpectedOpen ' + $ExpectedOpen +
        ' -ExpectedCreateInstance ' + $ExpectedCreate
    if ($ProbeQueueReadOnly) { $arguments += ' -ProbeQueueReadOnly' }
    if ($B03Status -ne 'None') { $arguments += ' -B03Status ' + $B03Status }
    if ($B06InventoryStatus -ne 'None') { $arguments += ' -B06InventoryStatus ' + $B06InventoryStatus }
    if ($B06MediaStatus -ne 'None') { $arguments += ' -B06MediaStatus ' + $B06MediaStatus }
    if ($ProbeB05Package) {
        $arguments += ' -ProbeB05Package -B05KeyFile "' + $keyPath +
            '" -B05ServiceDll "' + $dll + '" -B05BinDirectory "' + $bin + '"'
    }
    $child=$null
    try {
        $errFile=Join-Path $root ('child-' + $Username + '-stderr.txt')
        $outFile=Join-Path $root ('child-' + $Username + '-stdout.txt')
        $launch=@{ FilePath=$exe; ArgumentList=$arguments; Credential=$cred;
                   PassThru=$true; ErrorAction='Stop';
                   RedirectStandardError=$errFile; RedirectStandardOutput=$outFile }
        $child=Start-Process @launch
        if ($null -eq $child -or $child.Id -eq $PID) {
            throw 'C05B03R_CHILD_NOT_REAL_PROCESS'
        }
        # A Windows hosted runner may cold-start the secondary OS account.
        # Still strictly bounded, fail-closed and NO automatic retry: a
        # child stalled beyond 30s is an explicit failed security FUE.
        if (-not $child.WaitForExit(30000)) {
            $child.Kill($true)
            throw 'C05B03R_CHILD_30S_TIMEOUT'
        }
        if ($child.ExitCode -ne 0) {
            $diagnostic=''
            if (Test-Path -LiteralPath $errFile) {
                $diagnostic=((Get-Content -LiteralPath $errFile -Raw) -replace '[\r\n]+',' ')
            }
            if ($diagnostic.Length -gt 600) { $diagnostic=$diagnostic.Substring(0,600) }
            throw ('C05B03R_CHILD_OS_PROBE_FAILED_' + $child.ExitCode +
                '_CHILD_STDERR_' + $diagnostic)
        }
    }
    finally {
        if ($null -ne $child) {
            if (-not $child.HasExited) { $child.Kill($true) }
            $child.Dispose()
        }
        $cred=$null
    }
}
try {
    New-Item -Path $root -ItemType Directory -Force -ErrorAction Stop | Out-Null
    $createdDir=$true
    $grant=@(& icacls.exe $root /grant '*S-1-5-19:(OI)(CI)RX' /T)
    if ($LASTEXITCODE -ne 0) { throw 'C05B03R_LOCAL_SERVICE_CANNOT_READ_FIXTURE' }
    $newPasswordA='R!7m' + [Guid]::NewGuid().ToString('N') + 'xZ'
    $newPasswordB='R!7m' + [Guid]::NewGuid().ToString('N') + 'yZ'
    foreach ($entry in @(
      @{Name=$allowedUser;Password=$newPasswordA},
      @{Name=$deniedUser;Password=$newPasswordB}
    )) {
        New-LocalUser -Name $entry.Name -Password (
            ConvertTo-SecureString $entry.Password -AsPlainText -Force
        ) -Description 'Digital Crown disposable security CI account' -ErrorAction Stop | Out-Null
        $createdUsers+= $entry.Name
    }
    $allowedSid=(Get-LocalUser -Name $allowedUser -ErrorAction Stop).SID.Value
    $deniedSid=(Get-LocalUser -Name $deniedUser -ErrorAction Stop).SID.Value
    if ($allowedSid -eq $deniedSid) { throw 'C05B03R_USERS_SHARE_SID' }

    $dotnet=(Get-Command dotnet -ErrorAction Stop).Source
    & $dotnet publish $project -c Release -r win-x64 --self-contained false -o $bin
    if ($LASTEXITCODE -ne 0) { throw 'C05B03R_DOTNET_BUILD_FAILED' }
    $dll=Join-Path $bin 'ScmPipeFixture.dll'
    if (-not (Test-Path -LiteralPath $dll)) { throw 'C05B03R_NO_SERVICE_DLL' }
    $binPath='"' + $dotnet + '" "' + $dll + '" --service ' + $serviceName
    # Service SID is derived by SCM from the service name; query before binding.
    $create=Invoke-ScChecked -Params @('create',$serviceName,'type=','own','start=','demand',
                                'obj=','NT AUTHORITY\LocalService','binPath=',$binPath)
    $createdService=$true
    $null=Invoke-ScChecked -Params @('sidtype',$serviceName,'restricted')
    $configuredSid=Invoke-ScChecked -Params @('qsidtype',$serviceName)
    if ($configuredSid -notmatch 'RESTRICTED') { throw 'C05B03R_NOT_RESTRICTED_SID_TYPE' }
    $sids=Invoke-ScChecked -Params @('showsid',$serviceName)
    $found=[regex]::Match($sids,'S-1-5-80-(?:[0-9]+-){4}[0-9]+')
    if (-not $found.Success) { throw 'C05B03R_CANNOT_GET_WINDOWS_SERVICE_SID' }
    $serviceSid=$found.Value
    if ($env:DC06B03_SERVICE_SPOOL -eq '1') {
        # A RESTRICTED service token requires the service SID at every
        # traversed lab-owned ancestor, not only inside private/spool.
        & icacls.exe $root /grant ('*' + $serviceSid + ':(OI)(CI)RX') /T | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'DC06B03_RESTRICTED_SID_ROOT_TRAVERSE_DENIED' }
    }
    if ($env:DC06B05_PACKAGE_ACL_TEST -eq '1') {
        # A restricted service token needs both LocalService and its service
        # SID for RX. The DLL and every published package child deny write
        # access to both pipe-authorized and unapproved user accounts.
        # GitHub-hosted synthetic binary ONLY. Not a production installer.
        & icacls.exe $bin /inheritance:r /grant:r '*S-1-5-19:(OI)(CI)RX' ('*' + $serviceSid + ':(OI)(CI)RX') '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' /T | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'DC06B05_SERVICE_PACKAGE_DACL_FAILED' }
        # File ACEs must be effective on leaf assemblies and deps, not only
        # inheritable ACEs on the directory. Keep the same minimal SIDs.
        $packageFiles=@(Get-ChildItem -LiteralPath $bin -Recurse -File -Force)
        if ($packageFiles.Count -lt 3) { throw 'DC06B05_INCOMPLETE_SYNTHETIC_PACKAGE' }
        foreach ($file in $packageFiles) {
            & icacls.exe $file.FullName /inheritance:r /grant:r '*S-1-5-19:RX' ('*' + $serviceSid + ':RX') '*S-1-5-18:F' '*S-1-5-32-544:F' | Out-Null
            if ($LASTEXITCODE -ne 0) { throw 'DC06B05_PACKAGE_LEAF_DACL_FAILED' }
        }
        Write-Output 'DC06B05_EXPLICIT_SCOPED_PACKAGE_LEAF_ACL_PASS'
        if (-not (Test-Path -LiteralPath $dll -PathType Leaf)) {
            throw 'DC06B05_PROTECTED_SERVICE_DLL_MISSING'
        }
        Write-Output 'DC06B05_PACKAGE_DACL_SERVICE_SID_RX_SYSTEM_ADMIN_F_PASS'
    }
    $binPath += ' "' + $pipeName + '" ' + $serviceSid + ' ' + $allowedSid
    if ($env:DC06B03_SERVICE_SPOOL -eq '1') {
        $python=(Get-Command python -ErrorAction Stop).Source
        $reader=Join-Path $PSScriptRoot 'scm_spool_read_b03.py'
        $watch=Join-Path $root 'incoming'
        $private=Join-Path $root 'private'
        $keyPath=Join-Path $root 'spool-key.lab'
        New-Item -ItemType Directory -Path $watch,$private -Force | Out-Null
        $keyBytes=New-Object byte[] 32
        [System.Security.Cryptography.RandomNumberGenerator]::Fill($keyBytes)
        [System.IO.File]::WriteAllBytes($keyPath,$keyBytes)
        # Apply ACL BEFORE staging any ciphertext or SQLite file; every
        # created child inherits the service and CI-admin DACL atomically.
        # Only synthetic fixture; CABINET secrets must use hardware TPM.
        foreach ($target in @($watch,$private)) {
            & icacls.exe $target /inheritance:r /grant:r ('*S-1-5-19:(OI)(CI)M') ('*' + $serviceSid + ':(OI)(CI)M') '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' | Out-Null
            if ($LASTEXITCODE -ne 0) { throw 'DC06B03_SPOOL_DIRECTORY_ACL_FAILED' }
        }
        & icacls.exe $keyPath /inheritance:r /grant:r '*S-1-5-19:R' ('*' + $serviceSid + ':R') '*S-1-5-18:F' '*S-1-5-32-544:F' | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'DC06B03_KEY_FILE_ACL_FAILED' }
        $env:PYTHONDONTWRITEBYTECODE='1'
        & $python -I $reader seed $watch $private $keyPath DC06B03_SYNTHETIC_ONLY
        if ($LASTEXITCODE -ne 0) { throw 'DC06B03_SYNTHETIC_REAL_SPOOL_SEED_FAILED' }
        # EC diagnostic (native Win32 ERROR_ACCESS_DENIED=5): the spool
        # directory is created by HotFolder AFTER the parent ACL is set.
        # Pin its own exact DACL, including children. This does not grant
        # access to Users, Everyone, any patient or any remote account.
        $spool=Join-Path $private 'spool'
        if (-not (Test-Path -LiteralPath $spool -PathType Container)) {
            throw 'DC06B03_SPOOL_ROOT_MISSING_AFTER_SYNTHETIC_SEED'
        }
        & icacls.exe $spool /inheritance:r /grant:r ('*S-1-5-19:(OI)(CI)M') ('*' + $serviceSid + ':(OI)(CI)M') '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' /T | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'DC06B03_RESTRICTED_SPOOL_ACL_REPAIR_FAILED' }
        Write-Output 'DC06B03_SPOOL_SID_DACL_EXPLICIT_ON_NEW_DIRECTORY'
        # EN = native NtCreateFile relative read refused on the one seeded
        # ciphertext leaf. Hard-pin the explicit leaf DACL too, not just
        # parent inheritance. Only synthetic data on a disposable CI VM.
        $cipherLeaves=@(Get-ChildItem -LiteralPath $spool -File -Filter '*.dc6')
        if ($cipherLeaves.Count -ne 1) { throw 'DC06B03_NOT_EXACTLY_ONE_SYNTHETIC_CIPHER' }
        foreach ($cipherLeaf in $cipherLeaves) {
            & icacls.exe $cipherLeaf.FullName /inheritance:r /grant:r '*S-1-5-19:R' ('*' + $serviceSid + ':R') '*S-1-5-18:F' '*S-1-5-32-544:F' | Out-Null
            if ($LASTEXITCODE -ne 0) { throw 'DC06B03_SYNTHETIC_CIPHER_LEAF_ACL_FAILED' }
        }
        Write-Output 'DC06B03_SYNTHETIC_CIPHER_LEAF_SID_DACL_EXPLICIT'
        $binPath += ' --b03-spool "' + $python + '" "' + $reader + '" "' +
            $watch + '" "' + $private + '" "' + $keyPath + '"'
    }
    $b05Phase='CONFIG'
    $null=Invoke-ScChecked -Params @('config',$serviceName,'binPath=',$binPath)
    $b05Phase='START'
    $null=Invoke-ScChecked -Params @('start',$serviceName)
    $b05Phase='RUNNING_WAIT'
    Wait-ServiceState $serviceName 'RUNNING' 20
    Write-Output 'C05B03R_REAL_SCM_LOCAL_SERVICE_RESTRICTED_SERVICE_SID_AND_PIPE_RUNNING_PASS'

    Invoke-Child $allowedUser $newPasswordA $allowedSid 0 5
    Write-Output 'C05B03R_REAL_APPROVED_OTHER_USER_PROCESS_DATA_RW_ALLOWED_CREATE_INSTANCE_DENIED_PASS'
    if ($env:DC06B02_PROBE -eq '1') {
        Invoke-Child $allowedUser $newPasswordA $allowedSid 0 5 -ProbeQueueReadOnly
        Write-Output 'DC06B02_NATIVE_SCM_Q_U_PEER_PROBE_NOT_CLINICAL_AUTHORITY_PASS'
    }
    if ($env:DC06B03_SERVICE_SPOOL -eq '1') {
        Invoke-Child $allowedUser $newPasswordA $allowedSid 0 5 -B03Status Valid
        Write-Output 'DC06B03_SCM_LOCAL_SERVICE_REALLY_READ_ENCRYPTED_SPOOL_PASS'
        if ($env:DC06B06_NATIVE_INVENTORY -eq '1') {
            Invoke-Child $allowedUser $newPasswordA $allowedSid 0 5 -B06InventoryStatus Valid
            Write-Output 'DC06_B06_NATIVE_SCM_APPROVED_USER_PER_CAPTURE_PASS'
            if ($env:DC06B06_NATIVE_MEDIA -eq '1') {
                Invoke-Child $allowedUser $newPasswordA $allowedSid 0 5 -B06MediaStatus Valid
                # Valid child also executed the actual product bridge
                # against the restricted SCM pipe with cross-tenant denial.
                Write-Output 'DC06_B06_PRODUCT_NATIVE_BRIDGE_REAL_SCM_SCOPED_INVENTORY_PASS'
                Write-Output 'DC06_B06_NATIVE_MEDIA_REAL_WINDOWS_AES_BYTES_PASS'
            }
        }
        if ($env:DC06B05_PACKAGE_ACL_TEST -eq '1') {
            # The same approved Windows user that can query the pipe
            # must NOT be able to read fixture key, overwrite DLL or drop
            # an executable into the SCM binary directory.
            $dllHashBefore=(Get-FileHash -LiteralPath $dll -Algorithm SHA256).Hash
            Invoke-Child $allowedUser $newPasswordA $allowedSid 0 5 -ProbeB05Package
            $dllHashAfter=(Get-FileHash -LiteralPath $dll -Algorithm SHA256).Hash
            if ($dllHashBefore -ne $dllHashAfter) {
                throw 'DC06B05_SERVICE_DLL_HASH_CHANGED_DURING_PROBE'
            }
            Write-Output 'DC06B05_SERVICE_DLL_SHA256_PIN_UNCHANGED_PASS'
            Invoke-Child $allowedUser $newPasswordA $allowedSid 0 5 -B03Status Valid
            Write-Output 'DC06B05_RESTRICTED_LOCAL_SERVICE_S1_AFTER_PACKAGE_LOCK_PASS'
        }
        if ($env:DC06B04_RESTART_KEY_TEST -eq '1') {
            # B04 synthetic-only: restart the real SCM service without reseed,
            # database reset, ciphertext rewrite or new service identity.
            $originalCipher=@(Get-ChildItem -LiteralPath (Join-Path $private 'spool') -File -Filter '*.dc6')
            if ($originalCipher.Count -ne 1) { throw 'DC06B04_EXPECT_ONE_CIPHER_BEFORE_RESTART' }
            $cipherHashBefore=(Get-FileHash -LiteralPath $originalCipher[0].FullName -Algorithm SHA256).Hash
            $null=Invoke-ScChecked -Params @('stop',$serviceName)
            Wait-ServiceState $serviceName 'STOPPED' 15
            Write-Output 'DC06B04_REAL_SCM_STOP_CONFIRMED_PASS'
            $null=Invoke-ScChecked -Params @('start',$serviceName)
            Wait-ServiceState $serviceName 'RUNNING' 20
            Invoke-Child $allowedUser $newPasswordA $allowedSid 0 5 -B03Status Valid
            $cipherHashAfter=(Get-FileHash -LiteralPath $originalCipher[0].FullName -Algorithm SHA256).Hash
            if ($cipherHashBefore -ne $cipherHashAfter) {
                throw 'DC06B04_CIPHERTEXT_CHANGED_DURING_SCM_RESTART'
            }
            Write-Output 'DC06B04_RESTART_SAME_CIPHERTEXT_S1_PASS'
            if ($env:DC06B06_NATIVE_INVENTORY -eq '1') {
                Invoke-Child $allowedUser $newPasswordA $allowedSid 0 5 -B06InventoryStatus Valid
                Write-Output 'DC06_B06_NATIVE_INVENTORY_RESTART_STABLE_PASS'
                if ($env:DC06B06_NATIVE_MEDIA -eq '1') {
                    Invoke-Child $allowedUser $newPasswordA $allowedSid 0 5 -B06MediaStatus Valid
                    Write-Output 'DC06_B06_NATIVE_MEDIA_RESTART_SHA_STABLE_PASS'
                }
            }

            # A different 256-bit synthetic key must be rejected at the AES-GCM
            # authentication stage, not confused with S0 (empty queue).
            # Original key is held in memory for this one-shot CI fixture.
            $badKey=[byte[]]$keyBytes.Clone()
            $badKey[0] = $badKey[0] -bxor 1
            try {
                [System.IO.File]::WriteAllBytes($keyPath,$badKey)
                Invoke-Child $allowedUser $newPasswordA $allowedSid 0 5 -B03Status WrongKey
                Write-Output 'DC06B04_WRONG_KEY_AES_AUTH_FAIL_CLOSED_PASS'
                if ($env:DC06B06_NATIVE_INVENTORY -eq '1') {
                    Invoke-Child $allowedUser $newPasswordA $allowedSid 0 5 -B06InventoryStatus WrongKey
                    Write-Output 'DC06_B06_NATIVE_WRONG_KEY_DENIED_PASS'
                    if ($env:DC06B06_NATIVE_MEDIA -eq '1') {
                        Invoke-Child $allowedUser $newPasswordA $allowedSid 0 5 -B06MediaStatus WrongKey
                        Write-Output 'DC06_B06_NATIVE_MEDIA_WRONG_KEY_DENIED_PASS'
                    }
                }
            }
            finally {
                [System.IO.File]::WriteAllBytes($keyPath,$keyBytes)
                [Array]::Clear($badKey,0,$badKey.Length)
            }
            Invoke-Child $allowedUser $newPasswordA $allowedSid 0 5 -B03Status Valid
            Write-Output 'DC06B04_KEY_RESTORE_SAME_SPOOL_S1_PASS'
        }
        # ciphertext integrity must be checked fresh from disk under the service
        $cipher=Get-ChildItem -LiteralPath (Join-Path $private 'spool') -Filter '*.dc6' |
            Select-Object -First 1
        if ($null -eq $cipher) { throw 'DC06B03_SPOOL_CIPHER_MISSING' }
        $blob=[System.IO.File]::ReadAllBytes($cipher.FullName)
        $blob[$blob.Length-1] = $blob[$blob.Length-1] -bxor 1
        [System.IO.File]::WriteAllBytes($cipher.FullName,$blob)
        Invoke-Child $allowedUser $newPasswordA $allowedSid 0 5 -B03Status Tampered
        # No silent count=0 or any valid queue when ciphertext is damaged.
        Write-Output 'DC06B03_SCM_CORRUPTED_REAL_AES_SPOOL_FAIL_CLOSED_PASS'
        if ($env:DC06B06_NATIVE_INVENTORY -eq '1') {
            Invoke-Child $allowedUser $newPasswordA $allowedSid 0 5 -B06InventoryStatus Tampered
            Write-Output 'DC06_B06_NATIVE_TAMPER_DENIED_PASS'
            if ($env:DC06B06_NATIVE_MEDIA -eq '1') {
                Invoke-Child $allowedUser $newPasswordA $allowedSid 0 5 -B06MediaStatus Tampered
                Write-Output 'DC06_B06_NATIVE_MEDIA_TAMPER_DENIED_PASS'
            }
        }
    }
    Invoke-Child $deniedUser $newPasswordB $deniedSid 5 5
    if ($env:DC06B06_NATIVE_INVENTORY -eq '1') {
        Invoke-Child $deniedUser $newPasswordB $deniedSid 5 5 -B06InventoryStatus Unauthorized
        Write-Output 'DC06_B06_NATIVE_SECOND_USER_DENIED_PASS'
        if ($env:DC06B06_NATIVE_MEDIA -eq '1') {
            Invoke-Child $deniedUser $newPasswordB $deniedSid 5 5 -B06MediaStatus Unauthorized
            Write-Output 'DC06_B06_NATIVE_MEDIA_SECOND_USER_DENIED_PASS'
        }
    }
    Write-Output 'C05B03R_REAL_UNAUTHORIZED_OTHER_USER_PROCESS_ALL_DENIED_PASS'
    Write-Output 'C05B03R_REAL_HOSTED_WINDOWS_SERVICE_LEAST_PRIVILEGE_PASS'
    Write-Output 'C05B03R_REMOTE_SECOND_HOST_TPM_PHYSICAL_CABINET_NOT_TESTED'
}
catch {
    if ($env:DC06B05_PACKAGE_ACL_TEST -eq '1') {
        $class='OTHER'
        if ($_.Exception.Message.StartsWith('C05B03R_SC_FAIL_config_')) { $class='CONFIG_FAIL' }
        if ($_.Exception.Message.StartsWith('C05B03R_SC_FAIL_start_')) { $class='START_FAIL' }
        if ($_.Exception.Message.StartsWith('C05B03R_SCM_STATE_NOT_')) { $class='STATE_FAIL' }
        Write-Output ('DC06B05_PRIMARY_' + $b05Phase + '_' + $class)
    }
    Write-Output 'DC06B05_FAIL_CLOSED'
    throw
}
finally {
    if ($createdService) {
        $null=@(& sc.exe stop $serviceName)
        try { Wait-ServiceState $serviceName 'STOPPED' 12 }
        catch { Write-Output 'C05B03R_SCM_STOP_NOT_CONFIRMED' }
        $null=@(& sc.exe delete $serviceName)
        if ($LASTEXITCODE -ne 0) { throw 'C05B03R_SERVICE_DELETE_FAILED' }
        Write-Output 'C05B03R_DISPOSABLE_SCM_SERVICE_DELETE_REQUESTED'
    }
    foreach ($user in $createdUsers) {
        Remove-LocalUser -Name $user -ErrorAction Stop
    }
    if ($createdDir) {
        # After stopping the disposable service, CI administrator is the
        # cleanup authority. No synthetic key/files may survive the job.
        & icacls.exe $root /grant '*S-1-5-32-544:(OI)(CI)F' /T | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'DC06B03_RESTORE_TEST_CLEANUP_ACL_FAILED' }
        if ($env:DC06B03_SERVICE_SPOOL -eq '1') {
            # Synthetic fixture only: descendants from an existing encrypted
            # collector may carry a protected file-level DACL. Admins regain
            # delete rights here only after the ephemeral SCM service stops.
            $spoolForCleanup=Join-Path $root 'private/spool'
            if (Test-Path -LiteralPath $spoolForCleanup -PathType Container) {
                $leaves=Get-ChildItem -LiteralPath $spoolForCleanup -File -Force -ErrorAction Stop
                foreach ($leaf in $leaves) {
                    & icacls.exe $leaf.FullName /grant '*S-1-5-32-544:F' | Out-Null
                    if ($LASTEXITCODE -ne 0) { throw 'DC06B03_RESTORE_BLOB_CLEANUP_ACL_FAILED' }
                }
            }
        }
        Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction Stop
    }
    $newPasswordA=$null
    $newPasswordB=$null
}
