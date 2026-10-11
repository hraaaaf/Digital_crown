# FAC-TRIAL-C / F04.1: allowlisted process-owned UIA metadata only.
# No tab selection, menu leaf invocation, export, save, load, patient reads or writes.
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
  throw 'F04.1 surface inventory: HWND / Facad PID mismatch'
}
$dir=[IO.Path]::GetFullPath($OutDir)
[void][IO.Directory]::CreateDirectory($dir)
$log=Join-Path $dir 'f04-1-surface-status.txt'
$csv=Join-Path $dir 'f04-1-surface-allowlist.csv'
'F04_1_SURFACE_SCOPE=PROCESS_OWNED_UIA_METADATA_ONLY' | Set-Content -Encoding utf8 $log
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
for($i=0;$i -lt $windows.Count;$i++){
  $window=$windows.Item($i)
  try{
    if($window.Current.ProcessId -eq $FacadProcessId -and
       $window.Current.NativeWindowHandle -ne $MainWindowHwnd){
      $scopes.Add($window)
    }
  }catch{}
}
$matched=0
$visible=0
$unique=New-Object 'System.Collections.Generic.HashSet[string]'
try{
  foreach($scope in $scopes){
    # Read metadata exclusively from the Facad process and allowlisted names.
    $nodes=$scope.FindAll(
      [System.Windows.Automation.TreeScope]::Descendants,
      [System.Windows.Automation.Condition]::TrueCondition)
    for($j=0;$j -lt $nodes.Count;$j++){
      $e=$nodes.Item($j)
      try{
        if($e.Current.ProcessId -ne $FacadProcessId){continue}
        $name=[string]$e.Current.Name
        if($targetNames -notcontains $name){continue}
        $type=[string]$e.Current.ControlType.ProgrammaticName
        $offscreen=[bool]$e.Current.IsOffscreen
        $selected='NOT_AVAILABLE'
        # Selection state is queried, never invoked; absent pattern is explicit.
        try{
          $pat=$e.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)
          $selected=[string]$pat.Current.IsSelected
        }catch{}
        $key="$name|$type|$($e.Current.BoundingRectangle)|$offscreen"
        if(-not $unique.Add($key)){continue}
        $matched++
        if(-not $offscreen){$visible++}
        if($matched -gt 100){throw 'UIA allowlist exceeded bounded result limit'}
        $values=@($name,$type,[string]$e.Current.IsEnabled,
                  [string]$offscreen,$selected,
                  [string]$e.Current.BoundingRectangle,
                  'FACAD_PROCESS_OWNED')
        Add-Content -Encoding utf8 $csv (($values|ForEach-Object {CsvField $_}) -join ',')
      }catch{
        if($_.Exception.Message -eq 'UIA allowlist exceeded bounded result limit'){throw}
      }
    }
  }
}finally{
  Record "WINDOW_SCOPES_SCANNED=$($scopes.Count)"
  Record "TARGET_ALLOWLIST_HITS=$matched"
  Record "TARGET_ALLOWLIST_VISIBLE=$visible"
  Record 'TAB_SELECT_INVOKED=false'
  Record 'LEAF_CLICK_INVOKED=false'
  Record 'SAVE_INVOKED=false'
  Record 'LOAD_INVOKED=false'
  Record 'EXPORT_INVOKED=false'
  Record 'NO_PATIENT_CONTENT_COLLECTED_BY_THIS_SCRIPT=true'
  Record 'SHARED_APP_STORAGE_ISOLATION=UNVERIFIED'
  Record 'F04_1_SURFACE_BEHAVIOR_PROVEN=false'
  Record 'F04_1_EXPORT_VALIDATED=false'
  Record 'FAC05_NUMERIC_PARITY_TESTED=false'
}
Record 'F04_1_ALLOWLIST_CENSUS_COMPLETE=true'
