#Requires -Version 7.0
# C05B-03O Win32 CNG disposable key probe. No clinic provisioning.
# A real TPM is optional on hosted Windows; absence MUST be a NO-GO,
# never a quiet promotion of a software key.
$ErrorActionPreference = "Stop"
if (-not $IsWindows -or $env:ENVIRONMENT -ne "test" -or
    $env:DIGITALCROWN_ISOLATED_RUNTIME -ne "true") {
    throw "C05B03O_WINDOWS_CNG_TEST_ONLY"
}
$hardwareSucceeded = $false
$providers = @(
    @{Name="PLATFORM_TPM"; Provider=[System.Security.Cryptography.CngProvider]::MicrosoftPlatformCryptoProvider},
    @{Name="SOFTWARE_LAB_ONLY"; Provider=[System.Security.Cryptography.CngProvider]::MicrosoftSoftwareKeyStorageProvider}
)
foreach ($attempt in $providers) {
    $key = $null
    $signer = $null
    $keyname = "DigitalCrown-LAB-ONLY-" + [Guid]::NewGuid().ToString("N")
    try {
        $settings = [System.Security.Cryptography.CngKeyCreationParameters]::new()
        $settings.Provider = $attempt.Provider
        $settings.ExportPolicy = [System.Security.Cryptography.CngExportPolicies]::None
        $settings.KeyUsage = [System.Security.Cryptography.CngKeyUsages]::Signing
        $key = [System.Security.Cryptography.CngKey]::Create(
            [System.Security.Cryptography.CngAlgorithm]::ECDsaP256,
            $keyname, $settings
        )
        if ($key.Algorithm.Algorithm -ne "ECDSA_P256" -or
            $key.ExportPolicy -ne [System.Security.Cryptography.CngExportPolicies]::None) {
            throw "C05B03O_KEY_NOT_P256_NONEXPORTABLE"
        }
        $signer = [System.Security.Cryptography.ECDsaCng]::new($key)
        $bytes = [System.Text.Encoding]::UTF8.GetBytes("LOT06-O-NO-PATIENT-OR-SECRET")
        $signature = $signer.SignData(
            $bytes, [System.Security.Cryptography.HashAlgorithmName]::SHA256
        )
        if (-not $signer.VerifyData(
            $bytes, $signature, [System.Security.Cryptography.HashAlgorithmName]::SHA256
        )) {
            throw "C05B03O_NATIVE_CNG_SIGNATURE_BAD"
        }
        $tampered = [System.Text.Encoding]::UTF8.GetBytes("LOT06-O-MODIFIED")
        if ($signer.VerifyData(
            $tampered, $signature, [System.Security.Cryptography.HashAlgorithmName]::SHA256
        )) {
            throw "C05B03O_NATIVE_CNG_TAMPER_ACCEPTED"
        }
        $exportSucceeded = $false
        try {
            $null = $key.Export([System.Security.Cryptography.CngKeyBlobFormat]::Pkcs8PrivateBlob)
            $exportSucceeded = $true
        }
        catch [System.Security.Cryptography.CryptographicException] {
            $exportSucceeded = $false
        }
        if ($exportSucceeded) { throw "C05B03O_PRIVATE_KEY_EXPORTED" }
        if ($attempt.Name -eq "PLATFORM_TPM") {
            $hardwareSucceeded = $true
            Write-Output "C05B03O_WINDOWS_TPM_CNG_P256_NONEXPORT_SIGN_VERIFY_PASS"
        }
        else {
            Write-Output "C05B03O_WINDOWS_SOFTWARE_CNG_P256_LAB_CONTROL_PASS_NOT_PRODUCTION"
        }
    }
    catch [System.Security.Cryptography.CryptographicException] {
        if ($attempt.Name -eq "PLATFORM_TPM") {
            Write-Output "C05B03O_WINDOWS_HOSTED_RUNNER_TPM_UNAVAILABLE_CABINET_HARD_STOP"
        } else {
            throw "C05B03O_NATIVE_SOFTWARE_CNG_CONTROL_FAILED"
        }
    }
    finally {
        if ($null -ne $signer) { $signer.Dispose() }
        if ($null -ne $key) {
            try {
                $key.Delete()
            }
            finally { $key.Dispose() }
        }
    }
}
if (-not $hardwareSucceeded) {
    Write-Output "C05B03O_NO_HARDWARE_TPM_CNG_CERTIFICATION_NO_FALLBACK"
}
Write-Output "C05B03O_KEYS_EPHEMERAL_PROBE_DELETED_NOT_CABINET_ENROLLED"
