# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None
ROOT = Path.cwd()


def _required(path: str) -> str:
    p = ROOT / path
    if not p.exists():
        raise SystemExit(f"P6 packaging required asset missing: {path}")
    return path


# P6 packages only the product/runtime resources that are currently authorized.
# Scientific weights remain external/deferred and their absence is the expected
# fail-closed state until their separate scientific/product gates are complete.
datas = [
    (_required('VERSION'), '.'),
    (_required('frontend/dist'), 'frontend/dist'),
    (_required('backend/templates'), 'backend/templates'),
    (_required('backend/static/assets'), 'backend/static/assets'),
    (_required('backend/data'), 'backend/data'),
    (_required('backend/scientific_assets.json'), 'backend'),
]

version_file = _required('build/windows-version-info.txt')

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
        'backend.services.sync_manager', 'backend.seed_templates', 'backend.seed_user', 'backend.seed_clinical'
    ],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[],
    win_no_prefer_redirects=False, win_private_assemblies=False,
    cipher=block_cipher, noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True,
    name='DigitalCrown', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, console=False, disable_windowed_traceback=False,
    target_arch=None, codesign_identity=None, entitlements_file=None,
    version=version_file,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=True, upx_exclude=[], name='DigitalCrown',
)
