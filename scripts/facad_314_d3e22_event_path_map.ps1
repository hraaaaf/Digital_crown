# D3E22 - Windows Security 4663 exact storage-scope identity.
# Source-only until called by a separate authorized experiment; never logs paths.
function Get-ScopedNtVolume {
 param([Parameter(Mandatory=$true)][string]$ScopeRoot)
 try {
  $root=[IO.Path]::GetFullPath($ScopeRoot)
  if($root -notmatch '^[A-Za-z]:\\'){return $null}
  if(-not ('D3E22.VolumeApi' -as [type])){
   Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;
namespace D3E22 {
 public static class VolumeApi {
  [DllImport("kernel32.dll", CharSet=CharSet.Unicode, EntryPoint="QueryDosDeviceW", SetLastError=true)]
  private static extern uint QueryDosDeviceW(string drive, StringBuilder buffer, uint length);
  public static string Current(string drive) {
   var buffer=new StringBuilder(2048);
   if(QueryDosDeviceW(drive,buffer,(uint)buffer.Capacity)==0) return null;
   return buffer.ToString().Split('\0')[0];
  }
 }
}
'@ -ErrorAction Stop
  }
  $device=[D3E22.VolumeApi]::Current($root.Substring(0,2))
  if($null -eq $device -or $device -cnotmatch '^\\Device\\HarddiskVolume[0-9]+$'){return $null}
  return $device
 }catch{return $null}
}

function Resolve-ScopedEventRelative {
 param(
  [Parameter(Mandatory=$true)][string]$ScopeRoot,
  [Parameter(Mandatory=$true)][string]$ObservedPath,
  [string]$ExpectedNtDevice = ''
 )
 if($ScopeRoot.Length -gt 4096 -or $ObservedPath.Length -gt 8192 -or
    $ScopeRoot.Contains([char]0) -or $ObservedPath.Contains([char]0)){return $null}
 $root=[IO.Path]::GetFullPath($ScopeRoot).TrimEnd('\')
 if($root -notmatch '^[A-Za-z]:\\' -or
    -not $root.EndsWith('\AppData\Roaming\Ilexis',[StringComparison]::OrdinalIgnoreCase)){
    return $null
 }
 $dosPrefix=$root+'\'
 if($ObservedPath.StartsWith($dosPrefix,[StringComparison]::OrdinalIgnoreCase)){
   $relative=$ObservedPath.Substring($dosPrefix.Length)
 }else{
   if($ExpectedNtDevice -cnotmatch '^\\Device\\HarddiskVolume[0-9]+$'){return $null}
   $ntPrefix=$ExpectedNtDevice+$root.Substring(2)+'\'
   if(-not $ObservedPath.StartsWith($ntPrefix,[StringComparison]::OrdinalIgnoreCase)){return $null}
   $relative=$ObservedPath.Substring($ntPrefix.Length)
 }
 if([string]::IsNullOrWhiteSpace($relative) -or $relative.Length -gt 4096 -or
    $relative.StartsWith('\') -or $relative.Contains('/') -or $relative.Contains(':')){
    return $null
 }
 $segments=$relative.Split('\')
 if(@($segments | Where-Object {$_ -eq '' -or $_ -eq '.' -or $_ -eq '..'}).Count){
   return $null
 }
 return $relative
}
