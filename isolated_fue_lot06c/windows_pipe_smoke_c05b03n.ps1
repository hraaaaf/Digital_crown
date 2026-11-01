#Requires -Version 7.0
# C05B-03N disposable Win32-backed pipe CREATION/DISPOSAL probe only.
# No client connection, handshake, read/write, service SID/DACL,
# PIPE_REJECT_REMOTE_CLIENTS, impersonation, CNG or TPM is validated.
$ErrorActionPreference = "Stop"
if (-not $IsWindows) { throw "C05B03N_WINDOWS_RUNNER_REQUIRED" }
if ($env:ENVIRONMENT -ne "test" -or $env:DIGITALCROWN_ISOLATED_RUNTIME -ne "true") {
    throw "C05B03N_ISOLATED_TEST_REQUIRED"
}
$name = "DigitalCrown-LOT06-fue-" + [Guid]::NewGuid().ToString("N")
$options = [System.IO.Pipes.PipeOptions]::Asynchronous -bor [System.IO.Pipes.PipeOptions]::CurrentUserOnly
$server = $null
try {
    $server = [System.IO.Pipes.NamedPipeServerStream]::new(
        $name, [System.IO.Pipes.PipeDirection]::InOut, 1,
        [System.IO.Pipes.PipeTransmissionMode]::Byte, $options
    )
    if ($null -eq $server -or $server.IsConnected) {
        throw "C05B03N_WINDOWS_PIPE_CREATION_FAILED"
    }
    Write-Output "C05B03N_WINDOWS_CURRENT_USER_PIPE_CREATION_ONLY_PASS"
    Write-Output "C05B03N_INTERPROCESS_IO_DACL_SERVICE_SID_REMOTE_DENIAL_NOT_TESTED"
}
finally {
    if ($null -ne $server) { $server.Dispose() }
}
