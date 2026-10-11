# FACAD D3E27 local-only bounded SHA-256 oracle. No filenames/digests exported.
# Hashing reads bytes locally; it does not inspect, print or transfer content.
Set-StrictMode -Version Latest

# Share-aware reader: Windows applications often keep append-only log files open.
# A sharing violation is explicitly UNKNOWN, never treated as a zero-length file,
# a missing file, or evidence of a mutation. All other IO failures fail closed.
$script:D3E27_UNREADABLE='D3E27_UNREADABLE_SHARING_VIOLATION'
function Get-D3E27SharedDigest {
  param([Parameter(Mandatory=$true)][string]$Path)
  for($attempt=0;$attempt -lt 3;$attempt++){
    $stream=$null;$sha=$null
    try {
      $share=[IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete
      $stream=[IO.FileStream]::new($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,$share)
      if($stream.Length -gt 67108864){throw 'D3E27_OPEN_FILE_TOO_BIG'}
      $startLength=$stream.Length
      $sha=[Security.Cryptography.SHA256]::Create()
      $hash=[Convert]::ToHexString($sha.ComputeHash($stream)).ToLowerInvariant()
      if($stream.Position -ne $startLength -or $stream.Length -ne $startLength){
        throw 'D3E27_UNSTABLE_FILE_WHILE_HASHING'
      }
      return [pscustomobject]@{ digest=$hash; length=[long]$startLength }
    }catch [IO.IOException] {
      # 32 = sharing violation; 33 = lock violation. No private filenames in logs.
      $win32=($_.Exception.HResult -band 0xffff)
      if($win32 -notin @(32,33)){throw 'D3E27_UNEXPECTED_IO_ERROR'}
      if($attempt -eq 2){
        return [pscustomobject]@{ digest=$script:D3E27_UNREADABLE; length=-1 }
      }
      Start-Sleep -Milliseconds 100
    }finally{
      if($null -ne $sha){$sha.Dispose()}
      if($null -ne $stream){$stream.Dispose()}
    }
  }
  throw 'D3E27_HASH_RETRY_EXHAUSTED'
}

function Get-D3E27Snapshot {
  param([Parameter(Mandatory=$true)][string]$Root)
  $full=[IO.Path]::GetFullPath($Root).TrimEnd('\')
  if($full -cnotmatch '^[A-Za-z]:\\' -or
     -not $full.EndsWith('\AppData\Roaming\Ilexis',[StringComparison]::OrdinalIgnoreCase)){
     throw 'D3E27_SCOPE_INVALID'
  }
  if(-not (Test-Path -LiteralPath $full -PathType Container)){throw 'D3E27_SCOPE_ABSENT'}
  $rootItem=Get-Item -LiteralPath $full -Force -ErrorAction Stop
  if(($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'D3E27_SCOPE_REPARSE'}
  $dirs=@(Get-ChildItem -LiteralPath $full -Directory -Recurse -Force -ErrorAction Stop)
  if($dirs.Count -gt 3000){throw 'D3E27_DIR_CAP'}
  foreach($dir in $dirs){
    if(($dir.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'D3E27_CHILD_REPARSE'}
  }
  $files=@(Get-ChildItem -LiteralPath $full -File -Recurse -Force -ErrorAction Stop)
  if($files.Count -gt 3000){throw 'D3E27_FILE_CAP'}
  $map=@{};$total=[long]0
  foreach($file in $files){
    if(($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'D3E27_FILE_REPARSE'}
    if($file.Length -gt 67108864){throw 'D3E27_SINGLE_FILE_TOO_BIG'}
    $total+=[long]$file.Length
    if($total -gt 268435456){throw 'D3E27_TOTAL_BYTES_CAP'}
    $relative=$file.FullName.Substring($full.Length).TrimStart('\')
    if([string]::IsNullOrWhiteSpace($relative) -or $relative.Contains('/') -or
       $relative.Contains(':') -or $relative.Contains('..')){throw 'D3E27_BAD_IDENTITY'}
    # Same SHA-256 private relative-key derivation as D3E2 event manifest.
    $id=[Convert]::ToHexString(
      [Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($relative.ToLowerInvariant()))
    ).ToLowerInvariant()
    if($map.ContainsKey($id)){throw 'D3E27_DUPLICATE_IDENTITY'}
    $map[$id]=Get-D3E27SharedDigest -Path $file.FullName
  }
  return ,$map
}
function Get-D3E27Delta {
  param([hashtable]$Before,[hashtable]$After)
  $ids=@($Before.Keys)+@($After.Keys)
  $changed=New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal)
  $created=0;$deleted=0;$content=0;$size=0
  foreach($id in ($ids | Sort-Object -Unique)){
    # An unreadable file is UNKNOWN: do not invent creates/deletes/changes.
    if(($Before.ContainsKey($id) -and $Before[$id].digest -ceq $script:D3E27_UNREADABLE) -or
       ($After.ContainsKey($id) -and $After[$id].digest -ceq $script:D3E27_UNREADABLE)){continue}
    if(-not $Before.ContainsKey($id)){$null=$changed.Add($id);$created++;continue}
    if(-not $After.ContainsKey($id)){$null=$changed.Add($id);$deleted++;continue}
    if($Before[$id].digest -cne $After[$id].digest){
      $null=$changed.Add($id);$content++
      if($Before[$id].length -ne $After[$id].length){$size++}
    }
  }
  return [pscustomobject]@{
    changed_keys=@($changed)
    changed_count=[int]$changed.Count
    created_count=$created
    deleted_count=$deleted
    content_changed_count=$content
    different_size_content_changed_count=$size
  }
}
function Get-D3E27StableResult {
  param(
    [hashtable]$ControlBefore,[hashtable]$ControlAfter,
    [hashtable]$ActiveBefore,[hashtable]$AfterStopped,[hashtable]$AfterSettled,
    [string[]]$RootEventKeys
  )
  $negative=Get-D3E27Delta $ControlBefore $ControlAfter
  $active=Get-D3E27Delta $ActiveBefore $AfterStopped
  $settle=Get-D3E27Delta $ActiveBefore $AfterSettled
  $unstable=Get-D3E27Delta $AfterStopped $AfterSettled
  $root=New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal)
  foreach($k in $RootEventKeys){
    if($k -cnotmatch '^[0-9a-f]{64}$'){throw 'D3E27_BAD_PRIVATE_EVENT_KEY'}
    $null=$root.Add($k)
  }
  $control=New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal)
  foreach($k in $negative.changed_keys){$null=$control.Add($k)}
  $settled=New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal)
  foreach($k in $settle.changed_keys){$null=$settled.Add($k)}
  $post=New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal)
  foreach($k in $active.changed_keys){$null=$post.Add($k)}
  $stable=0;$stableContents=0;$matched=0;$stableWithoutControl=0;$stableMatched=0
  foreach($id in $settled){
    if(-not $post.Contains($id)){continue}
    # Same state after FACAD termination AND after the settling delay.
    $p=$AfterStopped.ContainsKey($id);$q=$AfterSettled.ContainsKey($id)
    if($p -ne $q){continue}
    if($p -and ($AfterStopped[$id].digest -cne $AfterSettled[$id].digest)){continue}
    $stable++
    if($ActiveBefore.ContainsKey($id) -and $p){$stableContents++}
    if($root.Contains($id)){$matched++}
    if(-not $control.Contains($id)){
      $stableWithoutControl++
      if($root.Contains($id)){$stableMatched++}
    }
  }
  # Sharing-locked files remain unknown across this finite observation window.
  $unknown=0
  foreach($snapshot in @($ControlBefore,$ControlAfter,$ActiveBefore,$AfterStopped,$AfterSettled)){
    foreach($value in $snapshot.Values){
      if($value.digest -ceq $script:D3E27_UNREADABLE){$unknown++}
    }
  }
  # Never return per-file names or digests, even their private pseudonyms.
  return [ordered]@{
    sharing_locked_file_observations=$unknown
    hash_coverage_complete=($unknown -eq 0)
    schema='facad314_d3e27_persisted_content_aggregate_v1'
    negative_control_changed_count=$negative.changed_count
    after_facad_stop_changed_count=$active.changed_count
    after_settle_changed_count=$settle.changed_count
    post_stop_unstable_count=$unstable.changed_count
    stable_change_count=$stable
    stable_existing_file_content_changed_count=$stableContents
    stable_without_negative_control_count=$stableWithoutControl
    stable_root_pid_4663_overlap_count=$matched
    stable_root_pid_overlap_without_control_count=$stableMatched
    root_pid_unique_event_file_count=$root.Count
    sample_count_before_control=$ControlBefore.Count
    sample_count_before_facad=$ActiveBefore.Count
    sample_count_after_stop=$AfterStopped.Count
    sample_count_after_settle=$AfterSettled.Count
    sha256_bytes_read_locally=$true
    file_names_or_digests_exported=$false
    patient_files_or_settings_content_exported=$false
    stored_content_persistence_observed=($stableContents -gt 0)
    complete_process_causality_proven=$false
    complete_descendant_coverage_proven=$false
    shared_app_storage_isolation_verified=$false
    clinical_edit_allowed=$false
    verdict=$(if($unknown -gt 0){'PARTIAL_HASH_COVERAGE_BOUNDED_NO_FULL_SCOPE_CLAIM'}elseif($stableMatched -gt 0){'OBSERVED_STABLE_FILE_CONTENT_DRIFT_WITH_ROOT_PID_4663_OVERLAP_NOT_CAUSALITY'}elseif($stableContents -gt 0){'OBSERVED_STABLE_CONTENT_CHANGE_NO_ROOT_PID_OVERLAP'}elseif($stable -gt 0){'OBSERVED_STABLE_FILE_IDENTITY_CHANGE_NOT_CONTENT'}else{'NO_STABLE_CONTENT_DRIFT_OBSERVED_IN_BOUNDED_WINDOW'})
  }
}
