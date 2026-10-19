# LOT05.7-J7: ONLY ephemeral GitHub-hosted Windows admin runner, fake SCM.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if ($env:LOT05J7_REAL_SCM_SIGNED_FAKE_ONLY -ne '1' -or
    $env:CI -ne 'true' -or $env:GITHUB_ACTIONS -ne 'true' -or
    $env:RUNNER_OS -ne 'Windows') {throw 'J7_ONLY_EPHEMERAL_WINDOWS_CI'}
$wp=[Security.Principal.WindowsPrincipal]([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $wp.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'J7_CI_ADMIN_REQUIRED'
}
function Strict([string]$program,[string[]]$parameters) {
    $result=& $program @parameters 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw ('J7_COMMAND_FAILED '+$program+' rc='+$LASTEXITCODE+' '+($result -join '; '))
    }
    return ($result -join [Environment]::NewLine)
}
function AwaitProof([string]$file) {
    for($i=0;$i -lt 70;$i++) {
        if (Test-Path -LiteralPath $file -PathType Leaf) {
            return Get-Content -LiteralPath $file -Raw
        }
        Start-Sleep -Milliseconds 350
    }
    throw ('J7_SCM_PROOF_MISSING '+$file)
}
function ExactAcl([string]$target,[string]$serviceSid,[string]$rights,[bool]$directory) {
    $acl=Get-Acl -LiteralPath $target
    $acl.SetAccessRuleProtection($true,$false)
    foreach($rule in @($acl.Access)) {$acl.PurgeAccessRules($rule.IdentityReference)}
    $inherit=if($directory) {
        [Security.AccessControl.InheritanceFlags]::ContainerInherit -bor
        [Security.AccessControl.InheritanceFlags]::ObjectInherit
    }else{[Security.AccessControl.InheritanceFlags]::None}
    $allow=[Security.AccessControl.AccessControlType]::Allow
    $prop=[Security.AccessControl.PropagationFlags]::None
    foreach($row in @(
        @('S-1-5-18',[Security.AccessControl.FileSystemRights]::FullControl),
        @('S-1-5-32-544',[Security.AccessControl.FileSystemRights]::FullControl),
        @($serviceSid,[Security.AccessControl.FileSystemRights]([enum]::Parse(
            [Security.AccessControl.FileSystemRights],$rights)))
    )) {
        $who=[Security.Principal.SecurityIdentifier]::new([string]$row[0])
        $ace=[Security.AccessControl.FileSystemAccessRule]::new(
            $who,[Security.AccessControl.FileSystemRights]$row[1],
            [Security.AccessControl.InheritanceFlags]$inherit,$prop,$allow)
        $acl.AddAccessRule($ace)
    }
    Set-Acl -LiteralPath $target -AclObject $acl
}
function ValidateAcl([string]$target,[string]$serviceSid) {
    $acl=Get-Acl -LiteralPath $target
    $rules=@($acl.Access)
    $actual=@($rules | ForEach-Object {
        $_.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
    })
    $wanted=@('S-1-5-18','S-1-5-32-544',$serviceSid)
    if($actual.Count -ne 3 -or $acl.AreAccessRulesProtected -ne $true -or
       @($actual | Where-Object {$_ -notin $wanted}).Count -gt 0 -or
       @($wanted | Where-Object {$_ -notin $actual}).Count -gt 0 -or
       @($rules | Where-Object {$_.AccessControlType -ne 'Allow'}).Count -gt 0) {
        throw ('J7_PINNED_PUBLIC_KEY_ACL_UNSAFE '+($actual -join ','))
    }
}
$nonce=[Guid]::NewGuid().ToString('N').Substring(0,12)
$nameA='DCJ7A_'+$nonce
$nameB='DCJ7B_'+$nonce
$created=New-Object 'System.Collections.Generic.List[string]'
$root=Join-Path $env:ProgramData ('lot05j7_fake_'+$nonce)
$pin=Join-Path $root 'pinned'
$ledger=Join-Path $root 'consumed'
$telemetry=Join-Path $root 'telemetry'
$keyFile=Join-Path $pin 'trusted-rsa-public.fake'
$valid=Join-Path $root 'signed-order.fake'
$forged=Join-Path $root 'tampered-order.fake'
$first=Join-Path $telemetry 'first.txt'
$replay=Join-Path $telemetry 'replay.txt'
$negative=Join-Path $telemetry 'without-sid.txt'
$source=Join-Path $env:GITHUB_WORKSPACE 'backend\tests\fixtures\lot05j7_windows_signed_worker.cs'
$csc=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$exe=Join-Path $root 'J7FakeSignedWorker.exe'
if((Test-Path -LiteralPath $root) -or
   -not (Test-Path -LiteralPath $source -PathType Leaf) -or
   -not (Test-Path -LiteralPath $csc -PathType Leaf)) {
    throw 'J7_SOURCE_OR_FAKE_ROOT_INVALID'
}
New-Item -ItemType Directory -Path $root,$pin,$ledger,$telemetry | Out-Null
try {
    Strict $csc @('/nologo','/target:exe',('/out:'+$exe),
                  '/reference:System.ServiceProcess.dll',$source) | Out-Null
    if(-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
        throw 'J7_SERVICE_COMPILE_MISSING'
    }
    foreach($name in @($nameA,$nameB)) {
        $args= ('"{0}" "{1}" "{2}" "{3}" "{4}" "{5}" "{6}" "{7}"' -f
                $exe,$name,$first,$keyFile,$valid,$forged,'PLACEHOLDER_SID',$ledger)
        Strict 'sc.exe' @('create',$name,'binPath=',$args,
                         'type=','own','start=','demand',
                         'obj=','NT AUTHORITY\LocalService') | Out-Null
        $created.Add($name)
    }
    Strict 'sc.exe' @('sidtype',$nameA,'unrestricted') | Out-Null
    Strict 'sc.exe' @('sidtype',$nameB,'none') | Out-Null
    $typeA=Strict 'sc.exe' @('qsidtype',$nameA)
    $typeB=Strict 'sc.exe' @('qsidtype',$nameB)
    if($typeA -notmatch 'SERVICE_SID_TYPE:\s+UNRESTRICTED' -or
       $typeB -notmatch 'SERVICE_SID_TYPE:\s+NONE') {
        throw 'J7_REAL_SERVICE_SID_TYPES_MISMATCH'
    }
    $account=New-Object Security.Principal.NTAccount(('NT SERVICE\'+$nameA))
    $sid=$account.Translate([Security.Principal.SecurityIdentifier]).Value
    if($sid -notmatch '^S-1-5-80-') {throw 'J7_REAL_SERVICE_SID_MISSING'}
    if((Strict 'sc.exe' @('showsid',$nameA)) -notmatch [regex]::Escape($sid)) {
        throw 'J7_LSA_SCM_SID_MISMATCH'
    }
    # The private key lives only inside this interactive PowerShell process.
    # Only the public modulus/exponent are saved, never a private key.
    $provider=[Security.Cryptography.CspParameters]::new(24)
    $private=[Security.Cryptography.RSACryptoServiceProvider]::new(2048,$provider)
    $private.PersistKeyInCsp=$false
    $pub=$private.ExportParameters($false)
    Set-Content -LiteralPath $keyFile -Encoding Ascii -Value @(
        [Convert]::ToBase64String($pub.Modulus),
        [Convert]::ToBase64String($pub.Exponent))
    $jobNonce=[Guid]::NewGuid().ToString('N')
    $expiry=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()+100
    $body=('owner=17|audience=LOT05J7_FAKE_WORKER|nonce={0}|expires={1}' -f
           $jobNonce,$expiry)
    $bytes=[Text.Encoding]::UTF8.GetBytes($body)
    $digest=[Security.Cryptography.SHA256CryptoServiceProvider]::new()
    try {$signature=[Convert]::ToBase64String($private.SignData($bytes,$digest))}
    finally {$digest.Dispose();$private.Dispose()}
    Set-Content -LiteralPath $valid -Encoding Ascii -Value @($body,$signature)
    $forgedBody=$body.Replace(('nonce='+$jobNonce),('nonce='+('a'*32)))
    if($forgedBody -eq $body) {throw 'J7_TAMPER_FIXTURE_FAILED'}
    Set-Content -LiteralPath $forged -Encoding Ascii -Value @($forgedBody,$signature)
    # EXACT service-SID-only key pin and consumption ledger ACLs.
    ExactAcl $pin $sid 'ReadAndExecute' $true
    ExactAcl $keyFile $sid 'ReadAndExecute' $false
    ExactAcl $ledger $sid 'Modify' $true
    ValidateAcl $pin $sid
    ValidateAcl $keyFile $sid
    ValidateAcl $ledger $sid
    Write-Output 'J7_EXACT_PUBLIC_PIN_AND_LEDGER_SERVICE_SID_ACL'
    # Telemetry is deliberately low trust and writable by both LocalService
    # service instances. It cannot be used as protected authorization state.
    Strict 'icacls.exe' @($telemetry,'/inheritance:r') | Out-Null
    Strict 'icacls.exe' @($telemetry,'/grant:r',
       '*S-1-5-18:(OI)(CI)F','*S-1-5-32-544:(OI)(CI)F',
       '*S-1-5-19:(OI)(CI)M') | Out-Null
    function Configure([string]$name,[string]$report) {
        $bin= ('"{0}" "{1}" "{2}" "{3}" "{4}" "{5}" "{6}" "{7}"' -f
             $exe,$name,$report,$keyFile,$valid,$forged,$sid,$ledger)
        Strict 'sc.exe' @('config',$name,'binPath=',$bin) | Out-Null
    }
    Configure $nameA $first
    Configure $nameB $negative
    Strict 'sc.exe' @('start',$nameA) | Out-Null
    $p1=AwaitProof $first
    if($p1 -notmatch 'identity=NT AUTHORITY\\LOCAL SERVICE' -or
       $p1 -notmatch 'service_sid_in_actual_token=True' -or
       $p1 -notmatch 'pinned_public_key_read=True' -or
       $p1 -notmatch 'signed_fake_job_valid=True' -or
       $p1 -notmatch 'forged_signature_denied=True' -or
       $p1 -notmatch 'first_nonce_consumption=True' -or
       $p1 -notmatch 'replayed_nonce_denied=False') {
        throw ('J7_SERVICE_PINNED_RSA_FIRST_USE_INVALID '+$p1)
    }
    Write-Output 'J7_REAL_SCM_PINNED_PUBLIC_KEY_RSA_SIGNATURE_VERIFIED'
    Write-Output 'J7_REAL_SCM_FORGED_SIGNATURE_DENIED'
    Strict 'sc.exe' @('stop',$nameA) | Out-Null
    Start-Sleep -Seconds 2
    Configure $nameA $replay
    Strict 'sc.exe' @('start',$nameA) | Out-Null
    $p2=AwaitProof $replay
    if($p2 -notmatch 'service_sid_in_actual_token=True' -or
       $p2 -notmatch 'signed_fake_job_valid=True' -or
       $p2 -notmatch 'first_nonce_consumption=False' -or
       $p2 -notmatch 'replayed_nonce_denied=True') {
        throw ('J7_SERVICE_RESTART_REPLAY_BYPASS '+$p2)
    }
    Write-Output 'J7_REAL_SCM_RESTART_PERSISTENT_NONCE_REPLAY_DENIED'
    Strict 'sc.exe' @('start',$nameB) | Out-Null
    $p3=AwaitProof $negative
    if($p3 -notmatch 'identity=NT AUTHORITY\\LOCAL SERVICE' -or
       $p3 -notmatch 'service_sid_in_actual_token=False' -or
       $p3 -notmatch 'pinned_public_key_read=False' -or
       $p3 -notmatch 'signed_fake_job_valid=False' -or
       $p3 -notmatch 'reason=pinned_public_key_access_denied') {
        throw ('J7_SAME_ACCOUNT_DIFFERENT_SID_ACL_BYPASS '+$p3)
    }
    Write-Output 'J7_SAME_LOCALSERVICE_WITHOUT_SERVICE_SID_CANNOT_VERIFY'
    Write-Output 'J7_SIGNER_PRIVATE_KEY_NEVER_PERSISTED_IN_FAKE_TREE'
    Write-Output 'J7_NO_CLINICAL_RESTORE_ENABLED'
}
finally {
    foreach($svc in $created) {& sc.exe stop $svc 2>&1 | Out-Null}
    Start-Sleep -Seconds 2
    foreach($svc in $created) {& sc.exe delete $svc 2>&1 | Out-Null}
    Start-Sleep -Seconds 1
    if(Test-Path -LiteralPath $root) {
        Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction Stop
    }
    foreach($svc in $created) {
        & sc.exe query $svc 2>&1 | Out-Null
        if($LASTEXITCODE -eq 0) {throw ('J7_SCM_CLEANUP_FAILED '+$svc)}
    }
}
