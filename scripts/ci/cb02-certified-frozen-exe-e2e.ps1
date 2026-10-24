# Only run this script on disposable GitHub Actions Windows runner.
# It launches the exact authentic installed EXE; no real clinic or patient records.
$ErrorActionPreference='Stop'
$expected='46362e2986e3b6b08598f518eff95fa01f161571'
$report=Join-Path $env:GITHUB_WORKSPACE 'evidence/output/cb02-real-exe-runtime-smoke.txt'
New-Item -Force -ItemType Directory -Path (Split-Path $report) | Out-Null
$observations=New-Object System.Collections.Generic.List[string]
function Proof([string]$x) {
  $script:observations.Add($x)
  $script:observations | Set-Content -LiteralPath $script:report -Encoding utf8
  Write-Host $x
}
function Need([bool]$x,[string]$why) {
  if(-not $x) {throw "CB02_FAIL_CLOSED: $why"}
}
function StopOwned($p) {
  if($null -ne $p) {
    $p.Refresh()
    if(-not $p.HasExited) {
      Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
      try {Wait-Process -Id $p.Id -Timeout 8 -ErrorAction SilentlyContinue} catch {}
    }
  }
}
function Probe() {
  try {return Invoke-RestMethod 'http://127.0.0.1:18765/health' -TimeoutSec 2 -ErrorAction Stop}
  catch {return $null}
}
$app=$null
$bad=$null
$installed=$false
$install=''
$sentinel=''
$sentinelDigest=''
$py=''
try {
  Need ($env:GITHUB_ACTIONS -eq 'true' -and $env:GITHUB_REPOSITORY -eq 'hraaaaf/Digital_crown') 'Wrong environment/repository'
  Need ($env:CB02_SOURCE_SHA -eq $expected) 'Wrong exact certified source'
  $official=(gh api 'repos/hraaaaf/Digital_crown/actions/runs/40091568086' | ConvertFrom-Json)
  Need ($LASTEXITCODE -eq 0 -and $official.conclusion -eq 'success' -and $official.head_sha -eq $expected) 'Official CODE_CERTIFIED run invalid'
  $win=(gh api 'repos/hraaaaf/Digital_crown/actions/runs/40091912817' | ConvertFrom-Json)
  Need ($LASTEXITCODE -eq 0 -and $win.conclusion -eq 'success' -and $win.head_sha -eq 'd30dae7ee83dfa30df8ddf88d068fa90f6e7058c') 'Source installer Windows run invalid'
  Proof 'OFFICIAL_CODE_CERTIFIED_AND_WINDOWS_RUNS=SUCCESS; EXACT_SHA=46362e2986e3b6b08598f518eff95fa01f161571'
  $sandbox=Join-Path $env:RUNNER_TEMP 'CB02-EXE-E2E-SYNTHETIC'
  Need (-not (Test-Path $sandbox)) 'Nonempty sandbox refused'
  New-Item -Force -ItemType Directory -Path $sandbox | Out-Null
  $archive=Join-Path $sandbox 'artifact'
  gh run download 40091912817 --repo hraaaaf/Digital_crown --name dc-windows-verified-installer-46362e --dir $archive
  Need ($LASTEXITCODE -eq 0) 'Cannot download pinned installer artifact'
  $found=@(Get-ChildItem $archive -Recurse -File -Filter 'DigitalCrownSetup-INSTALLABLE-CERTIFIED.exe')
  Need ($found.Count -eq 1) 'Wrong number of setup files'
  $setup=$found[0]
  $sha=(Get-FileHash $setup.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  Need ($sha -eq 'd6661fc93246aa04270144c4068a749084cbfa0f066276440450645114825949' -and $setup.Length -eq 623138132L) 'Setup SHA256/byte-count mismatch'
  Proof "OFFICIAL_INSTALLER_BYTES_VERIFIED=PASS; SIZE=$($setup.Length); SHA256=$sha"
  $install=Join-Path $sandbox 'installed'
  $base=Join-Path $sandbox 'no-patient-rehearsal'
  $config=Join-Path $base 'config'
  $data=Join-Path $base 'data'
  $logs=Join-Path $base 'logs'
  $runtime=Join-Path $base 'runtime'
  $db=Join-Path $data 'empty-encrypted.db'
  $profile=Join-Path $config '.env'
  $sentinel=Join-Path $sandbox 'outside-sentinel.txt'
  Set-Content -LiteralPath $sentinel -Value 'SYNTHETIC ONLY - NO PATIENT' -Encoding ascii
  $sentinelDigest=(Get-FileHash $sentinel -Algorithm SHA256).Hash
  $a=Start-Process -FilePath $setup.FullName -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',"/DIR=$install") -Wait -PassThru -WindowStyle Hidden
  Need ($a.ExitCode -eq 0) 'Authentic installer failed'
  $installed=$true
  $exe=Join-Path $install 'DigitalCrown.exe'
  Need (Test-Path -LiteralPath $exe -PathType Leaf) 'Installed executable absent'
  $code=(Get-Content (Join-Path $install '_internal/release-certification.json') -Raw | ConvertFrom-Json)
  $cert=(Get-Content (Join-Path $install '_internal/installable-certification.json') -Raw | ConvertFrom-Json)
  Need ($code.commit_sha -eq $expected -and $code.certification_level -eq 'CODE_CERTIFIED') 'Invalid embedded CODE certificate'
  Need ($cert.commit_sha -eq $expected -and $cert.installable -eq $true -and $cert.github_attestation_verified -eq $true) 'Invalid embedded installable certificate'
  Proof 'AUTHENTIC_WINDOWS_SETUP_INSTALLED_WITH_PROVENANCE=PASS'
  foreach($dir in @($config,$data,$logs,$runtime)) {New-Item -Force -ItemType Directory -Path $dir | Out-Null}
  $env:ENVIRONMENT='rehearsal'
  $env:DIGITALCROWN_ISOLATED_RUNTIME='1'
  $env:TELEMETRY_ENABLED='false'
  $env:CLOUD_AI_ENABLED='false'
  $env:DEBUG='false'
  $env:CROWN_BOT_GUIDED_NLU_ENABLED='false'
  $env:CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED='false'
  $env:DIGITALCROWN_RESTORE_RESTART='1'
  $env:CABINET_HOST='127.0.0.1'
  $env:CABINET_PORT='18765'
  $env:SQLCIPHER_KEY_HEX=[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).ToLowerInvariant()
  $env:CABINET_MASTER_KEY_HEX=[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).ToLowerInvariant()
  $env:SECRET_KEY=[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).ToLowerInvariant()
  $env:DIGITALCROWN_USER_DATA_DIR=$data
  $env:DIGITALCROWN_CONFIG_DIR=$config
  $env:DIGITALCROWN_LOG_DIR=$logs
  $env:DIGITALCROWN_RUNTIME_DIR=$runtime
  $env:DIGITALCROWN_ENV_FILE=$profile
  $env:DIGITALCROWN_INSTANCE_ID="CB02-EXE-$env:GITHUB_RUN_ID"
  $env:DATABASE_URL='sqlite:///'+($db -replace '\\','/')
  $env:ALLOWED_ORIGINS='http://127.0.0.1:18765'
  $env:PYTHONDONTWRITEBYTECODE='1'
  & python -m venv (Join-Path $sandbox 'operator-venv')
  Need ($LASTEXITCODE -eq 0) 'Disposable operator Python venv failed'
  $py=Join-Path $sandbox 'operator-venv/Scripts/python.exe'
  & $py -m pip install --disable-pip-version-check -r backend/requirements.txt
  Need ($LASTEXITCODE -eq 0) 'Pinned operator deps failed'
  & $py -m pip check
  Need ($LASTEXITCODE -eq 0) 'Operator dependencies incompatible'
  $fingerprint=(& $py -c "import os; from backend.core.runtime_safety import database_target_fingerprint; print(database_target_fingerprint(os.environ['DATABASE_URL']))").Trim()
  Need ($LASTEXITCODE -eq 0 -and $fingerprint -match '^[0-9a-f]{64}$') 'Invalid DB attestation'
  $env:DIGITALCROWN_ISOLATION_DB_FINGERPRINT=$fingerprint
  $profileBody=@(
    'ENVIRONMENT=rehearsal',
    ('SECRET_KEY='+$env:SECRET_KEY),
    ('CABINET_MASTER_KEY_HEX='+$env:CABINET_MASTER_KEY_HEX),
    ('SQLCIPHER_KEY_HEX='+$env:SQLCIPHER_KEY_HEX),
    ('DATABASE_URL="'+$env:DATABASE_URL+'"'),
    'DIGITALCROWN_ISOLATED_RUNTIME=1',
    ('DIGITALCROWN_ISOLATION_DB_FINGERPRINT='+$fingerprint),
    ('DIGITALCROWN_INSTANCE_ID='+$env:DIGITALCROWN_INSTANCE_ID),
    ('DIGITALCROWN_ENV_FILE="'+$profile+'"'),
    ('DIGITALCROWN_USER_DATA_DIR="'+$data+'"'),
    ('DIGITALCROWN_CONFIG_DIR="'+$config+'"'),
    ('DIGITALCROWN_RUNTIME_DIR="'+$runtime+'"'),
    ('DIGITALCROWN_LOG_DIR="'+$logs+'"'),
    'CABINET_HOST=127.0.0.1','CABINET_PORT=18765',
    'ALLOWED_ORIGINS=http://127.0.0.1:18765',
    'TELEMETRY_ENABLED=false','CLOUD_AI_ENABLED=false',
    'CROWN_BOT_GUIDED_NLU_ENABLED=false',
    'CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED=false',
    'DEBUG=false'
  )
  $profileBody | Set-Content -LiteralPath $profile -Encoding utf8
  Need (Test-Path -LiteralPath $profile -PathType Leaf) 'Explicit .env must exist before migration'
  Need (-not (Test-Path -LiteralPath $db)) 'DB unexpectedly preexisted'
  & $py -m alembic -c alembic.ini upgrade head
  Need ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $db -PathType Leaf)) 'Explicit disposable encrypted DB migration failed'
  $bytes=[IO.File]::ReadAllBytes($db)
  Need (-not ([Text.Encoding]::ASCII.GetString($bytes,0,[Math]::Min(16,$bytes.Length)).StartsWith('SQLite format 3'))) 'Database plaintext'
  $check=@'
