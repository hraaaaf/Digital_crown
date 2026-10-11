# FAC-TRIAL-C F04.1 — bounded vendor UIA exact-name allowlist inventory, no interaction.
# Deliberately no patient-field enumeration, no tab/menu selection and no Save/Load/Export.
param(
  [Parameter(Mandatory=$true)][int]$FacadProcessId,
  [Parameter(Mandatory=$true)][long]$MainWindowHwnd,
  [Parameter(Mandatory=$true)][string]$OutDir
)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$main=[System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$MainWindowHwnd)
if($null -eq $main -or $main.Current.ProcessId -ne $FacadProcessId){
  throw 'F04.1 inventory: vendor HWND/PID mismatch'
}
$dir=[IO.Path]::GetFullPath($OutDir)
[void][IO.Directory]::CreateDirectory($dir)
$log=Join-Path $dir 'f04-1-surface-status.txt'
$csv=Join-Path $dir 'f04-1-surface-allowlist.csv'
'F04_1_SURFACE_SCOPE=EXACT_NAME_PROCESS_OWNED_UIA_METADATA_ONLY' | Set-Content -Encoding utf8 $log
'surface,control_type,enabled,offscreen,selected,rect,scope' | Set-Content -Encoding utf8 $csv
function Record([string]$value){Add-Content -Encoding utf8 $log $value}
function CsvField([string]$value){return '"'+($value -replace '"','""')+'"'}
$targetNames=@('Values','Properties','Analysis Values','Analysis Properties','Marker Positions','Object Values')
$root=[System.Windows.Automation.AutomationElement]::RootElement
$windows=$root.FindAll(
  [System.Windows.Automation.TreeScope]::Children,
  [System.Windows.Automation.PropertyCondition]::new(
    [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
    [System.Windows.Automation.ControlType]::Window))
$scopes=New-Object 'System.Collections.Generic.List[System.Windows.Automation.AutomationElement]'
$scopes.Add($main)
$uiaErrors=0
for($i=0;$i -lt $windows.Count;$i++){
  $window=$windows.Item($i)
  try{
    if($window.Current.ProcessId -eq $FacadProcessId -and
       $window.Current.NativeWindowHandle -ne $MainWindowHwnd){$scopes.Add($window)}
  }catch{$uiaErrors++} # Count stale windows, never publish their names/exception details.
}
$matched=0
$visible=0
$unique=New-Object 'System.Collections.Generic.HashSet[string]'
try{
  foreach($name in $targetNames){
    $targetCount=0
    foreach($scope in $scopes){
      try{
        # Windows UIA filters by exact approved name *before* results reach this script.
        $condition=[System.Windows.Automation.PropertyCondition]::new(
          [System.Windows.Automation.AutomationElement]::NameProperty,$name)
        $nodes=$scope.FindAll([System.Windows.Automation.TreeScope]::Descendants,$condition)
      }catch{$uiaErrors++;continue}
      for($j=0;$j -lt $nodes.Count;$j++){
        try{
          $e=$nodes.Item($j)
          if($e.Current.ProcessId -ne $FacadProcessId){continue}
          $type=[string]$e.Current.ControlType.ProgrammaticName
          $offscreen=[bool]$e.Current.IsOffscreen
          $rect=[string]$e.Current.BoundingRectangle
          $enabled=[string]$e.Current.IsEnabled
          $selected='NOT_AVAILABLE'
          try{
            $pat=$e.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)
            $selected=[string]$pat.Current.IsSelected
          }catch{} # Unsupported optional pattern, not an inventory failure.
          $key="$name|$type|$rect|$offscreen"
          if(-not $unique.Add($key)){continue}
          $matched++
          $targetCount++
          if(-not $offscreen){$visible++}
          if($matched -gt 100){throw 'FACAD_UIA_LIMIT_EXCEEDED'}
          $values=@($name,$type,$enabled,[string]$offscreen,$selected,$rect,
                    'FACAD_PROCESS_OWNED')
          Add-Content -Encoding utf8 $csv (($values|ForEach-Object {CsvField $_}) -join ',')
        }catch{
          if($_.Exception.Message -eq 'FACAD_UIA_LIMIT_EXCEEDED'){throw}
          $uiaErrors++ # No patient labels or untrusted exception text in evidence.
        }
      }
    }
    if($targetCount -gt 0){
      Record "TARGET_$([array]::IndexOf($targetNames,$name))=OBSERVED_COUNT_$targetCount"
    }else{
      Record "TARGET_$([array]::IndexOf($targetNames,$name))=NOT_OBSERVED_IN_CURRENT_STATE"
    }
  }
}finally{
  Record "WINDOW_SCOPES_SCANNED=$($scopes.Count)"
  Record "TARGET_ALLOWLIST_HITS=$matched"
  Record "TARGET_ALLOWLIST_VISIBLE=$visible"
  Record "UIA_READ_ERRORS=$uiaErrors"
  Record 'NO_VENDOR_CONTROL_ACTIVATED_BY_THIS_SCRIPT=true'
  Record 'TAB_SELECT_INVOKED=false'
  Record 'LEAF_CLICK_INVOKED=false'
  Record 'SAVE_INVOKED=false'
  Record 'LOAD_INVOKED=false'
  Record 'EXPORT_INVOKED=false'
  Record 'PERSISTED_UIA_NAMES=ALLOWLIST_ONLY'
  Record 'SHARED_APP_STORAGE_ISOLATION=UNVERIFIED'
  Record 'F04_1_SURFACE_BEHAVIOR_PROVEN=false'
  Record 'F04_1_EXPORT_VALIDATED=false'
  Record 'FAC05_NUMERIC_PARITY_TESTED=false'
}
if($uiaErrors -gt 0){
  Record 'F04_1_INVENTORY_VERDICT=INCONCLUSIVE_UIA_READ_ERRORS'
  throw 'F04.1 UIA read errors: census incomplete, no negative claims'
}
Record 'F04_1_INVENTORY_VERDICT=COMPLETE_CURRENT_STATE_ONLY'
Record 'F04_1_ALLOWLIST_CENSUS_COMPLETE=true'
