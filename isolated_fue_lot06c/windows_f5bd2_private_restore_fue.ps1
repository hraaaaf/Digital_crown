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

  # J4/F5B-D4d: Windows actually allows a held parent's name to be
  # renamed. A safe restore MUST create relative to the VERIFIED parent
  # HANDLE, even when an attacker replaces the old name with a junction.
  # Only publicly synthetic key material, on the ephemeral Windows runner.
  $env:DC06_J4_CURRENT_SID = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
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

probe = load("backend.services.windows_keyring_handle_probe",
             "backend/services/windows_keyring_handle_probe.py")
load("backend.services.clinical_media_keyring_recovery",
     "backend/services/clinical_media_keyring_recovery.py")
restore = load("backend.services.windows_keyring_restore",
               "backend/services/windows_keyring_restore.py")

root = Path(os.environ["DC06_F5BD2_ROOT"])
parent, moved, trap = (root / name for name in
                       ("held-parent", "moved-parent", "trap-outside"))
parent.mkdir()
trap.mkdir()
kernel = ctypes.WinDLL("kernel32", use_last_error=True)
kernel.CreateFileW.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
    ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
]
kernel.CreateFileW.restype = wintypes.HANDLE
kernel.CloseHandle.argtypes = [wintypes.HANDLE]
kernel.CloseHandle.restype = wintypes.BOOL
kernel.WriteFile.argtypes = [
    wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p,
]
kernel.WriteFile.restype = wintypes.BOOL
kernel.FlushFileBuffers.argtypes = [wintypes.HANDLE]
kernel.FlushFileBuffers.restype = wintypes.BOOL
kernel.LocalFree.argtypes = [ctypes.c_void_p]
kernel.LocalFree.restype = ctypes.c_void_p
INVALID = ctypes.c_void_p(-1).value
# Exact same parent access/share/flags as the product's ancestor validation.
parent_handle = kernel.CreateFileW(
    str(parent), 0x00000080 | 0x00020000, 0x00000001,
    None, 3, 0x00200000 | 0x02000000, None,
)
if parent_handle is None or parent_handle == INVALID:
    raise AssertionError("J4_PARENT_HANDLE_UNAVAILABLE")
descriptor = ctypes.c_void_p()
try:
    # Run the attacker in its own process; the former security assumption that
    # a READ-only shared handle blocks rename has been empirically disproved.
    rename = subprocess.run(
        [sys.executable, "-c",
         "import os,sys;os.rename(sys.argv[1],sys.argv[2])",
         str(parent), str(moved)],
        capture_output=True, text=True, timeout=20,
    )
    if rename.returncode != 0:
        raise AssertionError("J4_RENAME_REPRO_NOT_OBSERVED")
    assert moved.is_dir() and not parent.exists()
    print("DC06_J4_PARENT_RENAME_CONFIRMED_PASS")

    # Attacker supplies an alternative filesystem target at the stale path.
    # Old CreateFileW(str(path)) would follow this junction into trap-outside.
    junction = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(parent), str(trap)],
        capture_output=True, text=True, timeout=20,
    )
    if junction.returncode != 0 or not parent.is_junction():
        raise AssertionError("J4_ATTACK_JUNCTION_SETUP_FAILED")
    print("DC06_J4_ATTACKER_REPLACEMENT_JUNCTION_CONFIRMED_PASS")

    # Same user-owner+SYSTEM protected SDDL as the production restore.
    sid = os.environ["DC06_J4_CURRENT_SID"]
    if not sid.startswith("S-1-"):
        raise AssertionError("J4_WINDOWS_SID_UNAVAILABLE")
    sddl = "O:" + sid + "D:P(A;;GA;;;" + sid + ")(A;;GA;;;SY)"
    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    adv.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.DWORD),
    ]
    adv.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = wintypes.BOOL
    if not adv.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            sddl, 1, ctypes.byref(descriptor), None):
        raise AssertionError("J4_PRIVATE_DACL_UNAVAILABLE")

    payload = {
        "active_media_id": "media2", "active_locator_id": "loc2",
        "media_keys": {"media1": "11" * 32, "media2": "22" * 32},
        "locator_keys": {"loc1": "33" * 32, "loc2": "44" * 32},
    }
    raw = json.dumps(payload).encode("utf-8")
    # This is the exact production helper, no test-time hook or alternate writer.
    new_file = restore._create_new_under_checked_parent(
        parent_handle, "recovered.json", descriptor)
    try:
        written = wintypes.DWORD()
        buffer = ctypes.create_string_buffer(raw)
        if not kernel.WriteFile(new_file, buffer, len(raw),
                                ctypes.byref(written), None):
            raise AssertionError("J4_NATIVE_WRITE_DENIED")
        if written.value != len(raw) or not kernel.FlushFileBuffers(new_file):
            raise AssertionError("J4_NATIVE_WRITE_FLUSH_DENIED")
    finally:
        kernel.CloseHandle(new_file)

    genuine = moved / "recovered.json"
    injected = trap / "recovered.json"
    assert genuine.is_file() and not injected.exists()
    assert probe.read_no_reparse_file(str(genuine)) == raw
    print("DC06_J4_HANDLE_RELATIVE_PARENT_ISOLATION_PASS")
finally:
    if descriptor.value:
        kernel.LocalFree(descriptor)
    kernel.CloseHandle(parent_handle)
'@ | python -
  if ($LASTEXITCODE -ne 0) { throw 'F5BD2_J4_HANDLE_RELATIVE_PARENT_ISOLATION_FAILED' }

} finally {
  Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
