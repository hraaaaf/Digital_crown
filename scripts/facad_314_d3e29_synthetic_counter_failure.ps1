# D3E29: controlled synthetic P/Invoke failure tests; never install/run FACAD or query 4663.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_OS -cne 'Windows' -or
   [string]::IsNullOrWhiteSpace($env:GITHUB_WORKSPACE)){throw 'D3E29_WINDOWS_ONLY'}
$ws=[IO.Path]::GetFullPath($env:GITHUB_WORKSPACE).TrimEnd('\')
$observer=Join-Path $ws 'scripts/facad_314_d3_process_io_observer.ps1'
$summary=Join-Path $ws 'd3e29-safe-counter-failclosed.json'
if(Test-Path -LiteralPath $summary){throw 'D3E29_EXISTING_OUTPUT'}
$tokens=$null;$errors=$null
$tree=[System.Management.Automation.Language.Parser]::ParseFile($observer,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'D3E29_PARSE_FAILURE'}
$fn=@($tree.FindAll({param($n)
   $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
   $n.Name -ceq 'Get-SafeCounters'
},$true))
if($fn.Count -ne 1){throw 'D3E29_COUNTER_FUNCTION_MISSING'}

# Test-only drop-in C# with identical callable ABI. No system I/O is performed by this stub.
# Mode 0: a valid synthetic counter; 1: Win32 API returns false;
# Mode 2: API throws confidential diagnostic text after Process.Handle is resolved.
Add-Type -TypeDefinition @'
using System;
public static class D3SafeProcessIoCounters {
  public struct Counters {
    public ulong ReadOperationCount, WriteOperationCount, OtherOperationCount;
    public ulong ReadTransferCount, WriteTransferCount, OtherTransferCount;
  }
  public static int Mode=0;
  public static bool GetProcessIoCounters(IntPtr handle, out Counters c) {
    c = new Counters {
      ReadOperationCount=5,WriteOperationCount=7,
      ReadTransferCount=11,WriteTransferCount=13
    };
    if(Mode==1) return false;
    if(Mode==2) throw new InvalidOperationException("D3E29_INTERNAL_DETAIL_MUST_NOT_ESCAPE");
    return true;
  }
}
'@
Invoke-Expression $fn[0].Extent.Text

$p=$null;$passed=0
try {
  $pwsh=(Get-Command pwsh -ErrorAction Stop).Source
  $p=Start-Process -FilePath $pwsh -ArgumentList @('-NoProfile','-NonInteractive','-Command','Start-Sleep -Seconds 25') -PassThru
  # Two positive controls: root and child role call the exact real function with stub mode 0.
  foreach($role in @('root','child')){
    [D3SafeProcessIoCounters]::Mode=0
    $rootId=if($role -ceq 'root'){[int]$p.Id}else{0}
    $sample=Get-SafeCounters ([int]$p.Id) $rootId
    if($null -eq $sample -or
       $sample.write_ops -ne 7 -or $sample.write_bytes -ne 13 -or
       $sample.read_ops -ne 5 -or $sample.read_bytes -ne 11){
      throw 'D3E29_POSITIVE_COUNTER_CONTROL_FAILED'
    }
    $passed++
  }
  # Four negative controls: both real-root/child roles, for both API false and throw.
  foreach($role in @('root','child')){
    $rootId=if($role -ceq 'root'){[int]$p.Id}else{0}
    foreach($mode in @(1,2)){
      [D3SafeProcessIoCounters]::Mode=$mode
      $failedClosed=$false
      try {
        $null=Get-SafeCounters ([int]$p.Id) $rootId
      }catch{
        # Do not upload or print native exception, PID, file or process details.
        if($_.Exception.Message -cne 'D3_PROCESS_COUNTER_READ_UNAVAILABLE' -or
           ([string]$_).Contains('D3E29_INTERNAL_DETAIL_MUST_NOT_ESCAPE')){
          throw 'D3E29_ERROR_DETAIL_EXPOSED_OR_WRONG_GATE'
        }
        $failedClosed=$true
      }
      if(-not $failedClosed){throw 'D3E29_COUNTER_FAILURE_MISCLASSIFIED_AS_SUCCESS'}
      $passed++
    }
  }
}finally{
  if($null -ne $p -and -not $p.HasExited){
    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
  }
}

# Two additional real-lookup controls: already exited child => null, root => fail closed.
[D3SafeProcessIoCounters]::Mode=0
$dead=Start-Process -FilePath (Get-Command pwsh).Source -ArgumentList @('-NoProfile','-NonInteractive','-Command','exit 0') -PassThru -Wait
$x=Get-SafeCounters ([int]$dead.Id) 0
if($null -ne $x){throw 'D3E29_DEAD_CHILD_NOT_IGNORED'}
$passed++
$rootFailed=$false
try {$null=Get-SafeCounters ([int]$dead.Id) ([int]$dead.Id)}
catch {
  if($_.Exception.Message -cne 'D3_ROOT_PROCESS_ABSENT_AT_COUNTER_LOOKUP'){throw 'D3E29_WRONG_ROOT_FAILURE'}
  $rootFailed=$true
}
if(-not $rootFailed){throw 'D3E29_ABSENT_ROOT_ACCEPTED'}
$passed++
if($passed -ne 8){throw 'D3E29_CASE_COUNT_INVALID'}

# A negative control must never set an isolation or clinical gate to true.
$report=[ordered]@{
  schema='facad_d3e29_synthetic_counter_failclosed_v1'
  executed_synthetic_cases=$passed
  positive_counter_cases=2
  counter_failures_rejected=4
  child_absent_allowed_only_at_lookup=$true
  root_absent_rejected=$true
  late_root_and_child_counter_fail_closed=$true
  native_exception_details_redacted=$true
  facad_executed=$false
  security_4663_queried=$false
  audit_4663_certified=$false
  clinical_edit_allowed=$false
  shared_app_storage_isolation_verified=$false
  verdict='COUNTERS_SYNTHETIC_ONLY_D3_OPEN_RED'
}
$report|ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $summary -Encoding utf8
Write-Host 'D3E29_SYNTHETIC_COUNTER_CASES=8'
Write-Host 'D3E29_FAIL_CLOSED_COUNTER_FAILURES=4'
Write-Host 'D3E29_CONFIDENTIAL_EXCEPTION_REDACTED=true'
Write-Host 'D3E29_FACAD_EXECUTED=false'
Write-Host 'D3E29_D3=OPEN_RED'
