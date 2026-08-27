#requires -Version 7.0
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$worker = Join-Path $PSScriptRoot "windows_update_worker.ps1"
if (-not (Test-Path -LiteralPath $worker -PathType Leaf)) {
    throw "P10 worker missing: $worker"
}

$tokens = $null
$parseErrors = $null
[System.Management.Automation.Language.Parser]::ParseFile(
    $worker,
    [ref]$tokens,
    [ref]$parseErrors
) | Out-Null
if (@($parseErrors).Count -gt 0) {
    $messages = @($parseErrors | ForEach-Object { $_.Message }) -join " | "
    throw "P10 worker PowerShell parse failed: $messages"
}

function Publish-TestExe {
    param(
        [Parameter(Mandatory = $true)][string]$ProjectDir,
        [Parameter(Mandatory = $true)][string]$AssemblyName,
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$OutputDir
    )
    New-Item -ItemType Directory -Path $ProjectDir,$OutputDir -Force | Out-Null
    $project = Join-Path $ProjectDir "$AssemblyName.csproj"
    $program = Join-Path $ProjectDir "Program.cs"
    $csproj = @"
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <AssemblyName>$AssemblyName</AssemblyName>
    <ImplicitUsings>disable</ImplicitUsings>
    <Nullable>disable</Nullable>
    <UseAppHost>true</UseAppHost>
  </PropertyGroup>
</Project>
"@
    [IO.File]::WriteAllText($project, $csproj, [Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText($program, $Source, [Text.UTF8Encoding]::new($false))
    & dotnet publish $project -c Release -r win-x64 --self-contained false --nologo -o $OutputDir | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "dotnet publish failed: $AssemblyName"
    }
    $exe = Join-Path $OutputDir "$AssemblyName.exe"
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
        throw "published exe missing: $exe"
    }
    return $OutputDir
}

function New-FakeRuntime {
    param(
        [Parameter(Mandatory = $true)][string]$ProjectDir,
        [Parameter(Mandatory = $true)][string]$OutputDir,
        [Parameter(Mandatory = $true)][string]$Version,
        [Parameter(Mandatory = $true)][bool]$Healthy
    )
    $healthyLiteral = if ($Healthy) { "true" } else { "false" }
    $source = @"
using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;

public static class Program
{
    private const string VersionValue = "$Version";
    private const bool Healthy = $healthyLiteral;

    public static int Main(string[] args)
    {
        if (args.Length > 0 && args[0] == "--package-self-test")
        {
            var report = Environment.GetEnvironmentVariable("DIGITALCROWN_PACKAGE_SELF_TEST_REPORT");
            if (String.IsNullOrWhiteSpace(report)) return 11;
            var json = "{\"status\":\"ok\",\"frozen\":true,\"version\":\"" + VersionValue +
                "\",\"missing\":[],\"forbidden_present\":[],\"unqualified_scientific_weights_present\":[]," +
                "\"scientific_manifest_policy_ok\":true,\"scientific_capabilities\":\"FAIL_CLOSED_NO_WEIGHTS\"}";
            File.WriteAllText(report, json, new UTF8Encoding(false));
            return 0;
        }

        if (!Healthy) return 9;

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
        finally
        {
            listener.Stop();
        }
    }
}
"@
    return Publish-TestExe -ProjectDir $ProjectDir -AssemblyName "DigitalCrown" -Source $source -OutputDir $OutputDir
}

function New-FakeInstaller {
    param(
        [Parameter(Mandatory = $true)][string]$ProjectDir,
        [Parameter(Mandatory = $true)][string]$OutputDir
    )
    $source = @"
using System;
using System.IO;
using Microsoft.Win32;

public static class Program
{
    public static int Main(string[] args)
    {
        string installDir = null;
        foreach (var arg in args)
        {
            if (arg.StartsWith("/DIR=", StringComparison.OrdinalIgnoreCase))
            {
                installDir = arg.Substring(5).Trim('"');
            }
        }

        var candidateDir = Environment.GetEnvironmentVariable("P10_FAKE_CANDIDATE_DIR");
        var version = Environment.GetEnvironmentVariable("P10_FAKE_TARGET_VERSION");
        if (String.IsNullOrWhiteSpace(installDir) || String.IsNullOrWhiteSpace(candidateDir) || String.IsNullOrWhiteSpace(version))
            return 21;

        Directory.CreateDirectory(installDir);
        foreach (var sourceFile in Directory.GetFiles(candidateDir, "*", SearchOption.AllDirectories))
        {
            var relative = Path.GetRelativePath(candidateDir, sourceFile);
            var destination = Path.Combine(installDir, relative);
            var parent = Path.GetDirectoryName(destination);
            if (!String.IsNullOrWhiteSpace(parent)) Directory.CreateDirectory(parent);
            File.Copy(sourceFile, destination, true);
        }
        File.WriteAllText(Path.Combine(installDir, "unins000.exe"), "fake-uninstaller");

        using (var key = Registry.CurrentUser.CreateSubKey(
            @"Software\Microsoft\Windows\CurrentVersion\Uninstall\DigitalCrownP10Test_is1"))
        {
            key.SetValue("DisplayName", "DigitalCrown");
            key.SetValue("DisplayVersion", version);
            key.SetValue("InstallLocation", installDir);
            key.SetValue("UninstallString", Path.Combine(installDir, "unins000.exe"));
        }
        return 0;
    }
}
"@
    return Publish-TestExe -ProjectDir $ProjectDir -AssemblyName "FakeInstaller" -Source $source -OutputDir $OutputDir
}

