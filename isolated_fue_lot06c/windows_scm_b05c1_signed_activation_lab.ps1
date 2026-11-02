#Requires -Version 7.0
# LOT06 B05-C1: disposable GitHub-hosted real Windows SCM signed-stage activation.
# No patient, no production install, no hardware signing authority.
$ErrorActionPreference='Stop'
if (-not $IsWindows -or $env:GITHUB_ACTIONS -ne 'true' -or
    $env:RUNNER_OS -ne 'Windows' -or $env:ENVIRONMENT -ne 'test' -or
    $env:DIGITALCROWN_ISOLATED_RUNTIME -ne 'true' -or
    $env:DC06B05C1_LAB -ne '1') {
    throw 'DC06B05C1_HOSTED_WINDOWS_LAB_ONLY'
}
$guid=[guid]::NewGuid().ToString('N')
$serviceName='DC06R' + $guid.Substring(0,11)
$clientName='dc06rc' + $guid.Substring(0,8)
$pipeName='\\.\pipe\DigitalCrown-LAB-R-' + $guid
$stage=Join-Path $env:ProgramData ('DC06B05C-LAB-' + $guid)
$pin=Join-Path $env:RUNNER_TEMP ('DC06B05C-pub-' + $guid + '.bin')
$admission=Join-Path $PSScriptRoot 'b05c1_admission_lab.py'
$client=Join-Path $PSScriptRoot 'windows_scm_client_c05b03r.ps1'
$project=Join-Path $PSScriptRoot 'scm_fixture_c05b03r/ScmPipeFixture.csproj'
$binary=Join-Path $stage 'ScmPipeFixture.exe'
$serviceCreated=$false
$userCreated=$false
$stageCreated=$false
$serviceSid=''
$clientSid=''

