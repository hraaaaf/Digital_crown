# LOT05.7-J3: REAL SCM service SID and NTFS probe on synthetic CI fixtures only.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if ($env:LOT05J3_WINDOWS_SCM_FAKE_ONLY -ne '1' -or $env:CI -ne 'true' -or
    $env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows') {
    throw 'J3_DENY_NOT_EPHEMERAL_WINDOWS_CI'
}
$wp=[Security.Principal.WindowsPrincipal]([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $wp.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'J3_DENY_CI_SCM_ADMIN_UNAVAILABLE'
}
function Strict([string]$program,[string[]]$parameters) {
    $output=& $program @parameters 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw ('J3_COMMAND_FAILED '+$program+' rc='+$LASTEXITCODE+' output='+($output -join '; '))
    }
    return ($output -join [Environment]::NewLine)
}
function AwaitProof([string]$file) {
    for($k=0;$k -lt 70;$k++) {
        if(Test-Path -LiteralPath $file -PathType Leaf) {return Get-Content -LiteralPath $file -Raw}
        Start-Sleep -Milliseconds 350
    }
    throw ('J3_SERVICE_DID_NOT_WRITE_PROOF '+$file)
}
$nonce=[Guid]::NewGuid().ToString('N').Substring(0,12)
$allowName='DCJ3A_'+$nonce
$denyName='DCJ3B_'+$nonce
$created=New-Object 'System.Collections.Generic.List[string]'
$root=Join-Path $env:ProgramData ('lot05j3_fake_'+$nonce)
$source=Join-Path $env:GITHUB_WORKSPACE 'backend\tests\fixtures\lot05j3_windows_fake_service.cs'
$csc=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$exe=Join-Path $root 'FakeSidProbe.exe'
$protected=Join-Path $root 'protected'
$telemetry=Join-Path $root 'telemetry'
$challenge=Join-Path $protected 'challenge.fake'
$allowEvidence=Join-Path $telemetry 'allow.fake.txt'
$denyEvidence=Join-Path $telemetry 'deny.fake.txt'
if (-not (Test-Path -LiteralPath $source -PathType Leaf) -or
    -not (Test-Path -LiteralPath $csc -PathType Leaf)) {throw 'J3_FAKE_CSC_SOURCE_MISSING'}
