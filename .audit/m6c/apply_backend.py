from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_exact(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text()
    if old not in text:
        raise SystemExit(f'Expected source block missing in {path}')
    target.write_text(text.replace(old, new, 1))


replace_exact(
    'frontend/src/features/mobile/Dashboard/components/ApptCard.tsx',
    'className="w-full flex items-center justify-center gap-1.5 py-2.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-600 rounded-[16px] text-[10px] font-black uppercase tracking-widest transition-all active:scale-95"',
    'className="w-full min-h-12 flex items-center justify-center gap-1.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-600 rounded-[16px] text-[10px] font-black uppercase tracking-widest transition-all active:scale-95"',
)

replace_exact(
    'backend/routers/mobile_legacy.py',
    "\nimport base64\n\n@router.get('/patients/{patient_id}/documents'",
    "\nimport base64\nimport binascii\nimport io\n\n@router.get('/patients/{patient_id}/documents'",
)

replace_exact(
    'backend/routers/mobile_legacy.py',
    '        signed = cdata.get("signed", False)\n        res.append({',
    '        signed = cdata.get("signed", False)\n        if signed:\n            continue\n        res.append({',
)

helper = '''_MOBILE_SIGNATURE_MAX_BYTES = 2 * 1024 * 1024
_MOBILE_SIGNATURE_MAX_PIXELS = 8_000_000
_MOBILE_SIGNATURE_MIN_INK_PIXELS = 24
_MOBILE_SIGNATURE_PREFIX = "data:image/png;base64,"


def _validated_mobile_signature_png(signature_base64: str) -> bytes:
    from PIL import Image, UnidentifiedImageError

    if not isinstance(signature_base64, str) or not signature_base64.startswith(_MOBILE_SIGNATURE_PREFIX):
        raise HTTPException(status_code=422, detail="Signature PNG invalide")

    encoded = signature_base64[len(_MOBILE_SIGNATURE_PREFIX):].strip()
    if not encoded:
        raise HTTPException(status_code=422, detail="Signature vide")

    encoded_limit = ((_MOBILE_SIGNATURE_MAX_BYTES + 2) // 3) * 4 + 32
    if len(encoded) > encoded_limit:
        raise HTTPException(status_code=413, detail="Signature trop volumineuse")

    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=422, detail="Signature invalide")

    if not raw:
        raise HTTPException(status_code=422, detail="Signature vide")
    if len(raw) > _MOBILE_SIGNATURE_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Signature trop volumineuse")

    try:
        with Image.open(io.BytesIO(raw)) as probe:
            if probe.format != "PNG":
                raise HTTPException(status_code=422, detail="Signature PNG invalide")
            width, height = probe.size
            if width < 32 or height < 32:
                raise HTTPException(status_code=422, detail="Dimensions de signature invalides")
            if width * height > _MOBILE_SIGNATURE_MAX_PIXELS:
                raise HTTPException(status_code=413, detail="Signature trop grande")
            probe.load()
            rgba = probe.convert("RGBA")
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=422, detail="Image de signature invalide")

    ink_pixels = 0
    for red, green, blue, alpha in rgba.getdata():
        if alpha >= 16 and (red < 245 or green < 245 or blue < 245):
            ink_pixels += 1
            if ink_pixels >= _MOBILE_SIGNATURE_MIN_INK_PIXELS:
                break
    if ink_pixels < _MOBILE_SIGNATURE_MIN_INK_PIXELS:
        raise HTTPException(status_code=422, detail="Signature vide")

    output = io.BytesIO()
    rgba.save(output, format="PNG", optimize=True)
    normalized = output.getvalue()
    if len(normalized) > _MOBILE_SIGNATURE_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Signature trop volumineuse")
    return normalized
'''

replace_exact(
    'backend/routers/mobile_legacy.py',
    'class SignatureSubmit(BaseModel):\n    signature_base64: str\n',
    'class SignatureSubmit(BaseModel):\n    signature_base64: str\n\n' + helper + '\n',
)

replace_exact(
    'backend/routers/mobile_legacy.py',
    '''    doc = db.query(models.DocumentArchive).filter(\n        models.DocumentArchive.id == document_id,\n        models.DocumentArchive.status == models.DocumentStatus.ACTIF\n    ).first()\n''',
    '''    doc = db.query(models.DocumentArchive).filter(\n        models.DocumentArchive.id == document_id,\n        models.DocumentArchive.status == models.DocumentStatus.ACTIF,\n        models.DocumentArchive.document_type == models.DocumentType.DEVIS,\n    ).with_for_update().first()\n''',
)

replace_exact(
    'backend/routers/mobile_legacy.py',
    '''    sig_data = body.signature_base64\n    if "," in sig_data:\n        sig_data = sig_data.split(",")[1]\n\n    try:\n        sig_bytes = base64.b64decode(sig_data)\n    except Exception:\n        raise HTTPException(status_code=400, detail="Signature invalide")\n''',
    '''    cdata = dict(doc.clinical_data or {})\n    if cdata.get("signed", False):\n        raise HTTPException(status_code=409, detail="Document déjà signé")\n\n    sig_bytes = _validated_mobile_signature_png(body.signature_base64)\n''',
)

replace_exact(
    'backend/routers/mobile_legacy.py',
    '''    cdata = dict(doc.clinical_data or {})\n    cdata["signed"] = True\n''',
    '''    cdata["signed"] = True\n''',
)
