# LOT05.7A-C native Windows SCM IPC + detached Ed25519 FUE (no product install).
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:CI -ne 'true' -or
    $env:RUNNER_OS -ne 'Windows' -or $env:LOT05_7A_C_FAKE_ONLY -ne '1') {
    throw '05C_DISPOSABLE_WINDOWS_CI_ONLY'
}
$principal=[Security.Principal.WindowsPrincipal]([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {throw '05C_CI_ADMIN_REQUIRED'}
$callerSid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$nonce=[guid]::NewGuid().ToString('N').Substring(0,12)
$goodName="DC05CG_$nonce"
$badName="DC05CB_$nonce"
$goodPipe="dc05c_good_$nonce"
$badPipe="dc05c_bad_$nonce"
$root=Join-Path $env:ProgramData ("dc05c_fake_$nonce")
$exe=Join-Path $root 'SignedPipeLab.exe'
$protected=Join-Path $root 'protected'
$ledger=Join-Path $protected 'ledger'
$config=Join-Path $protected 'provision.json'
$proof=Join-Path $root 'good_proof.txt'
$badProof=Join-Path $root 'bad_proof.txt'
$source=Join-Path $env:GITHUB_WORKSPACE 'backend\tests\fixtures\lot05_7a_c_windows_scm_signed_noop.cs'
$ticketMaker=Join-Path $env:GITHUB_WORKSPACE 'backend\tests\fixtures\lot05_7a_c_make_tickets.py'
$verifier=Join-Path $env:GITHUB_WORKSPACE 'backend\tests\fixtures\lot05_7a_c_signed_ipc_worker.py'
$pythonVerifier=Join-Path $env:GITHUB_WORKSPACE 'backend\services\legacy_migration_trust_root_v15.py'
$csc=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$python=(python -c 'import sys; print(sys.executable)').Trim()
$created=[System.Collections.Generic.List[string]]::new()
function Strict([string]$program,[string[]]$parameters) {
    $result=& $program @parameters 2>&1
    if ($LASTEXITCODE -ne 0) {throw ('05C_EXTERNAL_FAIL '+$program+' code='+$LASTEXITCODE+' '+($result -join '; '))}
    return ($result -join [Environment]::NewLine)
}
function ServiceSid([string]$name) {
    $sid=([Security.Principal.NTAccount]::new(('NT SERVICE\'+$name))).Translate(
        [Security.Principal.SecurityIdentifier]).Value
    if ($sid -notmatch '^S-1-5-80-') {throw '05C_SERVICE_SID_INVALID'}
    if ((Strict 'sc.exe' @('showsid',$name)) -notmatch [regex]::Escape($sid)) {throw '05C_LSA_SERVICE_SID_INVALID'}
    return $sid
}
function ExactAcl([string]$target,[string]$serviceSid,[string]$rights,[bool]$directory) {
    $acl=Get-Acl -LiteralPath $target
    $acl.SetAccessRuleProtection($true,$false)
    foreach ($old in @($acl.Access)) {$acl.PurgeAccessRules($old.IdentityReference)}
    $inherit=if ($directory) {
        [Security.AccessControl.InheritanceFlags]::ContainerInherit -bor
        [Security.AccessControl.InheritanceFlags]::ObjectInherit
    } else {[Security.AccessControl.InheritanceFlags]::None}
    $allow=[Security.AccessControl.AccessControlType]::Allow
    $none=[Security.AccessControl.PropagationFlags]::None
    foreach ($entry in @(
        @('S-1-5-18',[Security.AccessControl.FileSystemRights]::FullControl),
        @('S-1-5-32-544',[Security.AccessControl.FileSystemRights]::FullControl),
        @($serviceSid,[Security.AccessControl.FileSystemRights]([enum]::Parse(
            [Security.AccessControl.FileSystemRights],$rights)))
    )) {
        $who=[Security.Principal.SecurityIdentifier]::new([string]$entry[0])
        $ace=[Security.AccessControl.FileSystemAccessRule]::new(
            $who,[Security.AccessControl.FileSystemRights]$entry[1],
            [Security.AccessControl.InheritanceFlags]$inherit,$none,$allow)
        $acl.AddAccessRule($ace)
    }
    Set-Acl -LiteralPath $target -AclObject $acl
    $check=Get-Acl -LiteralPath $target
    $ids=@($check.Access | ForEach-Object {
        $_.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
    })
    if (-not ($ids -contains $serviceSid) -or
        $ids -contains 'S-1-5-19' -or $ids -contains 'S-1-1-0' -or
        $ids -contains 'S-1-5-11') {throw ('05C_PROTECTED_ACL_INVALID '+$target)}
}
function Configure([string]$name,[string]$pipe,[string]$allowed,[string]$expected,
                   [string]$serviceSid,[string]$proofPath,[string]$limit) {
    $bin=('"{0}" "{1}" "{2}" "{3}" "{4}" "{5}" "{6}" "{7}" "{8}" "{9}" "{10}" "{11}" "{12}"' -f
        $exe,$name,$pipe,$allowed,$expected,$serviceSid,$proofPath,$python,
        $config,$ledger,$verifier,$pythonVerifier,$limit)
    Strict 'sc.exe' @('config',$name,'binPath=',$bin) | Out-Null
}
function AwaitReady([string]$file) {
    for ($i=0;$i -lt 70;$i++) {
        if (Test-Path -LiteralPath $file -PathType Leaf) {
            $body=Get-Content -LiteralPath $file -Raw
            if ($body.Contains('READY=YES')) {return}
            if ($body.Contains('DENY_SERVICE_ERROR')) {throw ('05C_SERVICE_FAILED '+$body)}
        }
        Start-Sleep -Milliseconds 350
    }
    throw ('05C_SERVICE_NOT_READY '+$file)
}
function Send([string]$pipeName,[string]$ticket) {
    $pipe=[IO.Pipes.NamedPipeClientStream]::new(
        '.',$pipeName,[IO.Pipes.PipeDirection]::InOut,
        [IO.Pipes.PipeOptions]::Asynchronous,
        [Security.Principal.TokenImpersonationLevel]::Impersonation)
    try {
        $pipe.Connect(5000)
        $writer=[IO.StreamWriter]::new($pipe,[Text.Encoding]::ASCII,128,$true)
        $reader=[IO.StreamReader]::new($pipe,[Text.Encoding]::ASCII,$false,128,$true)
        $writer.NewLine=[string][char]10
        $writer.WriteLine($ticket)
        $writer.Flush()
        $task=$reader.ReadLineAsync()
        if (-not $task.Wait(7000)) {throw '05C_REPLY_TIMEOUT'}
        $response=$task.GetAwaiter().GetResult()
        if ($null -eq $response) {throw '05C_EMPTY_PIPE_REPLY'}
        return $response
    } finally {$pipe.Dispose()}
}
function Ticket([string]$name) {
    $path=Join-Path $root ('tickets\'+$name+'.json')
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {throw ('05C_TICKET_MISSING '+$name)}
    return (Get-Content -LiteralPath $path -Raw -Encoding UTF8).Trim()
}
foreach($file in @($source,$ticketMaker,$verifier,$pythonVerifier,$csc,$python)) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {throw ('05C_REQUIRED_FILE_MISSING '+$file)}
}
if (Test-Path -LiteralPath $root) {throw '05C_DISPOSABLE_ROOT_EXISTS'}
New-Item -ItemType Directory -Path $root | Out-Null
try {
    Strict $csc @('/nologo','/target:exe',('/out:'+$exe),
        '/reference:System.ServiceProcess.dll','/reference:System.Core.dll',$source) | Out-Null
    foreach($name in @($goodName,$badName)) {
        Strict 'sc.exe' @('create',$name,'binPath=',('"' + $exe + '"'),
            'type=','own','start=','demand','obj=','NT AUTHORITY\LocalService') | Out-Null
        $created.Add($name)
        Strict 'sc.exe' @('sidtype',$name,'unrestricted') | Out-Null
        if ((Strict 'sc.exe' @('qsidtype',$name)) -notmatch 'SERVICE_SID_TYPE:\s+UNRESTRICTED') {
            throw ('05C_BAD_SCM_SERVICE_SID_TYPE '+$name)
        }
    }
    $goodSid=ServiceSid $goodName
    $badSid=ServiceSid $badName
    Strict 'icacls.exe' @($root,'/inheritance:r','/grant:r',
       '*S-1-5-18:(OI)(CI)F','*S-1-5-32-544:(OI)(CI)F',
       '*S-1-5-19:(OI)(CI)M') | Out-Null
    $env:LOT05_7A_C_FAKE_ONLY='1'
    Strict $python @('-B',$ticketMaker,$root,$goodSid) | Out-Null
    New-Item -ItemType Directory -Path $protected,$ledger | Out-Null
    Move-Item -LiteralPath (Join-Path $root 'provision.json') -Destination $config
    ExactAcl $protected $goodSid 'Modify' $true
    ExactAcl $ledger $goodSid 'Modify' $true
    ExactAcl $config $goodSid 'ReadAndExecute' $false
    Write-Output '05C_SERVICE_SID_PROTECTED_PIN_AND_LEDGER'
    Configure $goodName $goodPipe $callerSid $callerSid $goodSid $proof '10'
    Configure $badName $badPipe $callerSid 'S-1-5-19' $badSid $badProof '1'
    Strict 'sc.exe' @('start',$goodName) | Out-Null
    AwaitReady $proof
    $allowed=Send $goodPipe (Ticket 'valid')
    if($allowed -ne 'NOOP_SIGNED_VERIFIED_NO_CLINICAL_IMPORT') {
        throw ('05C_SIGNED_VALID_NOOP_FAILED '+$allowed+' '+(Get-Content -Raw $proof))
    }
    Write-Output '05C_SIGNED_ED25519_TICKET_ACCEPTED_VIA_OS_AUTHENTICATED_SCM_IPC'
    Strict 'sc.exe' @('stop',$goodName) | Out-Null
    Start-Sleep -Seconds 2
    Strict 'sc.exe' @('start',$goodName) | Out-Null
    $replay=Send $goodPipe (Ticket 'valid')
    if($replay -ne 'DENY') {throw ('05C_RESTART_REPLAY_ACCEPTED '+$replay)}
    Write-Output '05C_REPLAY_AFTER_SCM_RESTART_DENIED'
    foreach ($negative in @('wrong_tenant','wrong_source','wrong_service',
                             'expired','clinical','forged','tampered','malformed')) {
        $denied=Send $goodPipe (Ticket $negative)
        if($denied -ne 'DENY') {throw ('05C_ADVERSARIAL_TICKET_ACCEPTED '+$negative)}
    }
    Write-Output '05C_SIGNED_CONTEXT_EXPIRY_TAMPER_FORGERY_AND_CLINICAL_DENIED'
    Strict 'sc.exe' @('start',$badName) | Out-Null
    AwaitReady $badProof
    $badPeer=Send $badPipe (Ticket 'valid')
    if($badPeer -ne 'DENY') {throw '05C_UNAUTHORIZED_OS_PEER_ACCEPTED'}
    $badLog=Get-Content -LiteralPath $badProof -Raw
    if (-not $badLog.Contains('PEER_MATCH=False') -or
        -not $badLog.Contains('PEER_SID_FROM_OS='+$callerSid)) {
        throw ('05C_MISMATCHED_PEER_NOT_OS_ATTESTED '+$badLog)
    }
    Write-Output '05C_VALID_SIGNATURE_WRONG_OS_PRINCIPAL_DENIED'
    Write-Output '05C_SYNTHETIC_NOOP_ONLY_NO_CLINICAL_IMPORT'
} finally {
    foreach($name in $created) {& sc.exe stop $name 2>&1 | Out-Null}
    Start-Sleep -Seconds 2
    foreach($name in $created) {& sc.exe delete $name 2>&1 | Out-Null}
    Start-Sleep -Seconds 2
    for ($i=0;$i -lt 10;$i++) {
        try {
            if(Test-Path -LiteralPath $root) {Remove-Item -LiteralPath $root -Force -Recurse -ErrorAction Stop}
            break
        } catch {
            if ($i -eq 9) {throw}
            Start-Sleep -Milliseconds 400
        }
    }
    foreach($name in $created) {
        & sc.exe query $name 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {throw ('05C_SCM_CLEANUP_FAILED '+$name)}
    }
    Write-Output '05C_EPHEMERAL_SERVICES_AND_FILES_CLEANED'
}
