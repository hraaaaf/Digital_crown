# Source-only / no Facad executable. Covers fail-closed negative states.
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'facad_314_f04_1_census_gate.ps1')
$cases=@(
  @{name='nominal_two_tab_hits';read=0;hits=2;anchors=2;windows=1;want='COMPLETE_CURRENT_STATE_ONLY'},
  @{name='read_error_must_fail';read=1;hits=2;anchors=2;windows=1;want='INCONCLUSIVE_UIA_READ_ERRORS'},
  @{name='zero_hit_must_fail';read=0;hits=0;anchors=0;windows=1;want='INCONCLUSIVE_NO_VISIBLE_ANCHOR'},
  @{name='offscreen_only_must_fail';read=0;hits=2;anchors=0;windows=1;want='INCONCLUSIVE_NO_VISIBLE_ANCHOR'},
  @{name='zero_windows_must_fail';read=0;hits=0;anchors=0;windows=0;want='INCONCLUSIVE_NO_WINDOW_SCOPE'},
  @{name='bad_counts_must_fail';read=0;hits=1;anchors=2;windows=1;want='INCONCLUSIVE_INVALID_COUNTS'},
  @{name='negative_counts_must_fail';read=-1;hits=2;anchors=1;windows=1;want='INCONCLUSIVE_INVALID_COUNTS'}
)
foreach($c in $cases){
  $actual=Get-FacadF04CensusVerdict -UiaReadErrors $c.read -Hits $c.hits -VisibleAnchors $c.anchors -WindowScopes $c.windows
  if($actual -cne $c.want){throw "F04.1 negative control failed: $($c.name): $actual != $($c.want)"}
  Write-Host "F04_1_VERDICT_TEST_PASS=$($c.name)"
}
Write-Host "F04_1_NEGATIVE_CONTROL_CONTRACT_PASS=$($cases.Count)"
