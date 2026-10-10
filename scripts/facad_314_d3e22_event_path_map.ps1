# D3E22: pure path-identity adapter for observed 4663 ObjectName.
# No filesystem, Security log, patient/license read or event export occurs here.
function Resolve-ScopedEventRelative {
 param(
  [Parameter(Mandatory=$true)][string]$ScopeRoot,
  [Parameter(Mandatory=$true)][string]$ObservedPath
 )
 if($ScopeRoot.Length -gt 4096 -or $ObservedPath.Length -gt 8192){return $null}
 if($ScopeRoot.Contains([char]0) -or $ObservedPath.Contains([char]0)){return $null}
 $root=[IO.Path]::GetFullPath($ScopeRoot).TrimEnd('\')
 if($root.Length -lt 4 -or $root[1] -cne ':' -or $root[2] -cne '\'){return $null}
 if(-not $root.EndsWith('\AppData\Roaming\Ilexis',[StringComparison]::OrdinalIgnoreCase)){return $null}
 $normalPrefix=$root+'\'
 $relative=$null
 if($ObservedPath.StartsWith($normalPrefix,[StringComparison]::OrdinalIgnoreCase)){
   $relative=$ObservedPath.Substring($normalPrefix.Length)
 } else {
   # Native 4663 can express the same volume by device name instead of C:\.
   # Only accept a known NT volume alias and the ENTIRE user-specific root tail.
   # Never infer user-specific storage from a basename or 'Ilexis' alone.
   $rootTail=$root.Substring(2)+'\'
   $index=$ObservedPath.IndexOf($rootTail,[StringComparison]::OrdinalIgnoreCase)
   if($index -lt 0){return $null}
   $prefix=$ObservedPath.Substring(0,$index)
   if($prefix -cnotmatch '^\\Device\\HarddiskVolume[0-9]+$'){return $null}
   $relative=$ObservedPath.Substring($index+$rootTail.Length)
 }
 if([string]::IsNullOrWhiteSpace($relative) -or
    $relative.Length -gt 4096 -or $relative.StartsWith('\') -or
    $relative.Contains('/') -or $relative.Contains(':')){return $null}
 $segments=$relative.Split('\')
 if(@($segments | Where-Object { $_ -eq '' -or $_ -eq '.' -or $_ -eq '..' }).Count -gt 0){
   return $null
 }
 return $relative
}
