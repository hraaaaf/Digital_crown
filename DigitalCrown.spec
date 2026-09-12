# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

from backend.release_certification import verify_installable_release_directory
from backend.runtime_asset_certification import iter_runtime_asset_files

# A production EXE may only be built from an INSTALLABLE_CERTIFIED release.
# This validates exact SHA identity, GitHub provenance composition, BASIC/GOLD/ELITE
# coverage, every code hash and every packaged external runtime-asset hash BEFORE
# PyInstaller transforms the Python sources.
_CERTIFIED_RELEASE_ROOT = os.getcwd()
verify_installable_release_directory(_CERTIFIED_RELEASE_ROOT)

block_cipher = None


def _collect_ai_models_datas():
    """Use the exact same selection policy as runtime-asset certification."""
    root = Path('backend') / 'ai_models'
    entries = []
    for source in iter_runtime_asset_files(root):
        relative = source.resolve().relative_to(root.resolve())
        destination = (Path('backend') / 'ai_models' / relative.parent).as_posix()
        entries.append((str(source), destination))
    return entries


a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('frontend/dist', 'frontend/dist'),
        # Embedded release identity / deployment-integrity proofs. run.py rechecks
        # these before first-boot writes. Full source hashes were checked above.
        ('release-certification.json', '.'),
        ('.digitalcrown-release-sha', '.'),
        ('release-content.sha256', '.'),
        ('installable-certification.json', '.'),
        ('runtime-assets-certification.json', '.'),
        ('runtime-assets-content.sha256', '.'),
        ('github-attestation-verification.json', '.'),
        ('backend/scientific_assets.json', 'backend'),
        # SÉCURITÉ : ne JAMAIS embarquer de fichier .env contenant des secrets.
    ] + _collect_ai_models_datas(),
    hiddenimports=[
        'uvicorn', 'fastapi', 'sqlalchemy', 'sqlite3', 'pydantic', 'sentry_sdk',
        'onnxruntime', 'cv2', 'numpy', 'PIL', 'python-multipart', 'passlib', 'bcrypt', 'jose',
        'passlib.handlers', 'passlib.handlers.bcrypt',
        'jose.backends', 'jose.backends.cryptography_backend', 'jose.backends.native',
        'backend.services.sync_manager', 'backend.seed_templates', 'backend.seed_user', 'backend.seed_clinical',
        'backend.release_certification', 'backend.runtime_asset_certification'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DigitalCrown',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DigitalCrown',
)
