# D3E28: Windows-only synthetic regression study. No FACAD, Ilexis, patients, security log or SACL.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if($env:RUNNER_OS -cne 'Windows' -or $env:GITHUB_ACTIONS -cne 'true' -or
   [string]::IsNullOrWhiteSpace($env:GITHUB_WORKSPACE)){
  throw 'D3E28_WINDOWS_GITHUB_ONLY'
}
$root=[IO.Path]::GetFullPath($env:GITHUB_WORKSPACE).TrimEnd('\')
$scriptPath=Join-Path $root 'scripts/facad_314_d3_process_io_observer.ps1'
$summary=Join-Path $root 'd3e28-synthetic-safe-summary.json'
if(Test-Path -LiteralPath $summary){throw 'D3E28_OUTPUT_ALREADY_PRESENT'}
$tokens=$null;$parseErrors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile($scriptPath,[ref]$tokens,[ref]$parseErrors)
if($parseErrors.Count -ne 0){throw 'D3E28_OBSERVER_PARSE_FAILURE'}
$defs=@($ast.FindAll({param($n)
  $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
  $n.Name -ceq 'Get-SafeCounters'
},$true))
if($defs.Count -ne 1){throw 'D3E28_EXPECTED_COUNTER_FUNCTION'}
Invoke-Expression $defs[0].Extent.Text

$pwsh=(Get-Command pwsh -ErrorAction Stop).Source
$dead=Start-Process -FilePath $pwsh -ArgumentList @('-NoProfile','-NonInteractive','-Command','exit 0') -Wait -PassThru
$raceReproduced=$false
try {
  $null=Get-SafeCounters ([int]$dead.Id)
} catch {
  # Only enum, never exception message, path, PID or command line in published summary.
  $kind=$_.Exception.GetType().Name
  if($kind -in @('ArgumentException','MethodInvocationException','RuntimeException','InvalidOperationException')){
    $raceReproduced=$true
  }else{
    throw 'D3E28_UNEXPECTED_EXCEPTION_CLASS'
  }
}
if(-not $raceReproduced){throw 'D3E28_EXPECTED_CHILD_EXIT_RACE_NOT_REPRODUCED'}

# Healthy root process: the *real* observer must collect process I/O without vendor.
$live=$null
$healthySamples=0
try {
  $live=Start-Process -FilePath $pwsh -ArgumentList @('-NoProfile','-NonInteractive','-Command','Start-Sleep -Seconds 24') -PassThru
  $healthyPath=Join-Path $root 'd3e28-healthy-local-only.json'
  & $scriptPath -TargetPid ([int]$live.Id) -DurationSeconds 3 -OutputPath $healthyPath | Out-Null
  if(-not (Test-Path -LiteralPath $healthyPath)){throw 'D3E28_HEALTHY_OBSERVER_NO_OUTPUT'}
  $healthy=Get-Content -LiteralPath $healthyPath -Raw | ConvertFrom-Json
  if($healthy.schema -cne 'facad314_d3_process_io_v1' -or
    $healthy.sample_count -ne 6 -or $healthy.target_observed_every_poll -ne $true -or
    $healthy.path_attribution_available -ne $false -or
    $healthy.d3_isolation_verified -ne $false -or
    $healthy.clinical_edit_allowed -ne $false){
    throw 'D3E28_HEALTHY_OBSERVER_BAD_CONTRACT'
  }
  $healthySamples=[int]$healthy.sample_count
  Remove-Item -LiteralPath $healthyPath -Force
} finally {
  if($null -ne $live -and -not $live.HasExited){Stop-Process -Id $live.Id -Force -ErrorAction SilentlyContinue}
}
# Dead root must never be accepted: GetProcessById may fail, but output must stay absent.
$gonePath=Join-Path $root 'd3e28-dead-root-local-only.json'
$rootGoneFails=$false
try{
  $null = & $scriptPath -TargetPid ([int]$dead.Id) -DurationSeconds 3 -OutputPath $gonePath 2>$null
} catch {
  $rootGoneFails=$true
}
if(-not $rootGoneFails -or (Test-Path -LiteralPath $gonePath)){
  throw 'D3E28_ROOT_GONE_DID_NOT_FAIL_CLOSED'
}
$result=[ordered]@{
  schema='facad_d3e28_synthetic_observer_reproducer_v1'
  source='WINDOWS_SYNTHETIC_PROCESS_ONLY'
  old_observer_child_exit_exception_reproduced=$raceReproduced
  healthy_root_sample_count=$healthySamples
  root_absent_fails_closed=$rootGoneFails
  synthetic_vendor_launches=0
  clinical_edit_allowed=$false
  facad_executable_used=$false
  security_4663_queried=$false
  shared_app_storage_isolation_verified=$false
  d3_gate='OPEN_RED'
}
$result|ConvertTo-Json -Depth 4|Set-Content -LiteralPath $summary -Encoding utf8
Write-Host 'D3E28_CHILD_EXIT_RACE=REPRODUCED_ON_OLD_FUNCTION'
Write-Host "D3E28_SYNTHETIC_HEALTHY_ROOT_SAMPLES=$healthySamples"
Write-Host 'D3E28_ROOT_ABSENT_FAIL_CLOSED=true'
Write-Host 'D3E28_FACAD_EXECUTED=false'
Write-Host 'D3E28_D3=OPEN_RED'
