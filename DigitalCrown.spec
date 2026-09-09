# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

block_cipher = None
ROOT = Path.cwd()
IS_WINDOWS = os.name == 'nt'
IS_MACOS = sys.platform == 'darwin'
APP_VERSION = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()


def _required(path: str) -> str:
    p = ROOT / path
    if not p.exists():
        raise SystemExit(f"Packaging required asset missing: {path}")
    return path


# Scientific weights are intentionally absent until separately qualified.
# P6/P7 package only authorized shared resources; runtime remains fail-closed.
datas = [
    (_required('VERSION'), '.'),
    (_required('frontend/dist'), 'frontend/dist'),
    (_required('backend/templates'), 'backend/templates'),
    (_required('backend/static/assets'), 'backend/static/assets'),
    (_required('backend/data'), 'backend/data'),
    (_required('backend/scientific_assets.json'), 'backend'),
]
if IS_WINDOWS:
    # P10 production apply must copy its external workers from the frozen package,
    # never from a mutable checkout or download location.
    datas.extend([
        (_required('scripts/windows_update_worker_entry.ps1'), 'scripts'),
        (_required('scripts/windows_update_worker.ps1'), 'scripts'),
        (_required('scripts/windows_update_worker_core.ps1'), 'scripts'),
        (_required('scripts/windows_update_recovery.ps1'), 'scripts'),
    ])

version_file = _required('build/windows-version-info.txt') if IS_WINDOWS else None
codesign_identity = (os.environ.get('DIGITALCROWN_CODESIGN_IDENTITY') or '').strip() or None
entitlements_file = None
if IS_MACOS and codesign_identity:
    entitlements_file = _required('macos/DigitalCrown.entitlements')

runtime_hooks = []
if IS_MACOS:
    runtime_hooks.append(_required('backend/macos_private_trust_runtime_hook.py'))

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'uvicorn', 'fastapi', 'sqlalchemy', 'sqlite3', 'pydantic', 'sentry_sdk',
        'onnxruntime', 'cv2', 'numpy', 'PIL', 'python-multipart', 'passlib', 'bcrypt', 'jose',
        'sqlcipher3', 'reportlab', 'weasyprint', 'qrcode', 'torch',
        'passlib.handlers', 'passlib.handlers.bcrypt',
        'jose.backends', 'jose.backends.cryptography_backend', 'jose.backends.native',
        'backend.services.sync_manager', 'backend.seed_templates', 'backend.seed_user', 'backend.seed_clinical',
        'backend.services.macos_private_trust'
    ],
    hookspath=[], hooksconfig={}, runtime_hooks=runtime_hooks, excludes=[],
    win_no_prefer_redirects=False, win_private_assemblies=False,
    cipher=block_cipher, noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True,
    name='DigitalCrown', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=not IS_MACOS, console=False, disable_windowed_traceback=False,
    target_arch='arm64' if IS_MACOS else None,
    codesign_identity=codesign_identity if IS_MACOS else None,
    entitlements_file=entitlements_file,
    version=version_file,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=not IS_MACOS, upx_exclude=[], name='DigitalCrown',
)

if IS_MACOS:
    app = BUNDLE(
        coll,
        name='DigitalCrown.app',
        icon=_required('build/macos/DigitalCrown.icns'),
        bundle_identifier='com.saninova.digitalcrown',
        version=APP_VERSION,
        info_plist={
            'CFBundleDisplayName': 'Digital Crown',
            'CFBundleName': 'Digital Crown',
            'CFBundleShortVersionString': APP_VERSION,
            'CFBundleVersion': APP_VERSION,
            'NSHighResolutionCapable': True,
            'NSAppleScriptEnabled': False,
        },
    )
