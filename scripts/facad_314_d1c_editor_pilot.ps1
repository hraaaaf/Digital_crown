# D1C Facad Quick Demo: inspect three BUILT-IN analysis PRESET DEFINITIONS
# using the nonpatient "Edit Cephalometric Analysis" window.
# OFFICIAL ROBERT COPY ONLY. Never click Save, never invoke patient Load analysis.
param([Parameter(Mandatory=$true)][int]$FacadProcessId,
      [Parameter(Mandatory=$true)][long]$MainWindowHwnd,
      [Parameter(Mandatory=$true)][string]$OutDir,
      [Parameter(Mandatory=$true)][string]$ProfileName)
$ErrorActionPreference='Stop'
# Fail-closed allowlist: exact names from D1's already certified 65-item Standard catalog.
# Never substitute an approximate name or accept a profile absent from the reference CSV.
$catalogPath=Join-Path $PSScriptRoot '..\docs\audits\data\FACAD_314_D1_LATERAL_STANDARD_65.csv'
if(-not (Test-Path -LiteralPath $catalogPath -PathType Leaf)){
 throw 'D1C exact-name reference catalog missing'
}
$referenceRows=@(Import-Csv -LiteralPath $catalogPath)
if($referenceRows.Count -ne 65){throw "D1C catalog must contain 65 definitions, found $($referenceRows.Count)"}
$matched=@($referenceRows | Where-Object {
 $_.analysis_name -ceq $ProfileName -and $_.catalog_tab -ceq 'Standard' -and
 $_.facad_modality -ceq 'lateral'
})
if($matched.Count -ne 1){throw "D1C profile not uniquely present in canonical Standard catalog"}

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class FacadD1CMouse {
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint x,uint y,uint d,UIntPtr e);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd,out uint pid);
}
'@
$root=[Windows.Automation.AutomationElement]::RootElement
$main=[Windows.Automation.AutomationElement]::FromHandle([IntPtr]$MainWindowHwnd)
if($null -eq $main -or $main.Current.ProcessId -ne $FacadProcessId){throw 'D1C PID mismatch'}
$dir=[IO.Path]::GetFullPath($OutDir)
[void][IO.Directory]::CreateDirectory($dir)
$log=Join-Path $dir 'd1c-editor-pilot-status.txt'
$csv=Join-Path $dir 'd1c-editor-pilot.csv'
'D1C_PILOT=STARTED' | Set-Content -Encoding utf8 $log
'analysis,selected_catalog,editor_name,measurement_texts,lines_texts,markers_texts,verdict,evidence,notes' |
 Set-Content -Encoding utf8 $csv
