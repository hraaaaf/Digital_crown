# LOT05.7A-E Windows SCM actual image -> signed manifest lab FUE.
# Disposable GitHub Windows service; never runs clinical code or a real installer.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:CI -ne 'true' -or
    $env:RUNNER_OS -ne 'Windows' -or $env:LOT05_7A_E_FAKE_ONLY -ne '1') {
    throw '05E_WINDOWS_CI_FAKE_ONLY'
}
$principal=[Security.Principal.WindowsPrincipal]([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw '05E_CI_ADMIN_REQUIRED'
}
$callerSid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$nonce=[guid]::NewGuid().ToString('N').Substring(0,12)
$serviceName="DC05E_$nonce"
$pipeName="dc05b_e_$nonce"
$root=Join-Path $env:ProgramData ("dc05e_fake_$nonce")
$exe=Join-Path $root 'MeasuredScmWorker.exe'
$proof=Join-Path $root 'service_probe.txt'
$source=Join-Path $env:GITHUB_WORKSPACE 'backend\tests\fixtures\lot05_7a_b_windows_scm_pipe_noop.cs'
$manifestVerifier=Join-Path $env:GITHUB_WORKSPACE 'backend\services\legacy_migration_install_attestation_v15.py'
$manifestLab=Join-Path $env:GITHUB_WORKSPACE 'backend\tests\fixtures\lot05_7a_e_windows_image_manifest_lab.py'
$csc=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$python=(python -c 'import sys; print(sys.executable)').Trim()
$created=$false
function Strict([string]$program,[string[]]$parameters) {
    $output=& $program @parameters 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw ('05E_EXTERNAL_FAIL '+$program+' exit='+$LASTEXITCODE+' '+($output -join '; '))
    }
    return ($output -join [Environment]::NewLine)
}
function AwaitReady([string]$file) {
    for($i=0;$i -lt 75;$i++) {
        if (Test-Path -LiteralPath $file -PathType Leaf) {
            $value=Get-Content -LiteralPath $file -Raw
            if ($value.Contains('READY=YES')) {return}
            if ($value.Contains('DENY_SERVER_ERROR')) {throw ('05E_WORKER_FAILED '+$value)}
        }
        Start-Sleep -Milliseconds 300
    }
    throw '05E_SERVICE_NOT_READY'
}
function SendNoop([string]$name) {
    $pipe=[IO.Pipes.NamedPipeClientStream]::new(
        '.',$name,[IO.Pipes.PipeDirection]::InOut,
        [IO.Pipes.PipeOptions]::Asynchronous,
        [Security.Principal.TokenImpersonationLevel]::Impersonation)
    try {
        $pipe.Connect(5000)
        $writer=[IO.StreamWriter]::new($pipe,[Text.Encoding]::ASCII,128,$true)
        $reader=[IO.StreamReader]::new($pipe,[Text.Encoding]::ASCII,$false,128,$true)
        $writer.NewLine=[string][char]10
        $writer.WriteLine('SYNTHETIC_NOOP_V1')
        $writer.Flush()
        $task=$reader.ReadLineAsync()
        if (-not $task.Wait(5000)) {throw '05E_PIPE_REPLY_TIMEOUT'}
        return $task.GetAwaiter().GetResult()
    } finally {$pipe.Dispose()}
}
foreach($f in @($source,$manifestVerifier,$manifestLab,$csc,$python)) {
    if (-not (Test-Path -LiteralPath $f -PathType Leaf)) {
        throw ('05E_REQUIRED_DEPENDENCY_MISSING '+$f)
    }
}
if(Test-Path -LiteralPath $root) {throw '05E_TEST_ROOT_ALREADY_EXISTS'}
New-Item -ItemType Directory -Path $root | Out-Null
try {
    Strict $csc @('/nologo','/target:exe',('/out:'+$exe),
        '/reference:System.ServiceProcess.dll','/reference:System.Core.dll',$source) | Out-Null
    if(-not (Test-Path -LiteralPath $exe -PathType Leaf)) {throw '05E_SCMBINARY_NOT_COMPILED'}

    Strict 'sc.exe' @('create',$serviceName,'binPath=',('"' + $exe + '"'),
        'type=','own','start=','demand','obj=','NT AUTHORITY\LocalService') | Out-Null
    $created=$true
    Strict 'sc.exe' @('sidtype',$serviceName,'unrestricted') | Out-Null
    if((Strict 'sc.exe' @('qsidtype',$serviceName)) -notmatch 'SERVICE_SID_TYPE:\s+UNRESTRICTED') {
        throw '05E_REAL_UNRESTRICTED_SID_NOT_CONFIGURED'
    }
    $account=[Security.Principal.NTAccount]::new(('NT SERVICE\'+$serviceName))
    $sid=$account.Translate([Security.Principal.SecurityIdentifier]).Value
    if($sid -notmatch '^S-1-5-80-') {throw '05E_SERVICE_SID_MISSING'}
    if((Strict 'sc.exe' @('showsid',$serviceName)) -notmatch [regex]::Escape($sid)) {
        throw '05E_SCM_SERVICE_SID_MISMATCH'
    }

    Strict 'icacls.exe' @($root,'/inheritance:r','/grant:r',
        '*S-1-5-18:(OI)(CI)F','*S-1-5-32-544:(OI)(CI)F',
        '*S-1-5-19:(OI)(CI)M') | Out-Null
    $command=('"{0}" "{1}" "{2}" "{3}" "{4}" "{5}" "{6}" "{7}"' -f
        $exe,$serviceName,$pipeName,$callerSid,$callerSid,$sid,$proof,'1')
    Strict 'sc.exe' @('config',$serviceName,'binPath=',$command) | Out-Null
    Strict 'sc.exe' @('start',$serviceName) | Out-Null
    AwaitReady $proof

    $svc=$null
    for($i=0;$i -lt 30;$i++) {
        $svc=Get-CimInstance Win32_Service -Filter ("Name='"+$serviceName+"'")
        if($null -ne $svc -and $svc.ProcessId -gt 0 -and $svc.State -eq 'Running') {break}
        Start-Sleep -Milliseconds 200
    }
    if($null -eq $svc -or $svc.ProcessId -le 0 -or $svc.State -ne 'Running') {
        throw '05E_NO_REAL_RUNNING_SCM_PID'
    }
    if($svc.StartName -notmatch '(?i)LocalService') {throw '05E_UNEXPECTED_SERVICE_ACCOUNT'}
    if(-not $svc.PathName.StartsWith(('"'+$exe+'"'),
        [StringComparison]::OrdinalIgnoreCase)) {throw '05E_SCM_BINPATH_NOT_INSTALLED_IMAGE'}

    $pidFromScm=[int]$svc.ProcessId
    $process=Get-Process -Id $pidFromScm -ErrorAction Stop
    $loadedImage=$process.MainModule.FileName
    if([string]::IsNullOrWhiteSpace($loadedImage)) {throw '05E_NO_OS_LOADED_IMAGE_PATH'}
    $fullImage=[IO.Path]::GetFullPath($loadedImage)
    if(-not [string]::Equals($fullImage,[IO.Path]::GetFullPath($exe),
        [StringComparison]::OrdinalIgnoreCase)) {throw '05E_PROCESS_IMAGE_DIFFERS_FROM_SCM_BINPATH'}
    $digest=(Get-FileHash -LiteralPath $fullImage -Algorithm SHA256).Hash.ToLowerInvariant()
    if($digest -notmatch '^[a-f0-9]{64}$') {throw '05E_OS_IMAGE_DIGEST_INVALID'}
    Write-Output '05E_REAL_SCM_PID_MATCHES_OS_PROCESS_LOADED_EXE'
    Write-Output '05E_REAL_WINDOWS_LOADED_IMAGE_SHA256_MEASURED'

    $env:LOT05_7A_E_FAKE_ONLY='1'
    Strict $python @('-B',$manifestLab,$manifestVerifier,
        $serviceName,$sid,$fullImage,$digest) | Write-Output

    $reply=SendNoop $pipeName
    if($reply -ne 'NOOP_VERIFIED_NO_CLINICAL_IMPORT') {
        throw ('05E_UNEXPECTED_SERVICE_NOOP_REPLY '+$reply)
    }
    $report=Get-Content -LiteralPath $proof -Raw
    if(-not $report.Contains('SERVICE_SID_PRESENT=True') -or
       -not $report.Contains('PEER_FROM_OS='+$callerSid) -or
       -not $report.Contains('PEER_MATCH=True') -or
       -not $report.Contains('RESPONSE=NOOP_VERIFIED_NO_CLINICAL_IMPORT')) {
       throw ('05E_SERVICE_TOKEN_IPC_NOT_ATTESTED '+$report)
    }
    Write-Output '05E_REAL_SERVICE_SID_AND_PEER_TOKEN_NOOP_ONLY'
} finally {
    if($created) {
        & sc.exe stop $serviceName 2>&1 | Out-Null
        Start-Sleep -Seconds 2
        & sc.exe delete $serviceName 2>&1 | Out-Null
        Start-Sleep -Seconds 2
    }
    for($i=0;$i -lt 12;$i++) {
        try {
            if(Test-Path -LiteralPath $root) {
                Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction Stop
            }
            break
        } catch {
            if($i -eq 11) {throw}
            Start-Sleep -Milliseconds 500
        }
    }
    if($created) {
        & sc.exe query $serviceName 2>&1 | Out-Null
        if($LASTEXITCODE -eq 0) {throw '05E_EPHEMERAL_SCM_CLEANUP_FAILED'}
    }
    Write-Output '05E_DISPOSABLE_SCM_BINARY_AND_MANIFEST_LAB_CLEANED'
}
