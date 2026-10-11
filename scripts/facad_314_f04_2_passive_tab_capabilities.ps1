# F04.2 read-only capability inventory of two allowlisted FACAD tabs.
# Does not select tabs, inspect child contents, invoke patterns, read patient data,
# change global application settings, Save, Load, Export, or edit anything.
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
  throw 'F04.2 vendor PID/HWND scope mismatch'
}
$dir=[IO.Path]::GetFullPath($OutDir)
[void][IO.Directory]::CreateDirectory($dir)
$status=Join-Path $dir 'f04-2-status.txt'
$csv=Join-Path $dir 'f04-2-tab-capabilities.csv'
'F04_2_SCOPE=ALLOWLIST_TABITEM_CAPABILITIES_ONLY' | Set-Content -Encoding utf8 $status
'tab,control_type,enabled,offscreen,keyboard_focusable,selected,selection_item_pattern,invoke_pattern,value_pattern,pattern_count' |
  Set-Content -Encoding utf8 $csv
$targetNames=@('Values','Properties')
$hits=0
$visible=0
$errors=0
$seen=New-Object 'System.Collections.Generic.HashSet[string]'
function Csv([string]$s){return '"'+($s -replace '"','""')+'"'}
try{
  foreach($name in $targetNames){
    try{
      $byName=[System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::NameProperty,$name)
      $byTab=[System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
        [System.Windows.Automation.ControlType]::TabItem)
      $filter=[System.Windows.Automation.AndCondition]::new($byName,$byTab)
      $nodes=$main.FindAll([System.Windows.Automation.TreeScope]::Descendants,$filter)
    }catch{$errors++;continue}
    for($i=0;$i -lt $nodes.Count;$i++){
      try{
        $e=$nodes.Item($i)
        if($e.Current.ProcessId -ne $FacadProcessId){continue}
        $type=[string]$e.Current.ControlType.ProgrammaticName
        $offscreen=[bool]$e.Current.IsOffscreen
        $enabled=[bool]$e.Current.IsEnabled
        $focusable=[bool]$e.Current.IsKeyboardFocusable
        $rect=[string]$e.Current.BoundingRectangle
        $key="$name|$type|$rect"
        if(-not $seen.Add($key)){continue}
        $patterns=@($e.GetSupportedPatterns())
        $patternNames=@($patterns | ForEach-Object {$_.ProgrammaticName})
        $selSupported=[bool]($patternNames -contains 'SelectionItemPatternIdentifiers.Pattern')
        $invokeSupported=[bool]($patternNames -contains 'InvokePatternIdentifiers.Pattern')
        $valueSupported=[bool]($patternNames -contains 'ValuePatternIdentifiers.Pattern')
        $selected='NOT_AVAILABLE'
        if($selSupported){
          $pat=$e.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)
          $selected=[string]$pat.Current.IsSelected
        }
        $hits++
        if(-not $offscreen){$visible++}
        if($hits -gt 20){throw 'F04_2_ALLOWLIST_BOUND_EXCEEDED'}
        $values=@($name,$type,[string]$enabled,[string]$offscreen,
                  [string]$focusable,$selected,[string]$selSupported,
                  [string]$invokeSupported,[string]$valueSupported,[string]$patterns.Count)
        Add-Content -Encoding utf8 $csv (($values|ForEach-Object {Csv $_}) -join ',')
      }catch{
        if($_.Exception.Message -eq 'F04_2_ALLOWLIST_BOUND_EXCEEDED'){throw}
        $errors++
      }
    }
  }
}finally{
  "F04_2_TARGET_HITS=$hits" | Add-Content -Encoding utf8 $status
  "F04_2_VISIBLE_TABS=$visible" | Add-Content -Encoding utf8 $status
  "F04_2_UIA_READ_ERRORS=$errors" | Add-Content -Encoding utf8 $status
  'F04_2_TAB_SELECT_INVOKED=false' | Add-Content -Encoding utf8 $status
  'F04_2_CHILD_CONTENT_READ=false' | Add-Content -Encoding utf8 $status
  'F04_2_SAVE_LOAD_EXPORT_INVOKED=false' | Add-Content -Encoding utf8 $status
  'F04_2_BEHAVIOR_PROVEN=false' | Add-Content -Encoding utf8 $status
  'F04_2_PATIENT_NUMBERS_COLLECTED=false' | Add-Content -Encoding utf8 $status
  'FAC03_D3=OPEN_RED' | Add-Content -Encoding utf8 $status
}
if($errors -gt 0 -or $visible -eq 0 -or $hits -eq 0){
  'F04_2_VERDICT=INCONCLUSIVE_FAIL_CLOSED' | Add-Content -Encoding utf8 $status
  throw 'F04.2 UIA capability inventory inconclusive'
}
'F04_2_VERDICT=OBSERVED_CAPABILITIES_ONLY' | Add-Content -Encoding utf8 $status
