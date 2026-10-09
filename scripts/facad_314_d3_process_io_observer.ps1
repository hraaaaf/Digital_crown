# EXPERIMENTAL process-level I/O sampling, not file-path tracing or isolation proof.
# Designed for a fresh Windows runner; no command lines, filenames, registry or file contents read.
param(
  [Parameter(Mandatory=$true)][ValidateRange(1,2147483647)][int]$TargetPid,
  [Parameter(Mandatory=$true)][ValidateRange(3,30)][int]$DurationSeconds,
  [Parameter(Mandatory=$true)][string]$OutputPath
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$workspace=[IO.Path]::GetFullPath($env:GITHUB_WORKSPACE).TrimEnd('\')
$outFull=[IO.Path]::GetFullPath($OutputPath)
if(-not $outFull.StartsWith($workspace+'\', [StringComparison]::OrdinalIgnoreCase)){
  throw 'D3 process observation output must remain in the workspace'
}
if(Test-Path -LiteralPath $outFull){throw 'D3 output already exists; refusing overwrite'}

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class D3SafeProcessIoCounters {
  [StructLayout(LayoutKind.Sequential)]
  public struct Counters {
    public ulong ReadOperationCount, WriteOperationCount, OtherOperationCount;
    public ulong ReadTransferCount, WriteTransferCount, OtherTransferCount;
  }
  [DllImport("kernel32.dll", SetLastError = true)]
  public static extern bool GetProcessIoCounters(IntPtr handle, out Counters counters);
}
'@

function Get-SafeCounters([int]$id){
  $proc=[Diagnostics.Process]::GetProcessById($id)
  try{
    $c=[D3SafeProcessIoCounters+Counters]::new()
    if(-not [D3SafeProcessIoCounters]::GetProcessIoCounters($proc.Handle,[ref]$c)){
      throw 'Windows process I/O counter query failed'
    }
    return @{
      write_ops=[uint64]$c.WriteOperationCount
      write_bytes=[uint64]$c.WriteTransferCount
      read_ops=[uint64]$c.ReadOperationCount
      read_bytes=[uint64]$c.ReadTransferCount
    }
  }finally{$proc.Dispose()}
}
function Read-ProcessIds([int]$rootId){
  # Only PID / parent PID, no command line, executable path, environment or window title.
  $rows=@(Get-CimInstance -ClassName Win32_Process -Property ProcessId,ParentProcessId -ErrorAction Stop)
  if(-not (@($rows | Where-Object {[int]$_.ProcessId -eq $rootId}).Count)){
    throw 'Target process absent in process lineage enumeration'
  }
  $ids=@{};$ids[$rootId]=$true
  $changed=$true
  while($changed){
    $changed=$false
    foreach($p in $rows){
      $pidNow=[int]$p.ProcessId;$parent=[int]$p.ParentProcessId
      if($ids.ContainsKey($parent) -and -not $ids.ContainsKey($pidNow)){
        $ids[$pidNow]=$true;$changed=$true
      }
    }
  }
  return @($ids.Keys | ForEach-Object {[int]$_})
}

$baselines=@{}
$latest=@{}
$observedPids=@{}
$rootPolls=0
$sampleCount=0
$intervalMs=500
$polls=$DurationSeconds*2
for($poll=0;$poll -lt $polls;$poll++){
  $ids=@(Read-ProcessIds $TargetPid)
  foreach($id in $ids){
    $counter=Get-SafeCounters ([int]$id)
    if(-not $baselines.ContainsKey($id)){$baselines[$id]=$counter}
    $latest[$id]=$counter
    $observedPids[$id]=$true
    if($id -eq $TargetPid){$rootPolls++}
  }
  $sampleCount++
  if($poll -lt ($polls-1)){Start-Sleep -Milliseconds $intervalMs}
}
if($rootPolls -ne $sampleCount -or $sampleCount -lt 2){
  throw 'D3 root process counter coverage incomplete'
}
$writes=[uint64]0;$writeOps=[uint64]0;$reads=[uint64]0;$readOps=[uint64]0
foreach($key in $latest.Keys){
  $a=$baselines[$key];$b=$latest[$key]
  if($b.write_bytes -lt $a.write_bytes -or $b.write_ops -lt $a.write_ops -or
     $b.read_bytes -lt $a.read_bytes -or $b.read_ops -lt $a.read_ops){
    throw 'Counter rollover or PID reuse: observation not interpretable'
  }
  $writes+=$b.write_bytes-$a.write_bytes
  $writeOps+=$b.write_ops-$a.write_ops
  $reads+=$b.read_bytes-$a.read_bytes
  $readOps+=$b.read_ops-$a.read_ops
}
# This does NOT establish which files, if any, were written. Fast-lived children
# can escape polling; process I/O also includes non-filesystem operations.
$result=@{
  schema='facad314_d3_process_io_v1'
  sample_count=$sampleCount
  target_observed_every_poll=$true
  related_processes_observed=$observedPids.Count
  write_transfer_bytes_delta=$writes
  write_operation_count_delta=$writeOps
  read_transfer_bytes_delta=$reads
  read_operation_count_delta=$readOps
  path_attribution_available=$false
  complete_child_process_coverage=$false
  registry_values_read=$false
  files_or_command_lines_read=$false
  d3_isolation_verified=$false
  clinical_edit_allowed=$false
  verdict='INCONCLUSIVE_PROCESS_IO_COUNTERS_ONLY'
}
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $outFull -Encoding utf8
Write-Host 'D3_PROCESS_IO_CAPTURE_COMPLETE=true'
Write-Host "D3_PROCESS_IO_SAMPLES=$sampleCount"
Write-Host "D3_PROCESS_IO_RELATED_PROCESSES=$($observedPids.Count)"
Write-Host "D3_PROCESS_IO_WRITE_TRANSFER_BYTES_DELTA=$writes"
Write-Host 'D3_PROCESS_IO_PATH_ATTRIBUTION=false'
Write-Host 'D3_ISOLATION_VERIFIED=false'
Write-Host 'CLINICAL_EDIT_ALLOWED=false'
