# H05 synthetic probe, executed exclusively as LocalService on ephemeral Windows CI.
param([Parameter(Mandatory=$true)][string]$InputPath)
$ErrorActionPreference='Stop'
$stage='read-input'
try {
$d=Get-Content -LiteralPath $InputPath -Raw | ConvertFrom-Json
$stage='identity'
$sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$distinct=($sid -eq 'S-1-5-19') -and ($sid -ne $d.owner_sid)
$stage='check-vault'
$fileDenied=$false
$dpapiDenied=$false
if ($distinct) {
  try { $null=[IO.File]::ReadAllBytes([string]$d.vault_file) }
  catch [UnauthorizedAccessException] { $fileDenied=$true }
  # Windows PowerShell 5.1 may not auto-load the System.Security assembly.
  # A missing .NET type is NOT evidence of the DPAPI user-scope boundary.
  $stage='dpapi-load-assembly'
  Add-Type -AssemblyName System.Security -ErrorAction Stop
  $stage='dpapi-verify-type'
  if (-not ('System.Security.Cryptography.ProtectedData' -as [type])) {
    throw 'DPAPI_PROTECTEDDATA_TYPE_MISSING'
  }
  $stage='dpapi-unseal'
  try {
    $blob=[Convert]::FromBase64String([string]$d.ciphertext)
    $entropy=[Convert]::FromBase64String([string]$d.entropy)
    $null=[System.Security.Cryptography.ProtectedData]::Unprotect(
      $blob,$entropy,[System.Security.Cryptography.DataProtectionScope]::CurrentUser)
  } catch {
    # Windows PowerShell may wrap native .NET CryptographicException in a
    # MethodInvocationException. Only the underlying crypto error is allowed.
    $root=$_.Exception.GetBaseException()
    if ($root -is [System.Security.Cryptography.CryptographicException]) {
      $dpapiDenied=$true
    } else {
      throw
    }
  }
}
[pscustomobject]@{identity_sid=$sid;distinct=$distinct;file_denied=$fileDenied;dpapi_denied=$dpapiDenied} |
  ConvertTo-Json -Compress | Set-Content -LiteralPath ([string]$d.output) -Encoding Ascii
if (-not ($distinct -and $fileDenied -and $dpapiDenied)) { exit 42 }
exit 0
} catch {
  # Do not expose exception message, file path, token or ciphertext.
  $errorReport=[pscustomobject]@{stage=$stage;type=$_.Exception.GetType().Name;root_type=$_.Exception.GetBaseException().GetType().Name}
  $errorReport | ConvertTo-Json -Compress |
    Set-Content -LiteralPath (Join-Path (Split-Path -Parent $InputPath) 'probe-error.json') -Encoding Ascii
  exit 43
}
