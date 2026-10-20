# LOT05.7-J9: transient SCM signer key isolation + real JWT, no production runtime.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if($env:LOT05J9_SIGNER_SID_FAKE_ONLY -ne '1' -or $env:CI -ne 'true' -or
   $env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows') {throw 'J9_WINDOWS_CI_FAKE_ONLY'}
$wp=[Security.Principal.WindowsPrincipal]([Security.Principal.WindowsIdentity]::GetCurrent())
if(-not $wp.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {throw 'J9_FIXTURE_ADMIN_REQUIRED'}
foreach($key in @('LOT05J9_FAKE_PYTHON','LOT05J9_FAKE_SOURCE_DB','LOT05J9_FAKE_SQL_KEY',
 'LOT05J9_FAKE_JWT_SECRET','LOT05J9_FAKE_JWT','LOT05J9_FAKE_OWNER','LOT05J9_FAKE_OUTPUT_ROOT',
 'LOT05J10C_EXPECT_JOB','LOT05J10C_EXPECT_GENERATION','LOT05J10C_EXPECT_MANIFEST')) {
 if([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($key))) {throw ('J9_MISSING_TEST_INPUT '+$key)}
}
function Strict([string]$program,[string[]]$argv) {
 $out=& $program @argv 2>&1
 if($LASTEXITCODE -ne 0) {throw ('J9_COMMAND_FAILED '+$program+' rc='+$LASTEXITCODE+' '+($out -join ';'))}
 return ($out -join [Environment]::NewLine)
}
function AwaitProof([string]$file) {
 for($i=0;$i -lt 110;$i++) {
   if(Test-Path -LiteralPath $file -PathType Leaf) {return Get-Content -LiteralPath $file -Raw}
   Start-Sleep -Milliseconds 350
 }
 throw 'J9_SCM_EVIDENCE_TIMED_OUT'
}
function Protect([string]$file,[string]$sid,[string]$right,[bool]$directory) {
 $acl=Get-Acl -LiteralPath $file
 $acl.SetAccessRuleProtection($true,$false)
 foreach($rule in @($acl.Access)) {$acl.PurgeAccessRules($rule.IdentityReference)}
 $inherit=if($directory) {
    [Security.AccessControl.InheritanceFlags]::ContainerInherit -bor
    [Security.AccessControl.InheritanceFlags]::ObjectInherit
 } else {[Security.AccessControl.InheritanceFlags]::None}
 foreach($row in @(
   @('S-1-5-18','FullControl'),
   @('S-1-5-32-544','FullControl'),
   @($sid,$right)
 )) {
  $ace=[Security.AccessControl.FileSystemAccessRule]::new(
   [Security.Principal.SecurityIdentifier]::new([string]$row[0]),
   [Security.AccessControl.FileSystemRights]([enum]::Parse(
     [Security.AccessControl.FileSystemRights],[string]$row[1])),
   [Security.AccessControl.InheritanceFlags]$inherit,
   [Security.AccessControl.PropagationFlags]::None,
   [Security.AccessControl.AccessControlType]::Allow)
  $acl.AddAccessRule($ace)
 }
 Set-Acl -LiteralPath $file -AclObject $acl
 $actual=Get-Acl -LiteralPath $file
 $sids=@($actual.Access | ForEach-Object {
   $_.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
 })
 if(-not $actual.AreAccessRulesProtected -or $sids.Count -ne 3 -or
    @($sids | Where-Object {$_ -notin @('S-1-5-18','S-1-5-32-544',$sid)}).Count -ne 0) {
   throw ('J9_PROTECTED_ACL_MISMATCH '+$file)
 }
}
$tag=[Guid]::NewGuid().ToString('N').Substring(0,12)
$nameA='DCJ9SIGN_'+$tag
$nameB='DCJ9CLIENT_'+$tag
$nameC='DCJ10DC_'+$tag
$pipe='dcj10d-direct-'+$tag
$created=New-Object 'System.Collections.Generic.List[string]'
$root=Join-Path $env:ProgramData ('lot05j9_fake_sid_'+$tag)
$protected=Join-Path $root ('lot05j9_fake_signer_'+$tag)
$dbroot=Join-Path $root ('lot05e_fake_sqlcipher_'+$tag)
$telemetry=Join-Path $root 'telemetry'
$outbox=Join-Path $root 'signer-outbox'
$consumerTrust=Join-Path $root 'consumer-trust'
$consumerLedger=Join-Path $root 'consumer-ledger'
$consumerPin=Join-Path $consumerTrust 'pinned-rsa-public.fake'
$consumerExe=Join-Path $root 'consumer-scm.exe'
$consumerSource=Join-Path $env:GITHUB_WORKSPACE 'backend\tests\fixtures\lot05j10d_windows_authenticated_pipe_consumer.cs'
$reportReplay=Join-Path $telemetry 'replay.txt'
$reportHostile=Join-Path $telemetry 'hostile-pipe.txt'
$exe=Join-Path $root 'signer-scm.exe'
$publicPin=Join-Path $root 'trusted-rsa-public.fake'
$rootAttack=Join-Path $root 'J9_SIDLESS_ROOT_WRITE.fake'
$private=Join-Path $protected 'signer-private.pem'
$config=Join-Path $protected 'fake-config.txt'
$binding=Join-Path $protected 'expected-manifest.json'
$source=Join-Path $env:GITHUB_WORKSPACE 'backend\tests\fixtures\lot05j10d_windows_direct_scm_jwt_signer.cs'
$csc=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$requestValid=Join-Path $root 'valid.jwt.fake'
$requestAbsent=Join-Path $root 'missing.jwt.fake'
$requestBadBinding=Join-Path $root 'wrong-manifest.jwt.fake'
$outputBadBinding=Join-Path $outbox 'wrong-manifest-refused.json'
$reportBadBinding=Join-Path $telemetry 'wrong-manifest.txt'
$outputSigned=Join-Path $outbox 'authorized.json'
$outputDenied=Join-Path $outbox 'refused.json'
$reportClient=Join-Path $telemetry 'client.txt'
$reportClientAfter=Join-Path $telemetry 'client-after-signature.txt'
$reportValid=Join-Path $telemetry 'valid.txt'
$reportMissing=Join-Path $telemetry 'missing.txt'
if((Split-Path -Leaf $env:LOT05J9_FAKE_OUTPUT_ROOT) -notlike 'lot05j9_fake_*' -or
   (Test-Path -LiteralPath $root) -or
   -not (Test-Path -LiteralPath $csc -PathType Leaf)) {throw 'J9_FAKE_ROOT_OR_COMPILER_INVALID'}
New-Item -ItemType Directory -Path $root,$protected,$dbroot,$telemetry,$outbox,$consumerTrust,$consumerLedger | Out-Null
try {
 Strict $csc @('/nologo','/target:exe',('/out:'+$exe),'/reference:System.ServiceProcess.dll','/reference:System.Core.dll',$source) | Out-Null
 Strict $csc @('/nologo','/target:exe',('/out:'+$consumerExe),
   '/reference:System.ServiceProcess.dll','/reference:System.Web.Extensions.dll',
   '/reference:System.Core.dll',$consumerSource) | Out-Null
 foreach($name in @($nameA,$nameB)) {
   $args= ('"{0}" "{1}" "attacker" "{2}" "{3}" "{4}" "{5}" "{6}" "{7}" "{8}" "{9}"' -f
    $exe,$name,$reportClient,$private,$config,$requestAbsent,$outputDenied,$env:LOT05J9_FAKE_PYTHON,$env:GITHUB_WORKSPACE,'PLACEHOLDER')
   Strict 'sc.exe' @('create',$name,'binPath=',$args,'type=','own','start=','demand',
       'obj=','NT AUTHORITY\LocalService') | Out-Null
   $created.Add($name)
 }
 Strict 'sc.exe' @('sidtype',$nameA,'unrestricted') | Out-Null
 Strict 'sc.exe' @('sidtype',$nameB,'none') | Out-Null
 $consumerCommand=('"{0}" "{1}"' -f $consumerExe,$nameC)
 Strict 'sc.exe' @('create',$nameC,'binPath=',$consumerCommand,
                  'type=','own','start=','demand','obj=','NT AUTHORITY\LocalService') | Out-Null
 $created.Add($nameC)
 Strict 'sc.exe' @('sidtype',$nameC,'unrestricted') | Out-Null
 $consumerSid=([Security.Principal.NTAccount]::new(('NT SERVICE\'+$nameC))).Translate(
       [Security.Principal.SecurityIdentifier]).Value
 if(!$consumerSid.StartsWith('S-1-5-80-')) {throw 'J10D_CONSUMER_SID_INVALID'}
 $sid=([Security.Principal.NTAccount]::new(('NT SERVICE\'+$nameA))).Translate(
       [Security.Principal.SecurityIdentifier]).Value
 if($sid -notmatch '^S-1-5-80-' -or
   (Strict 'sc.exe' @('qsidtype',$nameA)) -notmatch 'SERVICE_SID_TYPE:\s+UNRESTRICTED' -or
   (Strict 'sc.exe' @('qsidtype',$nameB)) -notmatch 'SERVICE_SID_TYPE:\s+NONE') {
     throw 'J9_SCMSID_UNVERIFIED'
 }
 # This installer creates a disposable RSA key. TEST ADMIN still controls the root of trust.
 $generator=@'
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding,PrivateFormat,NoEncryption
from pathlib import Path
import sys,base64
key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
folder=Path(sys.argv[1]); owner=sys.argv[2]
(folder/'signer-private.pem').write_bytes(key.private_bytes(Encoding.PEM,PrivateFormat.PKCS8,NoEncryption()))
pub=key.public_key().public_numbers()
(folder.parent/'trusted-rsa-public.fake').write_text(
base64.b64encode(pub.n.to_bytes(256,'big')).decode('ascii')+'\n'+
base64.b64encode(pub.e.to_bytes((pub.e.bit_length()+7)//8,'big')).decode('ascii')+'\n'+owner+'\n',encoding='ascii')
'@
 $generatorPath=Join-Path $root 'keygen.py'
 [IO.File]::WriteAllText($generatorPath,$generator)
 Strict $env:LOT05J9_FAKE_PYTHON @($generatorPath,$protected,$env:LOT05J9_FAKE_OWNER) | Out-Null
 Remove-Item -LiteralPath $generatorPath -Force
 Copy-Item -LiteralPath (Join-Path $root 'trusted-rsa-public.fake') -Destination (Join-Path $env:LOT05J9_FAKE_OUTPUT_ROOT 'trusted-rsa-public.fake')
 Copy-Item -LiteralPath (Join-Path $root 'trusted-rsa-public.fake') -Destination $consumerPin
 Copy-Item -LiteralPath $env:LOT05J9_FAKE_SOURCE_DB -Destination (Join-Path $dbroot 'fake_source.db')
 $dbUrl='sqlite:///'+(Join-Path $dbroot 'fake_source.db').Replace('\','/')
 [IO.File]::WriteAllLines($config,[string[]]@(
   ('DATABASE_URL='+$dbUrl),
   ('SQLCIPHER_KEY_HEX='+$env:LOT05J9_FAKE_SQL_KEY),
   ('SECRET_KEY='+$env:LOT05J9_FAKE_JWT_SECRET),
   ('CABINET_MASTER_KEY_HEX='+('e1'*32))))
 [IO.File]::WriteAllText($binding,(@{owner=[int]$env:LOT05J9_FAKE_OWNER;job=$env:LOT05J10C_EXPECT_JOB;generation=$env:LOT05J10C_EXPECT_GENERATION;manifest=$env:LOT05J10C_EXPECT_MANIFEST} | ConvertTo-Json -Compress))
 [IO.File]::WriteAllText($requestValid,(@{jwt=$env:LOT05J9_FAKE_JWT;owner=[int]$env:LOT05J9_FAKE_OWNER;job=$env:LOT05J10C_EXPECT_JOB;generation=$env:LOT05J10C_EXPECT_GENERATION;manifest=$env:LOT05J10C_EXPECT_MANIFEST} | ConvertTo-Json -Compress))
 [IO.File]::WriteAllText($requestAbsent,(@{jwt='';owner=[int]$env:LOT05J9_FAKE_OWNER;job=$env:LOT05J10C_EXPECT_JOB;generation=$env:LOT05J10C_EXPECT_GENERATION;manifest=$env:LOT05J10C_EXPECT_MANIFEST} | ConvertTo-Json -Compress))
 [IO.File]::WriteAllText($requestBadBinding,(@{jwt=$env:LOT05J9_FAKE_JWT;owner=[int]$env:LOT05J9_FAKE_OWNER;job=$env:LOT05J10C_EXPECT_JOB;generation=$env:LOT05J10C_EXPECT_GENERATION;manifest=('f'*64)} | ConvertTo-Json -Compress))
 Protect $protected $sid 'Modify' $true
 Protect $private $sid 'ReadAndExecute' $false
 Protect $config $sid 'ReadAndExecute' $false
 Protect $binding $sid 'ReadAndExecute' $false
 Protect $dbroot $sid 'Modify' $true
 Protect (Join-Path $dbroot 'fake_source.db') $sid 'Modify' $false
 Protect $requestValid $sid 'ReadAndExecute' $false
 Protect $requestAbsent $sid 'ReadAndExecute' $false
 Protect $requestBadBinding $sid 'ReadAndExecute' $false
 # The signature handoff must NOT be writable by another LocalService
 # process, unlike the deliberately low-trust diagnostic telemetry.
 Protect $outbox $sid 'Modify' $true
 # Protect the package directory against a second same-account service
 # replacing the installed signer EXE, the provisioned RSA pin or a sibling
 # path. Both services need ONLY read/execute for the same compiled EXE.
 Protect $root 'S-1-5-19' 'ReadAndExecute' $true
 Protect $exe 'S-1-5-19' 'ReadAndExecute' $false
 Protect $publicPin 'S-1-5-19' 'ReadAndExecute' $false
 Protect $consumerExe 'S-1-5-19' 'ReadAndExecute' $false
 Protect $consumerTrust $consumerSid 'ReadAndExecute' $true
 Protect $consumerPin $consumerSid 'ReadAndExecute' $false
 Protect $consumerLedger $consumerSid 'Modify' $true
 $signerDirAcl=Get-Acl -LiteralPath $protected
 $nonceAcl=Get-Acl -LiteralPath $consumerLedger
 if(-not $signerDirAcl.AreAccessRulesProtected -or -not $nonceAcl.AreAccessRulesProtected) {
     throw 'J10D_DIRECT_SIGNER_OR_NONCE_ACL_UNPROTECTED'
 }
 Write-Output 'J10D_DIRECT_SCM_SIGNER_AND_CONSUMER_PRIVATE_ACLS_PASS'
 Strict 'icacls.exe' @($telemetry,'/inheritance:r') | Out-Null
 Strict 'icacls.exe' @($telemetry,'/grant:r',
   '*S-1-5-18:(OI)(CI)F','*S-1-5-32-544:(OI)(CI)F','*S-1-5-19:(OI)(CI)M') | Out-Null
 Write-Output 'J9_REAL_SIGNER_PRIVATE_PINNED_TO_DISTINCT_SCM_SID'
 Write-Output 'J9_SIGNER_EXECUTABLE_ROOT_AND_RSA_PUBLIC_PIN_READ_ONLY_FOR_LOCALSERVICE'
 $expectedPinHash=(Get-FileHash -LiteralPath $publicPin -Algorithm SHA256).Hash
 function Configure([string]$name,[string]$mode,[string]$proof,[string]$request,[string]$output) {
  $command= ('"{0}" "{1}" "{2}" "{3}" "{4}" "{5}" "{6}" "{7}" "{8}" "{9}" "{10}" "{11}"' -f
     $exe,$name,$mode,$proof,$private,$config,$request,$output,$env:LOT05J9_FAKE_PYTHON,$env:GITHUB_WORKSPACE,$sid,$pipe)
  Strict 'sc.exe' @('config',$name,'binPath=',$command) | Out-Null
 }
 $cmdConsumer=('"{0}" "{1}" "{2}" "{3}" "{4}" "{5}" "{6}" "{7}" "{8}" "{9}" "{10}"' -f
   $consumerExe,$nameC,$pipe,$sid,$consumerSid,$consumerPin,$consumerLedger,
   $env:LOT05J9_FAKE_OWNER,$env:LOT05J10C_EXPECT_JOB,$env:LOT05J10C_EXPECT_GENERATION,
   $env:LOT05J10C_EXPECT_MANIFEST)
 Strict 'sc.exe' @('config',$nameC,'binPath=',$cmdConsumer) | Out-Null
 Strict 'sc.exe' @('start',$nameC) | Out-Null
 (Get-Service $nameC).WaitForStatus('Running',[TimeSpan]::FromSeconds(15))
 Configure $nameB 'attacker' $reportClient $requestValid $outputSigned
 Strict 'sc.exe' @('start',$nameB) | Out-Null
 $p=AwaitProof $reportClient
 if($p -notmatch 'service_sid_in_token=False' -or
    $p -notmatch 'client_private_read=False' -or
    $p -notmatch 'client_config_read=False' -or
    $p -notmatch 'client_request_read=False' -or
    $p -notmatch 'client_private_write=False' -or
    $p -notmatch 'client_config_write=False' -or
    $p -notmatch 'client_request_write=False' -or
    $p -notmatch 'client_output_forge=False' -or
    $p -notmatch 'client_pin_write=False' -or
    $p -notmatch 'client_root_create=False' -or
    (Test-Path -LiteralPath $rootAttack) -or
    (Get-FileHash -LiteralPath $publicPin -Algorithm SHA256).Hash -ne $expectedPinHash -or
    $p -notmatch 'reason=client_access_denied') {throw ('J9_CLIENT_CAN_READ_KEY '+$p)}
 Write-Output 'J9_UNPRIVILEGED_SAME_LOCALSERVICE_CLIENT_CANNOT_READ_RSA_PRIVATE_OR_JWT_SECRET'
 Write-Output 'J9_SIDLESS_CLIENT_CANNOT_TAMPER_RSA_CONFIG_JWT_REQUEST_OR_SIGNER_OUTBOX'
 Write-Output 'J9_SIDLESS_CLIENT_CANNOT_WRITE_SIGNER_ROOT_OR_RSA_PIN'
 Configure $nameA 'sign' $reportValid $requestValid $outputSigned
 Strict 'sc.exe' @('start',$nameA) | Out-Null
 $good=AwaitProof $reportValid
 if($good -notmatch 'identity=NT AUTHORITY\\LOCAL SERVICE' -or
    $good -notmatch 'service_sid_in_token=True' -or
    $good -notmatch 'ticket_issued=True' -or
    $good -notmatch 'reason=authenticated_jwt_signed' -or
    -not (Test-Path -LiteralPath $outputSigned)) {throw ('J9_AUTH_SIGNER_SCM_DENIED_VALID_JWT '+$good)}
 if($good -notmatch 'pipe_response=DENY_J10D_RSA_VERIFIED_NONCE_BURNED' -or
   @(Get-ChildItem -LiteralPath $consumerLedger -Filter '*.nonce' -File).Count -ne 1) {
   throw ('J10D_DIRECT_ISSUER_PIPE_SIGNATURE_NOT_BURNED '+$good)
 }
 Write-Output 'J10D_J10C_ORIGINAL_SCM_SIGNER_DIRECT_AUTHENTICATED_PIPE_PASS'
 Write-Output 'J9_TRUE_BACKEND_JWT_IN_DETACHED_WINDOWS_SCM_SIGNER'
 # A second actual SCM attacker run attempts to overwrite an ALREADY ISSUED
 # signed object, not merely to precreate a file in an empty directory.
 $issuedHash=(Get-FileHash -LiteralPath $outputSigned -Algorithm SHA256).Hash
 Strict 'sc.exe' @('stop',$nameB) | Out-Null
 Start-Sleep -Seconds 2
 Configure $nameB 'attacker' $reportClientAfter $requestValid $outputSigned
 Strict 'sc.exe' @('start',$nameB) | Out-Null
 $pAfter=AwaitProof $reportClientAfter
 if($pAfter -notmatch 'service_sid_in_token=False' -or
    $pAfter -notmatch 'client_private_read=False' -or
    $pAfter -notmatch 'client_config_read=False' -or
    $pAfter -notmatch 'client_request_read=False' -or
    $pAfter -notmatch 'client_private_write=False' -or
    $pAfter -notmatch 'client_config_write=False' -or
    $pAfter -notmatch 'client_request_write=False' -or
    $pAfter -notmatch 'client_output_forge=False' -or
    $pAfter -notmatch 'client_pin_write=False' -or
    $pAfter -notmatch 'client_root_create=False' -or
    (Test-Path -LiteralPath $rootAttack) -or
    (Get-FileHash -LiteralPath $publicPin -Algorithm SHA256).Hash -ne $expectedPinHash -or
    $pAfter -notmatch 'reason=client_access_denied' -or
    (Get-FileHash -LiteralPath $outputSigned -Algorithm SHA256).Hash -ne $issuedHash) {
    throw ('J9_SIDLESS_CLIENT_TAMPERED_ISSUED_TICKET '+$pAfter)
 }
 Write-Output 'J9_ISSUED_RSA_TICKET_INTEGRITY_SURVIVES_SECOND_REAL_CLIENT_ATTACK'
 Strict 'sc.exe' @('stop',$nameA) | Out-Null
 Start-Sleep -Seconds 2
 Configure $nameA 'sign' $reportMissing $requestAbsent $outputDenied
 Strict 'sc.exe' @('start',$nameA) | Out-Null
 $bad=AwaitProof $reportMissing
 if($bad -notmatch 'service_sid_in_token=True' -or $bad -notmatch 'ticket_issued=False' -or
    $bad -notmatch 'reason=preauth_guard_denied' -or (Test-Path -LiteralPath $outputDenied)) {
    throw ('J9_SIGNER_ISSUED_TICKET_WITHOUT_JWT '+$bad)
 }
 Write-Output 'J9_SIGNER_REJECTS_MISSING_JWT_WITHOUT_RSA_SIGNATURE'
 # An authenticated JWT with a mismatched SQLCipher manifest MUST NOT get
 # a signature. This checks the signer guard, not just verifier-side checks.
 Strict 'sc.exe' @('stop',$nameA) | Out-Null
 Start-Sleep -Seconds 2
 Configure $nameA 'sign' $reportBadBinding $requestBadBinding $outputBadBinding
 Strict 'sc.exe' @('start',$nameA) | Out-Null
 $badManifest=AwaitProof $reportBadBinding
 if($badManifest -notmatch 'service_sid_in_token=True' -or
    $badManifest -notmatch 'ticket_issued=False' -or
    $badManifest -notmatch 'reason=preauth_guard_denied' -or
    (Test-Path -LiteralPath $outputBadBinding)) {
    throw ('J10C_SIGNER_ACCEPTED_WRONG_SQLCIPHER_MANIFEST '+$badManifest)
 }
 Write-Output 'J10C_SIGNER_REJECTS_AUTHENTICATED_JWT_WITH_WRONG_SQLCIPHER_MANIFEST'
 # Restart consumer under SCM and replay the exact prior ticket from the
 # SAME Windows signer Service SID, without reissuing JWT or nonce.
 Strict 'sc.exe' @('stop',$nameA) | Out-Null
 Strict 'sc.exe' @('stop',$nameC) | Out-Null
 (Get-Service $nameC).WaitForStatus('Stopped',[TimeSpan]::FromSeconds(15))
 Start-Sleep -Seconds 2
 Strict 'sc.exe' @('start',$nameC) | Out-Null
 (Get-Service $nameC).WaitForStatus('Running',[TimeSpan]::FromSeconds(15))
 Configure $nameA 'replay' $reportReplay $requestValid $outputSigned
 Strict 'sc.exe' @('start',$nameA) | Out-Null
 $nonceProof=AwaitProof $reportReplay
 if($nonceProof -notmatch 'service_sid_in_token=True' -or
    $nonceProof -notmatch 'reason=nonce_replay_probe' -or
    $nonceProof -notmatch 'pipe_response=DENY_J10D_NONCE_REPLAY_OR_LEDGER' -or
    @(Get-ChildItem -LiteralPath $consumerLedger -Filter '*.nonce' -File).Count -ne 1) {
    throw ('J10D_DIRECT_ORIGINAL_SIGNER_REPLAY_NOT_DENIED '+$nonceProof)
 }
 Write-Output 'J10D_DIRECT_ORIGINAL_SCM_SIGNER_REPLAY_AFTER_CONSUMER_RESTART_DENIED_PASS'
 # The historical J10C second SCM process has same LocalService account,
 # but Service SID type NONE; a forged direct pipe connection must fail.
 Strict 'sc.exe' @('stop',$nameB) | Out-Null
 Start-Sleep -Seconds 2
 Configure $nameB 'pipe_hostile' $reportHostile $requestValid $outputSigned
 Strict 'sc.exe' @('start',$nameB) | Out-Null
 $hostileProof=AwaitProof $reportHostile
 if($hostileProof -notmatch 'service_sid_in_token=False' -or
   $hostileProof -notmatch 'reason=hostile_pipe_probe' -or
   $hostileProof -notmatch 'pipe_response=DENY_J10D_OS_ACCESS_DENIED' -or
   @(Get-ChildItem -LiteralPath $consumerLedger -Filter '*.nonce' -File).Count -ne 1) {
   throw ('J10D_DIRECT_HOSTILE_SID_PIPE_NOT_DENIED '+$hostileProof)
 }
 Write-Output 'J10D_DIRECT_SAME_ACCOUNT_SIDLESS_SIGNER_PIPE_DENIED_PASS'
 Write-Output 'J10D_DIRECT_NO_CLINICAL_APPLY_PASS'
 Copy-Item -LiteralPath $outputSigned -Destination (Join-Path $env:LOT05J9_FAKE_OUTPUT_ROOT 'isolated-signed.json')
 Write-Output 'J9_CLINICAL_WORKER_REMAINS_DENIED'
}
finally {
 foreach($name in $created) { & sc.exe stop $name 2>&1 | Out-Null }
 Start-Sleep -Seconds 2
 foreach($name in $created) { & sc.exe delete $name 2>&1 | Out-Null }
 Start-Sleep -Seconds 1
 if(Test-Path -LiteralPath $root) { Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction Stop }
 foreach($name in $created) {
   & sc.exe query $name 2>&1 | Out-Null
   if($LASTEXITCODE -eq 0) {throw ('J9_SCM_SERVICE_NOT_DELETED '+$name)}
 }
}
