# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('frontend/dist', 'frontend/dist'),
        ('backend/ai_models', 'backend/ai_models'),
        # SÉCURITÉ : ne JAMAIS embarquer de fichier .env dans l'EXE distribué
        # (risque de secrets figés dans le binaire). La config cabinet est
        # chargée depuis %APPDATA%/DigitalCrown/.env ou DIGITALCROWN_ENV_FILE
        # (cf. backend/env_loader.py), posée par la procédure d'installation.
    ],
    hiddenimports=[
        'uvicorn', 'fastapi', 'sqlalchemy', 'sqlite3', 'pydantic', 'sentry_sdk',
        'onnxruntime', 'cv2', 'numpy', 'PIL', 'python-multipart', 'passlib', 'bcrypt', 'jose',
        # Imports dynamiques ratés par l'analyse statique PyInstaller :
        # - passlib charge ses handlers par nom au runtime (crash au boot sinon)
        # - jose charge ses backends paresseusement au premier encode/decode JWT
        #   (crash au premier login sinon)
        'passlib.handlers', 'passlib.handlers.bcrypt',
        'jose.backends', 'jose.backends.cryptography_backend', 'jose.backends.native',
        'backend.services.sync_manager', 'backend.seed_templates', 'backend.seed_user', 'backend.seed_clinical'
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
    console=True,
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
