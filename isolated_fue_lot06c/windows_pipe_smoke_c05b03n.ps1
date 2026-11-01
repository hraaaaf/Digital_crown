#Requires -Version 7.0
# C05B-03N Windows-hosted disposable SAME-USER named-pipe smoke.
# NOT a service SID/DACL verification, remote-client denial, Win32 impersonation
# or CNG/TPM non-exportability test. No install, registry or clinical data.
$ErrorActionPreference = "Stop"
if (-not $IsWindows) { throw "C05B03N_WINDOWS_RUNNER_REQUIRED" }
if ($env:ENVIRONMENT -ne "test" -or $env:DIGITALCROWN_ISOLATED_RUNTIME -ne "true") {
    throw "C05B03N_ISOLATED_TEST_REQUIRED"
}
$name = "DigitalCrown-LOT06-fue-" + [Guid]::NewGuid().ToString("N")
$options = [System.IO.Pipes.PipeOptions]::Asynchronous -bor [System.IO.Pipes.PipeOptions]::CurrentUserOnly
$server = $null
$client = $null
try {
    $server = [System.IO.Pipes.NamedPipeServerStream]::new(
        $name, [System.IO.Pipes.PipeDirection]::InOut, 1,
        [System.IO.Pipes.PipeTransmissionMode]::Byte, $options
    )
    $client = [System.IO.Pipes.NamedPipeClientStream]::new(
        ".", $name, [System.IO.Pipes.PipeDirection]::InOut,
        [System.IO.Pipes.PipeOptions]::None
    )
    $pending = $server.WaitForConnectionAsync()
    $client.Connect(5000)
    $pending.GetAwaiter().GetResult()
    if (-not $server.IsConnected -or -not $client.IsConnected) {
        throw "C05B03N_PIPE_HANDSHAKE_MISSING"
    }
    $data = [System.Text.Encoding]::ASCII.GetBytes("C05B03N-SYNTHETIC-NO-PHI")
    $client.Write($data, 0, $data.Length)
    $client.Flush()
    $buffer = [byte[]]::new(128)
    $count = $server.Read($buffer, 0, $buffer.Length)
    $received = [System.Text.Encoding]::ASCII.GetString($buffer, 0, $count)
    if ($received -ne "C05B03N-SYNTHETIC-NO-PHI") {
        throw "C05B03N_PIPE_MEDIA_CORRUPTION"
    }
    $ack = [System.Text.Encoding]::ASCII.GetBytes("LAB-ONLY-ACK")
    $server.Write($ack, 0, $ack.Length)
    $server.Flush()
    $count = $client.Read($buffer, 0, $buffer.Length)
    if ([System.Text.Encoding]::ASCII.GetString($buffer, 0, $count) -ne "LAB-ONLY-ACK") {
        throw "C05B03N_PIPE_RESPONSE_MISSING"
    }
    Write-Output "C05B03N_WINDOWS_REAL_SAME_USER_NAMED_PIPE_SMOKE_PASS"
    Write-Output "C05B03N_NATIVE_SERVICE_SID_DACL_CNG_TPM_AND_REMOTE_DENIAL_NOT_TESTED"
}
finally {
    if ($client -ne $null) { $client.Dispose() }
    if ($server -ne $null) { $server.Dispose() }
}
