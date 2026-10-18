#Requires -Version 5.1
# P2-F01: synthetic, disposable GitHub-hosted Windows SCM service oracle.
[CmdletBinding()]
param([ValidateSet('Harness','Peer')][string]$Mode='Harness',
      [string]$WorkRoot='', [string]$ExpectedPeerSid='')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
function Assert-P2([bool]$ok,[string]$code){if(-not $ok){throw ('P2_SCM_'+$code)}}
function Deny([scriptblock]$act,[string]$code){
  try{& $act}catch{
    $e=$_.Exception;while($e.InnerException){$e=$e.InnerException}
    if($e -is [UnauthorizedAccessException]){return}
    throw
  }
  throw ('P2_SCM_UNAUTHORIZED_SUCCESS_'+$code)
}
function Ic([string[]]$arguments){
  & icacls.exe @arguments | Out-Null
  Assert-P2 ($LASTEXITCODE -eq 0) 'ICACLS_FAILED'
}
function Sc([string[]]$arguments){
  & sc.exe @arguments | Out-Null
  Assert-P2 ($LASTEXITCODE -eq 0) ('SC_'+$arguments[0]+'_FAILED')
}
function Ace([string]$path,[string[]]$allowed){
  $a=Get-Acl -LiteralPath $path
  foreach($r in $a.Access){
    if($r.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow){
      $sid=$r.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
      Assert-P2 ($allowed -contains $sid) 'UNEXPECTED_ALLOWED_SID'
    }
  }
}
function Wait-Proof([string]$file){
  for($i=0;$i -lt 140;$i++){
    if(Test-Path -LiteralPath $file -PathType Leaf){return}
    $fail=Join-Path (Split-Path -Parent $file) 'service.error'
    if(Test-Path -LiteralPath $fail){
      Write-Host ('P2_SCM_WORKER_EXCEPTION_TYPE='+(Get-Content -LiteralPath $fail -Raw).Trim())
      throw 'P2_SCM_SERVICE_WORKER_FAILED'
    }
    Start-Sleep -Milliseconds 300
  }
  throw 'P2_SCM_SERVICE_PROOF_TIMEOUT'
}
# Both Peer and Harness must pass this gate before any filesystem probe.
Assert-P2 ([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT) 'WINDOWS_ONLY'
Assert-P2 ($env:CI -eq 'true' -and $env:GITHUB_ACTIONS -eq 'true' -and
  $env:P2_RUNNER_ENVIRONMENT -eq 'github-hosted' -and
  $env:GITHUB_REPOSITORY -eq 'hraaaaf/Digital_crown' -and
  $env:P2_SCM_OWNER_GO -eq 'synthetic-ephemeral-only') 'DISPOSABLE_RUNNER_AND_OWNER_SCOPE'
if($Mode -eq 'Peer'){
  Assert-P2 (-not [string]::IsNullOrWhiteSpace($WorkRoot)) 'PEER_ROOT_REQUIRED'
  $root=[IO.Path]::GetFullPath($WorkRoot)
  $base=[IO.Path]::GetFullPath($env:ProgramData).TrimEnd('\','/')
  Assert-P2 (([IO.Path]::GetDirectoryName($root) -ieq $base) -and
    ([IO.Path]::GetFileName($root) -match '^dc-p2-scm-ci-[0-9a-f]{8}$')) 'PEER_ROOT_NOT_DISPOSABLE_FIXTURE'
  $WorkRoot=$root
  $ident=[Security.Principal.WindowsIdentity]::GetCurrent()
  $principal=[Security.Principal.WindowsPrincipal]::new($ident)
  Assert-P2 ($ident.User.Value -eq $ExpectedPeerSid) 'PEER_SID_MISMATCH'
  Assert-P2 (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) 'PEER_NOT_STANDARD'
  $private=Join-Path $WorkRoot 'private'
  $db=Join-Path $private 'synthetic.sqlite3'
  $n=0;$dac=0;$owner=0
  foreach($leaf in @($db,($db+'-wal'),($db+'-shm'))){
    $file=$leaf
    Deny { $f=[IO.File]::Open($file,[IO.FileMode]::Open,[IO.FileAccess]::Read);$f.Dispose() } 'READ';$n++
    Deny { $f=[IO.File]::Open($file,[IO.FileMode]::Open,[IO.FileAccess]::Write);$f.Dispose() } 'WRITE';$n++
    Deny {
      $f=[IO.FileStream]::new($file,[IO.FileMode]::Open,[Security.AccessControl.FileSystemRights]::Delete,
        ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete),4096,[IO.FileOptions]::None)
      $f.Dispose()
    } 'DELETE';$n++
    # Requests only; never change DACL or owner. Unexpected successful OPEN fails.
    Deny {
      $f=[IO.FileStream]::new($file,[IO.FileMode]::Open,
        [Security.AccessControl.FileSystemRights]::ChangePermissions,
        ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete),4096,[IO.FileOptions]::None)
      $f.Dispose()
    } 'WRITE_DAC';$n++;$dac++
    Deny {
      $f=[IO.FileStream]::new($file,[IO.FileMode]::Open,
        [Security.AccessControl.FileSystemRights]::TakeOwnership,
        ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete),4096,[IO.FileOptions]::None)
      $f.Dispose()
    } 'WRITE_OWNER';$n++;$owner++
  }
  Deny { [IO.File]::WriteAllText((Join-Path $private 'peer-new.txt'),'synthetic') } 'CREATE';$n++
  $exe=Get-ChildItem -LiteralPath (Join-Path $WorkRoot 'bin') -Filter '*.exe'|Select-Object -First 1
  Assert-P2 ($null -ne $exe) 'SERVICE_EXE_ABSENT'
  Deny { $f=[IO.File]::Open($exe.FullName,[IO.FileMode]::Open,[IO.FileAccess]::Write);$f.Dispose() } 'BINARY_TAMPER';$n++
  Assert-P2 ($n -eq 17 -and $dac -eq 3 -and $owner -eq 3) 'DENIAL_COUNT_WRONG'
  [IO.File]::WriteAllText((Join-Path $WorkRoot 'evidence\peer\report.txt'),
    ('PEER_SID='+$ident.User.Value+[Environment]::NewLine+
     'DENIALS='+$n+[Environment]::NewLine+
     'WRITE_DAC_DENIED='+$dac+[Environment]::NewLine+
     'WRITE_OWNER_DENIED='+$owner))
  exit 0
}
$runner=[Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
Assert-P2 ($runner.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) 'RUNNER_ADMIN_REQUIRED'
$tag=[Guid]::NewGuid().ToString('N').Substring(0,8)
$service='DCP2S'+$tag;$peer='dcp2p'+$tag
$WorkRoot=Join-Path $env:ProgramData ('dc-p2-scm-ci-'+$tag)
Assert-P2 (-not (Test-Path -LiteralPath $WorkRoot)) 'NONFRESH_ROOT'
Assert-P2 (([IO.DriveInfo]::new([IO.Path]::GetPathRoot($WorkRoot))).DriveFormat -eq 'NTFS') 'NTFS_REQUIRED'
$created=$false;$userCreated=$false;$cleanupError=$null;$mainError=$null
try{
  $bytes=New-Object byte[] 40
  $rng=[Security.Cryptography.RandomNumberGenerator]::Create()
  try{$rng.GetBytes($bytes)}finally{$rng.Dispose()}
  $pw='P2!'+[Convert]::ToBase64String($bytes).Replace('+','X').Replace('/','Y')
  $cred=[pscredential]::new(('.\'+$peer),(ConvertTo-SecureString $pw -AsPlainText -Force))
  $u=New-LocalUser -Name $peer -Password $cred.Password -Description 'Disposable SCM synthetic peer'
  $userCreated=$true;$peerSid=$u.SID.Value
  New-Item -Path $WorkRoot -ItemType Directory | Out-Null
  $bin=New-Item -Path (Join-Path $WorkRoot 'bin') -ItemType Directory
  $private=New-Item -Path (Join-Path $WorkRoot 'private') -ItemType Directory
  $evidence=New-Item -Path (Join-Path $WorkRoot 'evidence\peer') -ItemType Directory -Force
  $cs=Join-Path (Get-Location) 'tools\imaging_gateway\windows\p2_scm_synthetic_service.cs'
  Assert-P2 (Test-Path -LiteralPath $cs -PathType Leaf) 'CS_SOURCE_ABSENT'
  $exe=Join-Path $bin.FullName ($service+'.exe')
  Add-Type -Path $cs -OutputAssembly $exe -OutputType WindowsApplication -ReferencedAssemblies @('System.ServiceProcess.dll') -ErrorAction Stop
  Assert-P2 (Test-Path -LiteralPath $exe) 'CS_BUILD_FAILED'
  $peerScript=Join-Path $bin.FullName 'peer.ps1'
  Copy-Item -LiteralPath $PSCommandPath -Destination $peerScript
  Sc -arguments @('create',$service,'binPath=',('"'+$exe+'"'),'start=','demand','type=','own','obj=',('NT SERVICE\'+$service))
  $created=$true
  Sc -arguments @('sidtype',$service,'unrestricted')
  $principal='NT SERVICE\'+$service
  $sid=([Security.Principal.NTAccount]::new($principal)).Translate([Security.Principal.SecurityIdentifier]).Value
  Assert-P2 ($sid.StartsWith('S-1-5-80-')) 'SERVICE_SID_INVALID'
  $config=Get-CimInstance Win32_Service -Filter ("Name='"+$service+"'")
  Assert-P2 ($config.StartName -eq $principal) 'SCM_IDENTITY_CONFIG_INCORRECT'
  $sys='*S-1-5-18';$admins='*S-1-5-32-544';$serv='*'+$sid;$p='*'+$peerSid
  Ic -arguments @($WorkRoot,'/inheritance:r')
  Ic -arguments @($WorkRoot,'/grant:r',($sys+':(OI)(CI)F'),($admins+':(OI)(CI)F'),($serv+':(OI)(CI)RX'),($p+':(OI)(CI)RX'))
  Ic -arguments @($bin.FullName,'/inheritance:r')
  Ic -arguments @($bin.FullName,'/grant:r',($sys+':(OI)(CI)F'),($admins+':(OI)(CI)F'),($serv+':(OI)(CI)RX'),($p+':(OI)(CI)RX'))
  foreach($file in @($exe,$peerScript)){
    Ic -arguments @($file,'/inheritance:r')
    Ic -arguments @($file,'/grant:r',($sys+':F'),($admins+':F'),($serv+':RX'),($p+':RX'))
  }
  Ic -arguments @($private.FullName,'/inheritance:r')
  Ic -arguments @($private.FullName,'/grant:r',($sys+':(OI)(CI)F'),($admins+':(OI)(CI)F'),($serv+':(OI)(CI)M'),'*S-1-3-4:(OI)(CI)M')
  Ic -arguments @($evidence.FullName,'/inheritance:r')
  Ic -arguments @($evidence.FullName,'/grant:r',($sys+':(OI)(CI)F'),($admins+':(OI)(CI)F'),($p+':(OI)(CI)M'))
  Assert-P2 (Get-Acl -LiteralPath $private.FullName).AreAccessRulesProtected 'PRIVATE_ACL_INHERITS'
  Ace $private.FullName @($sid,'S-1-5-18','S-1-5-32-544','S-1-3-4')
  Ace $exe @($sid,$peerSid,'S-1-5-18','S-1-5-32-544')
  Write-Host 'P2_SCM_CONFIG_AND_PROTECTED_ACL=PASS'
  Sc -arguments @('start',$service)
  Wait-Proof (Join-Path $private.FullName 'service.ready')
  $proof=@{}
  foreach($line in (Get-Content -LiteralPath (Join-Path $private.FullName 'service.ready'))){
    $parts=$line.Split('=',2);if($parts.Length -eq 2){$proof[$parts[0]]=$parts[1]}
  }
  Assert-P2 ($proof['TOKEN_USER_SID'] -eq $sid) 'SERVICE_RUNTIME_SID_MISMATCH'
  Assert-P2 ($proof['SESSION_ID'] -eq '0') 'SERVICE_NOT_SESSION0'
  Assert-P2 ($proof['SQLITE_COMMIT'] -eq 'PASS') 'SERVICE_DB_WRITE_FAILED'
  $running=Get-CimInstance Win32_Service -Filter ("Name='"+$service+"'")
  Assert-P2 ($running.State -eq 'Running' -and [int]$running.ProcessId -eq [int]$proof['PID']) 'SCM_RUNNING_PID_MISMATCH'
  Write-Host 'P2_SCM_REAL_SERVICE_TOKEN_AND_SESSION0=PASS'
  $db=Join-Path $private.FullName 'synthetic.sqlite3'
  foreach($file in @($db,($db+'-wal'),($db+'-shm'))){
    Assert-P2 (Test-Path -LiteralPath $file -PathType Leaf) 'SQLITE_SIDECAR_MISSING'
    Ace $file @($sid,'S-1-5-18','S-1-5-32-544','S-1-3-4')
  }
  Write-Host 'P2_SCM_SQLITE_DB_WAL_SHM=PASS'
  $out=Join-Path $env:RUNNER_TEMP ('p2peer-'+$tag+'.out')
  $err=Join-Path $env:RUNNER_TEMP ('p2peer-'+$tag+'.err')
  $arguments=@('-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass',
    '-File',('"'+$peerScript+'"'),'-Mode','Peer','-WorkRoot',('"'+$WorkRoot+'"'),'-ExpectedPeerSid',$peerSid)
  $proc=Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -Credential $cred -ArgumentList $arguments -PassThru -WindowStyle Hidden -WorkingDirectory $WorkRoot -RedirectStandardOutput $out -RedirectStandardError $err
  try{
    Assert-P2 ($proc.Handle -ne [IntPtr]::Zero) 'PEER_HANDLE_INVALID'
    if(-not $proc.WaitForExit(90000)){
      Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
      throw 'P2_SCM_PEER_TIMEOUT'
    }
    $proc.Refresh();$code=$proc.ExitCode
    if($code -ne 0){
      Write-Host ('P2_SCM_PEER_EXIT='+$code)
      if(Test-Path -LiteralPath $err){Get-Content -LiteralPath $err -Tail 8|ForEach-Object{Write-Host ('P2_SCM_PEER_ERROR_CLASS='+($_ -split ':')[0])}}
    }
    Assert-P2 ($code -eq 0) 'PEER_RUN_FAILED'
  }finally{$proc.Dispose()}
  $report=Join-Path $evidence.FullName 'report.txt'
  Assert-P2 (Test-Path -LiteralPath $report) 'PEER_REPORT_MISSING'
  $reportText=Get-Content -LiteralPath $report -Raw
  Assert-P2 ($reportText.Contains('PEER_SID='+$peerSid) -and
    $reportText.Contains('DENIALS=17') -and
    $reportText.Contains('WRITE_DAC_DENIED=3') -and
    $reportText.Contains('WRITE_OWNER_DENIED=3')) 'PEER_PROOF_INCORRECT'
  Write-Host 'P2_SCM_INTERACTIVE_PEER_DENIED=17/17'
  Write-Host 'P2_SCM_PEER_WRITE_DAC_DENIED=3/3'
  Write-Host 'P2_SCM_PEER_WRITE_OWNER_DENIED=3/3'
  [IO.File]::WriteAllText((Join-Path $private.FullName 'trigger'),'synthetic')
  Wait-Proof (Join-Path $private.FullName 'service.after')
  Assert-P2 ((Get-Content -LiteralPath (Join-Path $private.FullName 'service.after') -Raw).Contains('AFTER_DENIAL_COMMIT=PASS')) 'SERVICE_AFTER_DENIAL_FAILED'
  Write-Host 'P2_SCM_POSITIVE_TRANSACTION_AFTER_DENIAL=PASS'
  Sc -arguments @('stop',$service)
  $stopped=$false
  for($i=0;$i -lt 70;$i++){
    $state=Get-CimInstance Win32_Service -Filter ("Name='"+$service+"'")
    if($state.State -eq 'Stopped'){$stopped=$true;break}
    Start-Sleep -Milliseconds 200
  }
  Assert-P2 $stopped 'SERVICE_STOP_TIMEOUT'
  & python.exe -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); rows=[x[0] for x in c.execute('select label from ledger order by id')]; assert rows==['SCM_COMMITTED','SCM_AFTER_DENIAL'],rows; assert c.execute('pragma integrity_check').fetchone()[0]=='ok';print('P2_SCM_SQLITE_REOPEN_INTEGRITY=PASS')" $db
  Assert-P2 ($LASTEXITCODE -eq 0) 'SQLITE_REOPEN_FAILED'
  Write-Host 'P2_SCM_W01_W02_W03_W10_PARTIAL=PASS'
}catch{$mainError=$_}finally{
  if($created){
    try{
      & sc.exe stop $service 2>&1 | Out-Null
      & sc.exe delete $service 2>&1 | Out-Null
      Assert-P2 ($LASTEXITCODE -eq 0) 'SERVICE_DELETE_FAILED'
      for($j=0;$j -lt 40;$j++){
        if(-not (Get-CimInstance Win32_Service -Filter ("Name='"+$service+"'"))){break}
        Start-Sleep -Milliseconds 250
      }
      Assert-P2 (-not (Get-CimInstance Win32_Service -Filter ("Name='"+$service+"'"))) 'SERVICE_LEFTOVER'
    }catch{$cleanupError='SERVICE_CLEANUP_FAILED'}
  }
  if(Test-Path -LiteralPath $WorkRoot){
    try{Remove-Item -LiteralPath $WorkRoot -Recurse -Force -ErrorAction Stop}
    catch{$cleanupError='PRIVATE_FOLDER_CLEANUP_FAILED'}
  }
  if($userCreated){
    try{Remove-LocalUser -Name $peer -ErrorAction Stop}
    catch{$cleanupError='PEER_USER_CLEANUP_FAILED'}
  }
  Remove-Item -LiteralPath (Join-Path $env:RUNNER_TEMP ('p2peer-'+$tag+'.out')) -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath (Join-Path $env:RUNNER_TEMP ('p2peer-'+$tag+'.err')) -ErrorAction SilentlyContinue
}
if($cleanupError){throw $cleanupError}
if($mainError){throw $mainError}
Assert-P2 (-not (Test-Path -LiteralPath $WorkRoot)) 'WORKSPACE_LEFTOVER'
Assert-P2 (-not (Get-LocalUser -Name $peer -ErrorAction SilentlyContinue)) 'PEER_LEFTOVER'
Write-Host 'P2_SCM_DISPOSABLE_SERVICE_ACCOUNT_WORKSPACE_CLEANUP=PASS'
Write-Host 'P2_SCM_CLINICAL_CERTIFICATION=NOT_AUTHORIZED'
