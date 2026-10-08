# D3 PRECONDITION ONLY — prepares a scratch file copy of official example.
# This is NOT an authorization to edit, open, save or modify the Facad patient.
param([Parameter(Mandatory=$true)][string]$OutDir,
      [Parameter(Mandatory=$true)][string]$SourcePath)
$ErrorActionPreference='Stop'
$dir=[IO.Path]::GetFullPath($OutDir)
[void][IO.Directory]::CreateDirectory($dir)
$log=Join-Path $dir 'd3-sandbox-preflight.txt'
'D3_PREFLIGHT=STARTED' | Set-Content -Encoding utf8 $log
function Log([string]$v){Add-Content -Encoding utf8 $log $v}
# The bootstrap extracted the signed Facad release and actually launched
# `facad-quick-demo/release/Examples/Robert-2.0.fcd`. Receive THAT exact
# absolute path instead of assuming a separate install-folder example.
$source=[IO.Path]::GetFullPath($SourcePath)
if([IO.Path]::GetFileName($source) -ne 'Robert-2.0.fcd' -or
   $source -notlike '*facad-quick-demo*release*Examples*Robert-2.0.fcd'){
  throw 'D3 source path is not the verified official release sample'
}
Log "SAMPLE_SOURCE_RELATIVE=facad-quick-demo/release/Examples/Robert-2.0.fcd"
if(-not (Test-Path -LiteralPath $source -PathType Leaf)){
 Log "SAMPLE_SOURCE_PRESENT=false"
 Log 'D3_TEST_EXECUTION=BLOCKED_NO_SOURCE'
 return
}
$srcInfo=Get-Item -LiteralPath $source
$srcHashBefore=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
Log "SAMPLE_SOURCE_PRESENT=true"
Log "SAMPLE_SOURCE_BYTES=$($srcInfo.Length)"
Log "SAMPLE_SOURCE_SHA256_BEFORE=$srcHashBefore"
# Temporary workflow output remains within this runner's isolated workspace.
$sandbox=Join-Path $dir 'd3-disposable'
[void][IO.Directory]::CreateDirectory($sandbox)
$dest=Join-Path $sandbox 'Robert_D3_DISPOSABLE.fcd'
if(Test-Path -LiteralPath $dest){throw 'D3 destination already exists; refusing overwrite'}
Copy-Item -LiteralPath $source -Destination $dest -ErrorAction Stop
$dstHash=(Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash
$srcHashAfter=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
Log "SANDBOX_COPY_CREATED=true"
Log "SANDBOX_COPY_BYTES=$((Get-Item -LiteralPath $dest).Length)"
Log "SANDBOX_COPY_SHA256=$dstHash"
Log "SAMPLE_SOURCE_SHA256_AFTER=$srcHashAfter"
if($srcHashBefore -ne $dstHash -or $srcHashBefore -ne $srcHashAfter){
 Log 'D3_TEST_EXECUTION=BLOCKED_HASH_MISMATCH'
 throw 'Source and scratch hash differ; source modification suspected'
}
Log 'D3_COPY_BYTES_VERIFIED=true'
# The data model behind .fcd is not yet audited: copying the file is NOT
# proof that a Facad session can be isolated from user data / DB storage.
Log 'D3_TEST_EXECUTION=BLOCKED_PENDING_APPLICATION_LEVEL_ISOLATION'
Log 'D3_NEXT=Prove disposable case opens with a distinct identity and that sample backing storage is unchanged; only then enable mutation tests'
