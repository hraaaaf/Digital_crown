# P6 — Private Windows Code-Signing Ceremony

**Model:** zero-cost private Digital Crown trust for known clinic Windows machines. This is not public CA / SmartScreen reputation.

## Goal
Create one private Authenticode code-signing certificate offline, keep its private PFX secret, pin its public certificate SHA-256 in CI, and install only the public certificate on clinic machines.

## Generate offline
Use a Windows machine. Disconnect network before key generation.

Open PowerShell:

```powershell
New-Item -ItemType Directory -Force C:\dc-windows-signing | Out-Null
Set-Location C:\dc-windows-signing

$cert = New-SelfSignedCertificate `
  -Subject "CN=Digital Crown Private Publisher" `
  -FriendlyName "Digital Crown Private Code Signing" `
  -Type CodeSigningCert `
  -CertStoreLocation "Cert:\CurrentUser\My" `
  -HashAlgorithm SHA256 `
  -KeyAlgorithm RSA `
  -KeyLength 3072 `
  -KeyExportPolicy Exportable `
  -NotAfter (Get-Date).AddYears(5)

$password = Read-Host "PFX password" -AsSecureString
Export-PfxCertificate -Cert $cert -FilePath .\DigitalCrown-CodeSigning.pfx -Password $password | Out-Null
Export-Certificate -Cert $cert -FilePath .\DigitalCrown-CodeSigning.cer -Type CERT | Out-Null

$certSha256 = (Get-FileHash .\DigitalCrown-CodeSigning.cer -Algorithm SHA256).Hash.ToLowerInvariant()
$thumbprint = $cert.Thumbprint

Write-Host "WINDOWS_CODESIGN_CERT_SHA256=$certSha256"
Write-Host "CERT_THUMBPRINT=$thumbprint"
```

## Private material
Never commit or send in chat:
- `DigitalCrown-CodeSigning.pfx`
- PFX password
- Base64 of the PFX

Keep an encrypted offline backup of the PFX and keep its password separately.

## Public material
Safe to disclose/store:
- `DigitalCrown-CodeSigning.cer`
- `WINDOWS_CODESIGN_CERT_SHA256`
- certificate thumbprint

## GitHub provisioning
Repository secrets:
- `WINDOWS_CODESIGN_PFX_B64` = Base64 of `DigitalCrown-CodeSigning.pfx`
- `WINDOWS_CODESIGN_PASSWORD` = PFX password

Repository variable:
- `WINDOWS_CODESIGN_CERT_SHA256` = SHA-256 printed above

Generate Base64 locally without printing the PFX contents anywhere else:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\dc-windows-signing\DigitalCrown-CodeSigning.pfx"))
```

Paste that value directly into the GitHub secret field. Do not paste it into chat, issues, PRs or files.

## Clinic trust bootstrap
On each known clinic Windows machine, run as Administrator using only the public `.cer`:

```powershell
certutil -f -addstore Root .\DigitalCrown-CodeSigning.cer
certutil -f -addstore TrustedPublisher .\DigitalCrown-CodeSigning.cer
```

The private PFX must never be copied to clinic machines.

## Verification
After installing a Digital Crown package signed by this private publisher:

```powershell
Get-AuthenticodeSignature .\DigitalCrownSetup-1.0.0.exe | Format-List Status,StatusMessage,SignerCertificate,TimeStamperCertificate
```

Expected production gate:
- `Status = Valid`
- signer certificate = Digital Crown Private Publisher
- timestamp certificate present

## Security boundary
If the PFX/password is suspected compromised:
1. stop signing immediately;
2. remove/revoke trust for the old public certificate on clinic machines;
3. generate a new offline certificate;
4. pin its SHA-256 in CI;
5. distribute the new public `.cer` through the trusted admin channel.

No paid CA/HSM dependency. No Vercel.
