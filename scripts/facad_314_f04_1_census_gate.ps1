# Pure deterministic F04.1 verdict contract. No UIAutomation calls, vendor access or patient data.
function Get-FacadF04CensusVerdict {
  param(
    [Parameter(Mandatory=$true)][int]$UiaReadErrors,
    [Parameter(Mandatory=$true)][int]$Hits,
    [Parameter(Mandatory=$true)][int]$VisibleAnchors,
    [Parameter(Mandatory=$true)][int]$WindowScopes
  )
  if($UiaReadErrors -lt 0 -or $Hits -lt 0 -or $VisibleAnchors -lt 0 -or $WindowScopes -lt 0){
    return 'INCONCLUSIVE_INVALID_COUNTS'
  }
  if($UiaReadErrors -gt 0){return 'INCONCLUSIVE_UIA_READ_ERRORS'}
  if($WindowScopes -eq 0){return 'INCONCLUSIVE_NO_WINDOW_SCOPE'}
  if($Hits -eq 0 -or $VisibleAnchors -eq 0){return 'INCONCLUSIVE_NO_VISIBLE_ANCHOR'}
  if($VisibleAnchors -gt $Hits){return 'INCONCLUSIVE_INVALID_COUNTS'}
  return 'COMPLETE_CURRENT_STATE_ONLY'
}
