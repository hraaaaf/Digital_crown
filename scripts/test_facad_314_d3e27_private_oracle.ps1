# D3E27 pure synthetic oracle tests; never FACAD, Ilexis or file reads.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'facad_314_d3e27_private_oracle.ps1')
$a='a'*64;$b='b'*64;$c='c'*64
function S([string]$digest,[long]$length){
  return [pscustomobject]@{digest=$digest;length=$length}
}
function Check([bool]$condition,[string]$id){
  if(-not $condition){throw "D3E27_SYNTHETIC_CONTRACT_FAILED_$id"}
}
$x=@{$a=(S ('1'*64) 1);$b=(S ('2'*64) 1)}
$y=@{$a=(S ('1'*64) 1);$b=(S ('3'*64) 1)}
$d=Get-D3E27Delta $x $y
Check ($d.changed_count -eq 1 -and $d.content_changed_count -eq 1) 'SAME_SIZE_HASH_CHANGE'
$y2=@{$a=(S ('1'*64) 1);$b=(S ('3'*64) 3);$c=(S ('4'*64) 2)}
$d=Get-D3E27Delta $x $y2
Check ($d.created_count -eq 1 -and $d.different_size_content_changed_count -eq 1) 'CREATE_AND_SIZE'
$d=Get-D3E27Delta $y2 $x
Check ($d.deleted_count -eq 1) 'DELETE'
$original=@{$a=(S ('1'*64) 1);$b=(S ('2'*64) 1)}
$changed=@{$a=(S ('1'*64) 1);$b=(S ('3'*64) 1)}
$stable=Get-D3E27StableResult $original $original $original $changed $changed @($b)
Check ($stable.stable_existing_file_content_changed_count -eq 1 -and
       $stable.stable_root_pid_overlap_without_control_count -eq 1 -and
       $stable.stored_content_persistence_observed -eq $true) 'STABLE_PID_CONTENT'
$controlled=Get-D3E27StableResult $original $changed $original $changed $changed @($b)
Check ($controlled.negative_control_changed_count -eq 1 -and
       $controlled.stable_root_pid_overlap_without_control_count -eq 0) 'CONTROL_SUPPRESSES_PID_MATCH'
$unstable=Get-D3E27StableResult $original $original $original $changed $original @($b)
Check ($unstable.stable_change_count -eq 0 -and
       $unstable.post_stop_unstable_count -eq 1 -and
       $unstable.stored_content_persistence_observed -eq $false) 'POSTSTOP_REVERSION'
$never=@{$a=(S ('1'*64) 1)}
$unmatched=Get-D3E27StableResult $never $never $never $changed $changed @($b)
Check ($unmatched.complete_process_causality_proven -eq $false) 'NEVER_FORGE_CAUSALITY'
$text=$stable | ConvertTo-Json -Depth 5 -Compress
Check (-not $text.Contains($a) -and -not $text.Contains($b) -and
       -not $text.Contains('1'*64) -and -not $text.Contains('3'*64)) 'NO_FILENAME_OR_HASH_EXPORT'
$blocked=$false
try{$null=Get-D3E27StableResult $original $original $original $changed $changed @('not-a-hash')}catch{$blocked=$true}
Check $blocked 'MALFORMED_EVENT_KEY_REJECTED'
# Windows-native synthetic lock: an EXCLUSIVELY OPEN FACAD-style log
# must not prevent hashing an independent in-scope non-log file.
$testBase=Join-Path $env:RUNNER_TEMP ("d3e27-test-"+[Guid]::NewGuid().ToString('N'))
$testRoot=Join-Path $testBase 'AppData\Roaming\Ilexis'
$logDir=Join-Path $testRoot 'LogFiles'
$null=New-Item -ItemType Directory -Path $logDir -Force
$readable=Join-Path $testRoot 'settings-synthetic.txt'
$log=Join-Path $logDir 'Facad.log'
[IO.File]::WriteAllText($readable,'synthetic nonclinical content')
$locked=$null
try{
  $locked=[IO.File]::Open($log,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
  $observed=Get-D3E27Snapshot -Root $testRoot
  Check ($observed.Count -eq 1) 'LOCKED_LOG_EXCLUDED_NOT_HASHED'
}finally{
  if($null -ne $locked){$locked.Dispose()}
  Remove-Item -LiteralPath $testBase -Recurse -Force -ErrorAction Stop
}
Write-Host 'D3E27_LOCKED_VENDOR_LOG_TESTS_PASSED=1'
Write-Host 'D3E27_SYNTHETIC_ORACLE_TESTS_PASSED=9'
Write-Host 'D3E27_VENDOR_EXECUTED_IN_TESTS=false'
Write-Host 'D3E27_CONTENT_OR_IDENTITY_EXPORT_IN_TESTS=false'
