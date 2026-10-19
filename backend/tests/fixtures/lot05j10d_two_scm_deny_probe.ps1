# LOT05/J10D: two distinct installed SCM services, deny-only IPC, ephemeral.
$ErrorActionPreference='Stop'
$consumer='DCJ10DCon'+$PID
$caller='DCJ10DCall'+$PID
$pipe='dcj10d-two-scm-'+$PID
$consumerExe=Join-Path $env:RUNNER_TEMP 'j10d-deny-only-consumer.exe'
$callerExe=Join-Path $env:RUNNER_TEMP 'j10d-scm-caller.exe'
$dir=Join-Path $env:RUNNER_TEMP ('j10d-ipc-'+$PID)
$evidence=Join-Path $dir 'caller-result.txt'
$created=@()
try {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    # Grant LocalService only the disposable evidence directory, not clinical files.
    & icacls.exe $dir /inheritance:r /grant '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' '*S-1-5-19:(OI)(CI)M' | Out-Host
    if($LASTEXITCODE -ne 0) { throw 'Evidence ACL failed' }
    foreach($item in @(@($caller,$callerExe,'NT AUTHORITY\LocalService'),
                       @($consumer,$consumerExe,'LocalSystem'))) {
        $name=$item[0]; $exe=$item[1]; $account=$item[2]
        if(!(Test-Path -LiteralPath $exe -PathType Leaf)) { throw "Missing exe: $exe" }
        if($name -eq $caller) {
            $binary=('"{0}" {1} {2} "{3}"' -f $exe,$caller,$pipe,$evidence)
        } else {
            $sid=([System.Security.Principal.NTAccount]::new('NT SERVICE',$caller)).Translate([System.Security.Principal.SecurityIdentifier]).Value
            if(!$sid.StartsWith('S-1-5-80-')) { throw 'Caller service SID resolution failed' }
            $binary=('"{0}" {1} {2} {3}' -f $exe,$consumer,$pipe,$sid)
        }
        & sc.exe create $name binPath= $binary start= demand obj= $account | Out-Host
        if($LASTEXITCODE -ne 0) { throw "SCM create failed: $name" }
        $created+= $name
        & sc.exe sidtype $name unrestricted | Out-Host
        if($LASTEXITCODE -ne 0) { throw "SCM SID configuration failed: $name" }
    }
    foreach($name in @($consumer,$caller)) {
        & sc.exe start $name | Out-Host
        if($LASTEXITCODE -ne 0) { throw "SCM start failed: $name" }
        $svc=Get-Service -Name $name -ErrorAction Stop
        $svc.WaitForStatus('Running',[TimeSpan]::FromSeconds(15))
        if($svc.Status -ne 'Running') { throw "SCM not running: $name" }
    }
    $found=$false
    for($i=0;$i -lt 60;$i++) {
        if(Test-Path -LiteralPath $evidence -PathType Leaf) { $found=$true; break }
        Start-Sleep -Milliseconds 250
    }
    if(!$found) { throw 'Second SCM did not produce evidence' }
    $result=(Get-Content -LiteralPath $evidence -Raw).Trim()
    if($result -ne 'DENY_FROM_PIPE') { throw "Second SCM IPC did not reach deny-only consumer: $result" }
    Write-Output 'J10D_TWO_DISTINCT_SCM_DENY_ONLY_IPC_PASS'
} finally {
    [array]::Reverse($created)
    foreach($name in $created) {
        & sc.exe stop $name | Out-Host
        Start-Sleep -Milliseconds 600
        & sc.exe delete $name | Out-Host
    }
    if(Test-Path -LiteralPath $dir) { Remove-Item -LiteralPath $dir -Recurse -Force -ErrorAction SilentlyContinue }
}
