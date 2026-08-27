#requires -Version 5.1
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$sourceWrapper = Join-Path $PSScriptRoot "windows_update_worker.ps1"
$nativePs = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
if (-not (Test-Path -LiteralPath $nativePs -PathType Leaf)) {
    throw "Windows PowerShell 5.1 missing"
}

function Publish-FakeDigitalCrown {
    param([string]$ProjectDir, [string]$OutputDir)
    New-Item -ItemType Directory -Path $ProjectDir,$OutputDir -Force | Out-Null
    $project = Join-Path $ProjectDir "DigitalCrown.csproj"
    $program = Join-Path $ProjectDir "Program.cs"
    $csproj = @"
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <AssemblyName>DigitalCrown</AssemblyName>
    <ImplicitUsings>disable</ImplicitUsings>
    <Nullable>disable</Nullable>
    <UseAppHost>true</UseAppHost>
  </PropertyGroup>
</Project>
"@
    $source = @"
using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;

public static class Program
{
    public static int Main(string[] args)
    {
        if (args.Length == 2 && args[0] == "--update-db-rollback-worker")
        {
            var jobPath = args[1].Trim('"');
            var marker = Path.Combine(Path.GetDirectoryName(jobPath), "db-cli-invoked");
            File.WriteAllText(marker, "invoked", new UTF8Encoding(false));
            if (Environment.GetEnvironmentVariable("P10_FAKE_DB_ROLLBACK_FAIL") == "1") return 4;
            File.WriteAllText(Path.Combine(Path.GetDirectoryName(jobPath), "db-restored"), "ok", new UTF8Encoding(false));
            return 0;
        }

        var portRaw = Environment.GetEnvironmentVariable("CABINET_PORT");
        int port = 8005;
        if (!String.IsNullOrWhiteSpace(portRaw)) Int32.TryParse(portRaw, out port);
        var listener = new TcpListener(IPAddress.Loopback, port);
        listener.Start();
        try
        {
            while (true)
            {
                using (var client = listener.AcceptTcpClient())
                using (var stream = client.GetStream())
                {
                    var buffer = new byte[4096];
                    try { stream.Read(buffer, 0, buffer.Length); } catch { }
                    var body = "{\"status\":\"ok\",\"db\":\"ok\"}";
                    var response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: " +
                        Encoding.UTF8.GetByteCount(body) + "\r\nConnection: close\r\n\r\n" + body;
                    var bytes = Encoding.UTF8.GetBytes(response);
                    stream.Write(bytes, 0, bytes.Length);
                }
            }
        }
        finally { listener.Stop(); }
    }
}
"@
    [IO.File]::WriteAllText($project, $csproj, [Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText($program, $source, [Text.UTF8Encoding]::new($false))
    & dotnet publish $project -c Release -r win-x64 --self-contained false --nologo -o $OutputDir | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "fake DigitalCrown publish failed" }
    return (Join-Path $OutputDir "DigitalCrown.exe")
}

function Write-StubCore {
    param([string]$Path)
    $stub = @'
#requires -Version 5.1
param([string]$JobPath, [int]$ParentPid)
$ErrorActionPreference = "Stop"
$job = Get-Content -LiteralPath $JobPath -Raw | ConvertFrom-Json
function Set-Field($Object, [string]$Name, $Value) {
    if ($Object.PSObject.Properties.Name -contains $Name) { $Object.$Name = $Value }
    else { $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value }
}
Set-Field $job "status" "rollback_failed"
Set-Field $job "worker_result" "rollback_failed"
Set-Field $job "rollback" "failed"
Set-Field $job "database_rollback" "required_but_not_wired"
Set-Field $job "rollback_failure_reason" $env:P10_STUB_ROLLBACK_REASON
[IO.File]::WriteAllText($JobPath, ($job | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
exit 3
'@
    [IO.File]::WriteAllText($Path, $stub, [Text.UTF8Encoding]::new($false))
}

function New-Case {
    param([string]$Root, [string]$FakeExe, [int]$Port)
    $jobId = [Guid]::NewGuid().ToString("N")
    $jobDir = Join-Path $Root $jobId
    $installDir = Join-Path $jobDir "DigitalCrown"
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
    $fakePackageDir = Split-Path -Parent $FakeExe
    Copy-Item -Path (Join-Path $fakePackageDir "*") -Destination $installDir -Recurse -Force
    if (-not (Test-Path -LiteralPath (Join-Path $installDir "DigitalCrown.exe") -PathType Leaf)) {
        throw "fake DigitalCrown package copy failed"
    }
    $job = [ordered]@{
        schema = 1
        job_id = $jobId
        status = "scheduled"
        install_dir = $installDir
        health_url = "http://127.0.0.1:$Port/health"
        health_timeout_seconds = 4
    }
    $jobPath = Join-Path $jobDir "job.json"
    [IO.File]::WriteAllText($jobPath, ($job | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
    return $jobPath
}

function Invoke-Case {
    param([string]$Wrapper, [string]$JobPath, [int]$ExpectedExitCode)
    & $nativePs -NoProfile -ExecutionPolicy Bypass -File $Wrapper -JobPath $JobPath -ParentPid 4242
    $code = $LASTEXITCODE
    if ($code -ne $ExpectedExitCode) {
        $jobText = Get-Content -LiteralPath $JobPath -Raw
        throw "orchestrator exit mismatch expected=$ExpectedExitCode actual=$code job=$jobText"
    }
    return (Get-Content -LiteralPath $JobPath -Raw | ConvertFrom-Json)
}

$temp = Join-Path $env:RUNNER_TEMP ("p10-db-rollback-" + [Guid]::NewGuid().ToString("N"))
$workerDir = Join-Path $temp "worker"
New-Item -ItemType Directory -Path $workerDir -Force | Out-Null
$wrapper = Join-Path $workerDir "windows_update_worker.ps1"
$core = Join-Path $workerDir "windows_update_worker_core.ps1"
Copy-Item -LiteralPath $sourceWrapper -Destination $wrapper -Force
Write-StubCore $core
$fakeExe = Publish-FakeDigitalCrown -ProjectDir (Join-Path $temp "src") -OutputDir (Join-Path $temp "pkg")

try {
    # A: exact package-rollback health failure is the only path allowed to mutate DB.
    $env:P10_STUB_ROLLBACK_REASON = "UPDATE_WINDOWS_PACKAGE_ROLLBACK_HEALTH_FAILED"
    $env:CABINET_PORT = "18770"
    Remove-Item Env:P10_FAKE_DB_ROLLBACK_FAIL -ErrorAction SilentlyContinue
    $jobA = New-Case -Root (Join-Path $temp "case-eligible") -FakeExe $fakeExe -Port 18770
    $resultA = Invoke-Case -Wrapper $wrapper -JobPath $jobA -ExpectedExitCode 2
    if ($resultA.status -ne "rolled_back" -or $resultA.database_rollback -ne "passed") {
        throw "eligible DB fallback did not recover"
    }
    if (-not (Test-Path -LiteralPath (Join-Path (Split-Path -Parent $jobA) "db-cli-invoked"))) {
        throw "eligible DB fallback did not invoke old binary bridge"
    }
    Stop-Process -Id ([int]$resultA.runtime_pid) -Force -ErrorAction SilentlyContinue

    # B: any other rollback failure must leave DB untouched.
    $env:P10_STUB_ROLLBACK_REASON = "UPDATE_WINDOWS_UNINSTALL_REGISTRY_IMPORT_FAILED"
    $env:CABINET_PORT = "18771"
    $jobB = New-Case -Root (Join-Path $temp "case-ineligible") -FakeExe $fakeExe -Port 18771
    $resultB = Invoke-Case -Wrapper $wrapper -JobPath $jobB -ExpectedExitCode 3
    if ($resultB.database_rollback -ne "required_but_not_wired") {
        throw "ineligible fallback mutated DB state"
    }
    if (Test-Path -LiteralPath (Join-Path (Split-Path -Parent $jobB) "db-cli-invoked")) {
        throw "ineligible fallback invoked DB bridge"
    }

    # C: bridge failure remains fail-closed and does not launch a recovered runtime.
    $env:P10_STUB_ROLLBACK_REASON = "UPDATE_WINDOWS_PACKAGE_ROLLBACK_HEALTH_FAILED"
    $env:P10_FAKE_DB_ROLLBACK_FAIL = "1"
    $env:CABINET_PORT = "18772"
    $jobC = New-Case -Root (Join-Path $temp "case-db-fail") -FakeExe $fakeExe -Port 18772
    $resultC = Invoke-Case -Wrapper $wrapper -JobPath $jobC -ExpectedExitCode 3
    if ($resultC.database_rollback -ne "failed" -or $resultC.status -ne "rollback_failed") {
        throw "failed DB fallback did not remain fail-closed"
    }

    Write-Host "P10_WINDOWS_DB_ROLLBACK_BRIDGE=SUCCESS exact_health_gate=PASSED db_fail_closed=PASSED"
    exit 0
}
finally {
    Remove-Item Env:P10_STUB_ROLLBACK_REASON -ErrorAction SilentlyContinue
    Remove-Item Env:P10_FAKE_DB_ROLLBACK_FAIL -ErrorAction SilentlyContinue
    Remove-Item Env:CABINET_PORT -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
}
