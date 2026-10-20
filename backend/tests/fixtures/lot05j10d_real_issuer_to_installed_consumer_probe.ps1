# LOT05/J10D Windows CI only: real J10C SCM-issued ticket -> installed SCM verifier.
# Test-only protected file handoff; NOT an authenticated named-pipe IPC channel.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if($env:CI -ne 'true' -or $env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows' -or
   $env:LOT05J10D_FAKE_SCM_INTEROP_ONLY -ne '1') {throw 'J10D_WINDOWS_CI_ONLY'}
foreach($k in @('LOT05J10D_SOURCE_ROOT','LOT05J10D_OWNER','LOT05J10D_JOB',
               'LOT05J10D_GENERATION','LOT05J10D_MANIFEST')) {
    if([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($k))) {
        throw ('J10D_MISSING_FAKE_INPUT '+$k)
    }
}
function Native([string]$program,[string[]]$argv) {
    $lines=@(& $program @argv 2>&1)
    if($LASTEXITCODE -ne 0) {throw ('J10D_NATIVE_FAIL '+$program+' '+($lines -join ' '))}
}
function Sid([string]$service) {
    return ([Security.Principal.NTAccount]::new('NT SERVICE',$service)).Translate(
        [Security.Principal.SecurityIdentifier]).Value
}
function Acl([string]$path,[string]$serviceSid,[string]$rights,[bool]$dir) {
    $inherit=if($dir) {'(OI)(CI)'}else{''}
    $grant=('*{0}:{1}{2}' -f $serviceSid,$inherit,$rights)
    $sys=('*S-1-5-18:'+ $inherit+'F')
    $admin=('*S-1-5-32-544:'+ $inherit+'F')
    Native 'icacls.exe' @($path,'/inheritance:r','/grant:r',$sys,$admin,$grant)
    $actual=Get-Acl -LiteralPath $path
    $ids=@($actual.Access | ForEach-Object {$_.IdentityReference.Translate(
        [Security.Principal.SecurityIdentifier]).Value})
    if(-not $actual.AreAccessRulesProtected -or $ids.Count -ne 3 -or
       @($ids | Where-Object {$_ -notin @('S-1-5-18','S-1-5-32-544',$serviceSid)}).Count -ne 0) {
        throw 'J10D_ACL_NOT_EXACT'
    }
}
function Configure([string]$service,[string]$report,[string]$ticket,[string]$sid) {
    $cmd=('"{0}" "{1}" "{2}" "{3}" "{4}" "{5}" "{6}" "{7}" "{8}" "{9}" "{10}"' -f
         $exe,$service,$report,$pin,$ticket,$ledger,$env:LOT05J10D_OWNER,
         $env:LOT05J10D_JOB,$env:LOT05J10D_GENERATION,$sid,$env:LOT05J10D_MANIFEST)
    Native 'sc.exe' @('config',$service,'binPath=',$cmd)
}
function StartProof([string]$svc,[string]$path) {
    if(Test-Path -LiteralPath $path) {Remove-Item -LiteralPath $path -Force}
    Native 'sc.exe' @('start',$svc)
    for($i=0;$i -lt 80;$i++) {
        if(Test-Path -LiteralPath $path -PathType Leaf) {
            return (Get-Content -LiteralPath $path -Raw)
        }
        Start-Sleep -Milliseconds 300
    }
    throw 'J10D_SCM_REPORT_TIMEOUT'
}
$tag=[Guid]::NewGuid().ToString('N').Substring(0,10)
$good='DCJ10DV'+$tag
$bad='DCJ10DX'+$tag
$root=Join-Path $env:ProgramData ('lot05j10d_fake_signed_'+$tag)
$data=Join-Path $root 'protected'
$ledger=Join-Path $root 'ledger'
$goodDir=Join-Path $root 'good-evidence'
$badDir=Join-Path $root 'bad-evidence'
$pin=Join-Path $data 'trusted-rsa-public.fake'
$ticket=Join-Path $data 'j10c-signed.json'
$forged=Join-Path $data 'j10c-forged.json'
$exe=Join-Path $root 'signed-consumer.exe'
$first=Join-Path $goodDir 'first.txt'
$replay=Join-Path $goodDir 'replay.txt'
$tamper=Join-Path $goodDir 'tamper.txt'
$hostile=Join-Path $badDir 'hostile.txt'
$created=New-Object 'System.Collections.Generic.List[string]'
try {
    if(Test-Path -LiteralPath $root) {throw 'J10D_ROOT_EXISTS'}
    New-Item -ItemType Directory -Path $root,$data,$ledger,$goodDir,$badDir | Out-Null
    $source=Join-Path $env:GITHUB_WORKSPACE 'backend/tests/fixtures/lot05j10d_windows_real_ticket_consumer.cs'
    $compiler=Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    if(!(Test-Path -LiteralPath $compiler -PathType Leaf)) {throw 'J10D_CSC_MISSING'}
    Native $compiler @('/nologo','/target:exe',('/out:'+$exe),
         '/reference:System.ServiceProcess.dll','/reference:System.Web.Extensions.dll',$source)
    $prepared=Join-Path $env:LOT05J10D_SOURCE_ROOT 'isolated-signed.json'
    $preparedPin=Join-Path $env:LOT05J10D_SOURCE_ROOT 'trusted-rsa-public.fake'
    foreach($file in @($prepared,$preparedPin)) {
        $f=Get-Item -LiteralPath $file -ErrorAction Stop
        if($f.Attributes -band [IO.FileAttributes]::ReparsePoint) {throw 'J10D_HANDOFF_REPARSE'}
    }
    Copy-Item -LiteralPath $prepared -Destination $ticket
    Copy-Item -LiteralPath $preparedPin -Destination $pin
    $signed=Get-Content -LiteralPath $ticket -Raw | ConvertFrom-Json
    if($signed.body -notmatch '^owner=[1-9][0-9]*\|audience=LOT05J10C_SQLCIPHER_FAKE\|') {
        throw 'J10D_WRONG_ISSUER_AUDIENCE'
    }
    $signed.body=$signed.body.Replace(('job='+$env:LOT05J10D_JOB),('job='+('f'*32)))
    if($signed.body -eq ((Get-Content -LiteralPath $ticket -Raw | ConvertFrom-Json).body)) {
        throw 'J10D_TAMPER_NOT_CREATED'
    }
    [IO.File]::WriteAllText($forged,($signed | ConvertTo-Json -Compress))
    foreach($svc in @($good,$bad)) {
        $cmd=('"{0}" "{1}" placeholder' -f $exe,$svc)
        Native 'sc.exe' @('create',$svc,'binPath=',$cmd,'type=','own',
             'start=','demand','obj=','NT AUTHORITY\LocalService')
        $created.Add($svc)
        Native 'sc.exe' @('sidtype',$svc,'unrestricted')
    }
    $goodSid=Sid $good
    $badSid=Sid $bad
    if($goodSid -eq $badSid -or -not $goodSid.StartsWith('S-1-5-80-') -or
       -not $badSid.StartsWith('S-1-5-80-')) {throw 'J10D_SCM_SID_INVALID'}
    Native 'icacls.exe' @($root,'/inheritance:r','/grant:r',
          '*S-1-5-18:(OI)(CI)F','*S-1-5-32-544:(OI)(CI)F','*S-1-5-19:(OI)(CI)RX')
    Acl $data $goodSid 'RX' $true
    Acl $pin $goodSid 'R' $false
    Acl $ticket $goodSid 'R' $false
    Acl $forged $goodSid 'R' $false
    Acl $ledger $goodSid 'M' $true
    Acl $goodDir $goodSid 'M' $true
    Acl $badDir $badSid 'M' $true
    if((Get-FileHash -LiteralPath $pin -Algorithm SHA256).Hash -eq '') {throw 'J10D_PIN_HASH'}
    Write-Output 'J10D_SCM_ISSUED_TICKET_AND_PIN_ACL_PROTECTED'
    Configure $good $first $ticket $goodSid
    $p=StartProof $good $first
    if($p -notmatch 'sid=True' -or $p -notmatch 'verified=True' -or
       $p -notmatch 'first=True' -or $p -notmatch 'replay=False' -or
       $p -notmatch 'clinical_restore_permitted=False') {
        throw ('J10D_FIRST_TICKET_NOT_VERIFIED '+$p)
    }
    Write-Output 'J10D_REAL_ISSUER_TICKET_VERIFIED_IN_INSTALLED_SCM_CONSUMER_DENY_ONLY_PASS'
    Native 'sc.exe' @('stop',$good)
    Start-Sleep -Seconds 1
    Configure $good $replay $ticket $goodSid
    $p=StartProof $good $replay
    if($p -notmatch 'verified=True' -or $p -notmatch 'first=False' -or
       $p -notmatch 'replay=True' -or $p -notmatch 'clinical_restore_permitted=False') {
        throw ('J10D_REPLAY_AFTER_SCM_RESTART_NOT_DENIED '+$p)
    }
    Write-Output 'J10D_ACTUAL_SCM_RESTART_REPLAY_DENIED_PASS'
    Native 'sc.exe' @('stop',$good)
    Start-Sleep -Seconds 1
    Configure $good $tamper $forged $goodSid
    $p=StartProof $good $tamper
    if($p -notmatch 'verified=False' -or $p -notmatch 'first=False' -or
       $p -notmatch 'clinical_restore_permitted=False') {
        throw ('J10D_FORGED_RSA_ACCEPTED '+$p)
    }
    Write-Output 'J10D_REAL_SCM_TAMPER_DENIED_PASS'
    Configure $bad $hostile $ticket $goodSid
    $p=StartProof $bad $hostile
    if($p -notmatch 'sid=False' -or $p -notmatch 'hostile_pin_read=False' -or
       $p -notmatch 'hostile_ledger_write=False' -or
       $p -notmatch 'reason=sid_denied_acl' -or
       $p -notmatch 'clinical_restore_permitted=False') {
        throw ('J10D_HOSTILE_SCM_BYPASS '+$p)
    }
    if(Test-Path -LiteralPath (Join-Path $ledger 'hostile.nonce')) {
        throw 'J10D_HOSTILE_REPLAY_LEDGER_WRITE'
    }
    Write-Output 'J10D_SAME_ACCOUNT_OTHER_SERVICE_SID_CANNOT_READ_PIN_OR_WRITE_LEDGER_PASS'
    Write-Output 'J10D_NO_CLINICAL_APPLY_PASS'
} finally {
    foreach($svc in $created) {& sc.exe stop $svc 2>&1 | Out-Null}
    Start-Sleep -Seconds 1
    foreach($svc in $created) {& sc.exe delete $svc 2>&1 | Out-Null}
    if(Test-Path -LiteralPath $root) {
        Remove-Item -LiteralPath $root -Force -Recurse -ErrorAction SilentlyContinue
    }
}
