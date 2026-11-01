#Requires -Version 7.0
# LOT06 O. Disposable same-account, DIFFERENT PROCESS Windows Named Pipe proof.
# CurrentUserOnly is real .NET/Windows enforcement; there is NO service SID,
# custom installer DACL, PIPE_REJECT_REMOTE_CLIENTS, cross-user or LAN test.
# No clinical data, no installed Windows service or persistent resource.
$ErrorActionPreference = "Stop"
if (-not $IsWindows -or $env:ENVIRONMENT -ne "test" -or
    $env:DIGITALCROWN_ISOLATED_RUNTIME -ne "true") {
    throw "C05B03O_WINDOWS_TEST_RUNTIME_ONLY"
}
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class DC06NativeImpersonation {
    [DllImport("advapi32.dll", SetLastError = true)]
    public static extern bool ImpersonateNamedPipeClient(IntPtr hNamedPipe);
    [DllImport("advapi32.dll", SetLastError = true)]
    public static extern bool RevertToSelf();
}
'@
$name = "DigitalCrown-LOT06-O-" + [Guid]::NewGuid().ToString("N")
$server = $null
$job = $null
try {
    $opts = [System.IO.Pipes.PipeOptions]::Asynchronous -bor
        [System.IO.Pipes.PipeOptions]::CurrentUserOnly
    $server = [System.IO.Pipes.NamedPipeServerStream]::new(
        $name, [System.IO.Pipes.PipeDirection]::InOut, 1,
        [System.IO.Pipes.PipeTransmissionMode]::Byte, $opts
    )
    $parentPid = $PID
    $expectedSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $job = Start-Job -ArgumentList @($name, $parentPid) -ScriptBlock {
        param([string]$pipeName, [int]$parentId)
        $ErrorActionPreference = "Stop"
        $client = $null
        try {
            if ($PID -eq $parentId) { throw "C05B03O_NOT_SEPARATE_PROCESS" }
            $client = [System.IO.Pipes.NamedPipeClientStream]::new(
                ".", $pipeName, [System.IO.Pipes.PipeDirection]::InOut,
                [System.IO.Pipes.PipeOptions]::Asynchronous
            )
            $client.Connect(10000)
            $payload = [System.Text.Encoding]::ASCII.GetBytes("O-LAB-REQUEST")
            $client.Write($payload, 0, $payload.Length)
            $client.Flush()
            $data = [byte[]]::new(64)
            $read = $client.ReadAsync($data, 0, $data.Length)
            if (-not $read.Wait(6000)) { throw "C05B03O_CLIENT_REPLY_TIMEOUT" }
            if ([System.Text.Encoding]::ASCII.GetString($data, 0, $read.Result) -ne
                "O-LAB-ACK") { throw "C05B03O_BAD_REPLY" }
            Write-Output "C05B03O_CHILD_SEPARATE_PROCESS_ACK_PASS"
        }
        finally {
            if ($null -ne $client) { $client.Dispose() }
        }
    }
    $wait = $server.WaitForConnectionAsync()
    if (-not $wait.Wait(14000)) { throw "C05B03O_SERVER_CONNECT_TIMEOUT" }
    if (-not $server.IsConnected) { throw "C05B03O_NO_CONNECTION" }
    $inbound = [byte[]]::new(64)
    $read = $server.ReadAsync($inbound, 0, $inbound.Length)
    if (-not $read.Wait(6000)) { throw "C05B03O_SERVER_READ_TIMEOUT" }
    $received = [System.Text.Encoding]::ASCII.GetString($inbound, 0, $read.Result)
    if ($received -ne "O-LAB-REQUEST") { throw "C05B03O_BAD_OR_UNTRUSTED_PROTOCOL" }

    # Windows impersonation is explicitly checked, and RevertToSelf is mandatory.
    $handle = $server.SafePipeHandle.DangerousGetHandle()
    if (-not [DC06NativeImpersonation]::ImpersonateNamedPipeClient($handle)) {
        throw "C05B03O_NATIVE_IMPERSONATION_FAILED"
    }
    try {
        $peer = [System.Security.Principal.WindowsIdentity]::GetCurrent($true)
        try {
            if ($peer.User.Value -ne $expectedSid) {
                throw "C05B03O_NATIVE_PEER_SID_CONFLICT"
            }
        } finally { $peer.Dispose() }
    } finally {
        if (-not [DC06NativeImpersonation]::RevertToSelf()) {
            throw "C05B03O_REVERT_TO_SELF_FAILED"
        }
    }
    $reply = [System.Text.Encoding]::ASCII.GetBytes("O-LAB-ACK")
    $server.Write($reply, 0, $reply.Length)
    $server.Flush()
    $completed = $job | Wait-Job -Timeout 12
    if ($null -eq $completed) { throw "C05B03O_CLIENT_CHILD_TIMEOUT" }
    $output = @($job | Receive-Job -ErrorAction Stop)
    if ($job.State -ne "Completed" -or
        -not ($output -contains "C05B03O_CHILD_SEPARATE_PROCESS_ACK_PASS")) {
        throw "C05B03O_CLIENT_CHILD_FAILED"
    }
    Write-Output "C05B03O_WIN_NATIVE_INTERPROCESS_CURRENT_USER_SID_IMPERSONATE_REVERT_PASS"
    Write-Output "C05B03O_CUSTOM_DACL_SERVICE_SID_AND_CROSS_USER_DENIAL_NOT_TESTED"
}
finally {
    if ($null -ne $server) { $server.Dispose() }
    if ($null -ne $job) {
        if ($job.State -eq "Running") { $job | Stop-Job -ErrorAction SilentlyContinue }
        $job | Remove-Job -Force -ErrorAction SilentlyContinue
    }
}
