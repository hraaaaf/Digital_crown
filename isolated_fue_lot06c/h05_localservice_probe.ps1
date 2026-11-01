# H05 synthetic probe, executed exclusively as LocalService on ephemeral Windows CI.
param([Parameter(Mandatory=$true)][string]$InputPath)
$ErrorActionPreference='Stop'
$d=Get-Content -LiteralPath $InputPath -Raw | ConvertFrom-Json
$sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$distinct=($sid -eq 'S-1-5-19') -and ($sid -ne $d.owner_sid)
$fileDenied=$false
$dpapiDenied=$false
if ($distinct) {
  try { $null=[IO.File]::ReadAllBytes([string]$d.vault_file) }
  catch [UnauthorizedAccessException] { $fileDenied=$true }
  try {
    $blob=[Convert]::FromBase64String([string]$d.ciphertext)
    $entropy=[Convert]::FromBase64String([string]$d.entropy)
    $null=[Security.Cryptography.ProtectedData]::Unprotect($blob,$entropy,[Security.Cryptography.DataProtectionScope]::CurrentUser)
  } catch [Security.Cryptography.CryptographicException] { $dpapiDenied=$true }
}
[pscustomobject]@{identity_sid=$sid;distinct=$distinct;file_denied=$fileDenied;dpapi_denied=$dpapiDenied} |
  ConvertTo-Json -Compress | Set-Content -LiteralPath ([string]$d.output) -Encoding Ascii
if (-not ($distinct -and $fileDenied -and $dpapiDenied)) { exit 42 }
exit 0