function Copy-Package {
    param([string]$SourceDir, [string]$DestinationDir)
    New-Item -ItemType Directory -Path $DestinationDir -Force | Out-Null
    Copy-Item -Path (Join-Path $SourceDir "*") -Destination $DestinationDir -Recurse -Force
}

function Get-LowerSha {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Set-TestRegistry {
    param([string]$InstallDir, [string]$Version)
    $key = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\DigitalCrownP10Test_is1"
    New-Item -Path $key -Force | Out-Null
    New-ItemProperty -Path $key -Name DisplayName -Value "DigitalCrown" -PropertyType String -Force | Out-Null
    New-ItemProperty -Path $key -Name DisplayVersion -Value $Version -PropertyType String -Force | Out-Null
    New-ItemProperty -Path $key -Name InstallLocation -Value $InstallDir -PropertyType String -Force | Out-Null
    New-ItemProperty -Path $key -Name UninstallString -Value (Join-Path $InstallDir "unins000.exe") -PropertyType String -Force | Out-Null
}

function Remove-TestRegistry {
    Remove-Item "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\DigitalCrownP10Test_is1" -Recurse -Force -ErrorAction SilentlyContinue
}

function New-TestJob {
    param(
        [Parameter(Mandatory = $true)][string]$CaseRoot,
        [Parameter(Mandatory = $true)][string]$InstallDir,
        [Parameter(Mandatory = $true)][string]$InstallerDir,
        [Parameter(Mandatory = $true)][int]$Port,
        [Parameter(Mandatory = $true)][bool]$ApplyCertified
    )
    $jobId = [Guid]::NewGuid().ToString("N")
    $jobDir = Join-Path $CaseRoot $jobId
    New-Item -ItemType Directory -Path (Join-Path $jobDir "rescue") -Force | Out-Null
    Copy-Item -Path (Join-Path $InstallerDir "*") -Destination $jobDir -Recurse -Force
    $artifact = Join-Path $jobDir "FakeInstaller.exe"
    $rescue = Join-Path $jobDir "rescue\db_backup_test.db.enc"
    [IO.File]::WriteAllBytes($rescue, [Text.Encoding]::UTF8.GetBytes("encrypted-rescue"))

    $job = [ordered]@{
        schema = 1
        job_id = $jobId
        status = "scheduled"
        platform = "windows"
        architecture = "amd64"
        worker_contract = "windows-inno-v1"
        apply_certified = $ApplyCertified
        current_version = "1.0.0"
        version = "1.1.0"
        artifact_filename = "FakeInstaller.exe"
        artifact_sha256 = Get-LowerSha $artifact
        artifact_size_bytes = (Get-Item -LiteralPath $artifact).Length
        rescue_backup_filename = "rescue/db_backup_test.db.enc"
        rescue_backup_sha256 = Get-LowerSha $rescue
        install_dir = $InstallDir
        health_url = "http://127.0.0.1:$Port/health"
        health_timeout_seconds = 4
    }
    $path = Join-Path $jobDir "job.json"
    [IO.File]::WriteAllText(
        $path,
        ($job | ConvertTo-Json -Depth 10),
        [Text.UTF8Encoding]::new($false)
    )
    return $path
}

function Invoke-WorkerCase {
    param(
        [string]$JobPath,
        [int]$ExpectedExitCode
    )
    $parent = Start-Process pwsh -ArgumentList @("-NoProfile", "-Command", "Start-Sleep -Milliseconds 700") -PassThru
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $worker -JobPath $JobPath -ParentPid $parent.Id
    $code = $LASTEXITCODE
    if ($code -ne $ExpectedExitCode) {
        $jobText = Get-Content -LiteralPath $JobPath -Raw
        $logPath = Join-Path (Split-Path -Parent $JobPath) "windows-update-worker.log"
        $logText = if (Test-Path $logPath) { Get-Content $logPath -Raw } else { "<no worker log>" }
        throw "worker exit mismatch expected=$ExpectedExitCode actual=$code job=$jobText log=$logText"
    }
    return (Get-Content -LiteralPath $JobPath -Raw | ConvertFrom-Json)
}

$temp = Join-Path $env:RUNNER_TEMP ("p10-windows-worker-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $temp -Force | Out-Null

$currentDir = New-FakeRuntime -ProjectDir (Join-Path $temp "src-current") -OutputDir (Join-Path $temp "pkg-current") -Version "1.0.0" -Healthy $true
$goodDir = New-FakeRuntime -ProjectDir (Join-Path $temp "src-good") -OutputDir (Join-Path $temp "pkg-good") -Version "1.1.0" -Healthy $true
$badDir = New-FakeRuntime -ProjectDir (Join-Path $temp "src-bad") -OutputDir (Join-Path $temp "pkg-bad") -Version "1.1.0" -Healthy $false
$installerDir = New-FakeInstaller -ProjectDir (Join-Path $temp "src-installer") -OutputDir (Join-Path $temp "pkg-installer")

try {
    # Gate drill: uncertified apply must fail before any mutation.
    $case0 = Join-Path $temp "case-gate"
    $install0 = Join-Path $case0 "DigitalCrown"
    Copy-Package $currentDir $install0
    Set-Content -LiteralPath (Join-Path $install0 "unins000.exe") -Value "old-uninstaller" -NoNewline
    Set-TestRegistry -InstallDir $install0 -Version "1.0.0"
    $job0 = New-TestJob -CaseRoot $case0 -InstallDir $install0 -InstallerDir $installerDir -Port 18760 -ApplyCertified $false
    $beforeHash = Get-LowerSha (Join-Path $install0 "DigitalCrown.exe")
    $gate = Invoke-WorkerCase -JobPath $job0 -ExpectedExitCode 1
    if ($gate.status -ne "failed_pre_apply" -or $gate.worker_result -ne "blocked_before_mutation") {
        throw "uncertified apply did not fail closed"
    }
    if ((Get-LowerSha (Join-Path $install0 "DigitalCrown.exe")) -ne $beforeHash) {
        throw "uncertified apply mutated program files"
    }

    # Success drill.
    Remove-TestRegistry
    $case1 = Join-Path $temp "case-success"
    $install1 = Join-Path $case1 "DigitalCrown"
    Copy-Package $currentDir $install1
    Set-Content -LiteralPath (Join-Path $install1 "unins000.exe") -Value "old-uninstaller" -NoNewline
    Set-TestRegistry -InstallDir $install1 -Version "1.0.0"
    $env:P10_FAKE_CANDIDATE_DIR = $goodDir
    $env:P10_FAKE_TARGET_VERSION = "1.1.0"
    $env:CABINET_PORT = "18761"
    $job1 = New-TestJob -CaseRoot $case1 -InstallDir $install1 -InstallerDir $installerDir -Port 18761 -ApplyCertified $true
    $success = Invoke-WorkerCase -JobPath $job1 -ExpectedExitCode 0
    if ($success.status -ne "health_pending" -or $success.worker_result -ne "install_verified") {
        throw "success drill did not reach health_pending"
    }
    if ($success.package_self_test -ne "passed" -or $success.runtime_health -ne "passed") {
        throw "success drill missing post-install truth"
    }
    $displayVersion = (Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\DigitalCrownP10Test_is1").DisplayVersion
    if ($displayVersion -ne "1.1.0") {
        throw "success drill registry version mismatch: $displayVersion"
    }
    Stop-Process -Id ([int]$success.runtime_pid) -Force -ErrorAction SilentlyContinue

    # Rollback drill: target self-test passes, runtime health fails, old package + registry recover.
    Remove-TestRegistry
    $case2 = Join-Path $temp "case-rollback"
    $install2 = Join-Path $case2 "DigitalCrown"
    Copy-Package $currentDir $install2
    Set-Content -LiteralPath (Join-Path $install2 "unins000.exe") -Value "old-uninstaller" -NoNewline
    Set-TestRegistry -InstallDir $install2 -Version "1.0.0"
    $oldHash = Get-LowerSha (Join-Path $install2 "DigitalCrown.exe")
    $env:P10_FAKE_CANDIDATE_DIR = $badDir
    $env:P10_FAKE_TARGET_VERSION = "1.1.0"
    $env:CABINET_PORT = "18762"
    $job2 = New-TestJob -CaseRoot $case2 -InstallDir $install2 -InstallerDir $installerDir -Port 18762 -ApplyCertified $true
    $rollback = Invoke-WorkerCase -JobPath $job2 -ExpectedExitCode 2
    if ($rollback.status -ne "rolled_back" -or $rollback.rollback -ne "passed") {
        throw "rollback drill did not recover package"
    }
    if ($rollback.database_rollback -ne "not_needed") {
        throw "rollback drill restored DB unnecessarily"
    }
    if ((Get-LowerSha (Join-Path $install2 "DigitalCrown.exe")) -ne $oldHash) {
        throw "rollback drill did not restore exact program snapshot"
    }
    $rolledVersion = (Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\DigitalCrownP10Test_is1").DisplayVersion
    if ($rolledVersion -ne "1.0.0") {
        throw "rollback registry not restored: $rolledVersion"
    }
    Stop-Process -Id ([int]$rollback.runtime_pid) -Force -ErrorAction SilentlyContinue

    Write-Host "P10_WINDOWS_WORKER_CONTRACT=SUCCESS gate=FAIL_CLOSED success=HEALTH_PENDING rollback=PASSED db_restore=NOT_NEEDED"
}
finally {
    Remove-TestRegistry
    Remove-Item Env:P10_FAKE_CANDIDATE_DIR -ErrorAction SilentlyContinue
    Remove-Item Env:P10_FAKE_TARGET_VERSION -ErrorAction SilentlyContinue
    Remove-Item Env:CABINET_PORT -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
}