from backend.database import engine
from sqlalchemy import text
c=engine.connect()
assert c.execute(text("SELECT version_num FROM alembic_version")).scalar()=="neo000000032"
assert c.execute(text("SELECT COUNT(*) FROM patients")).scalar()==0
assert c.execute(text("SELECT COUNT(*) FROM users")).scalar()==0
c.close()
print("ZERO_REAL_OR_SYNTHETIC_PATIENT_ROWS=PASS")
'@
  & $py -c $check
  Need ($LASTEXITCODE -eq 0) 'Prepared DB not empty/current'

  Proof 'DISPOSABLE_EMPTY_SQLCIPHER_ALEMBIC_HEAD=PASS; PATIENT_ROWS=0; USER_ROWS=0'
  Need ($null -eq (Probe)) 'Health port preoccupied before launch'
  $app=Start-Process -FilePath $exe -WorkingDirectory $install -PassThru -WindowStyle Hidden
  $ready=$false
  for($i=0;$i -lt 120;$i++) {
    $app.Refresh()
    if($app.HasExited) {break}
    $h=Probe
    if($null -ne $h -and $h.status -eq 'ok' -and $h.db -eq 'ok' -and $h.instance_id -eq $env:DIGITALCROWN_INSTANCE_ID) {$ready=$true;break}
    Start-Sleep -Seconds 1
  }
  if(-not $ready) {
    # Before application logging exists, a windowed PyInstaller error may appear
    # as a native modal Windows dialog and keep the process alive indefinitely.
    # Inspect only this isolated EXE's windows, not other runner applications.
    $windowType=@'
using System;
using System.Collections.Generic;
using System.Text;
using System.Runtime.InteropServices;
public static class Cb02NativeWindowDiagnostics {
    public delegate bool Walker(IntPtr hWnd, IntPtr param);
    [DllImport("user32.dll")] static extern bool EnumWindows(Walker callback, IntPtr param);
    [DllImport("user32.dll")] static extern bool EnumChildWindows(IntPtr parent, Walker callback, IntPtr param);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetClassName(IntPtr hWnd, StringBuilder text, int count);
    static string Description(IntPtr h) {
      var name = new StringBuilder(1024); var klass = new StringBuilder(128);
      GetWindowText(h,name,name.Capacity); GetClassName(h,klass,klass.Capacity);
      return klass.ToString()+" "+name.ToString();
    }
    public static string[] Inspect(uint pid) {
      var lines=new List<string>();
      EnumWindows((h,l)=>{
        uint current; GetWindowThreadProcessId(h,out current);
        if(current==pid) {
          lines.Add("TOP "+Description(h));
          EnumChildWindows(h,(c,p)=> {
            if(lines.Count<32) lines.Add("CHILD "+Description(c));
            return lines.Count<32;
          },IntPtr.Zero);
        }
        return true;
      },IntPtr.Zero);
      return lines.ToArray();
    }
}
'@
    try {
      Add-Type -TypeDefinition $windowType -ErrorAction Stop
      $nativeWindows=@([Cb02NativeWindowDiagnostics]::Inspect([uint32]$app.Id))
      if($nativeWindows.Count -eq 0) {Proof 'RUNTIME_WINDOWS_UI=NONE_VISIBLE'}
      foreach($label in ($nativeWindows | Select-Object -First 18)) {
        $filtered=$label -replace '(?i)(secret|password|key|token)([=:\s]+)[^\s,;]+','$1$2[REDACTED]' -replace '(?i)\b[a-f0-9]{32,}\b','[REDACTED_HEX]'
        Proof ("RUNTIME_WINDOWS_UI="+$filtered.Substring(0,[Math]::Min(300,$filtered.Length)))
      }
    } catch {Proof ("RUNTIME_WINDOWS_UI_DIAGNOSTIC_FAILED="+$_.Exception.GetType().Name)}
    # Windows UI Automation can read cross-process Static error dialog text,
    # which GetWindowText intentionally cannot retrieve for certain controls.
    try {
      Add-Type -AssemblyName UIAutomationClient -ErrorAction Stop
      $desktop=[System.Windows.Automation.AutomationElement]::RootElement
      $condition=New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::ProcessIdProperty,
        [int]$app.Id
      )
      $top=$desktop.FindAll([System.Windows.Automation.TreeScope]::Children,$condition)
      for($w=0;$w -lt [Math]::Min($top.Count,4);$w++){
        $desc=$top.Item($w).FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
        for($i=0;$i -lt [Math]::Min($desc.Count,24);$i++) {
          $name=$desc.Item($i).Current.Name
          if($name -and $name.Trim()) {
            $filtered=$name -replace '(?i)(secret|password|key|token)([=:\s]+)[^\s,;]+','$1$2[REDACTED]' -replace '(?i)\b[a-f0-9]{32,}\b','[REDACTED_HEX]'
            Proof ("RUNTIME_UIA_MESSAGE="+$filtered.Substring(0,[Math]::Min(300,$filtered.Length)))
          }
        }
      }
      if($top.Count -eq 0) {Proof 'RUNTIME_UIA_TOP_LEVEL_WINDOWS=NONE'}
    } catch {Proof ("RUNTIME_UIA_DIAGNOSTIC_FAILED="+$_.Exception.GetType().Name)}
    $metrics=Get-Process -Id $app.Id -ErrorAction SilentlyContinue
    if($metrics) {Proof ("RUNTIME_PROCESS_METRICS=CPU_SEC:{0:N1}; RAM_MB:{1:N1}; THREADS:{2}" -f $metrics.CPU,($metrics.WorkingSet64 / 1MB),$metrics.Threads.Count)}
    $sockets=@(Get-NetTCPConnection -LocalPort 18765 -ErrorAction SilentlyContinue)
    Proof "RUNTIME_LOOPBACK_PORT_LISTENERS=$(@($sockets | Where-Object State -eq 'Listen').Count)"
    $app.Refresh()
    if($app.HasExited) {
      Proof "REAL_EXE_NO_HEALTH=EXITED; EXIT_CODE=$($app.ExitCode); PID=$($app.Id)"
    } else {
      Proof "REAL_EXE_NO_HEALTH=RUNNING_BUT_NOT_READY; PID=$($app.Id)"
    }
    $fileLog=Join-Path $logs 'digitalcrown.log'
    if(Test-Path -LiteralPath $fileLog -PathType Leaf) {
      $safeErrors=@(Get-Content -LiteralPath $fileLog -Tail 100 |
        Where-Object {$_ -match 'ERROR|CRITICAL|Traceback|Exception|ModuleNotFound|ImportError|RuntimeError|SECURITE|alembic|database|SQLCipher|Permission|OSError|failed|refused'} |
        ForEach-Object {
          $_ -replace '(?i)(secret|password|key|token)([=:\s]+)[^\s,;]+','$1$2[REDACTED]' -replace '(?i)\b[a-f0-9]{32,}\b','[DIGEST_OR_SECRET_REDACTED]'
        })
      if($safeErrors.Count -eq 0) {
        Proof 'RUNTIME_LOG_FOUND_NO_ALLOWED_ERROR_LINES'
      } else {
        foreach($line in $safeErrors) {Proof "RUNTIME_LOG_DIAGNOSTIC=$line"}
      }
    } else {
      Proof 'RUNTIME_FILE_LOG_ABSENT'
    }
    try {
      $resp=Invoke-WebRequest -Uri 'http://127.0.0.1:18765/health' -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
      Proof "RUNTIME_HTTP_DIAGNOSTIC_STATUS=$($resp.StatusCode)"
    } catch {
      Proof "RUNTIME_HTTP_DIAGNOSTIC_CATEGORY=$($_.CategoryInfo.Category)"
    }
    # The full signed source, binary, and fail-closed success condition are unchanged.
  }
  Need $ready 'Real installed EXE failed to respond at /health on correct instance'
  Proof "REAL_INSTALLED_DIGITALCROWN_EXE_HEALTH=PASS; PID=$($app.Id); LOOPBACK_ONLY=YES"
  StopOwned $app
  $app=$null
  Need ($null -eq (Probe)) 'Runtime listener survived process stop'
  & $py -c $check
  Need ($LASTEXITCODE -eq 0) 'Runtime created patient/user rows'
  Proof 'REAL_EXE_STOP_AND_EMPTY_DATA_PRESERVATION=PASS'
  $file=Join-Path $install '_internal/github-attestation-verification.json'
  Need (Test-Path -LiteralPath $file -PathType Leaf) 'Attestation proof missing before test'
  $original=(Get-FileHash $file -Algorithm SHA256).Hash
  $aside="$file.e2e-test-removed"
  Move-Item -LiteralPath $file -Destination $aside
  try {
    $bad=Start-Process -FilePath $exe -WorkingDirectory $install -PassThru -WindowStyle Hidden
    for($i=0;$i -lt 35;$i++) {
      $bad.Refresh()
      if($bad.HasExited) {break}
      Start-Sleep -Seconds 1
    }
    Need ($bad.HasExited -and $bad.ExitCode -ne 0) 'Missing Sigstore evidence did not exit with failure'
    Need ($null -eq (Probe)) 'EXE with missing Sigstore proof served health'
    Proof 'REAL_EXE_MISSING_ATTESTATION=REJECTED_BEFORE_STARTUP'
  } finally {
    StopOwned $bad
    $bad=$null
    Move-Item -LiteralPath $aside -Destination $file
  }
  Need ((Get-FileHash $file -Algorithm SHA256).Hash -eq $original) 'Installed proof restoration hash mismatch'
  & $py -c $check
  Need ($LASTEXITCODE -eq 0) 'Negative test mutated user/patient data'
  Proof 'REAL_FROZEN_EXE_E2E=PASS; CLINICAL_ACTIVATION=NOT_RUN; NO_PATIENTS; ALL_FLAGS_OFF'
} finally {
  StopOwned $app
  StopOwned $bad
  if($installed -and $install -and (Test-Path $install)) {
    $uninstaller=Join-Path $install 'unins000.exe'
    if(Test-Path -LiteralPath $uninstaller -PathType Leaf) {
      $p=Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') -Wait -PassThru -WindowStyle Hidden
      if($p.ExitCode -eq 0) {Proof 'RUNTIME_TEST_UNINSTALL=PASS'}
      else {Proof "RUNTIME_TEST_UNINSTALL=FAIL; EXIT=$($p.ExitCode)"}
    }
    if((Test-Path $sentinel) -and ((Get-FileHash $sentinel -Algorithm SHA256).Hash -eq $sentinelDigest)) {
      Proof 'OUTSIDE_SYNTHETIC_SENTINEL_PRESERVED=PASS'
    } else {Proof 'OUTSIDE_SYNTHETIC_SENTINEL_PRESERVED=FAIL'}
  }
  $env:SECRET_KEY=''
  $env:SQLCIPHER_KEY_HEX=''
  $env:CABINET_MASTER_KEY_HEX=''
}
