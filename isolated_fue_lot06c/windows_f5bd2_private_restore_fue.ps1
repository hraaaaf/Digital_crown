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
for label, bad in (
    ("malformed", b"{not-json"),
    ("incomplete", b'{"active_media_id":"media2"}'),
):
    rejected = root / (label + ".json")
    try:
        restore.restore_new_private_file(str(rejected), bad)
    except restore.WindowsRestoreDenied as exc:
        assert str(exc) == "RESTORE_KEYRING_INVALID", str(exc)
    else:
        raise AssertionError("INVALID_RESTORE_ACCEPTED_" + label)
    assert not rejected.exists()
    print("DC06_F5BD3_" + label.upper() + "_PREWRITE_DENIED_PASS")
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
    import json
    valid = {
        "active_media_id": "media2", "active_locator_id": "loc2",
        "media_keys": {"media1": "11" * 32, "media2": "22" * 32},
        "locator_keys": {"loc1": "33" * 32, "loc2": "44" * 32},
    }
    restore.restore_new_private_file(
        os.environ["DC06_F5BD2_JUNCTION"],
        json.dumps(valid).encode("utf-8"),
    )
except restore.WindowsRestoreDenied as exc:
    assert str(exc) in ("RESTORE_PARENT_REPARSE_DENIED", "RESTORE_PARENT_OPEN_DENIED"), str(exc)
else:
    raise AssertionError("JUNCTION_PARENT_ACCEPTED")
assert not pathlib.Path(os.environ["DC06_F5BD2_JUNCTION"]).exists()
print("DC06_F5BD2_PARENT_JUNCTION_DENIED_PASS")
'@ | python -
  if ($LASTEXITCODE -ne 0) { throw 'F5BD2_JUNCTION_FAILED' }

  # J4: a separate process attempts a live namespace mutation while a parent
  # directory handle has EXACTLY the no-write/no-delete sharing used by restore.
  # This is a bounded share-mode adversarial FUE, NOT a full concurrent race proof.
  @'
import ctypes
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import types
from ctypes import wintypes

for name in ("backend", "backend.services"):
    module = types.ModuleType(name)
    module.__path__ = [name.replace(".", "/")]
    sys.modules[name] = module

def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(filename))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

load("backend.services.windows_keyring_handle_probe",
     "backend/services/windows_keyring_handle_probe.py")
load("backend.services.clinical_media_keyring_recovery",
     "backend/services/clinical_media_keyring_recovery.py")
restore = load("backend.services.windows_keyring_restore",
               "backend/services/windows_keyring_restore.py")

parent = Path(os.environ["DC06_F5BD2_ROOT"]) / "held-parent"
moved = Path(os.environ["DC06_F5BD2_ROOT"]) / "attacker-moved"
parent.mkdir()
kernel = ctypes.WinDLL("kernel32", use_last_error=True)
kernel.CreateFileW.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
    wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
]
kernel.CreateFileW.restype = wintypes.HANDLE
kernel.CloseHandle.argtypes = [wintypes.HANDLE]
kernel.CloseHandle.restype = wintypes.BOOL
INVALID = ctypes.c_void_p(-1).value
# FILE_READ_ATTRIBUTES | READ_CONTROL, FILE_SHARE_READ, OPEN_EXISTING,
# FILE_FLAG_OPEN_REPARSE_POINT | FILE_FLAG_BACKUP_SEMANTICS.
handle = kernel.CreateFileW(str(parent), 0x00000080 | 0x00020000,
                            0x00000001, None, 3, 0x00200000 | 0x02000000, None)
if handle is None or handle == INVALID:
    raise AssertionError("J4_PARENT_HANDLE_UNAVAILABLE")