if (Test-Path -LiteralPath $root) {throw 'J3_SYNTHETIC_ROOT_COLLISION'}
New-Item -ItemType Directory -Path $root,$protected,$telemetry | Out-Null
try {
    Strict $csc @('/nologo','/target:exe',('/out:'+$exe),'/reference:System.ServiceProcess.dll',$source) | Out-Null
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {throw 'J3_FAKE_SERVICE_COMPILATION_MISSING'}
    Set-Content -LiteralPath $challenge -Value 'LOT05J3_FAKE_ONLY' -NoNewline -Encoding Ascii
    foreach ($svc in @($allowName,$denyName)) {
        $log=if($svc -eq $allowName){$allowEvidence}else{$denyEvidence}
        $bin= ('"{0}" "{1}" "{2}" "{3}" "{4}"' -f $exe,$svc,$log,$challenge,'PLACEHOLDER_SID')
        Strict 'sc.exe' @('create',$svc,'binPath=',$bin,'type=','own','start=','demand',
                         'obj=','NT AUTHORITY\LocalService') | Out-Null
        $created.Add($svc)
    }
    Strict 'sc.exe' @('sidtype',$allowName,'unrestricted') | Out-Null
    Strict 'sc.exe' @('sidtype',$denyName,'none') | Out-Null
    $positiveType=Strict 'sc.exe' @('qsidtype',$allowName)
    $negativeType=Strict 'sc.exe' @('qsidtype',$denyName)
    if ($positiveType -notmatch 'SERVICE_SID_TYPE:\s+UNRESTRICTED' -or
        $negativeType -notmatch 'SERVICE_SID_TYPE:\s+NONE') {throw 'J3_REAL_SCM_SID_TYPE_MISMATCH'}
    $account=New-Object Security.Principal.NTAccount(('NT SERVICE\'+$allowName))
    $sid=$account.Translate([Security.Principal.SecurityIdentifier]).Value
    if ($sid -notmatch '^S-1-5-80-') {throw 'J3_REAL_SERVICE_SID_INVALID'}
    $scSid=Strict 'sc.exe' @('showsid',$allowName)
    if ($scSid -notmatch [regex]::Escape($sid)) {throw 'J3_LSA_VS_SCM_SID_MISMATCH'}
    foreach ($svc in @($allowName,$denyName)) {
        $log=if($svc -eq $allowName){$allowEvidence}else{$denyEvidence}
        $bin= ('"{0}" "{1}" "{2}" "{3}" "{4}"' -f $exe,$svc,$log,$challenge,$sid)
        Strict 'sc.exe' @('config',$svc,'binPath=',$bin) | Out-Null
    }
    # Build from a NEW explicit DACL, not icacls /grant:r alone: that call
    # can preserve pre-existing explicit Users/Authenticated Users grants.
    # No owner, LocalService or generic user identity gets access.
    function ExactProtectedAcl([string]$path,[bool]$directory,[string]$serviceSid) {
        $acl=Get-Acl -LiteralPath $path
        $acl.SetAccessRuleProtection($true,$false)
        foreach($entry in @($acl.Access)) {
            $acl.PurgeAccessRules($entry.IdentityReference)
        }
        $none=[Security.AccessControl.InheritanceFlags]::None
        $inherit=if($directory) {
            [Security.AccessControl.InheritanceFlags]::ContainerInherit -bor
            [Security.AccessControl.InheritanceFlags]::ObjectInherit
        } else {$none}
        $propagation=[Security.AccessControl.PropagationFlags]::None
        $allow=[Security.AccessControl.AccessControlType]::Allow
        foreach($spec in @(
            @('S-1-5-18',[Security.AccessControl.FileSystemRights]::FullControl),
            @('S-1-5-32-544',[Security.AccessControl.FileSystemRights]::FullControl),
            @($serviceSid,[Security.AccessControl.FileSystemRights]::ReadAndExecute)
        )) {
            $who=[Security.Principal.SecurityIdentifier]::new([string]$spec[0])
            $rule=[Security.AccessControl.FileSystemAccessRule]::new(
                $who,[Security.AccessControl.FileSystemRights]$spec[1],
                [Security.AccessControl.InheritanceFlags]$inherit,$propagation,$allow)
            $acl.AddAccessRule($rule)
        }
        Set-Acl -LiteralPath $path -AclObject $acl
    }
    ExactProtectedAcl $protected $true $sid
    ExactProtectedAcl $challenge $false $sid
    # Telemetry is explicitly writable by both LocalService processes.
    Strict 'icacls.exe' @($telemetry,'/inheritance:r') | Out-Null
    Strict 'icacls.exe' @($telemetry,'/grant:r',
        '*S-1-5-18:(OI)(CI)F','*S-1-5-32-544:(OI)(CI)F','*S-1-5-19:(OI)(CI)M') | Out-Null
    $acl=Strict 'icacls.exe' @($challenge)
    Write-Output ('J3_PROTECTED_ACL_CHECK ' + $acl)
    if($acl -notmatch [regex]::Escape($sid) -or
       $acl -match 'S-1-5-19|Everyone|Authenticated Users') {throw 'J3_PROTECTED_FILE_ACL_UNSAFE'}
    $direct=Strict $exe @('--probe',$sid)
    if($direct -notmatch 'DIRECT_NO_TARGET_SID') {throw 'J3_DIRECT_INVOCATION_SID_SPOOF'}
    Strict 'sc.exe' @('start',$allowName) | Out-Null
    $allow=AwaitProof $allowEvidence
    if($allow -notmatch 'target_sid_in_process_token=True' -or
       $allow -notmatch 'protected_file_read=True' -or
       $allow -notmatch 'identity=NT AUTHORITY\\LOCAL SERVICE') {
        throw ('J3_SERVICE_SID_POSITIVE_MISMATCH '+$allow)
    }
    Strict 'sc.exe' @('start',$denyName) | Out-Null
    $deny=AwaitProof $denyEvidence
    if($deny -notmatch 'target_sid_in_process_token=False' -or
       $deny -notmatch 'protected_file_read=False' -or
       $deny -notmatch 'read_result=access_denied' -or
       $deny -notmatch 'identity=NT AUTHORITY\\LOCAL SERVICE') {
        throw ('J3_SAME_ACCOUNT_NEGATIVE_ACL_BYPASS '+$deny)
    }
    Write-Output 'J3_REAL_SCM_TWO_SERVICES_STARTED'
    Write-Output 'J3_SERVICE_SID_IN_REAL_LOCAL_SERVICE_PROCESS_TOKEN'
    Write-Output 'J3_NTFS_SID_ALLOW_AND_SAME_ACCOUNT_WITHOUT_SID_DENY'
    Write-Output 'J3_INTERACTIVE_PROCESS_LACKS_SID'
    Write-Output 'J3_NO_CLINICAL_RESTORE_ENABLED'
}
finally {
    foreach($svc in $created) {& sc.exe stop $svc 2>&1 | Out-Null}
    Start-Sleep -Seconds 2
    foreach($svc in $created) {& sc.exe delete $svc 2>&1 | Out-Null}
    Start-Sleep -Seconds 1
    if(Test-Path -LiteralPath $root) {Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction Stop}
    foreach($svc in $created) {
        & sc.exe query $svc 2>&1 | Out-Null
        if($LASTEXITCODE -eq 0) {throw ('J3_SCM_CLEANUP_FAILED '+$svc)}
    }
}