function Log([string]$v){Add-Content -Encoding utf8 -Path $log -Value $v}
function Row([string[]]$fields){
 $escaped=@($fields | ForEach-Object {'"'+($_ -replace '"','""')+'"'})
 Add-Content -Encoding utf8 $csv ($escaped -join ',')
}
function Shot([string]$name){
 $r=[Windows.Forms.SystemInformation]::VirtualScreen
 $b=New-Object Drawing.Bitmap $r.Width,$r.Height
 $g=[Drawing.Graphics]::FromImage($b)
 try{$g.CopyFromScreen($r.Left,$r.Top,0,0,$b.Size);$b.Save((Join-Path $dir $name),[Drawing.Imaging.ImageFormat]::Png)}
 finally{$g.Dispose();$b.Dispose()}
}
function DumpUi([string]$file){
 $items=$root.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
 $out=New-Object 'Collections.Generic.List[string]'
 for($i=0;$i -lt $items.Count;$i++){
  $e=$items.Item($i)
  try{if($e.Current.ProcessId -eq $FacadProcessId){
   $out.Add(("{0}|{1}|AUTOID={2}|ENABLED={3}|OFFSCREEN={4}|B={5}" -f
    $e.Current.ControlType.ProgrammaticName,$e.Current.Name,$e.Current.AutomationId,
    $e.Current.IsEnabled,$e.Current.IsOffscreen,$e.Current.BoundingRectangle))
  }}catch{}
 }
 $out | Set-Content -Encoding utf8 (Join-Path $dir $file)
}
function OwnedForeground{
 $h=[FacadD1CMouse]::GetForegroundWindow()
 if($h -eq [IntPtr]::Zero){return $false}
 [uint32]$seen=0
 [void][FacadD1CMouse]::GetWindowThreadProcessId($h,[ref]$seen)
 return $seen -eq [uint32]$FacadProcessId
}
function Named($parent,[string]$name,[string]$type){
 $found=$parent.FindAll([Windows.Automation.TreeScope]::Descendants,
  [Windows.Automation.PropertyCondition]::new(
   [Windows.Automation.AutomationElement]::NameProperty,$name))
 return ,@(for($i=0;$i -lt $found.Count;$i++){
  $e=$found.Item($i)
  if($e.Current.ControlType.ProgrammaticName -eq "ControlType.$type"){$e}
 })
}
function ExactWindow([string]$name){
 $found=Named $root $name 'Window'
 $visible=@($found | Where-Object {
  $_.Current.ProcessId -eq $FacadProcessId -and -not $_.Current.IsOffscreen
 })
 if($visible.Count -ne 1){throw "D1C window $name visible count=$($visible.Count)"}
 return $visible[0]
}
function Click($el){
 if($el.Current.ProcessId -ne $FacadProcessId -or -not $el.Current.IsEnabled -or
    -not (OwnedForeground)){throw 'Unsafe D1C click target'}
 $r=$el.Current.BoundingRectangle
 if($r.IsEmpty -or $r.Width -lt 9 -or $r.Height -lt 9 -or
    $r.Left -lt 0 -or $r.Top -lt 0 -or $r.Right -gt 5000 -or $r.Bottom -gt 3000){throw 'D1C target bounds invalid'}
 [void][FacadD1CMouse]::SetCursorPos([int]($r.Left+$r.Width/2),[int]($r.Top+$r.Height/2))
 Start-Sleep -Milliseconds 85
 [FacadD1CMouse]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
 Start-Sleep -Milliseconds 75
 [FacadD1CMouse]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
}
function TopFile{
 $bars=$main.FindAll([Windows.Automation.TreeScope]::Descendants,
  [Windows.Automation.PropertyCondition]::new(
   [Windows.Automation.AutomationElement]::ControlTypeProperty,
   [Windows.Automation.ControlType]::MenuBar))
 $apps=@(for($i=0;$i -lt $bars.Count;$i++){if($bars.Item($i).Current.Name -eq 'Application'){$bars.Item($i)}})
 if($apps.Count -ne 1){throw 'D1C application menu bar ambiguous'}
 $files=Named $apps[0] 'File' 'MenuItem'
 if($files.Count -ne 1){throw 'D1C File menu ambiguous'}
 return $files[0]
}
function Catalog{
 return (ExactWindow 'Load a cephalometric analysis (lateral)')
}
function Editor{
 return (ExactWindow 'Edit Cephalometric Analysis')
}
function EditorText($editor){
 $all=$editor.FindAll([Windows.Automation.TreeScope]::Descendants,
  [Windows.Automation.PropertyCondition]::new(
   [Windows.Automation.AutomationElement]::ControlTypeProperty,
   [Windows.Automation.ControlType]::Text))
 return ,@(for($i=0;$i -lt $all.Count;$i++){
  $e=$all.Item($i)
  if(-not $e.Current.IsOffscreen -and $e.Current.Name){$e.Current.Name}
 })
}
function EditorName($editor){
 $edits=$editor.FindAll([Windows.Automation.TreeScope]::Descendants,
  [Windows.Automation.PropertyCondition]::new(
   [Windows.Automation.AutomationElement]::ControlTypeProperty,
   [Windows.Automation.ControlType]::Edit))
 $names=@(for($i=0;$i -lt $edits.Count;$i++){
  $e=$edits.Item($i)
  if($e.Current.AutomationId -eq '1022'){
   try{$vp=$e.GetCurrentPattern([Windows.Automation.ValuePattern]::Pattern);$vp.Current.Value}catch{$e.Current.Name}
  }
 })
 if($names.Count -ne 1){return 'UNKNOWN'}
 return [string]$names[0]
}
$profiles=@($ProfileName)
Log "D1C_ONE_PROFILE_PER_FRESH_RUNNER=$ProfileName"
Shot 'd1c-before-editor.png'
DumpUi 'd1c-before-editor-ui.txt'
$loaded=0
$errors=@()
$editorOpened=$false
try{
 Click (TopFile)
 Start-Sleep -Milliseconds 250
 $actions=Named $root 'New/Edit ceph analysis...' 'MenuItem'
 $visible=@($actions | Where-Object {$_.Current.ProcessId -eq $FacadProcessId -and -not $_.Current.IsOffscreen})
 if($visible.Count -ne 1){throw 'D1C File > New/Edit ceph analysis menu action missing'}
 Click $visible[0]
 Start-Sleep -Milliseconds 550
 $ed=Editor
 $editorOpened=$true
 Shot 'd1c-editor-initial.png'
 DumpUi 'd1c-editor-initial-ui.txt'
 for($i=0;$i -lt $profiles.Count;$i++){
  $name=$profiles[$i]
  $safe=$name -replace '[^A-Za-z0-9_-]','_'
  $selected=$false;$editorName='';$measureCount=0;$lineCount=0;$markerCount=0
  try{
   # Only the editor's Load... is permitted. This populates the editor's
   # in-memory draft; it is NOT the patient Cephalometry > Load analysis.
   $ed=Editor
   $pick=Named $ed 'Load...' 'Button'
   if($pick.Count -ne 1){throw 'Editor Load... button ambiguous'}
   Click $pick[0]
   Start-Sleep -Milliseconds 380
   $catalog=Catalog
   $list=Named $catalog '' 'List'
   if($list.Count -ne 1){throw "D1C catalog list count=$($list.Count)"}
   $entry=Named $list[0] $name 'ListItem'
   if($entry.Count -ne 1){throw "D1C profile $name count=$($entry.Count)"}
   $selection=$entry[0].GetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern)
   $selection.Select()
   Start-Sleep -Milliseconds 120
   $selected=[bool]$selection.Current.IsSelected
   Shot "d1c-$safe-selected-before-load.png"
   if(-not $selected){throw 'D1C SelectionItem not selected'}
   # Clicking Load here DOES NOT click Save and does not touch the
   # patient analysis. No patient clinical result is certified.
   $load=Named $catalog 'Load' 'Button'
   if($load.Count -ne 1){throw 'D1C catalog Load button ambiguous'}
   Click $load[0]
   Start-Sleep -Milliseconds 700
   # Facad may prompt to overwrite existing marker properties when a
   # second preset is loaded into the same editor. Distinct runners avoid
   # this. If a prompt still appears, do NOT acknowledge or overwrite.
   $modals=$root.FindAll([Windows.Automation.TreeScope]::Descendants,
     [Windows.Automation.PropertyCondition]::new(
       [Windows.Automation.AutomationElement]::NameProperty,
       'Do you want to overwrite existing marker properties?'))
   if($modals.Count -gt 0){throw 'D1C overwrite-marker confirmation appeared; refuse mutation'}
   $ed=Editor
   $editorName=EditorName $ed
   Shot "d1c-$safe-measurements.png"
   DumpUi "d1c-$safe-measurements-ui.txt"
   $measureNames=EditorText $ed
   $measureCount=$measureNames.Count
   $measureNames | Set-Content -Encoding utf8 (Join-Path $dir "d1c-$safe-measurements-texts.txt")
   foreach($tab in @('Lines and calc. points','Markers')){
    $tabs=Named $ed $tab 'TabItem'
    if($tabs.Count -ne 1){throw "D1C editor tab $tab missing"}
    Click $tabs[0]
    Start-Sleep -Milliseconds 320
    $key=if($tab -eq 'Markers'){'markers'}else{'lines'}
    Shot "d1c-$safe-$key.png"
    DumpUi "d1c-$safe-$key-ui.txt"
    $names=EditorText $ed
    $names | Set-Content -Encoding utf8 (Join-Path $dir "d1c-$safe-$key-texts.txt")
    if($key -eq 'markers'){$markerCount=$names.Count}else{$lineCount=$names.Count}
   }
   $measureTab=Named $ed 'Measurements' 'TabItem'
   if($measureTab.Count -ne 1){throw 'D1C Measurements tab not found'}
   Click $measureTab[0]
   Start-Sleep -Milliseconds 200
   # Observed with the official Quick Demo in run 37957532659:
   # catalog label 'Tubingen' and the unsaved editor's exact label 'Tübingen'.
   # This is the ONLY permitted catalog/editor display-name difference.
   $verifiedLabelAlias=($name -ceq 'Tubingen' -and $editorName -ceq 'Tübingen')
   if($verifiedLabelAlias){Log 'D1C_VERIFIED_EDITOR_LABEL_ALIAS=Tubingen|Tübingen'}
   $verdict=if(($editorName -eq $name) -or $verifiedLabelAlias){'EDITOR_DEFINITION_LOADED_NOT_SAVED'}
     else{'DEFINITION_OBSERVED_NAME_UNVERIFIED'}
   Row @($name,[string]$selected,$editorName,[string]$measureCount,
    [string]$lineCount,[string]$markerCount,$verdict,"d1c-$safe-measurements.png",'No Save called')
   if($verdict -ne 'EDITOR_DEFINITION_LOADED_NOT_SAVED'){
    throw "Loaded name mismatch expected $name actual $editorName"
   }
   $loaded++
   Log "D1C_PROFILE_$safe=$measureCount measurement text controls, $lineCount lines, $markerCount markers; editorName=$editorName"
  }catch{
   $issue=$_.Exception.Message
   Log "D1C_PROFILE_$safe=BLOCKED: $issue"
   $errors+= "${name}: $issue"
   Row @($name,[string]$selected,$editorName,[string]$measureCount,
     [string]$lineCount,[string]$markerCount,'BLOCKED','',$issue)
   # If editor state is unknown after a failure, do not perform more
   # catalog interactions; avoid accidentally loading into the patient.
   break
  }
 }
}finally{
 # LEAVE the editor draft unsaved and Facad running. The workflow will
 # terminate the entire disposable application process after hashing files.
 # Closing the editor could invoke a Save changes dialog; avoid it entirely.
 Shot 'd1c-final-unsaved-editor.png'
 DumpUi 'd1c-final-unsaved-editor-ui.txt'
 Log 'D1C_EDITOR_SAVE_BUTTON_NOT_INVOKED=true'
 Log 'D1C_PATIENT_ANALYSIS_LOAD_NOT_INVOKED=true'
 Log "D1C_PRESETS_LOADED_IN_EDITOR=$loaded/$($profiles.Count)"
}
if($errors.Count -gt 0 -or $loaded -ne $profiles.Count){
 throw "D1C pilot incomplete $loaded/$($profiles.Count); errors=$($errors.Count)"
}
Log "D1C_ONE_PRESET_DEFINITION_EXPOSED=$ProfileName"
