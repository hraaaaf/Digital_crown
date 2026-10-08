# Facad D1B: exercise all 65 Standard/lateral catalog selections WITHOUT
# clicking Load or modifying a patient analysis; restore via dialog Cancel.
param([Parameter(Mandatory=$true)][int]$FacadProcessId,
      [Parameter(Mandatory=$true)][long]$MainWindowHwnd,
      [Parameter(Mandatory=$true)][string]$OutDir,
      [Parameter(Mandatory=$true)][string]$ExpectedCatalogPath)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class FacadD1BMouse {
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint dx,uint dy,uint d,UIntPtr x);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
}
'@
$root=[Windows.Automation.AutomationElement]::RootElement
$main=[Windows.Automation.AutomationElement]::FromHandle([IntPtr]$MainWindowHwnd)
if($null -eq $main -or $main.Current.ProcessId -ne $FacadProcessId){throw 'D1B Facad main PID/HWND mismatch'}
$dir=[IO.Path]::GetFullPath($OutDir)
[void][IO.Directory]::CreateDirectory($dir)
$log=Join-Path $dir 'd1b-selection-status.txt'
$csv=Join-Path $dir 'd1b-analysis-selection.csv'
'D1B_CATALOG_SELECTION=STARTED' | Set-Content -Encoding utf8 $log
'ordinal,analysis,enabled,selected,verdict,screenshot,error' | Set-Content -Encoding utf8 $csv
function Log([string]$v){Add-Content -Encoding utf8 $log $v}
function Row([string[]]$cols){
 $escaped=@($cols | ForEach-Object {'"'+($_ -replace '"','""')+'"'})
 Add-Content -Encoding utf8 $csv ($escaped -join ',')
}
function Screenshot([string]$file){
 $r=[Windows.Forms.SystemInformation]::VirtualScreen
 $bmp=New-Object Drawing.Bitmap $r.Width,$r.Height
 $g=[Drawing.Graphics]::FromImage($bmp)
 try{
  $g.CopyFromScreen($r.Left,$r.Top,0,0,$bmp.Size)
  $bmp.Save((Join-Path $dir $file),[Drawing.Imaging.ImageFormat]::Png)
 }finally{$g.Dispose();$bmp.Dispose()}
}
function OwnedForeground{
 $h=[FacadD1BMouse]::GetForegroundWindow()
 if($h -eq [IntPtr]::Zero){return $false}
 [uint32]$pidSeen=0
 [void][FacadD1BMouse]::GetWindowThreadProcessId($h,[ref]$pidSeen)
 return $pidSeen -eq [uint32]$FacadProcessId
}
function Named($parent,[string]$name,[string]$type){
 $els=$parent.FindAll([Windows.Automation.TreeScope]::Descendants,
   [Windows.Automation.PropertyCondition]::new(
     [Windows.Automation.AutomationElement]::NameProperty,$name))
 return ,@(for($i=0;$i -lt $els.Count;$i++){
  $e=$els.Item($i)
  if($e.Current.ControlType.ProgrammaticName -eq "ControlType.$type"){$e}
 })
}
function Click($element){
 if($element.Current.ProcessId -ne $FacadProcessId -or -not $element.Current.IsEnabled -or
    -not (OwnedForeground)){throw 'Unsafe D1B click context'}
 $r=$element.Current.BoundingRectangle
 if($r.IsEmpty -or $r.Width -lt 9 -or $r.Height -lt 9 -or
    $r.Left -lt 0 -or $r.Top -lt 0 -or $r.Right -gt 5000 -or $r.Bottom -gt 3000){
   throw 'D1B click bounds invalid'
 }
 [void][FacadD1BMouse]::SetCursorPos([int]($r.Left+$r.Width/2),[int]($r.Top+$r.Height/2))
 Start-Sleep -Milliseconds 90
 [FacadD1BMouse]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
 Start-Sleep -Milliseconds 75
 [FacadD1BMouse]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
}
function Menu([string]$name){
 $bars=$main.FindAll([Windows.Automation.TreeScope]::Descendants,
   [Windows.Automation.PropertyCondition]::new(
     [Windows.Automation.AutomationElement]::ControlTypeProperty,
     [Windows.Automation.ControlType]::MenuBar))
 $apps=@(for($i=0;$i -lt $bars.Count;$i++){
  if($bars.Item($i).Current.Name -eq 'Application'){$bars.Item($i)}
 })
 if($apps.Count -ne 1){throw 'D1B application menu bar ambiguous'}
 $matches=Named $apps[0] $name 'MenuItem'
 if($matches.Count -ne 1){throw "D1B menu $name ambiguous"}
 return $matches[0]
}
function AnalysisDialog{
 $all=$root.FindAll([Windows.Automation.TreeScope]::Descendants,
   [Windows.Automation.PropertyCondition]::new(
     [Windows.Automation.AutomationElement]::NameProperty,
     'Load a cephalometric analysis (lateral)'))
 $matches=@(for($i=0;$i -lt $all.Count;$i++){
  $e=$all.Item($i)
  if($e.Current.ProcessId -eq $FacadProcessId -and
     $e.Current.ControlType -eq [Windows.Automation.ControlType]::Window -and
     -not $e.Current.IsOffscreen){$e}
 })
 if($matches.Count -ne 1){throw "D1B lateral catalog window count=$($matches.Count)"}
 return $matches[0]
}
function CatalogList($dialog){
 $all=$dialog.FindAll([Windows.Automation.TreeScope]::Descendants,
   [Windows.Automation.PropertyCondition]::new(
     [Windows.Automation.AutomationElement]::ControlTypeProperty,
     [Windows.Automation.ControlType]::List))
 $lists=@(for($i=0;$i -lt $all.Count;$i++){
  if($all.Item($i).Current.IsEnabled){$all.Item($i)}
 })
 if($lists.Count -ne 1){throw "D1B active catalog list count=$($lists.Count)"}
 return $lists[0]
}
$expected=@(Import-Csv -Path $ExpectedCatalogPath -Encoding utf8 |
  Sort-Object {[int]$_.ordinal})
