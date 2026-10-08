# Evidence gate for Facad D2 after restoring toggles.
# Uses screenshot comparisons of *identical regions* from BEFORE, AFTER, RESTORE;
# menu overlays and mouse-hover UI are excluded from the test regions.
param([Parameter(Mandatory=$true)][string]$OutDir)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$dir=[IO.Path]::GetFullPath($OutDir)
$ledger=Join-Path $dir 'd2-visual-proof.csv'
$status=Join-Path $dir 'd2-visual-proof.txt'
'control,region,changed_before_after,changed_before_restored,verdict,notes' |
  Set-Content -Encoding utf8 $ledger
'D2_VISUAL_GATE=STARTED' | Set-Content -Encoding utf8 $status
function Log([string]$v){Add-Content -Encoding utf8 $status $v}
function Row([string]$name,[string]$region,[int]$changed,[int]$restored,[string]$verdict,[string]$note){
  $pieces=@($name,$region,$changed,$restored,$verdict,$note) |
    ForEach-Object {'"'+($_ -replace '"','""')+'"'}
  Add-Content -Encoding utf8 $ledger ($pieces -join ',')
}
function DeltaPixels([Drawing.Bitmap]$a,[Drawing.Bitmap]$b,[int]$x,[int]$y,[int]$w,[int]$h){
  $diff=0
  for($py=$y;$py -lt $y+$h;$py+=2){
    for($px=$x;$px -lt $x+$w;$px+=2){
      $ca=$a.GetPixel($px,$py)
      $cb=$b.GetPixel($px,$py)
      if([Math]::Abs([int]$ca.R-[int]$cb.R) -gt 10 -or
         [Math]::Abs([int]$ca.G-[int]$cb.G) -gt 10 -or
         [Math]::Abs([int]$ca.B-[int]$cb.B) -gt 10){$diff++}
    }
  }
  return $diff
}
$tests=@(
  @{id='d2-03-Hard_tissue';label='Hard tissue';roi='tracing';mustChange=$true},
  @{id='d2-04-Profile';label='Profile';roi='tracing';mustChange=$true},
  @{id='d2-05-Ceph_Lines';label='Ceph/Lines';roi='tracing';mustChange=$true},
  @{id='d2-11-Status_bar';label='Status bar';roi='status';mustChange=$true},
  @{id='d2-01-Marker_guide';label='Marker guide';roi='tracing';mustChange=$false}
)
$certified=0
foreach($t in $tests){
  $id=$t.id
  $paths=@(Join-Path $dir "$id-before.png";Join-Path $dir "$id-after.png";Join-Path $dir "$id-restored.png")
  $missing=@($paths | Where-Object {-not (Test-Path -LiteralPath $_)})
  if($missing.Count -gt 0){
    Row $t.label $t.roi 0 0 'BLOCKED_MISSING_CAPTURE' 'Required screenshot missing'
    if($t.mustChange){throw "D2 required visual evidence missing for $($t.label)"}
    continue
  }
  $bitmaps=@()
  try{
    foreach($p in $paths){$bitmaps+= [Drawing.Bitmap]::new($p)}
    foreach($bitmap in $bitmaps){
      if($bitmap.Width -ne 1024 -or $bitmap.Height -ne 768){
        throw "Unexpected screenshot viewport $($bitmap.Width)x$($bitmap.Height)"
      }
    }
    if($t.roi -eq 'tracing'){
      # Interior of official Robert pretreatment image: no popup/menu chrome.
      $x=556;$y=113;$w=429;$h=582
    }else{
      # Facad desktop status strip (below drawing area, above Windows taskbar).
      $x=0;$y=700;$w=1024;$h=28
    }
    $beforeAfter=DeltaPixels $bitmaps[0] $bitmaps[1] $x $y $w $h
    $beforeRestore=DeltaPixels $bitmaps[0] $bitmaps[2] $x $y $w $h
    $verdict=if($beforeAfter -gt 30 -and $beforeRestore -le 5){
      'VISUAL_CHANGE_AND_RESTORE_PROVEN'
    }elseif($beforeAfter -le 30 -and $beforeRestore -le 5){
      'RESTORE_MATCHES_BUT_CHANGE_NOT_PROVEN'
    }else{'VISUAL_RESTORE_NOT_PROVEN'}
    Row $t.label $t.roi $beforeAfter $beforeRestore $verdict 'RGB threshold 10, stride 2, stable ROI'
    Log "D2_VISUAL_$($t.label)=$verdict (changed=$beforeAfter restore=$beforeRestore)"
    if($t.mustChange -and $verdict -ne 'VISUAL_CHANGE_AND_RESTORE_PROVEN'){
      throw "D2 proof gate failed for $($t.label): $verdict"
    }
    if($verdict -eq 'VISUAL_CHANGE_AND_RESTORE_PROVEN'){$certified++}
  }finally{foreach($b in $bitmaps){$b.Dispose()}}
}
Log "D2_VERIFIED_REVERSIBLE_VISUAL_CONTROLS=$certified/4"
if($certified -lt 4){throw 'D2 visual proof incomplete: fewer than 4 observed reversible controls'}
Log 'D2_VISUAL_GATE=PASSED_FOR_FOUR_CONTROLS_ONLY'
