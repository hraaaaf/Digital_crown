# LOT05 J10D: three disposable SCM services. DENY-only synthetic IPC.
$ErrorActionPreference='Stop'
$tag=[Guid]::NewGuid().ToString('N').Substring(0,9)
$allowed='DCJ10DA'+$tag
$hostile='DCJ10DH'+$tag
$consumer='DCJ10DC'+$tag
$pipe='dcj10d-three-'+$tag
$root=Join-Path $env:RUNNER_TEMP ('j10d-three-'+$tag)
$goodDir=Join-Path $root 'allowed'
$badDir=Join-Path $root 'hostile'
$goodReport=Join-Path $goodDir 'result.txt'
$badReport=Join-Path $badDir 'result.txt'
$forgery=Join-Path $goodDir 'forgery.txt'
$clientExe=Join-Path $root 'caller.exe'
$serverExe=Join-Path $root 'consumer.exe'
$created=New-Object 'System.Collections.Generic.List[string]'

function Check-Exit([string]$what) {
    if($LASTEXITCODE -ne 0) { throw "$what returned $LASTEXITCODE" }
}
function Create-Lab([string]$name,[string]$bin,[string]$account) {
    & sc.exe create $name binPath= $bin start= demand obj= $account | Out-Host
    Check-Exit "SCM create $name"
    $created.Add($name)
    & sc.exe sidtype $name unrestricted | Out-Host
    Check-Exit "SCM sidtype $name"
}
function Get-LabSid([string]$name) {
    $sid=([System.Security.Principal.NTAccount]::new('NT SERVICE',$name)).Translate(
        [System.Security.Principal.SecurityIdentifier]).Value
    if(!$sid.StartsWith('S-1-5-80-')) { throw "Invalid SCM SID: $name" }
    return $sid
}
function Start-Lab([string]$name) {
    & sc.exe start $name | Out-Host
    Check-Exit "SCM start $name"
    $svc=Get-Service -Name $name -ErrorAction Stop
    $svc.WaitForStatus('Running',[TimeSpan]::FromSeconds(15))
    if($svc.Status -ne 'Running') { throw "SCM not running: $name" }
}
function Await-Result([string]$path) {
    for($i=0;$i -lt 90;$i++) {
        if(Test-Path -LiteralPath $path -PathType Leaf) {
            return (Get-Content -LiteralPath $path -Raw).Trim()
        }
        Start-Sleep -Milliseconds 250
    }
    throw "SCM report not received: $path"
}
try {
    New-Item -ItemType Directory -Path $goodDir,$badDir -Force | Out-Null
    $sourceClient=Join-Path $env:RUNNER_TEMP 'j10d-scm-caller.exe'
    $sourceServer=Join-Path $env:RUNNER_TEMP 'j10d-deny-only-consumer.exe'
    foreach($source in @($sourceClient,$sourceServer)) {
        if(!(Test-Path -LiteralPath $source -PathType Leaf)) { throw 'Lab binary missing' }
    }
    Copy-Item -LiteralPath $sourceClient -Destination $clientExe
    Copy-Item -LiteralPath $sourceServer -Destination $serverExe
    $cmdAllowed=('"{0}" {1} {2} "{3}"' -f $clientExe,$allowed,$pipe,$goodReport)
    $cmdHostile=('"{0}" {1} {2} "{3}" "{4}"' -f $clientExe,$hostile,$pipe,$badReport,$forgery)
    Create-Lab $allowed $cmdAllowed 'NT AUTHORITY\LocalService'
    Create-Lab $hostile $cmdHostile 'NT AUTHORITY\LocalService'
    $goodSid=Get-LabSid $allowed
    $badSid=Get-LabSid $hostile
    if($goodSid -eq $badSid) { throw 'Service SID collision' }

    # Generic LocalService: read/execute binaries only; cannot replace them.
    & icacls.exe $root /inheritance:r /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' '*S-1-5-19:(OI)(CI)RX' | Out-Host
    Check-Exit 'root ACL'
    & icacls.exe $clientExe /inheritance:r /grant:r '*S-1-5-18:F' '*S-1-5-32-544:F' '*S-1-5-19:RX' | Out-Host
    Check-Exit 'caller binary ACL'
    & icacls.exe $serverExe /inheritance:r /grant:r '*S-1-5-18:F' '*S-1-5-32-544:F' | Out-Host
    Check-Exit 'consumer binary ACL'

    # Reports are per-Service-SID, not writable by the common LocalService SID.
    $goodGrant=('*{0}:(OI)(CI)M' -f $goodSid)
    $badGrant=('*{0}:(OI)(CI)M' -f $badSid)
    & icacls.exe $goodDir /inheritance:r /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' $goodGrant | Out-Host
    Check-Exit 'allowed evidence ACL'
    & icacls.exe $badDir /inheritance:r /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' $badGrant | Out-Host
    Check-Exit 'hostile evidence ACL'
    $cmdConsumer=('"{0}" {1} {2} {3}' -f $serverExe,$consumer,$pipe,$goodSid)
    Create-Lab $consumer $cmdConsumer 'LocalSystem'
    foreach($name in @($allowed,$hostile,$consumer)) {
        & sc.exe qc $name | Out-Host
        Check-Exit "SCM config $name"
    }
    Start-Lab $consumer
    Start-Lab $hostile
    $bad=Await-Result $badReport
    if($bad -ne 'FAIL_ACCESS_DENIEDWRITE_DENIED') {
        throw "Hostile SID did not fail closed on pipe and private evidence: $bad"
    }
    if(Test-Path -LiteralPath $forgery -PathType Leaf) {
        throw 'Hostile successfully forged authorized evidence'
    }
    Start-Lab $allowed
    $good=Await-Result $goodReport
    if($good -ne 'DENY_SID_PROVEN') {
        throw "Peer SID not observed from actual Windows token: $good"
    }
    Write-Output 'J10D_THREE_SCM_SID_AND_EVIDENCE_ISOLATION_PASS'
} finally {
    for($i=$created.Count-1;$i -ge 0;$i--) {
        $name=$created[$i]
        & sc.exe stop $name | Out-Host
        Start-Sleep -Milliseconds 500
        & sc.exe delete $name | Out-Host
    }
    if(Test-Path -LiteralPath $root) {
        Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
    }
}
