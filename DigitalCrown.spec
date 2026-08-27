# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# Dépôts de recherche/compétition vendored dans backend/ai_models/, vérifiés
# un par un (grep sur backend/services + backend/routers, jamais un seul
# `import`/chemin réel ne les référence ; les vrais poids chargés au runtime
# — best.onnx, best.pt, panoramic_model.onnx/.pt/.pth — vivent tous à la
# racine de ai_models/, jamais dans ces dossiers) :
# - CLdetection2023-master : mmpose complet (docs/configs/tests), aucun poids
#   à l'intérieur. Son arborescence très profonde fait échouer la compilation
#   Inno Setup ("chemin introuvable", limite de longueur de chemin Windows).
# - dentex_repo, cephalometric-master, cephmark : aucun fichier de poids
#   (.onnx/.pt/.pth/.ckpt) à l'intérieur, zéro référence code.
# - CL-Detection2023 : contient un `.pt` (step5_docker_and_upload/best_model.pt,
#   27 Mo, 8 mars) mais c'est un artefact de soumission de compétition sans
#   rapport avec le vrai modèle chargé par l'app (best.pt, 367 Mo, 4 mai) —
#   tailles et dates incompatibles, jamais référencé par le code réel.
# Exclus de l'EXE packagé uniquement — ces dossiers restent dans le dépôt,
# rien n'est supprimé.
_AI_MODELS_EXCLUDE_DIRNAMES = {
    'CLdetection2023-master',
    'dentex_repo',
    'CL-Detection2023',
    'cephalometric-master',
    'cephmark',
}

# cephld_cca/ EST utilisé au runtime (backend/services/vision_service.py y
# injecte sys.path pour importer U_Net_w_Cartesian_SE, et charge son unique
# fichier de poids racine `ceph_weights.pth`, 35 Mo). Mais cephld_cca/model/
# contient 23 checkpoints d'entraînement intermédiaires (774 Mo, noms du
# style Best_Network_..._E_139.pth — historique d'époques) : aucun n'est
# jamais chargé par le code (seul `ceph_weights.pth` à la racine l'est,
# vérifié ligne par ligne dans vision_service.py). Chemin relatif exact
# (pas un simple nom de dossier) pour ne jamais exclure un futur dossier
# "model" ailleurs par erreur.
_AI_MODELS_EXCLUDE_RELPATHS = {
    os.path.join('cephld_cca', 'model'),
}


def _collect_ai_models_datas():
    root = os.path.join('backend', 'ai_models')
    entries = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _AI_MODELS_EXCLUDE_DIRNAMES]
        relpath = os.path.relpath(dirpath, root)
        if any(relpath == p or relpath.startswith(p + os.sep) for p in _AI_MODELS_EXCLUDE_RELPATHS):
            dirnames[:] = []
            continue
        for filename in filenames:
            src = os.path.join(dirpath, filename)
            entries.append((src, dirpath))
    return entries


a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('frontend/dist', 'frontend/dist'),
        # SÉCURITÉ : ne JAMAIS embarquer de fichier .env dans l'EXE distribué
        # (risque de secrets figés dans le binaire). La config cabinet est
        # chargée depuis %APPDATA%/DigitalCrown/.env ou DIGITALCROWN_ENV_FILE
        # (cf. backend/env_loader.py), posée par la procédure d'installation.
    ] + _collect_ai_models_datas(),
    hiddenimports=[
        'uvicorn', 'fastapi', 'sqlalchemy', 'sqlite3', 'pydantic', 'sentry_sdk',
        'onnxruntime', 'cv2', 'numpy', 'PIL', 'python-multipart', 'passlib', 'bcrypt', 'jose',
        # Imports dynamiques ratés par l'analyse statique PyInstaller :
        # - passlib charge ses handlers par nom au runtime (crash au boot sinon)
        # - jose charge ses backends paresseusement au premier encode/decode JWT
        #   (crash au premier login sinon)
        # - mobile_mdns charge zeroconf uniquement quand HTTPS LAN est actif
        'passlib.handlers', 'passlib.handlers.bcrypt',
        'jose.backends', 'jose.backends.cryptography_backend', 'jose.backends.native',
        'zeroconf',
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