if($expected.Count -ne 65){throw "Expected exactly 65 Standard/lateral names, got $($expected.Count)"}
if(@($expected | Select-Object -ExpandProperty analysis_name | Sort-Object -Unique).Count -ne 65){
 throw 'Reference catalog has duplicate names'
}
Log "EXPECTED_STANDARD_LATERAL=$($expected.Count)"
$success=0
$errors=@()
$opened=$false
$dialog=$null
$cancelled=$false
Screenshot 'd1b-before-dialog.png'
try{
 Click (Menu 'Cephalometry')
 Start-Sleep -Milliseconds 260
 $load=Named $root 'Load analysis...' 'MenuItem'
 $visible=@($load | Where-Object {
  $_.Current.ProcessId -eq $FacadProcessId -and -not $_.Current.IsOffscreen
 })
 if($visible.Count -ne 1){throw "Cephalometry > Load analysis count=$($visible.Count)"}
 Click $visible[0]
 Start-Sleep -Milliseconds 600
 $dialog=AnalysisDialog
 $opened=$true
 Screenshot 'd1b-standard-before-selection.png'
 $standard=Named $dialog 'Standard' 'TabItem'
 $local=Named $dialog 'Local' 'TabItem'
 if($standard.Count -ne 1 -or $local.Count -ne 1){throw 'D1B Standard/Local tabs ambiguous'}
 $list=CatalogList $dialog
 $items=$list.FindAll([Windows.Automation.TreeScope]::Descendants,
   [Windows.Automation.PropertyCondition]::new(
     [Windows.Automation.AutomationElement]::ControlTypeProperty,
     [Windows.Automation.ControlType]::ListItem))
 $found=@(for($i=0;$i -lt $items.Count;$i++){$items.Item($i).Current.Name})
 $found | Set-Content -Encoding utf8 (Join-Path $dir 'd1b-observed-standard-lateral.txt')
 Log "ACTUAL_STANDARD_LATERAL=$($found.Count)"
 $expectedNames=@($expected | Select-Object -ExpandProperty analysis_name)
 if($found.Count -ne $expected.Count -or
    @($found | Where-Object {$_ -notin $expectedNames}).Count -gt 0 -or
    @($expectedNames | Where-Object {$_ -notin $found}).Count -gt 0){
  throw 'D1B discovered catalog differs from reference 65 names'
 }
 for($i=0;$i -lt $expected.Count;$i++){
  $name=$expected[$i].analysis_name
  $safe=("{0:D2}_{1}" -f ($i+1),($name -replace '[^a-zA-Z0-9_-]','_'))
  if($safe.Length -gt 65){$safe=$safe.Substring(0,65)}
  try{
   # Find stable ListItem by exact UIA name; do not click the 'Load' action.
   $matches=Named $list $name 'ListItem'
   if($matches.Count -ne 1){throw "Catalog list item count=$($matches.Count)"}
   $e=$matches[0]
   if(-not $e.Current.IsEnabled){throw 'Catalog list item disabled'}
   if($e.Current.IsOffscreen){
    $scroll=$e.GetCurrentPattern([Windows.Automation.ScrollItemPattern]::Pattern)
    $scroll.ScrollIntoView()
    Start-Sleep -Milliseconds 70
   }
   $select=$e.GetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern)
   $select.Select()
   Start-Sleep -Milliseconds 90
   $selected=[bool]$select.Current.IsSelected
   $shot="d1b-selected-$safe.png"
   Screenshot $shot
   if(-not $selected){throw 'SelectionItemPattern did not select requested entry'}
   Row @([string]($i+1),$name,'true','true','SELECTED_IN_CATALOG_NOT_LOADED',$shot,'')
   $success++
  }catch{
   $err=$_.Exception.Message
   $errors+="$name : $err"
   Row @([string]($i+1),$name,'unknown','false','BLOCKED','',''+$err)
   Log "D1B_ENTRY_ERROR=$name : $err"
  }
 }
 Log "D1B_SELECTION_SUCCESS=$success/65"
 # Document the Local tab too, but never import or create local analysis.
 Click $local[0]
 Start-Sleep -Milliseconds 280
 Screenshot 'd1b-local-tab.png'
 $localItems=(CatalogList $dialog).FindAll([Windows.Automation.TreeScope]::Descendants,
   [Windows.Automation.PropertyCondition]::new(
     [Windows.Automation.AutomationElement]::ControlTypeProperty,
     [Windows.Automation.ControlType]::ListItem))
 $localNames=@(for($i=0;$i -lt $localItems.Count;$i++){$localItems.Item($i).Current.Name})
 $localNames | Set-Content -Encoding utf8 (Join-Path $dir 'd1b-local-items.txt')
 Log "D1B_LOCAL_TAB_COUNT=$($localNames.Count)"
 Click $standard[0]
 Start-Sleep -Milliseconds 210
 Screenshot 'd1b-standard-restored.png'
}finally{
 if($opened){
  try{
   $fresh=AnalysisDialog
   $cancel=Named $fresh 'Cancel' 'Button'
   if($cancel.Count -ne 1){throw 'D1B Cancel button unavailable'}
   Click $cancel[0]
   Start-Sleep -Milliseconds 450
   $cancelled=$true
  }catch{
   Log "D1B_CANCEL_FAILED=$($_.Exception.Message)"
   [Windows.Forms.SendKeys]::SendWait('{ESC}')
   Start-Sleep -Milliseconds 350
  }
 }
 Screenshot 'd1b-after-dialog-cancel.png'
 Log "D1B_DIALOG_CANCEL_CLICKED=$cancelled"
 Log "D1B_NO_ANALYSIS_LOADED_BY_SCRIPT=true"
}
if(-not $cancelled){throw 'D1B catalog Cancel not explicitly observed'}
if($errors.Count -gt 0 -or $success -ne 65){
 throw "D1B Standard lateral selection incomplete: $success/65; errors=$($errors.Count)"
}
$remaining=$root.FindAll([Windows.Automation.TreeScope]::Descendants,
 [Windows.Automation.PropertyCondition]::new(
  [Windows.Automation.AutomationElement]::NameProperty,
  'Load a cephalometric analysis (lateral)'))
$remainingWindows=@(for($i=0;$i -lt $remaining.Count;$i++){
 $e=$remaining.Item($i)
 if($e.Current.ProcessId -eq $FacadProcessId -and
    $e.Current.ControlType -eq [Windows.Automation.ControlType]::Window -and
    -not $e.Current.IsOffscreen){$e}
})
if($remainingWindows.Count -ne 0){throw 'D1B catalog remained open after Cancel'}
# Bergen short appears as a drawn label and is not exposed as a Text UIA
# control. Verify its screenshot-backed *actual* SNA and ANB rows instead.
$anwin=Named $main 'Pretreatment tracing (Robert Example / 850101-0010)  Analysis' 'Window'
if($anwin.Count -ne 1){throw 'D1B Robert analysis workspace missing after Cancel'}
$sna=Named $anwin[0] '67.7' 'Text'
$anb=Named $anwin[0] '-10.7' 'Text'
if($sna.Count -lt 1 -or $anb.Count -lt 1){
 throw 'D1B original Bergen short example values changed or could not be verified'
}
Log 'D1B_ORIGINAL_BERGEN_SHORT_VALUES_STILL_DISPLAYED=true'
Log 'D1B_STANDARD_LATERAL_65_SELECTIONS_VERIFIED=true'
