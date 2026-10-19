# LOT05.7-J9: detached JWT-authorized ticket to actual fake SCM; Windows GitHub runner only.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if ($env:LOT05J9_REAL_SCM_SIGNED_FAKE_ONLY -ne '1' -or
    $env:CI -ne 'true' -or $env:GITHUB_ACTIONS -ne 'true' -or
    $env:RUNNER_OS -ne 'Windows') {throw 'J9_ONLY_EPHEMERAL_WINDOWS_CI'}
$wp=[Security.Principal.WindowsPrincipal]([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $wp.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'J9_CI_ADMIN_REQUIRED'
}
function Strict([string]$program,[string[]]$parameters) {
    $result=& $program @parameters 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw ('J9_COMMAND_FAILED '+$program+' rc='+$LASTEXITCODE+' '+($result -join '; '))
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
    throw ('J9_SCM_PROOF_MISSING '+$file)
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
        throw ('J9_PINNED_PUBLIC_KEY_ACL_UNSAFE '+($actual -join ','))
    }
}
$nonce=[Guid]::NewGuid().ToString('N').Substring(0,12)
$nameA='DCJ9A_'+$nonce
$nameB='DCJ9B_'+$nonce
$created=New-Object 'System.Collections.Generic.List[string]'
$root=Join-Path $env:ProgramData ('lot05j9_fake_'+$nonce)
$pin=Join-Path $root 'pinned'
$ledger=Join-Path $root 'consumed'
$telemetry=Join-Path $root 'telemetry'
$keyFile=Join-Path $pin 'trusted-rsa-public.fake'
$valid=Join-Path $root 'signed-order.fake'
$forged=Join-Path $root 'tampered-order.fake'
$first=Join-Path $telemetry 'first.txt'
$replay=Join-Path $telemetry 'replay.txt'
$negative=Join-Path $telemetry 'without-sid.txt'
$source=Join-Path $env:GITHUB_WORKSPACE 'backend\tests\fixtures\lot05j9_windows_jwt_linked_worker.cs'
$csc=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$exe=Join-Path $root 'J9FakeLinkedWorker.exe'
if((Test-Path -LiteralPath $root) -or
   -not (Test-Path -LiteralPath $source -PathType Leaf) -or
   -not (Test-Path -LiteralPath $csc -PathType Leaf)) {
    throw 'J9_SOURCE_OR_FAKE_ROOT_INVALID'
}
New-Item -ItemType Directory -Path $root,$pin,$ledger,$telemetry | Out-Null
try {
    Strict $csc @('/nologo','/target:exe',('/out:'+$exe),
                  '/reference:System.ServiceProcess.dll',$source) | Out-Null
    if(-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
        throw 'J9_SERVICE_COMPILE_MISSING'
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
        throw 'J9_REAL_SERVICE_SID_TYPES_MISMATCH'
    }
    $account=New-Object Security.Principal.NTAccount(('NT SERVICE\'+$nameA))
    $sid=$account.Translate([Security.Principal.SecurityIdentifier]).Value
    if($sid -notmatch '^S-1-5-80-') {throw 'J9_REAL_SERVICE_SID_MISSING'}
    if((Strict 'sc.exe' @('showsid',$nameA)) -notmatch [regex]::Escape($sid)) {
        throw 'J9_LSA_SCM_SID_MISMATCH'
    }
    # The signer is an independently launched Python subprocess and has ALREADY
    # checked the actual backend JWT against a disposable native SQLCipher DB.
    # This privileged test installer only copies a preexisting public pin and order.
    # It does NOT receive a JWT, a private key, or a trusted pin from the job itself.
    $inputRoot=$env:LOT05J9_FAKE_INPUT_ROOT
    if([string]::IsNullOrWhiteSpace($inputRoot) -or
       (Split-Path -Leaf $inputRoot) -notlike 'lot05j9_fake_*' -or
       -not (Test-Path -LiteralPath $inputRoot -PathType Container)) {
        throw 'J9_ONLY_PREPARED_FAKE_INPUTS'
    }
    $publicSource=Join-Path $inputRoot 'trusted-rsa-public.fake'
    $orderSource=Join-Path $inputRoot 'signed-order.fake'
    foreach($file in @($publicSource,$orderSource)) {
        if(-not (Test-Path -LiteralPath $file -PathType Leaf)) {
            throw 'J9_MISSING_PREAUTHORIZED_FAKE_INPUT'
        }
        $item=Get-Item -LiteralPath $file -Force
        if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $item.LinkType) {
            throw 'J9_REPARSE_INPUT_DENIED'
        }
    }
    $pubLines=@(Get-Content -LiteralPath $publicSource)
    $orderLines=@(Get-Content -LiteralPath $orderSource)
    if($pubLines.Count -ne 3 -or $orderLines.Count -ne 2 -or
       $pubLines[2] -notmatch '^[1-9][0-9]*$' -or
       $orderLines[0] -notmatch '^owner=[1-9][0-9]*\|audience=LOT05J9_FAKE_WORKER\|nonce=[a-f0-9]{32}\|expires=[0-9]+$') {
        throw 'J9_SIGNED_INPUT_CONTRACT_INVALID'
    }
    if(-not $orderLines[0].StartsWith(('owner='+$pubLines[2]+'|'))) {
        throw 'J9_SIGNED_OWNER_MUST_MATCH_PIN'
    }
    Copy-Item -LiteralPath $publicSource -Destination $keyFile -ErrorAction Stop
    Copy-Item -LiteralPath $orderSource -Destination $valid -ErrorAction Stop
    $forgedBody=[regex]::Replace($orderLines[0],'nonce=[a-f0-9]{32}','nonce='+('a'*32))
    if($forgedBody -eq $orderLines[0]) {throw 'J9_TAMPER_FIXTURE_FAILED'}
    Set-Content -LiteralPath $forged -Encoding Ascii -Value @($forgedBody,$orderLines[1])
    # EXACT service-SID-only key pin and consumption ledger ACLs.
    ExactAcl $pin $sid 'ReadAndExecute' $true
    ExactAcl $keyFile $sid 'ReadAndExecute' $false
    ExactAcl $ledger $sid 'Modify' $true
    ValidateAcl $pin $sid
    ValidateAcl $keyFile $sid
    ValidateAcl $ledger $sid
    Write-Output 'J9_EXACT_PUBLIC_PIN_AND_LEDGER_SERVICE_SID_ACL'
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
        throw ('J9_SERVICE_PINNED_RSA_FIRST_USE_INVALID '+$p1)
    }
    Write-Output 'J9_REAL_SCM_PINNED_PUBLIC_KEY_RSA_SIGNATURE_VERIFIED'
    Write-Output 'J9_REAL_SCM_FORGED_SIGNATURE_DENIED'
    Strict 'sc.exe' @('stop',$nameA) | Out-Null
    Start-Sleep -Seconds 2
    Configure $nameA $replay
    Strict 'sc.exe' @('start',$nameA) | Out-Null
    $p2=AwaitProof $replay
    if($p2 -notmatch 'service_sid_in_actual_token=True' -or
       $p2 -notmatch 'signed_fake_job_valid=True' -or
       $p2 -notmatch 'first_nonce_consumption=False' -or
       $p2 -notmatch 'replayed_nonce_denied=True') {
        throw ('J9_SERVICE_RESTART_REPLAY_BYPASS '+$p2)
    }
    Write-Output 'J9_REAL_SCM_RESTART_PERSISTENT_NONCE_REPLAY_DENIED'
    Strict 'sc.exe' @('start',$nameB) | Out-Null
    $p3=AwaitProof $negative
    if($p3 -notmatch 'identity=NT AUTHORITY\\LOCAL SERVICE' -or
       $p3 -notmatch 'service_sid_in_actual_token=False' -or
       $p3 -notmatch 'pinned_public_key_read=False' -or
       $p3 -notmatch 'signed_fake_job_valid=False' -or
       $p3 -notmatch 'reason=pinned_public_key_access_denied') {
        throw ('J9_SAME_ACCOUNT_DIFFERENT_SID_ACL_BYPASS '+$p3)
    }
    Write-Output 'J9_SAME_LOCALSERVICE_WITHOUT_SERVICE_SID_CANNOT_VERIFY'
    Write-Output 'J9_DETACHED_JWT_SIGNED_TICKET_LINKED_TO_ACTUAL_SCM_FAKE'
    Write-Output 'J9_NO_CLINICAL_RESTORE_ENABLED'
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
        if($LASTEXITCODE -eq 0) {throw ('J9_SCM_CLEANUP_FAILED '+$svc)}
    }
}
