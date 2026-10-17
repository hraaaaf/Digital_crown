#Requires -Version 5.1
<#
F01 EXPERIMENTAL: disposable hosted Windows CI runner, synthetic bytes only.
Two real, distinct standard-user SIDs. NO SCM service/installer/clinical data.
#>
[CmdletBinding()]
param(
    [ValidateSet('Harness','Owner','Peer')][string]$Mode = 'Harness',
    [string]$WorkRoot = '',
    [string]$OwnerSid = '',
    [string]$PeerSid = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-F01([bool]$Good, [string]$Code) {
    if (-not $Good) { throw ('F01_' + $Code) }
}
function Private-Path([string]$Leaf) {
    Join-Path (Join-Path $WorkRoot 'private') $Leaf
}
function F01-Files {
    @(
        (Private-Path 'acquisitions.sqlite3'),
        (Private-Path 'acquisitions.sqlite3-wal'),
        (Private-Path 'acquisitions.sqlite3-shm'),
        (Private-Path 'acquisitions.sqlite3-journal'),
        (Private-Path 'spool\encrypted.synthetic'),
        (Private-Path 'keys\synthetic.key')
    )
}
function Write-Report([string]$Stage, [int]$Assertions) {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    $report = @{
        stage = $Stage
        sid = $identity.User.Value
        assertions = $Assertions
        synthetic = $true
        standard_user = (-not $principal.IsInRole(
            [Security.Principal.WindowsBuiltInRole]::Administrator))
    }
    [IO.File]::WriteAllText((Join-Path $WorkRoot ('report-' + $Stage + '.json')),
        (ConvertTo-Json $report -Compress), [Text.Encoding]::UTF8)
}
function Require-Denied([scriptblock]$Attempt, [string]$Name) {
    try { & $Attempt }
    catch [System.UnauthorizedAccessException] { return }
    throw ('F01_PEER_ACCESS_NOT_DENIED_' + $Name)
}
function Invoke-Icacls([string[]]$Arguments) {
    & icacls.exe @Arguments | Out-Null
    Assert-F01 ($LASTEXITCODE -eq 0) 'ICACLS_COMMAND_FAILED'
}
function Invoke-Child([string]$Stage, [pscredential]$Credential,
                      [string]$Script, [string]$Root, [string]$Owner, [string]$Peer) {
    $arguments = @(
        '-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass',
        '-File', ('"' + $Script + '"'), '-Mode',$Stage,
        '-WorkRoot', ('"' + $Root + '"'), '-OwnerSid',$Owner,'-PeerSid',$Peer
    )
    $process = Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -Credential $Credential -ArgumentList $arguments -WorkingDirectory $Root -PassThru -WindowStyle Hidden
    try {
        if (-not $process.WaitForExit(30000)) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            throw ('F01_CHILD_' + $Stage + '_TIMEOUT')
        }
        $exitCode = $process.ExitCode
    } finally { $process.Dispose() }
    Assert-F01 ($exitCode -eq 0) ('CHILD_' + $Stage + '_FAILED')
    $report = Join-Path $Root ('report-' + $Stage + '.json')
    Assert-F01 (Test-Path -LiteralPath $report -PathType Leaf) ('MISSING_REPORT_' + $Stage)
    Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
}
function Check-Acl([string]$Path, [string[]]$Allowed) {
    $acl = Get-Acl -LiteralPath $Path
    foreach ($ace in $acl.Access) {
        if ($ace.AccessControlType -ne [Security.AccessControl.AccessControlType]::Allow) { continue }
        $sid = $ace.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
        Assert-F01 ($Allowed -contains $sid) 'UNEXPECTED_ACL_ALLOW_SID'
    }
}

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
Assert-F01 ([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT) 'WINDOWS_REQUIRED'
if ($Mode -eq 'Owner') {
    Assert-F01 ($identity.User.Value -eq $OwnerSid) 'OWNER_TOKEN_MISMATCH'
    Assert-F01 (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) 'OWNER_NOT_STANDARD'
    [IO.Directory]::CreateDirectory((Private-Path 'spool')) | Out-Null
    [IO.Directory]::CreateDirectory((Private-Path 'keys')) | Out-Null
    $n = 0
    foreach ($file in F01-Files) {
        [IO.File]::WriteAllBytes($file, [Text.Encoding]::UTF8.GetBytes(
            ('F01_SYNTHETIC_ONLY_' + [IO.Path]::GetFileName($file))))
        $stream = [IO.File]::Open($file, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite)
        try {
            $byte = $stream.ReadByte()
            Assert-F01 ($byte -ge 0) 'POSITIVE_EMPTY_FILE'
            $stream.Position = 0
            $stream.WriteByte([byte]$byte)
        } finally { $stream.Dispose() }
        $n++
    }
    Write-Report 'Owner' $n
    return
}
if ($Mode -eq 'Peer') {
    Assert-F01 ($identity.User.Value -eq $PeerSid -and $OwnerSid -ne $PeerSid) 'PEER_TOKEN_MISMATCH'
    Assert-F01 (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) 'PEER_NOT_STANDARD'
    $n = 0
    foreach ($file in F01-Files) {
        $probe = $file
        Require-Denied {
            $stream = [IO.File]::Open($probe, [IO.FileMode]::Open, [IO.FileAccess]::Read)
            $stream.Dispose()
        } 'READ'
        $n++
        Require-Denied {
            $stream = [IO.File]::Open($probe, [IO.FileMode]::Open, [IO.FileAccess]::Write)
            $stream.Dispose()
        } 'WRITE'
        $n++
        Require-Denied { [IO.File]::Move($probe, ($probe + '.peer-moved')) } 'RENAME'
        $n++
    }
    Require-Denied {
        [IO.File]::WriteAllText((Private-Path 'new-peer-created.txt'), 'synthetic')
    } 'CREATE_NEW'
    $n++
    Write-Report 'Peer' $n
    return
}

Assert-F01 ($env:CI -eq 'true' -and $env:GITHUB_ACTIONS -eq 'true') 'CI_ONLY'
Assert-F01 $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) 'RUNNER_ADMIN_REQUIRED'
$tag = [Guid]::NewGuid().ToString('N').Substring(0,8)
$ownerName = 'dcf01o' + $tag
$peerName = 'dcf01p' + $tag
$work = Join-Path $env:PUBLIC ('dc-f01-ci-' + $tag)
$WorkRoot = $work
$ownerUser = $null
$peerUser = $null
$cleanupFailure = $null
$mainFailure = $null
try {
    $random = New-Object byte[] 32
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($random)
    $ownerPassword = 'Ac1!' + [Convert]::ToBase64String($random).Replace('+','X').Replace('/','Y')
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($random)
    $peerPassword = 'Ac1!' + [Convert]::ToBase64String($random).Replace('+','X').Replace('/','Y')
    $ownerCredential = [pscredential]::new(('.\' + $ownerName),
        (ConvertTo-SecureString $ownerPassword -AsPlainText -Force))
    $peerCredential = [pscredential]::new(('.\' + $peerName),
        (ConvertTo-SecureString $peerPassword -AsPlainText -Force))
    $ownerUser = New-LocalUser -Name $ownerName -Password $ownerCredential.Password -Description 'Disposable F01 CI user; delete'
    $peerUser = New-LocalUser -Name $peerName -Password $peerCredential.Password -Description 'Disposable F01 CI peer; delete'
    $owner = $ownerUser.SID.Value
    $peer = $peerUser.SID.Value
    Assert-F01 ($owner -ne $peer -and $owner -ne $identity.User.Value -and
                $peer -ne $identity.User.Value) 'DISTINCT_ACCOUNT_SIDS_REQUIRED'
    New-Item -Path $work -ItemType Directory | Out-Null
    $runner = Join-Path $work 'f01-probe.ps1'
    Copy-Item -LiteralPath $PSCommandPath -Destination $runner
    Invoke-Icacls -Arguments @($work, '/grant', ('*' + $owner + ':(OI)(CI)M'),
        ('*' + $peer + ':(OI)(CI)M'))
    $private = Join-Path $work 'private'
    New-Item -Path $private -ItemType Directory | Out-Null
    Invoke-Icacls -Arguments @($private, '/inheritance:r')
    Invoke-Icacls -Arguments @($private, '/grant:r',
        ('*' + $owner + ':(OI)(CI)M'),
        '*S-1-5-18:(OI)(CI)F', '*S-1-5-32-544:(OI)(CI)F')
    $acl = Get-Acl -LiteralPath $private
    Assert-F01 $acl.AreAccessRulesProtected 'PRIVATE_DACL_NOT_PROTECTED'
    $drive = [IO.DriveInfo]::new(([IO.Path]::GetPathRoot($private)))
    Assert-F01 ($drive.DriveFormat -eq 'NTFS') 'VOLUME_NOT_NTFS'
    $allowed = @($owner,'S-1-5-18','S-1-5-32-544')
    Check-Acl $private $allowed
    $yes = Invoke-Child 'Owner' $ownerCredential $runner $work $owner $peer
    Assert-F01 ($yes.sid -eq $owner -and $yes.standard_user -and [int]$yes.assertions -eq 6) 'OWNER_POSITIVE_FAILED'
    $hashes = @{}
    foreach ($file in F01-Files) {
        Assert-F01 (Test-Path -LiteralPath $file -PathType Leaf) 'MISSING_FILE'
        Check-Acl $file $allowed
        $hashes[$file] = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash
    }
    $no = Invoke-Child 'Peer' $peerCredential $runner $work $owner $peer
    Assert-F01 ($no.sid -eq $peer -and $no.standard_user -and [int]$no.assertions -eq 19) 'PEER_DENIAL_FAILED'
    foreach ($file in F01-Files) {
        Assert-F01 ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -eq $hashes[$file]) 'HASH_CHANGED'
    }
    Assert-F01 (-not (Test-Path -LiteralPath (Private-Path 'new-peer-created.txt'))) 'PEER_CREATED_FILE'
    # Never report a PASS before account/file cleanup finishes.
} catch {
    $mainFailure = $_
} finally {
    if ($work -and (Test-Path -LiteralPath $work)) {
        try { Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction Stop }
        catch { $cleanupFailure = 'F01_CLEANUP_FILES_FAILED' }
    }
    if ($peerUser) {
        try { Remove-LocalUser -Name $peerName -ErrorAction Stop }
        catch { $cleanupFailure = 'F01_CLEANUP_PEER_ACCOUNT_FAILED' }
    }
    if ($ownerUser) {
        try { Remove-LocalUser -Name $ownerName -ErrorAction Stop }
        catch { $cleanupFailure = 'F01_CLEANUP_OWNER_ACCOUNT_FAILED' }
    }
}
if ($cleanupFailure) { throw $cleanupFailure }
if ($mainFailure) { throw $mainFailure }
    Write-Host 'F01_CROSS_SID_LAB=PASS'
    Write-Host 'F01_DISTINCT_STANDARD_USER_TOKENS=PASS'
    Write-Host 'F01_PROTECTED_NTFS_DACL=PASS'
    Write-Host 'F01_OWNER_POSITIVE_FILE_IO=6/6'
    Write-Host 'F01_PEER_NEGATIVE_FILE_IO=19/19'
    Write-Host 'F01_SYNTHETIC_SHA256_UNCHANGED=6/6'
    Write-Host 'F01_SCM_SERVICE_SID=NOT_TESTED'
    Write-Host 'F01_COMMERCIAL_CERTIFICATION=NOT_AUTHORIZED'
