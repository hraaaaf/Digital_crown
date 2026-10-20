# LOT05/J10D, disposable CI Windows SCM authenticated transport relay; DENY-only.
# J10C signed a synthetic manifest/JWT ticket in its original SCM; this probe
# authenticates a NEW transport relay Service SID, not original issuer SID.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if($env:CI -ne 'true' -or $env:GITHUB_ACTIONS -ne 'true' -or
   $env:RUNNER_OS -ne 'Windows' -or $env:LOT05J10D_FAKE_SCM_INTEROP_ONLY -ne '1') {
    throw 'J10D_PIPE_WINDOWS_CI_ONLY'
}
foreach($key in @('LOT05J10D_SOURCE_ROOT','LOT05J10D_OWNER','LOT05J10D_JOB',
                   'LOT05J10D_GENERATION','LOT05J10D_MANIFEST')) {
    if([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($key))) {
        throw ('J10D_PIPE_MISSING_'+$key)
    }
}
function Native([string]$app,[string[]]$argv) {
    $result=@(& $app @argv 2>&1)
    if($LASTEXITCODE -ne 0) {throw ('J10D_PIPE_NATIVE_FAIL '+$app+' '+($result -join ' '))}
}
function Sid([string]$name) {
    $sid=([Security.Principal.NTAccount]::new('NT SERVICE',$name)).Translate(
        [Security.Principal.SecurityIdentifier]).Value
    if(-not $sid.StartsWith('S-1-5-80-')) {throw 'J10D_PIPE_NO_SID'}
    return $sid
}
function Protect([string]$path,[string]$sid,[string]$rights,[bool]$dir) {
    $suffix=if($dir){'(OI)(CI)'}else{''}
    Native 'icacls.exe' @($path,'/inheritance:r','/grant:r',
        ('*S-1-5-18:'+ $suffix+'F'),('*S-1-5-32-544:'+ $suffix+'F'),
        ('*'+$sid+':'+$suffix+$rights))
    $acl=Get-Acl -LiteralPath $path
    $ids=@($acl.Access | ForEach-Object {
        $_.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
    })
    if(!$acl.AreAccessRulesProtected -or $ids.Count -ne 3 -or
       @($ids | Where-Object {$_ -notin @('S-1-5-18','S-1-5-32-544',$sid)}).Count -ne 0) {
        throw ('J10D_PIPE_ACL_UNSAFE '+$path)
    }
}
function StartReport([string]$name,[string]$report) {
    if(Test-Path -LiteralPath $report) {Remove-Item -LiteralPath $report -Force}
    Native 'sc.exe' @('start',$name)
    $service=Get-Service -Name $name -ErrorAction Stop
    $service.WaitForStatus('Running',[TimeSpan]::FromSeconds(15))
    for($i=0;$i -lt 100;$i++) {
        if(Test-Path -LiteralPath $report -PathType Leaf) {
            return (Get-Content -LiteralPath $report -Raw)
        }
        Start-Sleep -Milliseconds 200
    }
    throw ('J10D_PIPE_REPORT_TIMEOUT '+$name)
}
function StopLab([string]$name) {
    Native 'sc.exe' @('stop',$name)
    (Get-Service -Name $name -ErrorAction Stop).WaitForStatus(
        'Stopped',[TimeSpan]::FromSeconds(15))
}
$tag=[Guid]::NewGuid().ToString('N').Substring(0,10)
$good='DCJ10DP'+$tag
$bad='DCJ10DX'+$tag
$consumer='DCJ10DC'+$tag
$pipeName='dcj10d-auth-'+$tag
$root=Join-Path $env:ProgramData ('lot05j10d_fake_pipe_'+$tag)
$issuer=Join-Path $root 'issuer-evidence'
$trusted=Join-Path $root 'consumer-trust'
$ledger=Join-Path $root 'consumer-ledger'
$goodDir=Join-Path $root 'relay-report'
$badDir=Join-Path $root 'hostile-report'
$report1=Join-Path $goodDir 'first.txt'
$report2=Join-Path $goodDir 'replayed.txt'
$report3=Join-Path $goodDir 'tamper.txt'
$reportBad=Join-Path $badDir 'hostile.txt'
$ticket=Join-Path $issuer 'signed-ticket.json'
$forged=Join-Path $issuer 'tampered-ticket.json'
$hostileFile=Join-Path $badDir 'fake-ticket.json'
$pin=Join-Path $trusted 'rsa-public.fake'
$consumerExe=Join-Path $root 'consumer.exe'
$relayExe=Join-Path $root 'relay.exe'
$created=New-Object 'System.Collections.Generic.List[string]'
try {
    if(Test-Path -LiteralPath $root) {throw 'J10D_PIPE_ROOT_ALREADY_EXISTS'}
    New-Item -ItemType Directory -Path $root,$issuer,$trusted,$ledger,$goodDir,$badDir | Out-Null
    $csc=Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    $csConsumer=Join-Path $env:GITHUB_WORKSPACE 'backend/tests/fixtures/lot05j10d_windows_authenticated_pipe_consumer.cs'
    $csRelay=Join-Path $env:GITHUB_WORKSPACE 'backend/tests/fixtures/lot05j10d_windows_authenticated_pipe_relay.cs'
    Native $csc @('/nologo','/target:exe',('/out:'+$consumerExe),
        '/reference:System.ServiceProcess.dll','/reference:System.Web.Extensions.dll',$csConsumer)
    Native $csc @('/nologo','/target:exe',('/out:'+$relayExe),
        '/reference:System.ServiceProcess.dll',$csRelay)
    foreach($row in @(@($consumer,$consumerExe),@($good,$relayExe),@($bad,$relayExe))) {
        $cmd=('"{0}" "{1}"' -f $row[1],$row[0])
        Native 'sc.exe' @('create',$row[0],'binPath=',$cmd,'start=','demand',
                          'type=','own','obj=','NT AUTHORITY\LocalService')
        $created.Add($row[0])
        Native 'sc.exe' @('sidtype',$row[0],'unrestricted')
    }
    $consumerSid=Sid $consumer
    $goodSid=Sid $good
    $badSid=Sid $bad
    if($consumerSid -eq $goodSid -or $goodSid -eq $badSid) {throw 'J10D_PIPE_SID_COLLISION'}
    Native 'icacls.exe' @($root,'/inheritance:r','/grant:r',
         '*S-1-5-18:(OI)(CI)F','*S-1-5-32-544:(OI)(CI)F','*S-1-5-19:(OI)(CI)RX')
    $srcTicket=Join-Path $env:LOT05J10D_SOURCE_ROOT 'isolated-signed.json'
    $srcPin=Join-Path $env:LOT05J10D_SOURCE_ROOT 'trusted-rsa-public.fake'
    foreach($source in @($srcTicket,$srcPin)) {
        $item=Get-Item -LiteralPath $source -ErrorAction Stop
        if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $item.LinkType) {
            throw 'J10D_PIPE_UNTRUSTED_SOURCE'
        }
    }
    Copy-Item -LiteralPath $srcTicket -Destination $ticket
    Copy-Item -LiteralPath $srcPin -Destination $pin
    $data=Get-Content -LiteralPath $ticket -Raw | ConvertFrom-Json
    if(!$data.body.StartsWith(('owner='+$env:LOT05J10D_OWNER+
         '|audience=LOT05J10C_SQLCIPHER_FAKE|'))) {throw 'J10D_PIPE_ISSUER_WRONG_AUDIENCE'}
    $changed=$data.body.Replace(('job='+$env:LOT05J10D_JOB),('job='+('f'*32)))
    if($changed -eq $data.body) {throw 'J10D_PIPE_NO_TAMPER'}
    $data.body=$changed
    [IO.File]::WriteAllText($forged,($data | ConvertTo-Json -Compress))
    [IO.File]::WriteAllText($hostileFile,'{"body":"forged"}')
    Protect $issuer $goodSid 'RX' $true
    Protect $ticket $goodSid 'R' $false
    Protect $forged $goodSid 'R' $false
    Protect $trusted $consumerSid 'RX' $true
    Protect $pin $consumerSid 'R' $false
    Protect $ledger $consumerSid 'M' $true
    Protect $goodDir $goodSid 'M' $true
    Protect $badDir $badSid 'M' $true
    Write-Output 'J10D_PIPE_SCM_PIN_LEDGER_AND_RELAY_SID_ACLS_PASS'
    $cmdConsumer=('"{0}" "{1}" "{2}" "{3}" "{4}" "{5}" "{6}" "{7}" "{8}" "{9}" "{10}"' -f
         $consumerExe,$consumer,$pipeName,$goodSid,$consumerSid,$pin,$ledger,
         $env:LOT05J10D_OWNER,$env:LOT05J10D_JOB,$env:LOT05J10D_GENERATION,$env:LOT05J10D_MANIFEST)
    Native 'sc.exe' @('config',$consumer,'binPath=',$cmdConsumer)
    function ConfigureRelay([string]$name,[string]$jobFile,[string]$report,[string]$expected) {
        $cmd=('"{0}" "{1}" "{2}" "{3}" "{4}" "{5}"' -f
              $relayExe,$name,$pipeName,$jobFile,$report,$expected)
        Native 'sc.exe' @('config',$name,'binPath=',$cmd)
    }
    ConfigureRelay $good $ticket $report1 $goodSid
    ConfigureRelay $bad $hostileFile $reportBad $goodSid
    Native 'sc.exe' @('start',$consumer)
    (Get-Service $consumer).WaitForStatus('Running',[TimeSpan]::FromSeconds(15))
    $first=StartReport $good $report1
    if($first -notmatch 'service_sid_present=True' -or
       $first -notmatch 'response=DENY_J10D_RSA_VERIFIED_NONCE_BURNED') {
        throw ('J10D_PIPE_RSA_FIRST_NOT_PROVED '+$first)
    }
    if(@(Get-ChildItem -LiteralPath $ledger -Filter '*.nonce' -File).Count -ne 1) {
        throw 'J10D_PIPE_NONCE_NOT_PERSISTED'
    }
    Write-Output 'J10D_PIPE_REAL_J10C_RSA_TICKET_SCMSID_PEER_VERIFIED_AND_DENIED_PASS'
    StopLab $good
    StopLab $consumer
    Native 'sc.exe' @('start',$consumer)
    (Get-Service $consumer).WaitForStatus('Running',[TimeSpan]::FromSeconds(15))
    ConfigureRelay $good $ticket $report2 $goodSid
    $replay=StartReport $good $report2
    if($replay -notmatch 'service_sid_present=True' -or
       $replay -notmatch 'response=DENY_J10D_NONCE_REPLAY_OR_LEDGER' -or
       @(Get-ChildItem -LiteralPath $ledger -Filter '*.nonce' -File).Count -ne 1) {
        throw ('J10D_PIPE_REPLAY_NOT_DENIED '+$replay)
    }
    Write-Output 'J10D_PIPE_ACTUAL_CONSUMER_SCM_RESTART_REPLAY_DENIED_PASS'
    StopLab $good
    ConfigureRelay $good $forged $report3 $goodSid
    $tampered=StartReport $good $report3
    if($tampered -notmatch 'response=DENY_J10D_SIGNATURE_OR_SCOPE' -or
       @(Get-ChildItem -LiteralPath $ledger -Filter '*.nonce' -File).Count -ne 1) {
        throw ('J10D_PIPE_TAMPER_BYPASS '+$tampered)
    }
    Write-Output 'J10D_PIPE_VALID_SERVICE_SID_FORGED_RSA_BODY_DENIED_PASS'
    $negative=StartReport $bad $reportBad
    if($negative -notmatch 'service_sid_present=False' -or
       $negative -notmatch 'response=DENY_PIPE_ACCESS') {
        throw ('J10D_PIPE_HOSTILE_SID_NOT_REJECTED '+$negative)
    }
    Write-Output 'J10D_PIPE_SAME_LOCALSERVICE_OTHER_SCM_SID_ACCESS_DENIED_PASS'
    Write-Output 'J10D_PIPE_NO_CLINICAL_APPLY_PASS'
}
finally {
    foreach($name in $created) { & sc.exe stop $name 2>&1 | Out-Null }
    Start-Sleep -Seconds 1
    foreach($name in $created) { & sc.exe delete $name 2>&1 | Out-Null }
    if(Test-Path -LiteralPath $root) {
        Remove-Item -LiteralPath $root -Force -Recurse -ErrorAction SilentlyContinue
    }
}
