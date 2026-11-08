$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'WINDOWS_ONLY' }
$root = Join-Path $env:RUNNER_TEMP ('dc06-f5bc-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root | Out-Null
$file = Join-Path $root 'private-keyring.json'
$env:DC_MEDIA_V2_KEYRING_FILE = $file
try {
  $sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
  $acl = Get-Acl -LiteralPath $root
  $acl.SetAccessRuleProtection($true,$false)
  $acl.SetOwner($sid)
  $acl.SetAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow')))
  Set-Acl -LiteralPath $root -AclObject $acl
  @'
import importlib.util
import json
import os
import pathlib
import sys
import types
# Import the real product module without unrelated backend SQLAlchemy side effects.
for name in ("backend", "backend.services"):
    mod = types.ModuleType(name)
    mod.__path__ = [name.replace(".", "/")]
    sys.modules[name] = mod
def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, pathlib.Path(filename))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
probe = load("backend.services.windows_keyring_handle_probe",
             "backend/services/windows_keyring_handle_probe.py")
product = load("backend.services.clinical_media_crypto_v2",
               "backend/services/clinical_media_crypto_v2.py")
path = pathlib.Path(os.environ["DC_MEDIA_V2_KEYRING_FILE"])
keyring = {
    "active_media_id": "media2", "active_locator_id": "loc2",
    "media_keys": {"media1": "11" * 32, "media2": "22" * 32},
    "locator_keys": {"loc1": "33" * 32, "loc2": "44" * 32},
}
path.write_text(json.dumps(keyring), encoding="utf-8")
print("DC06_F5BC_FIXTURE_CREATED_PASS")
'@ | python -
  if ($LASTEXITCODE -ne 0) { throw 'F5BC_FIXTURE_FAILED' }
  $acl = Get-Acl -LiteralPath $file
  $acl.SetAccessRuleProtection($true,$false)
  $acl.SetOwner($sid)
  $acl.SetAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($sid,'FullControl','Allow')))
  Set-Acl -LiteralPath $file -AclObject $acl
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
def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, pathlib.Path(filename))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
load("backend.services.windows_keyring_handle_probe",
     "backend/services/windows_keyring_handle_probe.py")
product = load("backend.services.clinical_media_crypto_v2",
               "backend/services/clinical_media_crypto_v2.py")
keyring, media_id, locator_id = product.configured_keyring()
assert media_id == "media2" and locator_id == "loc2"
assert keyring.media_keys["media1"] == bytes.fromhex("11" * 32)
print("DC06_F5BC_WINDOWS_PRODUCT_KEYRING_READ_PASS")
os.environ["DC_MEDIA_V2_ACTIVE_KEY_ID"] = "media2"
try:
    product.configured_keyring()
except product.MediaCryptoV2Denied as exc:
    assert str(exc) == "MIXED_KEYRING_SOURCES", str(exc)
else:
    raise AssertionError("MIXED_SOURCES_ACCEPTED")
del os.environ["DC_MEDIA_V2_ACTIVE_KEY_ID"]
print("DC06_F5BC_MIXED_SOURCES_DENIED_PASS")
'@ | python -
  if ($LASTEXITCODE -ne 0) { throw 'F5BC_PRODUCT_READ_FAILED' }
  $acl = Get-Acl -LiteralPath $file
  $everyone = New-Object System.Security.Principal.SecurityIdentifier('S-1-1-0')
  $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($everyone,'Read','Allow')))
  Set-Acl -LiteralPath $file -AclObject $acl
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
def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, pathlib.Path(filename))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
load("backend.services.windows_keyring_handle_probe",
     "backend/services/windows_keyring_handle_probe.py")
product = load("backend.services.clinical_media_crypto_v2",
               "backend/services/clinical_media_crypto_v2.py")
try:
    product.configured_keyring()
except product.MediaCryptoV2Denied as exc:
    assert str(exc) == "KEYRING_BROAD_ACL_DENIED", str(exc)
else:
    raise AssertionError("BROAD_ACL_ACCEPTED")
print("DC06_F5BC_PRODUCT_BROAD_ACL_DENIED_PASS")
'@ | python -
  if ($LASTEXITCODE -ne 0) { throw 'F5BC_PRODUCT_BROAD_ACL_FAILED' }
} finally {
  Remove-Item Env:DC_MEDIA_V2_KEYRING_FILE -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
