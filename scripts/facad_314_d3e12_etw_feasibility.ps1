# FAC-03 D3E12 ETW synthetic feasibility ONLY.
# This never opens or changes Facad/Ilexis, user records, or licences.
param([Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$traceName='D3E12_'+[guid]::NewGuid().ToString('N')
$root=$null;$etl=$null;$started=$false;$stopped=$false
$verified=$false;$providerAvailable=$false;$parsed=$false
$eventsCount=0;$matchedWrites=0;$matchedChild=0;$matchedOthers=0
$query='unavailable';$outputReady=$false;$rawGone=$false
try{
 if($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_OS -cne 'Windows' -or
    -not $env:RUNNER_TEMP -or -not $env:GITHUB_WORKSPACE -or -not $env:GITHUB_RUN_ID){throw 'RUNNER_ONLY'}
 $ws=[IO.Path]::GetFullPath($env:GITHUB_WORKSPACE).TrimEnd('\')
 $dest=[IO.Path]::GetFullPath($OutputPath)
 if(-not $dest.StartsWith($ws+'\', [StringComparison]::OrdinalIgnoreCase) -or
    [IO.Path]::GetFileName($dest) -cne 'd3e12-etw-feasibility.json' -or
    (Test-Path -LiteralPath $dest)){throw 'PUBLIC_OUTPUT_REJECTED'}
 $temp=[IO.Path]::GetFullPath($env:RUNNER_TEMP).TrimEnd('\')
 $root=Join-Path $temp $traceName
 New-Item -ItemType Directory -Path $root -ErrorAction Stop | Out-Null
 $etl=Join-Path $root 'local-trace.etl'
 $worker=Join-Path $root 'synthetic-writer.ps1'
 $name='d3e12-only-'+[guid]::NewGuid().ToString('N')+'.txt'
 $sentinel=Join-Path $root $name
 $workerCode=@'
param([Parameter(Mandatory=$true)][string]$SyntheticPath)
[IO.File]::WriteAllText($SyntheticPath,'D3E12_SYNTHETIC_NONCLINICAL_ONLY')
'@
 [IO.File]::WriteAllText($worker,$workerCode,[Text.Encoding]::UTF8)
 $provider=@(& logman.exe query providers 'Microsoft-Windows-Kernel-File' 2>$null)
 $providerAvailable=($LASTEXITCODE -eq 0 -and $provider.Count -gt 0)
 if($providerAvailable){
   # FILENAME=0x10 FILEIO=0x20 CREATE=0x80 WRITE=0x200 => 0x2B0.
   & logman.exe start $traceName '-p' 'Microsoft-Windows-Kernel-File' '0x2B0' '5' '-o' $etl '-f' 'bincirc' '-max' '12' '-ets' >$null 2>$null
   if($LASTEXITCODE -ne 0){throw 'TRACE_START_UNAVAILABLE'}
   $started=$true
 }
 if($started){
   $exe=(Get-Command pwsh -ErrorAction Stop).Source
   $argsText='-NoLogo -NoProfile -NonInteractive -File "'+$worker+'" -SyntheticPath "'+$sentinel+'"'
   $child=Start-Process -FilePath $exe -ArgumentList $argsText -Wait -PassThru -ErrorAction Stop
   $verified=($child.ExitCode -eq 0 -and (Test-Path -LiteralPath $sentinel -PathType Leaf) -and
       [IO.File]::ReadAllText($sentinel) -ceq 'D3E12_SYNTHETIC_NONCLINICAL_ONLY')
   Start-Sleep -Milliseconds 500
   & logman.exe stop $traceName '-ets' >$null 2>$null
   if($LASTEXITCODE -ne 0){throw 'TRACE_STOP_FAILED'}
   $stopped=$true
   if($verified -and (Test-Path -LiteralPath $etl)){
     $events=@()
     try{
       $events=@(Get-WinEvent -Path $etl -Oldest -MaxEvents 20000 -ErrorAction Stop)
       if($events.Count -ge 20000){throw 'EVENT_CAP'}
       $parsed=$true;$query='events_returned'
     }catch{
       $errorId=[string]$_.FullyQualifiedErrorId
       $query=if($errorId -like 'NoMatchingEventsFound*'){'no_matching_events'}else{'query_error'}
     }
     if($parsed){
       $objects=@{}
       foreach($ev in $events){
         try{
           if($ev.ProviderName -cne 'Microsoft-Windows-Kernel-File'){continue}
           [xml]$xml=$ev.ToXml();$fields=@{}
           foreach($v in $xml.Event.EventData.Data){$fields[[string]$v.Name]=[string]$v.'#text'}
           if($ev.Id -eq 12 -and $fields.ContainsKey('FileName') -and $fields.ContainsKey('FileObject')){
             $fn=[string]$fields['FileName']
             if($fn.EndsWith('\'+$name,[StringComparison]::OrdinalIgnoreCase) -or
                $fn.Equals($name,[StringComparison]::OrdinalIgnoreCase)){
               $objects[[string]$fields['FileObject']]=$true
             }
           }
           if($ev.Id -eq 16 -and $fields.ContainsKey('FileObject') -and
              $objects.ContainsKey([string]$fields['FileObject'])){
             $matchedWrites++
             $pidText=[string]$xml.Event.System.Execution.ProcessID
             if($pidText -match '^[0-9]+$' -and [long]$pidText -eq [long]$child.Id){
               $matchedChild++
             }else{$matchedOthers++}
           }
         }catch{
           $query='parse_error';$parsed=$false
           $matchedWrites=0;$matchedChild=0;$matchedOthers=0
           break
         }
       }
       $eventsCount=$events.Count
     }
   }
 }
 $outputReady=$true
}catch{
 # Don't print errors, raw trace path, process IDs, or file names.
 $query='probe_error'
}finally{
 if($started -and -not $stopped){
   try{
     & logman.exe stop $traceName '-ets' >$null 2>$null
     if($LASTEXITCODE -eq 0){$stopped=$true}
   }catch{}
 }
 if($null -ne $root -and (Test-Path -LiteralPath $root)){
   try{Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction Stop}catch{}
 }
 $rawGone=($null -ne $root -and -not (Test-Path -LiteralPath $root))
}
if(-not $rawGone){Write-Host 'D3E12_PRIVATE_ETW_CLEANUP_FAILED=true';exit 2}
if(-not $outputReady){$matchedWrites=0;$matchedChild=0;$matchedOthers=0}
if($matchedWrites -gt 4000 -or $matchedChild -gt $matchedWrites){
 Write-Host 'D3E12_EVENT_COUNT_UNSAFE=true';exit 2
}
$result=[ordered]@{
 schema='facad314_d3e12_synthetic_kernel_file_etw_v1'
 source='WINDOWS_EPHEMERAL_SYNTHETIC_FILE_ONLY'
 provider='Microsoft-Windows-Kernel-File'
 provider_discovered=$providerAvailable
 trace_started=$started
 trace_stopped=$stopped
 synthetic_write_verified=$verified
 etl_query_status=$query
 etl_events_parsed=$parsed
 etl_event_count=[int]$eventsCount
 synthetic_file_matched_write_event_count=[int]$matchedWrites
 synthetic_writer_pid_matched_write_event_count=[int]$matchedChild
 other_or_unknown_pid_matched_write_event_count=[int]$matchedOthers
 raw_trace_and_worker_deleted=$rawGone
 raw_etl_exported=$false
 private_file_identity_exported=$false
 process_pid_exported=$false
 clinical_file_touched=$false
 actual_ilexis_writer_identified=$false
 file_write_completion_proven=$false
 complete_etw_delivery_proven=$false
 shared_app_storage_isolation_verified=$false
 clinical_edit_allowed=$false
 verdict='SYNTHETIC_ETW_FEASIBILITY_NOT_ILEXIS_CAUSALITY'
}
$result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $dest -Encoding utf8 -ErrorAction Stop
Write-Host "D3E12_ETW_QUERY_STATUS=$query"
Write-Host "D3E12_SYNTHETIC_FILE_WRITE_EVENT_MATCH_COUNT=$matchedWrites"
Write-Host "D3E12_SYNTHETIC_WRITER_PID_EVENT_MATCH_COUNT=$matchedChild"
Write-Host "D3E12_RAW_TRACE_CLEANED=$($rawGone.ToString().ToLowerInvariant())"
Write-Host 'D3E12_ACTUAL_ILEXIS_WRITER_IDENTIFIED=false'
Write-Host 'CLINICAL_EDIT_ALLOWED=false'
