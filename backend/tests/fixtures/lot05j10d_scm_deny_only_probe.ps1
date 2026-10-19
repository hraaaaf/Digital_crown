# LOT05/J10D — isolated SCM install/start/pipe-deny/stop/delete probe.
# This proves a real SCM consumer instance, NOT signer authentication or clinical apply.
$ErrorActionPreference = 'Stop'
$serviceName = 'DCJ10DConsumer' + $PID
$pipeName = 'dcj10d-deny-' + $PID
$signerSid = 'S-1-5-80-0-0-0-0-0' # synthetic placeholder; never trust as signer
$exe = Join-Path $env:RUNNER_TEMP 'j10d-deny-only-consumer.exe'
if (!(Test-Path -LiteralPath $exe -PathType Leaf)) { throw 'Consumer binary missing' }
$binPath = ('"{0}" {1} {2} {3}' -f $exe,$serviceName,$pipeName,$signerSid)
$created = $false
try {
    & sc.exe create $serviceName binPath= $binPath start= demand obj= LocalSystem | Out-Host
    if ($LASTEXITCODE -ne 0) { throw 'SCM create failed' }
    $created = $true
    & sc.exe sidtype $serviceName unrestricted | Out-Host
    if ($LASTEXITCODE -ne 0) { throw 'SCM sidtype failed' }
    & sc.exe qc $serviceName | Out-Host
    if ($LASTEXITCODE -ne 0) { throw 'SCM qc failed' }
    & sc.exe start $serviceName | Out-Host
    if ($LASTEXITCODE -ne 0) { throw 'SCM start failed' }
    $running = $false
    for ($i=0; $i -lt 30; $i++) {
        $s = Get-Service -Name $serviceName -ErrorAction Stop
        if ($s.Status -eq 'Running') { $running = $true; break }
        Start-Sleep -Milliseconds 300
    }
    if (!$running) { throw 'SCM consumer never entered Running' }
    $denied = $false
    for ($i=0; $i -lt 25; $i++) {
        try {
            $client = [System.IO.Pipes.NamedPipeClientStream]::new('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
            try {
                $client.Connect(500)
                $buffer = New-Object byte[] 64
                $n = $client.Read($buffer,0,$buffer.Length)
                $response = [System.Text.Encoding]::ASCII.GetString($buffer,0,$n)
                if ($response -ne "DENY_J10D_UNATTESTED`n") { throw "Unexpected pipe response" }
                $denied = $true
                break
            } finally { $client.Dispose() }
        } catch [System.UnauthorizedAccessException] {
            # The GitHub runner's admin token is NOT the signer service SID.
            # An ACL refusal is the expected negative OS isolation proof.
            $denied = $true
            break
        } catch [System.TimeoutException] { Start-Sleep -Milliseconds 200 }
    }
    if (!$denied) { throw 'SCM consumer did not deny an untrusted pipe client' }
    Write-Output 'J10D_REAL_SCM_UNTRUSTED_DENIED_PASS'
} finally {
    if ($created) {
        & sc.exe stop $serviceName | Out-Host
        Start-Sleep -Seconds 1
        & sc.exe delete $serviceName | Out-Host
    }
}
