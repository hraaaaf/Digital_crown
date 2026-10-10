# D3E22: synthetic-only path alias tests. Dot-sources a pure function; no FACAD launch.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'facad_314_d3e22_event_path_map.ps1')
$root='C:\Users\example\AppData\Roaming\Ilexis'
$checks=@(
 @{ observed='C:\Users\example\AppData\Roaming\Ilexis\settings.bin'; expected='settings.bin' },
 @{ observed='\Device\HarddiskVolume3\Users\example\AppData\Roaming\Ilexis\settings.bin'; expected='settings.bin' },
 @{ observed='\Device\HarddiskVolume3\Users\example\AppData\Roaming\Ilexis\cache\settings.bin'; expected='cache\settings.bin' },
 @{ observed='C:\Users\example\AppData\Roaming\IlexisX\settings.bin'; expected=$null },
 @{ observed='D:\Users\example\AppData\Roaming\Ilexis\settings.bin'; expected=$null },
 @{ observed='\Device\HarddiskVolume3\Users\another\AppData\Roaming\Ilexis\settings.bin'; expected=$null },
 @{ observed='\Device\HarddiskVolume3\Temp\Users\example\AppData\Roaming\Ilexis\settings.bin'; expected=$null },
 @{ observed='\Device\HarddiskVolume3\Users\example\AppData\Roaming\Ilexis\..\outside'; expected=$null },
 @{ observed='\Device\HarddiskVolume3\Users\example\AppData\Roaming\Ilexis\cache\\double.bin'; expected=$null },
 @{ observed='\Device\HarddiskVolume3\Users\example\AppData\Roaming\Ilexis\cache\foo:bar'; expected=$null },
 @{ observed='\Device\HarddiskVolume3\Users\example\AppData\Roaming\Ilexis'; expected=$null }
)
$count=0
foreach($check in $checks){
  $actual=Resolve-ScopedEventRelative -ScopeRoot $root -ObservedPath $check.observed
  if($actual -cne $check.expected){throw 'D3E22_ALIAS_SYNTHETIC_CASE_FAILED'}
  $count++
}
Write-Host "D3E22_SOURCE_ALIAS_TESTS_PASSED=$count"
Write-Host 'D3E22_REAL_ILEXIS_FILE_TOUCHED=false'
Write-Host 'D3E22_FACAD_EXECUTED=false'
Write-Host 'CLINICAL_EDIT_ALLOWED=false'