try:
    attacker = r"""
import ctypes
import os
from pathlib import Path
import sys
from ctypes import wintypes
parent = Path(sys.argv[1])
moved = Path(sys.argv[2])
try:
    os.rename(parent, moved)
except OSError as exc:
    if getattr(exc, "winerror", None) not in (5, 32, 33):
        raise
    print("DC06_J4_PARENT_RENAME_DENIED_PASS")
else:
    raise AssertionError("PARENT_SWAP_RENAME_ALLOWED")

kernel = ctypes.WinDLL("kernel32", use_last_error=True)
kernel.CreateFileW.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
    wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
]
kernel.CreateFileW.restype = wintypes.HANDLE
kernel.CloseHandle.argtypes = [wintypes.HANDLE]
kernel.CloseHandle.restype = wintypes.BOOL
# A write-attributes handle is required to modify the directory reparse data;
# its open must conflict with the restore-held read-only share contract.
write_handle = kernel.CreateFileW(str(parent), 0x00000100, 0x00000007,
                                  None, 3, 0x00200000 | 0x02000000, None)
if write_handle is not None and write_handle != ctypes.c_void_p(-1).value:
    kernel.CloseHandle(write_handle)
    raise AssertionError("PARENT_WRITE_ATTRIBUTES_ALLOWED")
if ctypes.get_last_error() not in (5, 32, 33):
    raise AssertionError("PARENT_WRITE_ATTRIBUTES_UNEXPECTED_WINERROR")
print("DC06_J4_PARENT_WRITE_ATTRIBUTES_DENIED_PASS")
"""
    attack = subprocess.run(
        [sys.executable, "-c", attacker, str(parent), str(moved)],
        check=False, capture_output=True, text=True, timeout=20,
    )
    if attack.returncode != 0:
        # The previous check=True hid the actual attacker result from CI logs.
        # Only fixed marker names and the last exception CLASS are reported:
        # never print paths, stdout/stderr bodies or synthetic keyring bytes.
        last = attack.stderr.strip().splitlines()
        detail = last[-1] if last else ""
        reasons = (
            "PARENT_SWAP_RENAME_ALLOWED",
            "PARENT_WRITE_ATTRIBUTES_ALLOWED",
            "PARENT_WRITE_ATTRIBUTES_UNEXPECTED_WINERROR",
        )
        reason = next((token for token in reasons if token in detail), "")
        if not reason:
            reason = detail.split(":", 1)[0][:64] if detail else "CHILD_EXIT_NO_STDERR"
        print("DC06_J4_ATTACKER_DIAGNOSTIC_" + reason, flush=True)
        print("DC06_J4_RENAME_DENIAL_OBSERVED_" +
              str("DC06_J4_PARENT_RENAME_DENIED_PASS" in attack.stdout), flush=True)
        print("DC06_J4_WRITE_DENIAL_OBSERVED_" +
              str("DC06_J4_PARENT_WRITE_ATTRIBUTES_DENIED_PASS" in attack.stdout),
              flush=True)
        raise AssertionError("J4_CHILD_PROBE_FAILED")
    assert "DC06_J4_PARENT_RENAME_DENIED_PASS" in attack.stdout
    assert "DC06_J4_PARENT_WRITE_ATTRIBUTES_DENIED_PASS" in attack.stdout
    assert parent.is_dir() and not moved.exists()
    data = {
        "active_media_id": "media2", "active_locator_id": "loc2",
        "media_keys": {"media1": "11" * 32, "media2": "22" * 32},
        "locator_keys": {"loc1": "33" * 32, "loc2": "44" * 32},
    }
    target = parent / "restored.json"
    restore.restore_new_private_file(str(target), json.dumps(data).encode("utf-8"))
    assert target.is_file() and not moved.exists()
    assert json.loads(target.read_text(encoding="utf-8")) == data
    print(attack.stdout.strip())
    print("DC06_J4_PARENT_NAMESPACE_AND_RESTORE_PASS")
finally:
    kernel.CloseHandle(handle)
'@ | python -
  if ($LASTEXITCODE -ne 0) { throw 'F5BD2_J4_PARENT_SHARE_BARRIER_FAILED' }

} finally {
  Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
