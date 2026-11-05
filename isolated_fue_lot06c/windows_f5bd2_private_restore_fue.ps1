$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'WINDOWS_ONLY' }
$root = Join-Path $env:RUNNER_TEMP ('dc06-f5bd2-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root | Out-Null
$env:DC06_F5BD2_ROOT = $root
try {
  @'
import importlib.util
import json
import os
import pathlib
import sys
import types
for name in ("backend", "backend.services"):
    mod = types.ModuleType(name)
    mod.__path__ = [name.replace(".", "/")]
    sys.modules[name] = mod
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, pathlib.Path(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod
load("backend.services.windows_keyring_handle_probe",
     "backend/services/windows_keyring_handle_probe.py")
restore = load("backend.services.windows_keyring_restore",
               "backend/services/windows_keyring_restore.py")
recovery = load("backend.services.clinical_media_keyring_recovery",
                "backend/services/clinical_media_keyring_recovery.py")
product = load("backend.services.clinical_media_crypto_v2",
               "backend/services/clinical_media_crypto_v2.py")
root = pathlib.Path(os.environ["DC06_F5BD2_ROOT"])
target = root / "restored.json"
data = {
    "active_media_id": "media2", "active_locator_id": "loc2",
    "media_keys": {"media1": "11" * 32, "media2": "22" * 32},
    "locator_keys": {"loc1": "33" * 32, "loc2": "44" * 32},
}
password = b"synthetic-recovery-passphrase-for-lab"
sealed = recovery.seal_keyring(data, password)
raw = json.dumps(recovery.open_keyring(sealed, password)).encode("utf-8")
restore.restore_new_private_file(str(target), raw)
assert target.is_file()
print("DC06_F5BD2_PRIVATE_NEW_FILE_CREATED_PASS")
os.environ["DC_MEDIA_V2_KEYRING_FILE"] = str(target)
keyring, media_id, locator_id = product.configured_keyring()
assert (media_id, locator_id) == ("media2", "loc2")
assert keyring.media_keys["media1"] == bytes.fromhex("11" * 32)
print("DC06_F5BD2_PRODUCT_READBACK_RETAINED_PASS")
try:
    restore.restore_new_private_file(str(target), raw)
except restore.WindowsRestoreDenied as exc:
    assert str(exc) == "RESTORE_CREATE_NEW_DENIED", str(exc)
else:
    raise AssertionError("OVERWRITE_ACCEPTED")
print("DC06_F5BD2_OVERWRITE_DENIED_PASS")
try:
    restore.restore_new_private_file("relative.json", raw)
except restore.WindowsRestoreDenied as exc:
    assert str(exc) == "RESTORE_PATH_DENIED", str(exc)
else:
    raise AssertionError("RELATIVE_PATH_ACCEPTED")
print("DC06_F5BD2_RELATIVE_DENIED_PASS")
'@ | python -
  if ($LASTEXITCODE -ne 0) { throw 'F5BD2_PRODUCT_RESTORE_FAILED' }
  $real = Join-Path $root 'real'
  New-Item -ItemType Directory -Path $real | Out-Null
  $junction = Join-Path $root 'junction'
  New-Item -ItemType Junction -Path $junction -Target $real -ErrorAction SilentlyContinue | Out-Null
  if (-not (Test-Path -LiteralPath $junction)) { throw 'F5BD2_JUNCTION_TEST_UNAVAILABLE' }
  $env:DC06_F5BD2_JUNCTION = Join-Path $junction 'denied.json'
  @'
import importlib.util
import os
import pathlib
import sys
import types
for name in ("backend", "backend.services"):
    mod = types.ModuleType(name)
    mod.__path__ = [name.replace(".", "/")]
    sys.modules[name] = mod
spec = importlib.util.spec_from_file_location(
    "backend.services.windows_keyring_handle_probe",
    pathlib.Path("backend/services/windows_keyring_handle_probe.py"))
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
spec = importlib.util.spec_from_file_location(
    "backend.services.windows_keyring_restore",
    pathlib.Path("backend/services/windows_keyring_restore.py"))
restore = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = restore
spec.loader.exec_module(restore)
try:
    restore.restore_new_private_file(os.environ["DC06_F5BD2_JUNCTION"], b'{"synthetic":true}')
except restore.WindowsRestoreDenied as exc:
    assert str(exc) in ("RESTORE_PARENT_REPARSE_DENIED", "RESTORE_PARENT_OPEN_DENIED"), str(exc)
else:
    raise AssertionError("JUNCTION_PARENT_ACCEPTED")
assert not pathlib.Path(os.environ["DC06_F5BD2_JUNCTION"]).exists()
print("DC06_F5BD2_PARENT_JUNCTION_DENIED_PASS")
'@ | python -
  if ($LASTEXITCODE -ne 0) { throw 'F5BD2_JUNCTION_FAILED' }
} finally {
  Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