function Invoke-ScChecked([string[]]$Params) {
    $result=@(& sc.exe @Params)
    if ($LASTEXITCODE -ne 0) { throw ('DC06B05C1_SC_FAIL_' + $Params[0] + '_' + $LASTEXITCODE) }
    return ($result -join [Environment]::NewLine)
}
function Assert-ServiceState([string]$State,[int]$Limit=20) {
    $until=[DateTime]::UtcNow.AddSeconds($Limit)
    do {
        $result=(@(& sc.exe query $serviceName) -join [Environment]::NewLine)
        if ($LASTEXITCODE -eq 0 -and $result -match ('STATE\s*:\s*\d+\s+' + $State)) { return }
        Start-Sleep -Milliseconds 350
    } while ([DateTime]::UtcNow -lt $until)
    throw ('DC06B05C1_SCM_NOT_' + $State)
}
function Invoke-Admit([int]$Generation=1) {
    $null=@(& python -I $admission verify $stage $pin $Generation)
    return ($LASTEXITCODE -eq 0)
}
function Start-VerifiedService([int]$Generation=1) {
    # This wrapper is only a LAB launch gate; admins may bypass SCM protection.
    if (-not (Invoke-Admit $Generation)) { return $false }
    $null=Invoke-ScChecked -Params @('start',$serviceName)
    Assert-ServiceState 'RUNNING' 25
    return $true
}
function Assert-BlockedAdmission([string]$Marker,[int]$Generation=1) {
    Assert-ServiceState 'STOPPED' 10
    if (Start-VerifiedService $Generation) { throw ('DC06B05C1_UNEXPECTED_SERVICE_START_' + $Marker) }
    Assert-ServiceState 'STOPPED' 10
    Write-Output ('DC06B05C1_' + $Marker + '_SCM_STAYS_STOPPED_PASS')
}
function Invoke-Tamper([string]$Target,[string]$Marker) {
    $handle=[System.IO.File]::Open($Target,[System.IO.FileMode]::Open,[System.IO.FileAccess]::ReadWrite,[System.IO.FileShare]::None)
    try {
        $oldByte=$handle.ReadByte()
        if ($oldByte -lt 0) { throw 'DC06B05C1_EMPTY_SIGNED_FILE' }
        $null=$handle.Seek(0,[System.IO.SeekOrigin]::Begin)
        $handle.WriteByte([byte]($oldByte -bxor 1))
    }
    finally { $handle.Dispose() }
    try { Assert-BlockedAdmission $Marker }
    finally {
        $restorer=[System.IO.File]::Open($Target,[System.IO.FileMode]::Open,[System.IO.FileAccess]::ReadWrite,[System.IO.FileShare]::None)
        try { $restorer.WriteByte([byte]$oldByte) }
        finally { $restorer.Dispose() }
    }
}
function Assert-RunningBinaryIdentity {
    $row=Get-CimInstance Win32_Service -Filter ("Name='" + $serviceName + "'") -ErrorAction Stop
    if ($null -eq $row -or [int]$row.ProcessId -le 0) { throw 'DC06B05C1_NO_REAL_SCM_PID' }
    $proc=Get-CimInstance Win32_Process -Filter ("ProcessId=" + $row.ProcessId) -ErrorAction Stop
    if ($null -eq $proc -or [string]::IsNullOrEmpty($proc.ExecutablePath)) { throw 'DC06B05C1_NO_REAL_PROCESS_IMAGE' }
    if (-not [string]::Equals([System.IO.Path]::GetFullPath($proc.ExecutablePath),
        [System.IO.Path]::GetFullPath($binary),[StringComparison]::OrdinalIgnoreCase)) {
        throw 'DC06B05C1_PROCESS_NOT_SIGNED_STAGE_EXE'
    }
    Write-Output 'DC06B05C1_REAL_SCM_PROCESS_IMAGE_EQUALS_SIGNED_STAGE_EXE_PASS'
}
function Assert-NativePipePeer([string]$Password) {
    $credential=[System.Management.Automation.PSCredential]::new(
        ('.' + [char]92 + $clientName),(ConvertTo-SecureString $Password -AsPlainText -Force))
    $pwsh=(Get-Command pwsh -ErrorAction Stop).Source
    $stdout=Join-Path $env:RUNNER_TEMP ('DC06B05C1-' + $guid + '-out.txt')
    $stderr=Join-Path $env:RUNNER_TEMP ('DC06B05C1-' + $guid + '-err.txt')
    try {
        $args='-NoProfile -NonInteractive -File "' + $client +
            '" -PipeName "' + $pipeName + '" -ExpectedSid "' + $clientSid +
            '" -ParentPid ' + $PID + ' -ExpectedOpen 0 -ExpectedCreateInstance 5'
        $child=Start-Process -FilePath $pwsh -ArgumentList $args -Credential $credential -PassThru -ErrorAction Stop -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        try {
            if (-not $child.WaitForExit(15000)) {
                $child.Kill($true)
                throw 'DC06B05C1_NATIVE_PEER_TIMEOUT'
            }
            if ($child.ExitCode -ne 0) { throw 'DC06B05C1_NATIVE_PEER_FAILED' }
        }
        finally {
            if (-not $child.HasExited) { $child.Kill($true) }
            $child.Dispose()
        }
        Write-Output 'DC06B05C1_DISTINCT_WINDOWS_ACCOUNT_NATIVE_PIPE_FUE_PASS'
    }
    finally {
        Remove-Item -LiteralPath $stdout,$stderr -Force -ErrorAction SilentlyContinue
        $credential=$null
    }
}
try {
    # Ed25519 private key only in memory, pin outside stage; CI disposable.
    $password='L!7m' + [guid]::NewGuid().ToString('N') + 'cZ'
    New-LocalUser -Name $clientName -Password (ConvertTo-SecureString $password -AsPlainText -Force) -Description 'DC06B05C disposable CI account' -ErrorAction Stop | Out-Null
    $userCreated=$true
    $clientSid=(Get-LocalUser $clientName).SID.Value
    $stageCreated=$true
    & dotnet publish $project -c Release -r win-x64 --self-contained true '-p:PublishSingleFile=true' '-p:DebugType=None' '-p:DebugSymbols=false' -o $stage
    if ($LASTEXITCODE -ne 0) { throw 'DC06B05C1_BUILD_FAILED' }
    if (-not (Test-Path -LiteralPath $binary -PathType Leaf)) { throw 'DC06B05C1_SERVICE_EXE_MISSING' }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'scm_spool_read_b03.py') -Destination (Join-Path $stage 'scm_spool_read_b03.py')
    New-Item -ItemType Directory -Path (Join-Path $stage 'tools') -Force | Out-Null
    Copy-Item -LiteralPath 'tools/imaging_gateway' -Destination (Join-Path $stage 'tools/imaging_gateway') -Recurse
    & python -I $admission seal $stage $pin
    if ($LASTEXITCODE -ne 0) { throw 'DC06B05C1_SIGNING_FAILED' }

    $binPath='"' + $binary + '" --service ' + $serviceName
    $null=Invoke-ScChecked -Params @('create',$serviceName,'type=','own','start=','demand','obj=','NT AUTHORITY\LocalService','binPath=',$binPath)
    $serviceCreated=$true
    $null=Invoke-ScChecked -Params @('sidtype',$serviceName,'restricted')
    $type=Invoke-ScChecked -Params @('qsidtype',$serviceName)
    if ($type -notmatch 'RESTRICTED') { throw 'DC06B05C1_SID_NOT_RESTRICTED' }
    $sidInfo=Invoke-ScChecked -Params @('showsid',$serviceName)
    $match=[regex]::Match($sidInfo,'S-1-5-80-(?:[0-9]+-){4}[0-9]+')
    if (-not $match.Success) { throw 'DC06B05C1_NO_SERVICE_SID' }
    $serviceSid=$match.Value
    # Explicit leaf ACEs required under restricted SCM token; never Users/Everyone.
    & icacls.exe $stage /inheritance:r /grant:r '*S-1-5-19:(OI)(CI)RX' ('*' + $serviceSid + ':(OI)(CI)RX') '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' /T | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'DC06B05C1_ROOT_ACL_FAILED' }
    $leaves=@(Get-ChildItem -LiteralPath $stage -Recurse -File -Force)
    foreach ($leaf in $leaves) {
        & icacls.exe $leaf.FullName /inheritance:r /grant:r '*S-1-5-19:RX' ('*' + $serviceSid + ':RX') '*S-1-5-18:F' '*S-1-5-32-544:F' | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'DC06B05C1_LEAF_ACL_FAILED' }
    }
    Write-Output 'DC06B05C1_RESTRICTED_SID_SCOPED_PACKAGE_ACL_PASS'
    $binPath += ' "' + $pipeName + '" ' + $serviceSid + ' ' + $clientSid
    $null=Invoke-ScChecked -Params @('config',$serviceName,'binPath=',$binPath)
    if (-not (Start-VerifiedService)) { throw 'DC06B05C1_BASELINE_ADMISSION_FAILED' }
    Assert-RunningBinaryIdentity
    Assert-NativePipePeer $password
    $null=Invoke-ScChecked -Params @('stop',$serviceName)
    Assert-ServiceState 'STOPPED' 20
    Invoke-Tamper $binary 'ALTERED_EXE'
    Invoke-Tamper (Join-Path $stage 'scm_spool_read_b03.py') 'ALTERED_HELPER'
    $extra=Join-Path $stage 'unsigned-injected.ps1'
    try {
        [System.IO.File]::WriteAllText($extra,'synthetic only')
        Assert-BlockedAdmission 'UNSIGNED_FILE'
    }
    finally { Remove-Item -LiteralPath $extra -Force -ErrorAction SilentlyContinue }
    Assert-BlockedAdmission 'GENERATION_DOWNGRADE' 2
    if (-not (Start-VerifiedService)) { throw 'DC06B05C1_RESTORED_ADMISSION_FAILED' }
    Assert-RunningBinaryIdentity
    Write-Output 'DC06B05C1_RESTORED_SIGNED_STAGE_REAL_SCM_RESTART_PASS'
    Write-Output 'DC06B05C1_LAB_ONLY_NOT_NATIVE_SCM_ENFORCEMENT_PASS'
}
finally {
    if ($serviceCreated) {
        $null=@(& sc.exe stop $serviceName)
        try { Assert-ServiceState 'STOPPED' 15 }
        catch { Write-Output 'DC06B05C1_CLEANUP_STOP_NOT_CONFIRMED' }
        $null=@(& sc.exe delete $serviceName)
        if ($LASTEXITCODE -ne 0) { throw 'DC06B05C1_SERVICE_DELETE_FAILED' }
        Write-Output 'DC06B05C1_DISPOSABLE_SCM_SERVICE_DELETE_REQUESTED'
    }
    if ($userCreated) { Remove-LocalUser -Name $clientName -ErrorAction Stop }
    if ($stageCreated -and (Test-Path -LiteralPath $stage)) {
        Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction Stop
    }
    Remove-Item -LiteralPath $pin -Force -ErrorAction SilentlyContinue
    $password=$null
}
