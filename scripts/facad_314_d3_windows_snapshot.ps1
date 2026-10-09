# Facad D3 EXPERIMENTAL instrumentation; metadata-only except the official bundled Examples.
# NO registry value reads, NO license keys, NO real patients, NO clinical changes.
param(
  [Parameter(Mandatory=$true)][ValidateSet('before','after')][string]$Phase,
  [Parameter(Mandatory=$true)][string]$SessionId,
  [Parameter(Mandatory=$true)][string]$OfficialExamples,
  [Parameter(Mandatory=$true)][string]$DisposableExamples,
  [Parameter(Mandatory=$true)][string]$InstallDirectory,
  [Parameter(Mandatory=$true)][string]$OutputPath
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

function Sha([string]$value) {
  $bytes=[Text.Encoding]::UTF8.GetBytes($value)
  $sha=[Security.Cryptography.SHA256]::Create()
  try { return [BitConverter]::ToString($sha.ComputeHash($bytes)).Replace('-','').ToLowerInvariant() }
  finally { $sha.Dispose() }
}
function FileDigest([string]$path) {
  $sha=(Get-FileHash -LiteralPath $path -Algorithm SHA256 -ErrorAction Stop).Hash
  return $sha.ToLowerInvariant()
}
function SafeRoot([string]$path) {
  if([string]::IsNullOrWhiteSpace($path)) {throw 'Missing scope root'}
  return [IO.Path]::GetFullPath($path).TrimEnd('\').ToLowerInvariant()
}
function Entry([string]$hash,[long]$size) {
  return @{sha256=$hash;size=$size}
}
function TreeScope([string]$path,[bool]$officialContent) {
  $root=SafeRoot $path
  $scope=@{kind='filetree';root_fingerprint=(Sha $root);capture_ok=$true;present=$false;entries=@{}}
  try {
    if(-not (Test-Path -LiteralPath $root)){return $scope}
    if(-not (Test-Path -LiteralPath $root -PathType Container)){throw 'Root is not a directory'}
    $scope.present=$true
    $files=@(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop)
    if($files.Count -gt 5000){throw 'File enumeration cap'}
    foreach($file in $files){
      $relative=$file.FullName.Substring($root.Length).TrimStart('\','/')
      if(-not $relative -or $relative.Contains('..')){throw 'Untrusted relative path'}
      # Never read registry/license/credential files, even to hash.
      if($file.Name -match '(?i)licen[cs]e|secret|password|token|credential' -or
         $file.Extension -match '(?i)^\.(key|pem|pfx|p12|lic|license)$'){
        throw 'Restricted file under monitored root; scope incomplete'
      }
      $key=Sha $relative.ToLowerInvariant()
      if($scope.entries.ContainsKey($key)){throw 'Duplicate canonical relative key'}
      if($officialContent){
        # Content hashing is allowed ONLY for bundled/disposable official demo Examples.
        if($file.Length -gt 100MB){throw 'Example file size cap'}
        $digest=FileDigest $file.FullName
      } else {
        # Metadata-only fingerprint prevents consuming Facad config/database/license bytes.
        $digest=Sha ("size=$($file.Length);mtime=$($file.LastWriteTimeUtc.Ticks)")
      }
      $scope.entries[$key]=Entry $digest ([long]$file.Length)
    }
  } catch {
    $scope.capture_ok=$false
    $scope.entries=@{}
  }
  return $scope
}
function RegistryScope([string[]]$roots,[string]$identity) {
  # Key structure ONLY: Get-Item/Get-ChildItem. Do not use Get-ItemProperty.
  # Windows registry values can contain license tokens / patient info; intentionally UNSAMPLED.
  $scope=@{kind='registry';root_fingerprint=(Sha $identity.ToLowerInvariant());capture_ok=$true;present=$false;entries=@{}}
  try {
    foreach($root in $roots){
      if(-not (Test-Path -LiteralPath $root)){continue}
      $scope.present=$true
      $keys=@(Get-Item -LiteralPath $root -ErrorAction Stop)
      $keys+=@(Get-ChildItem -LiteralPath $root -Recurse -ErrorAction Stop)
      if($keys.Count -gt 2000){throw 'Registry key enumeration cap'}
      foreach($key in $keys){
        $id=Sha ($key.Name.ToLowerInvariant())
        if($scope.entries.ContainsKey($id)){continue}
        $scope.entries[$id]=Entry (Sha 'KEY_PRESENT_VALUE_CONTENT_UNOBSERVED') 0
      }
    }
  }catch{
    $scope.capture_ok=$false
    $scope.entries=@{}
  }
  return $scope
}

if($SessionId -notmatch '^[A-Za-z0-9_-]{1,128}$'){throw 'Invalid session ID'}
$official=SafeRoot $OfficialExamples
$copy=SafeRoot $DisposableExamples
$install=SafeRoot $InstallDirectory
$workspace=SafeRoot $env:GITHUB_WORKSPACE
if($official -eq $copy -or (-not $official.StartsWith($workspace+'\')) -or
  (-not $copy.StartsWith($workspace+'\')) -or
  (-not $official.EndsWith('\release\examples')) -or
  (-not $copy.EndsWith('\d3-app-copy'))){
  throw 'D3 root identity mismatch: official and disposable example must be disjoint workspace paths'
}
if(-not (Test-Path -LiteralPath (Join-Path $official 'Robert-2.0.fcd') -PathType Leaf) -or
  -not (Test-Path -LiteralPath (Join-Path $copy 'Robert-2.0.fcd') -PathType Leaf)){
  throw 'Official Robert sample and disposable copy must both exist'
}
$homeDocs=[Environment]::GetFolderPath('MyDocuments')
if([string]::IsNullOrWhiteSpace($homeDocs)){throw 'Documents scope unavailable'}
$scopes=@{
  official_examples_tree=TreeScope $official $true
  disposable_examples_tree=TreeScope $copy $true
  facad_install_tree=TreeScope $install $false
  facad_appdata_roaming=TreeScope (Join-Path $env:APPDATA 'Facad') $false
  facad_appdata_local=TreeScope (Join-Path $env:LOCALAPPDATA 'Facad') $false
  facad_programdata=TreeScope (Join-Path $env:ProgramData 'Facad') $false
  facad_documents=TreeScope (Join-Path $homeDocs 'Facad') $false
  facad_registry_hkcu=RegistryScope @('HKCU:\Software\Facad','HKCU:\Software\Citodent\Facad') 'HKCU:Facad+CitodentFacad'
  facad_registry_hklm=RegistryScope @('HKLM:\Software\Facad','HKLM:\Software\Citodent\Facad','HKLM:\Software\WOW6432Node\Facad') 'HKLM:Facad+CitodentFacad'
}
$result=@{schema='facad314_d3_snapshot_v1';phase=$Phase;session_id=$SessionId;scopes=$scopes}
$outFull=[IO.Path]::GetFullPath($OutputPath)
if(-not $outFull.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Snapshot output outside workspace'}
$result | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $outFull -Encoding utf8
$errors=@($scopes.Keys | Where-Object {-not $scopes[$_].capture_ok})
Write-Host "D3_SNAPSHOT_PHASE=$Phase"
Write-Host "D3_SCOPE_COUNT=$($scopes.Count)"
Write-Host "D3_SCOPE_CAPTURE_FAILURE_COUNT=$($errors.Count)"
Write-Host 'D3_REGISTRY_VALUES_SAMPLED=false'
Write-Host 'D3_INSTALL_FILE_CONTENT_SAMPLED=false'
Write-Host 'D3_APP_STORAGE_ISOLATION=UNVERIFIED'
Write-Host 'CLINICAL_EDIT_ALLOWED=false'
if($errors.Count){throw 'One or more monitoring scopes incomplete; no isolation claim allowed'}
