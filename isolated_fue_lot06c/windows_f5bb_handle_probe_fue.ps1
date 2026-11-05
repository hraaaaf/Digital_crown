$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'WINDOWS_ONLY' }
$root = Join-Path $env:RUNNER_TEMP ('dc06-f5bb-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root | Out-Null
try {
  $file = Join-Path $root 'synthetic.json'
  Set-Content -LiteralPath $file -Value '{"synthetic":true}' -NoNewline -Encoding utf8
  $env:DC06_F5BB_TEST_FILE = $file
  @'
import os
from pathlib import Path
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location("dc06_f5bb_handle", Path("backend/services/windows_keyring_handle_probe.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
read_no_reparse_file = module.read_no_reparse_file
WindowsKeyringHandleDenied = module.WindowsKeyringHandleDenied
path = Path(os.environ["DC06_F5BB_TEST_FILE"])
assert read_no_reparse_file(str(path)).decode("utf-8-sig") == '{"synthetic":true}'
print("DC06_F5BB_NATIVE_HANDLE_READ_PASS")
path.write_bytes(b"x" * 16385)
try:
    read_no_reparse_file(str(path))
except WindowsKeyringHandleDenied as e:
    assert str(e) == "KEYRING_FILE_TOO_LARGE", str(e)
else:
    raise AssertionError("OVERSIZE_ACCEPTED")
print("DC06_F5BB_OVERSIZE_DENIED_PASS")
try:
    read_no_reparse_file("relative.json")
except WindowsKeyringHandleDenied as e:
    assert str(e) == "KEYRING_PATH_NOT_ABSOLUTE", str(e)
else:
    raise AssertionError("RELATIVE_ACCEPTED")
print("DC06_F5BB_RELATIVE_DENIED_PASS")
'@ | python -
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  $link = Join-Path $root 'link.json'
  New-Item -ItemType SymbolicLink -Path $link -Target $file -ErrorAction SilentlyContinue | Out-Null
  if (Test-Path -LiteralPath $link) {
    $env:DC06_F5BB_TEST_FILE = $link
    @'
import os
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location("dc06_f5bb_handle", Path("backend/services/windows_keyring_handle_probe.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
read_no_reparse_file = module.read_no_reparse_file
WindowsKeyringHandleDenied = module.WindowsKeyringHandleDenied
try:
    read_no_reparse_file(os.environ["DC06_F5BB_TEST_FILE"])
except WindowsKeyringHandleDenied as e:
    assert str(e) in ("KEYRING_REPARSE_DENIED", "KEYRING_OPEN_DENIED"), str(e)
else:
    raise AssertionError("SYMLINK_ACCEPTED")
print("DC06_F5BB_REPARSE_DENIED_PASS")
'@ | python -
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  } else {
    Write-Output 'DC06_F5BB_REPARSE_SKIPPED_NO_PRIVILEGE'
  }
  # Strict boundary: no native probe imported by the product crypto module.
  $source = Get-Content -LiteralPath 'backend/services/clinical_media_crypto_v2.py' -Raw
  if (-not $source.Contains('KEYRING_FILE_PLATFORM_UNSUPPORTED')) { throw 'WINDOWS_FAIL_CLOSED_MISSING' }
  if ($source.Contains('windows_keyring_handle_probe')) { throw 'UNREVIEWED_PRODUCT_ACTIVATION' }
  Write-Output 'DC06_F5BB_PRODUCT_STILL_CLOSED_PASS'
} finally {
  Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
