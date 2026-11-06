# LOT05.7A-B: native Windows SCM LocalService + peer-token named pipe FUE.
# Disposable CI-only service, no cryptographic issuer, no clinical data/operation.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ($env:RUNNER_OS -ne 'Windows' -or $env:GITHUB_ACTIONS -ne 'true' -or
    $env:CI -ne 'true' -or $env:LOT05_7A_B_FAKE_ONLY -ne '1') {
    throw '05B_DISPOSABLE_WINDOWS_CI_ONLY'
}
$principal = [Security.Principal.WindowsPrincipal]([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw '05B_EPHEMERAL_CI_ADMIN_REQUIRED'
}
$callerSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$nonce = [guid]::NewGuid().ToString('N').Substring(0,12)
$goodName = "DC05BG_$nonce"
$badName = "DC05BB_$nonce"
$goodPipe = "dc05b_good_$nonce"
$badPipe = "dc05b_bad_$nonce"
$root = Join-Path $env:ProgramData ("dc05b_fake_$nonce")
$exe = Join-Path $root 'ScmPipeLab.exe'
$source = Join-Path $env:GITHUB_WORKSPACE 'backend\tests\fixtures\lot05_7a_b_windows_scm_pipe_noop.cs'
$csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$goodProof = Join-Path $root 'good_proof.txt'
$badProof = Join-Path $root 'bad_proof.txt'
$created = [System.Collections.Generic.List[string]]::new()

function Strict([string]$program,[string[]]$parameters) {
    $output = & $program @parameters 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw ('05B_EXTERNAL_COMMAND_FAIL '+$program+' code='+$LASTEXITCODE+' '+($output -join '; '))
    }
    return ($output -join [Environment]::NewLine)
}
function AwaitReady([string]$file) {
    for ($try = 0; $try -lt 70; $try++) {
        if (Test-Path -LiteralPath $file -PathType Leaf) {
            $body = Get-Content -LiteralPath $file -Raw
            if ($body.Contains('READY=YES')) { return }
            if ($body.Contains('DENY_SERVER_ERROR')) { throw ('05B_SERVICE_START_FAIL '+$body) }
        }
        Start-Sleep -Milliseconds 350
    }
    throw ('05B_SCM_PIPE_NOT_READY '+$file)
}
function Send([string]$pipeName,[string]$request) {
    $pipe = [IO.Pipes.NamedPipeClientStream]::new(
        '.', $pipeName, [IO.Pipes.PipeDirection]::InOut,
        [IO.Pipes.PipeOptions]::Asynchronous,
        [Security.Principal.TokenImpersonationLevel]::Impersonation)
    try {
        $pipe.Connect(5000)
        $writer = [IO.StreamWriter]::new($pipe,[Text.Encoding]::ASCII,128,$true)
        $reader = [IO.StreamReader]::new($pipe,[Text.Encoding]::ASCII,$false,128,$true)
        $writer.NewLine = "`n"
        $writer.WriteLine($request)
        $writer.Flush()
        $readTask = $reader.ReadLineAsync()
        if (-not $readTask.Wait(5000)) { throw '05B_PIPE_REPLY_TIMEOUT' }
        $value = $readTask.GetAwaiter().GetResult()
        if ($null -eq $value) { throw '05B_UNEXPECTED_EMPTY_PIPE_REPLY' }
        return $value
    } finally { $pipe.Dispose() }
}
function ServiceSid([string]$name) {
    $sid = ([Security.Principal.NTAccount]::new(('NT SERVICE\'+$name))).Translate(
       [Security.Principal.SecurityIdentifier]).Value
    if ($sid -notmatch '^S-1-5-80-') { throw '05B_BAD_SERVICE_SID' }
    return $sid
}
function Configure([string]$name,[string]$pipe,[string]$allowedSid,[string]$expectedSid,
                   [string]$serviceSid,[string]$proof,[string]$count) {
    $bin = ('"{0}" "{1}" "{2}" "{3}" "{4}" "{5}" "{6}" "{7}"' -f
        $exe,$name,$pipe,$allowedSid,$expectedSid,$serviceSid,$proof,$count)
    Strict 'sc.exe' @('config',$name,'binPath=',$bin) | Out-Null
}
if ((Test-Path -LiteralPath $root) -or -not (Test-Path -LiteralPath $source -PathType Leaf) -or
    -not (Test-Path -LiteralPath $csc -PathType Leaf)) {
    throw '05B_INVALID_DISPOSABLE_ROOT_OR_COMPILER'
}
New-Item -ItemType Directory -Path $root | Out-Null
try {
    Strict $csc @('/nologo','/target:exe',('/out:'+$exe),
        '/reference:System.ServiceProcess.dll','/reference:System.Core.dll',$source) | Out-Null
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { throw '05B_NO_SERVICE_BINARY' }
    foreach ($name in @($goodName,$badName)) {
        Strict 'sc.exe' @('create',$name,'binPath=',('"' + $exe + '"'),
            'type=','own','start=','demand','obj=','NT AUTHORITY\LocalService') | Out-Null
        $created.Add($name)
        Strict 'sc.exe' @('sidtype',$name,'unrestricted') | Out-Null
        $type = Strict 'sc.exe' @('qsidtype',$name)
        if ($type -notmatch 'SERVICE_SID_TYPE:\s+UNRESTRICTED') {
            throw ('05B_SERVICE_SID_NOT_UNRESTRICTED '+$name)
        }
    }
    $goodSid = ServiceSid $goodName
    $badSid = ServiceSid $badName
    # Only disposable telemetry/executable directory; NO keys or authorizing job files.
    Strict 'icacls.exe' @($root,'/inheritance:r','/grant:r',
        '*S-1-5-18:(OI)(CI)F','*S-1-5-32-544:(OI)(CI)F',
        '*S-1-5-19:(OI)(CI)M') | Out-Null
    Configure $goodName $goodPipe $callerSid $callerSid $goodSid $goodProof '3'
    Configure $badName $badPipe $callerSid 'S-1-5-19' $badSid $badProof '1'

    Strict 'sc.exe' @('start',$goodName) | Out-Null
    AwaitReady $goodProof
    $ok = Send $goodPipe 'SYNTHETIC_NOOP_V1'
    $claimedSid = Send $goodPipe ('SYNTHETIC_NOOP_V1|sid='+$goodSid)
    $clinical = Send $goodPipe 'IMPORT_PATIENTS'
    if ($ok -ne 'NOOP_VERIFIED_NO_CLINICAL_IMPORT' -or
        $claimedSid -ne 'DENY_SCHEMA' -or $clinical -ne 'DENY_SCHEMA') {
        throw ('05B_ALLOWED_OR_NEGATIVE_PIPE_MISMATCH ok='+$ok+
               ' claimed='+$claimedSid+' clinical='+$clinical)
    }
    $goodLog = Get-Content -LiteralPath $goodProof -Raw
    if ($goodLog -notmatch 'SERVICE_SID_PRESENT=True' -or
        -not $goodLog.Contains('PEER_FROM_OS='+$callerSid) -or
        -not $goodLog.Contains('PEER_MATCH=True') -or
        -not $goodLog.Contains('RESPONSE=DENY_SCHEMA')) {
        throw ('05B_REAL_TOKEN_NOT_ATTESTED '+$goodLog)
    }
    Write-Output '05B_NATIVE_SCM_LOCALSERVICE_SID_VERIFIED'
    Write-Output '05B_NATIVE_NAMED_PIPE_OS_PEER_SID_AUTHENTICATED'
    Write-Output '05B_FORGED_CLAIM_AND_CLINICAL_COMMAND_DENIED'

    Strict 'sc.exe' @('start',$badName) | Out-Null
    AwaitReady $badProof
    $wrong = Send $badPipe 'SYNTHETIC_NOOP_V1'
    $badLog = Get-Content -LiteralPath $badProof -Raw
    if ($wrong -ne 'DENY_PEER' -or
        -not $badLog.Contains('PEER_FROM_OS='+$callerSid) -or
        -not $badLog.Contains('PEER_MATCH=False') -or
        -not $badLog.Contains('SERVICE_SID_PRESENT=True')) {
        throw ('05B_WRONG_OS_PEER_NOT_DENIED '+$wrong+' '+$badLog)
    }
    Write-Output '05B_SAME_REAL_CLIENT_WRONG_ALLOWED_IDENTITY_DENIED'
    Write-Output '05B_ALL_OPERATIONS_SYNTHETIC_NOOP_NO_CLINICAL_IMPORT'
} finally {
    foreach ($service in $created) { & sc.exe stop $service 2>&1 | Out-Null }
    Start-Sleep -Seconds 2
    foreach ($service in $created) { & sc.exe delete $service 2>&1 | Out-Null }
    Start-Sleep -Seconds 2
    for ($i = 0; $i -lt 10; $i++) {
        try {
            if (Test-Path -LiteralPath $root) {
                Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction Stop
            }
            break
        } catch {
            if ($i -eq 9) { throw }
            Start-Sleep -Milliseconds 400
        }
    }
    foreach ($service in $created) {
        & sc.exe query $service 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { throw ('05B_SCM_CLEANUP_INCOMPLETE '+$service) }
    }
    Write-Output '05B_DISPOSABLE_SCM_AND_FILES_CLEANED'
}
