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
                       [int]$ExpectedCreate) {
    $cred=[System.Management.Automation.PSCredential]::new(
        ('.' + [char]92 + $Username), (ConvertTo-SecureString $Password -AsPlainText -Force)
    )
    $exe=(Get-Command pwsh -ErrorAction Stop).Source
    $arguments='-NoProfile -NonInteractive -File "' + $client +
        '" -PipeName "' + $pipeName + '" -ExpectedSid "' + $ExpectedSid +
        '" -ParentPid ' + $PID + ' -ExpectedOpen ' + $ExpectedOpen +
        ' -ExpectedCreateInstance ' + $ExpectedCreate
    $child=$null
    try {
        $launch=@{ FilePath=$exe; ArgumentList=$arguments; Credential=$cred;
                   PassThru=$true; ErrorAction='Stop' }
        $child=Start-Process @launch
        if ($null -eq $child -or $child.Id -eq $PID) {
            throw 'C05B03R_CHILD_NOT_REAL_PROCESS'
        }
        if (-not $child.WaitForExit(15000)) {
            $child.Kill($true)
            throw 'C05B03R_CHILD_15S_TIMEOUT'
        }
        if ($child.ExitCode -ne 0) {
            throw ('C05B03R_CHILD_OS_PROBE_FAILED_' + $child.ExitCode)
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
    $create=Invoke-ScChecked @('create',$serviceName,'type=','own','start=','demand',
                                'obj=','NT AUTHORITY\LocalService','binPath=',$binPath)
    $createdService=$true
    $null=Invoke-ScChecked @('sidtype',$serviceName,'restricted')
    $configuredSid=Invoke-ScChecked @('qsidtype',$serviceName)
    if ($configuredSid -notmatch 'RESTRICTED') { throw 'C05B03R_NOT_RESTRICTED_SID_TYPE' }
    $sids=Invoke-ScChecked @('showsid',$serviceName)
    $found=[regex]::Match($sids,'S-1-5-80-(?:[0-9]+-){4}[0-9]+')
    if (-not $found.Success) { throw 'C05B03R_CANNOT_GET_WINDOWS_SERVICE_SID' }
    $serviceSid=$found.Value
    $binPath += ' "' + $pipeName + '" ' + $serviceSid + ' ' + $allowedSid
    $null=Invoke-ScChecked @('config',$serviceName,'binPath=',$binPath)
    $null=Invoke-ScChecked @('start',$serviceName)
    Wait-ServiceState $serviceName 'RUNNING' 20
    Write-Output 'C05B03R_REAL_SCM_LOCAL_SERVICE_RESTRICTED_SERVICE_SID_AND_PIPE_RUNNING_PASS'

    Invoke-Child $allowedUser $newPasswordA $allowedSid 0 5
    Write-Output 'C05B03R_REAL_APPROVED_OTHER_USER_PROCESS_DATA_RW_ALLOWED_CREATE_INSTANCE_DENIED_PASS'
    Invoke-Child $deniedUser $newPasswordB $deniedSid 5 5
    Write-Output 'C05B03R_REAL_UNAUTHORIZED_OTHER_USER_PROCESS_ALL_DENIED_PASS'
    Write-Output 'C05B03R_REAL_HOSTED_WINDOWS_SERVICE_LEAST_PRIVILEGE_PASS'
    Write-Output 'C05B03R_REMOTE_SECOND_HOST_TPM_PHYSICAL_CABINET_NOT_TESTED'
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
        Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction Stop
    }
    $newPasswordA=$null
    $newPasswordB=$null
}
