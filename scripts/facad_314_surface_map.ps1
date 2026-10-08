# Facad 3.14 Quick Demo full-surface discovery; official Robert sample ONLY.
# No writes, clinical edits, print, license, network or destructive commands.
param([int]$FacadProcessId,[long]$MainWindowHwnd,[string]$OutDir)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class FacadSurfaceMouse {
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint flags,uint dx,uint dy,uint data,UIntPtr extra);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd,out uint pid);
}
'@
$dir=[IO.Path]::GetFullPath($OutDir)
[void][IO.Directory]::CreateDirectory($dir)
$root=[System.Windows.Automation.AutomationElement]::RootElement
$main=[System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$MainWindowHwnd)
if($null -eq $main -or $main.Current.ProcessId -ne $FacadProcessId){throw 'Facad HWND/PID mismatch'}
$log=Join-Path $dir 'surface-status.txt'
$csv=Join-Path $dir 'surface-coverage.csv'
'SURFACE_MAPPING=STARTED' | Set-Content -Encoding utf8 $log
'kind,name,enabled,status,evidence,notes' | Set-Content -Encoding utf8 $csv
function Log([string]$v){Add-Content -Encoding utf8 $log $v}
function Row([string]$type,[string]$name,[string]$enabled,[string]$status,[string]$file,[string]$note){
 $data=@($type,$name,$enabled,$status,$file,$note) | ForEach-Object {'"'+($_ -replace '"','""')+'"'}
 Add-Content -Encoding utf8 $csv ($data -join ',')
}
function Shot([string]$file){
 $r=[Windows.Forms.SystemInformation]::VirtualScreen
 $b=New-Object Drawing.Bitmap $r.Width,$r.Height
 $g=[Drawing.Graphics]::FromImage($b)
 try{$g.CopyFromScreen($r.Left,$r.Top,0,0,$b.Size);$b.Save((Join-Path $dir $file),[Drawing.Imaging.ImageFormat]::Png)}
 finally{$g.Dispose();$b.Dispose()}
}
function ForegroundOk{
 $h=[FacadSurfaceMouse]::GetForegroundWindow()
 if($h -eq [IntPtr]::Zero){return $false}
 [uint32]$pidSeen=0
 [void][FacadSurfaceMouse]::GetWindowThreadProcessId($h,[ref]$pidSeen)
 return $pidSeen -eq [uint32]$FacadProcessId
}
function Center([System.Windows.Automation.AutomationElement]$el){
 $r=$el.Current.BoundingRectangle
 if($r.IsEmpty -or $r.Width -lt 6 -or $r.Height -lt 8 -or $r.Left -lt 0 -or $r.Top -lt 0 -or $r.Right -gt 5000 -or $r.Bottom -gt 3000){throw 'invalid bounds'}
 return @{x=[int]($r.Left+$r.Width/2);y=[int]($r.Top+$r.Height/2)}
}
function Click([System.Windows.Automation.AutomationElement]$el){
 if($el.Current.ProcessId -ne $FacadProcessId -or -not $el.Current.IsEnabled -or -not (ForegroundOk)){throw 'Unsafe click context'}
 $pt=Center $el
 if(-not [FacadSurfaceMouse]::SetCursorPos($pt.x,$pt.y)){throw 'cursor failed'}
 Start-Sleep -Milliseconds 90
 [FacadSurfaceMouse]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
 Start-Sleep -Milliseconds 70
 [FacadSurfaceMouse]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
}
function Named($parent,[string]$name,[string]$type){
 $els=$parent.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::NameProperty,$name))
 return ,@(for($i=0;$i -lt $els.Count;$i++){if($els.Item($i).Current.ControlType.ProgrammaticName -eq "ControlType.$type"){$els.Item($i)}})
}
function AllMenus{
 $els=$root.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::MenuItem))
 return ,@(for($i=0;$i -lt $els.Count;$i++){
  $e=$els.Item($i)
  try{if($e.Current.ProcessId -eq $FacadProcessId -and -not $e.Current.IsOffscreen -and $e.Current.BoundingRectangle.Width -gt 0){$e}}catch{}
 })
}
function Menu([string]$name){
 $bars=$main.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::MenuBar))
 $apps=@(for($i=0;$i -lt $bars.Count;$i++){if($bars.Item($i).Current.Name -eq 'Application'){$bars.Item($i)}})
 if($apps.Count -ne 1){throw 'application menu bar ambiguous'}
 $found=Named $apps[0] $name 'MenuItem'
 if($found.Count -ne 1){throw "menu $name ambiguous"}
 return $found[0]
}
function Snapshot([string]$name){
 $els=$root.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
 $out=New-Object 'Collections.Generic.List[string]'
 for($i=0;$i -lt $els.Count;$i++){try{
  $e=$els.Item($i)
  if($e.Current.ProcessId -eq $FacadProcessId){$out.Add("$($e.Current.ControlType.ProgrammaticName)|$($e.Current.Name)|$($e.Current.AutomationId)|$($e.Current.IsEnabled)|$($e.Current.IsOffscreen)|$($e.Current.BoundingRectangle)")}
 }catch{}}
 $out | Set-Content -Encoding utf8 (Join-Path $dir $name)
}
function Escape{[Windows.Forms.SendKeys]::SendWait('{ESC}');Start-Sleep -Milliseconds 250}
$menuNames=@('File','Edit','Tracing','View','Cephalometry','Image','Tools','Window','Help')
Snapshot 'surface-before-ui.txt'
Shot 'surface-before.png'
$menusOpen=0
foreach($name in $menuNames){
 try{
  $item=Menu $name
  Click $item
  Start-Sleep -Milliseconds 300
  $file="surface-menu-$($name.ToLower()).png"
  Shot $file
  $items=AllMenus
  $rows=@($items | ForEach-Object {"$($_.Current.Name)|enabled=$($_.Current.IsEnabled)|bounds=$($_.Current.BoundingRectangle)"})
  $rows | Sort-Object -Unique | Set-Content -Encoding utf8 (Join-Path $dir "surface-menu-$($name.ToLower()).txt")
  Row 'MAIN_MENU' $name 'true' 'OPENED' $file "menu items $($rows.Count)"
  $menusOpen++
  # Hover all visible menu entries to reveal submenus, without activating leaves.
  $initial=@($items | ForEach-Object {$_.Current.Name})
  $hoverItems=@($items | Where-Object {$_.Current.IsEnabled -and $_.Current.BoundingRectangle.Top -gt 45 -and $_.Current.Name -notin $menuNames})
  $counter=0
  foreach($hoverItem in $hoverItems){
   if($counter -ge 65){Log "MENU_$($name)_HOVER_LIMIT";break}
   $counter++
   try{
    if(-not (ForegroundOk)){throw 'Facad lost foreground'}
    $xy=Center $hoverItem
    [void][FacadSurfaceMouse]::SetCursorPos($xy.x,$xy.y)
    Start-Sleep -Milliseconds 200
    $extra=@(AllMenus | ForEach-Object {$_.Current.Name} | Where-Object {$_ -notin $initial} | Sort-Object -Unique)
    if($extra.Count -gt 0){
     $safe=("$($name)-$counter" -replace '[^A-Za-z0-9_-]','_')
     $out="surface-submenu-$safe.png"
     Shot $out
     $extra | Set-Content -Encoding utf8 (Join-Path $dir "surface-submenu-$safe.txt")
     Row 'SUBMENU' "$name > $($hoverItem.Current.Name)" 'true' 'OPENED' $out ($extra -join '; ')
    }
   }catch{Log "HOVER_ERROR=$name/$($hoverItem.Current.Name): $($_.Exception.Message)"}
  }
  Log "MENU_$($name)=OPENED"
 }catch{
  Row 'MAIN_MENU' $name '?' 'BLOCKED' '' $_.Exception.Message
  Log "MENU_$($name)_ERROR=$($_.Exception.Message)"
 }finally{Escape}
}
Log "MENU_COVERAGE=$menusOpen/9"
Snapshot 'surface-all-controls-ui.txt'
$buttons=$main.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Button))
$tools=@()
for($i=0;$i -lt $buttons.Count;$i++){try{
 $el=$buttons.Item($i);$name=$el.Current.Name;$enabled=$el.Current.IsEnabled
 $status=if($name -match 'Save|Close_patient|New_patient|Open_patient|Print|Patient_Work_List|Copy|Undo'){'SKIPPED_RISK'}else{'DISCOVERED'}
 Row 'BUTTON' $name "$enabled" $status 'surface-all-controls-ui.txt' "bounds=$($el.Current.BoundingRectangle)"
 if($enabled -and $name -match '^\{FCD_'){$tools+= $el}
}catch{Log "BUTTON_READ_ERROR=$($_.Exception.Message)"}}
Log "BUTTON_COUNT=$($buttons.Count)"
Log "TOOLBAR_ENABLED=$($tools.Count)"
foreach($tool in $tools){try{
 if(-not (ForegroundOk)){break}
 $xy=Center $tool
 [void][FacadSurfaceMouse]::SetCursorPos($xy.x,$xy.y)
 Start-Sleep -Milliseconds 480
 $tips=$root.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::ToolTip))
 $names=@(for($k=0;$k -lt $tips.Count;$k++){if($tips.Item($k).Current.ProcessId -eq $FacadProcessId -and $tips.Item($k).Current.Name){$tips.Item($k).Current.Name}})
 if($names.Count -gt 0){Row 'TOOLTIP' $tool.Current.Name 'true' 'OBSERVED' '' ($names -join '; ')}
}catch{Log "TOOLTIP_ERROR=$($_.Exception.Message)"}}
foreach($name in @('{FCD_SelectMove}','{FCD_Zoom}','{FCD_Reset_Zoom}','{FCD_Measure_distance}','{FCD_Measure_distance_to_line}','{FCD_Measure_angle_3pt_Par}','{FCD_Measure_angle_4pt_Par}')){
 try{
  $b=Named $main $name 'Button'
  if($b.Count -ne 1){throw "button count $($b.Count)"}
  if(-not $b[0].Current.IsEnabled){Row 'TOOLBAR_MODE' $name 'false' 'DISABLED' '' '';continue}
  Click $b[0]
  Start-Sleep -Milliseconds 240
  $safe=$name -replace '[^A-Za-z0-9_-]','_'
  Shot "surface-tool-$safe.png"
  Row 'TOOLBAR_MODE' $name 'true' 'CLICKED_NO_IMAGE_ACTION' "surface-tool-$safe.png" 'Restored SelectMove after mode'
  if($name -ne '{FCD_SelectMove}'){
   $reset=Named $main '{FCD_SelectMove}' 'Button'
   if($reset.Count -eq 1 -and $reset[0].Current.IsEnabled){Click $reset[0]}
  }
 }catch{
  Row 'TOOLBAR_MODE' $name '?' 'BLOCKED' '' $_.Exception.Message
  Log "MODE_ERROR=$name/$($_.Exception.Message)"
 }
}
try{
 $windows=$main.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Window))
 $analysis=@(for($i=0;$i -lt $windows.Count;$i++){if($windows.Item($i).Current.Name -like '*  Analysis'){$windows.Item($i)}})
 if($analysis.Count -ne 1){throw "analysis window count $($analysis.Count)"}
 $props=Named $analysis[0] 'Properties' 'TabItem'
 $values=Named $analysis[0] 'Values' 'TabItem'
 if($props.Count -ne 1 -or $values.Count -ne 1){throw 'analysis tabs ambiguous'}
 Click $props[0]
 Start-Sleep -Milliseconds 650
 Shot 'surface-analysis-properties.png'
 Snapshot 'surface-analysis-properties-ui.txt'
 Row 'TAB' 'Analysis > Properties' 'true' 'OPENED' 'surface-analysis-properties.png' 'Tab only, read-only'
 Click $values[0]
 Start-Sleep -Milliseconds 350
 Shot 'surface-analysis-values-restored.png'
 Row 'TAB' 'Analysis > Values' 'true' 'RESTORED' 'surface-analysis-values-restored.png' ''
}catch{
 Row 'TAB' 'Analysis > Properties' '?' 'BLOCKED' '' $_.Exception.Message
 Log "PROPERTIES_ERROR=$($_.Exception.Message)"
}
# Open-only list of analyses. This is last: no writes and no workflows after it.
try{
 Click (Menu 'File')
 Start-Sleep -Milliseconds 280
 $candidate=Named $root 'New/Edit ceph analysis...' 'MenuItem'
 $allowed=@($candidate | Where-Object {$_.Current.ProcessId -eq $FacadProcessId -and -not $_.Current.IsOffscreen})
 if($allowed.Count -ne 1){throw "analysis catalog menu count $($allowed.Count)"}
 Click $allowed[0]
 Start-Sleep -Seconds 2
 Shot 'surface-analysis-catalog.png'
 Snapshot 'surface-analysis-catalog-ui.txt'
 Row 'DIALOG' 'New/Edit ceph analysis...' 'true' 'OPENED_READ_ONLY' 'surface-analysis-catalog.png' 'No Create/Edit/Save'
 Log 'ANALYSIS_CATALOG_OPENED=true'
 Escape
 Shot 'surface-analysis-catalog-after-escape.png'
}catch{
 Row 'DIALOG' 'New/Edit ceph analysis...' '?' 'BLOCKED' '' $_.Exception.Message
 Log "CATALOG_ERROR=$($_.Exception.Message)"
 Escape
}
Shot 'surface-after.png'
Snapshot 'surface-after-ui.txt'
Log 'SURFACE_MAPPING=COMPLETED_WITH_EXPLICIT_UNTESTED'
if($menusOpen -ne 9){throw "Only $menusOpen of 9 application menus opened"}
