from pathlib import Path

ROOT = Path('.')

# -----------------------------------------------------------------------------
# Backend: context-bound clinical photo upload
# -----------------------------------------------------------------------------
router_path = ROOT / 'backend/routers/mobile_resource_bridge.py'
router = router_path.read_text(encoding='utf-8')
if "'/resource-context-photo'" in router:
    raise SystemExit('M6-A backend already present')

router = router.replace(
    'from pathlib import Path\nimport base64',
    'from pathlib import Path\nfrom io import BytesIO\nimport base64',
    1,
)
router = router.replace(
    'from fastapi import APIRouter, Depends, Header, HTTPException',
    'from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile',
    1,
)
router = router.replace(
    'from pydantic import BaseModel\n',
    'from pydantic import BaseModel\nfrom PIL import Image, ImageOps, UnidentifiedImageError\n',
    1,
)

marker = "@router.get('/resource-bridge-options', summary='Cibles autorisées pour un pont mobile de ressource')"
helper = r'''_CLINICAL_PHOTO_MAX_BYTES = 12 * 1024 * 1024
_CLINICAL_PHOTO_MAX_PIXELS = 50_000_000
_CLINICAL_PHOTO_SOURCE_FORMATS = {'JPEG', 'PNG', 'WEBP'}


def _normalize_clinical_photo(raw: bytes) -> bytes:
    """Validate, orient and rewrite a clinical image as metadata-free JPEG."""
    if not raw:
        raise HTTPException(status_code=422, detail="La photo clinique est vide.")
    if len(raw) > _CLINICAL_PHOTO_MAX_BYTES:
        raise HTTPException(status_code=413, detail="La photo clinique dépasse la limite de 12 MiB.")

    try:
        with Image.open(BytesIO(raw)) as probe:
            source_format = str(probe.format or '').upper()
            width, height = probe.size
            if source_format not in _CLINICAL_PHOTO_SOURCE_FORMATS:
                raise HTTPException(status_code=422, detail="Format de photo non pris en charge. Utilisez JPEG, PNG ou WebP.")
            if width <= 0 or height <= 0 or width * height > _CLINICAL_PHOTO_MAX_PIXELS:
                raise HTTPException(status_code=413, detail="La résolution de la photo clinique est trop élevée.")
            probe.verify()

        with Image.open(BytesIO(raw)) as image:
            image = ImageOps.exif_transpose(image)
            image.load()
            if image.width <= 0 or image.height <= 0 or image.width * image.height > _CLINICAL_PHOTO_MAX_PIXELS:
                raise HTTPException(status_code=413, detail="La résolution de la photo clinique est trop élevée.")

            if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
                rgba = image.convert('RGBA')
                normalized_image = Image.new('RGB', rgba.size, 'white')
                normalized_image.paste(rgba, mask=rgba.getchannel('A'))
            else:
                normalized_image = image.convert('RGB')

            output = BytesIO()
            normalized_image.save(output, format='JPEG', quality=95, optimize=True)
            normalized = output.getvalue()
            if not normalized:
                raise HTTPException(status_code=422, detail="Impossible de normaliser la photo clinique.")
            return normalized
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise HTTPException(status_code=422, detail="Le fichier sélectionné n'est pas une image clinique valide.") from exc


'''
if marker not in router:
    raise SystemExit('M6-A backend insertion marker missing')
router = router.replace(marker, helper + marker, 1)

media_marker = "@router.post('/resource-context-media', summary='Charger le média protégé du contexte mobile')"
endpoint = r'''@router.post('/resource-context-photo', summary='Archiver une photo clinique depuis le contexte Patient mobile')
async def upload_resource_context_photo(
    context_key: str = Form(...),
    file: UploadFile = File(...),
    authorization: str = Header(...),
    db: Session = Depends(database.get_db),
):
    mobile_user, context = _validated_mobile_context(db, authorization, context_key)
    if str(context['resource_type']).lower() != 'patient':
        raise HTTPException(status_code=422, detail="La photo clinique exige un contexte Patient.")

    patient = _patient_resource(db, mobile_user, int(context['resource_id']))
    claimed_type = str(file.content_type or '').strip().lower()
    if claimed_type and not claimed_type.startswith('image/'):
        raise HTTPException(status_code=422, detail="Le fichier sélectionné n'est pas une image.")

    try:
        raw = await file.read(_CLINICAL_PHOTO_MAX_BYTES + 1)
    finally:
        await file.close()
    normalized = _normalize_clinical_photo(raw)

    filename = f"photo-clinique-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(4)}.jpg"
    archive_service = _documents.get_archive_service(db)
    document, _ = archive_service.archive_document(
        patient_id=patient.id,
        file_content=normalized,
        filename=filename,
        doc_type=models.DocumentType.PHOTO_CLINIQUE,
        uploaded_by_id=mobile_user.id,
        title='Photo clinique',
        description='Capture mobile contextuelle',
        tags=['mobile', 'photo-clinique'],
        is_accounted=False,
    )
    _documents.audit_service.log(
        db=db,
        user_id=mobile_user.id,
        employer_id=mobile_user.get_employer_id(),
        action='CLINICAL_PHOTO_CAPTURED',
        resource_type='PHOTO_CLINIQUE',
        resource_id=str(document.id),
        severity='INFO',
        details=f"Photo clinique mobile archivée document_id={document.id}",
    )
    return {
        'success': True,
        'document': {
            'id': document.id,
            'document_type': models.DocumentType.PHOTO_CLINIQUE.value,
            'title': document.title or 'Photo clinique',
            'created_at': document.created_at.isoformat() if document.created_at else None,
        },
    }


'''
if media_marker not in router:
    raise SystemExit('M6-A media marker missing')
router = router.replace(media_marker, endpoint + media_marker, 1)
router_path.write_text(router.rstrip() + '\n', encoding='utf-8')

# -----------------------------------------------------------------------------
# Frontend: camera picker, preview sheet, explicit save
# -----------------------------------------------------------------------------
front_path = ROOT / 'frontend/src/features/mobile/Context/MobileContext.tsx'
front = front_path.read_text(encoding='utf-8')
if 'data-m6a-photo-action' in front:
    raise SystemExit('M6-A frontend already present')

front = front.replace(
    "import { useEffect, useMemo, useRef, useState } from 'react';",
    "import { useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react';",
    1,
)
front = front.replace(
    'import { AlertTriangle, ArrowLeft, Calendar, Download, ExternalLink, FileText, Image as ImageIcon, Loader2, Phone, RefreshCcw, ShieldCheck } from \'lucide-react\';',
    'import { AlertTriangle, ArrowLeft, Calendar, Camera, CheckCircle2, Download, ExternalLink, FileText, Image as ImageIcon, Loader2, Phone, RefreshCcw, ShieldCheck, X } from \'lucide-react\';',
    1,
)

state_marker = "  const [error, setError] = useState('');\n"
state_block = r'''  const photoInputRef = useRef<HTMLInputElement | null>(null);
  const photoPreviewUrlRef = useRef<string | null>(null);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreviewUrl, setPhotoPreviewUrl] = useState<string | null>(null);
  const [photoPhase, setPhotoPhase] = useState<'idle' | 'preview' | 'uploading' | 'saved'>('idle');
  const [photoError, setPhotoError] = useState('');
'''
if state_marker not in front:
    raise SystemExit('M6-A frontend state marker missing')
front = front.replace(state_marker, state_marker + state_block, 1)

clear_marker = "  const load = async () => {\n"
clear_block = r'''  const clearClinicalPhoto = () => {
    if (photoPreviewUrlRef.current) URL.revokeObjectURL(photoPreviewUrlRef.current);
    photoPreviewUrlRef.current = null;
    setPhotoPreviewUrl(null);
    setPhotoFile(null);
    setPhotoPhase('idle');
    setPhotoError('');
    if (photoInputRef.current) photoInputRef.current.value = '';
  };

'''
if clear_marker not in front:
    raise SystemExit('M6-A frontend clear marker missing')
front = front.replace(clear_marker, clear_block + clear_marker, 1)
front = front.replace("    clearMedia();\n    const stored =", "    clearMedia();\n    clearClinicalPhoto();\n    const stored =", 1)
front = front.replace(
    "      if (mediaUrlRef.current) URL.revokeObjectURL(mediaUrlRef.current);\n    };",
    "      if (mediaUrlRef.current) URL.revokeObjectURL(mediaUrlRef.current);\n      if (photoPreviewUrlRef.current) URL.revokeObjectURL(photoPreviewUrlRef.current);\n    };",
    1,
)

handler_marker = "  if (phase === 'loading') {\n"
handlers = r'''  const openClinicalPhotoPicker = () => {
    setPhotoError('');
    photoInputRef.current?.click();
  };

  const handleClinicalPhotoSelected = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] || null;
    if (!file) return;
    if (file.type && !file.type.startsWith('image/')) {
      setPhotoError('Sélectionnez une image JPEG, PNG ou WebP.');
      event.target.value = '';
      return;
    }
    if (file.size > 12 * 1024 * 1024) {
      setPhotoError('La photo dépasse la limite de 12 MiB.');
      event.target.value = '';
      return;
    }
    if (photoPreviewUrlRef.current) URL.revokeObjectURL(photoPreviewUrlRef.current);
    const nextUrl = URL.createObjectURL(file);
    photoPreviewUrlRef.current = nextUrl;
    setPhotoFile(file);
    setPhotoPreviewUrl(nextUrl);
    setPhotoError('');
    setPhotoPhase('preview');
  };

  const uploadClinicalPhoto = async () => {
    if (!photoFile || !context || context.type !== 'patient') return;
    setPhotoPhase('uploading');
    setPhotoError('');
    try {
      let creds = await MobileStorage.getCredentials();
      if (!creds?.access_token) throw new Error('Session mobile non disponible. Régénérez le pont depuis le poste cabinet.');

      const request = async (accessToken: string) => {
        const form = new FormData();
        form.append('context_key', context.key);
        form.append('file', photoFile, photoFile.name || 'photo-clinique.jpg');
        return fetch(`${creds!.api_base_url.replace(/\/$/, '')}/api/mobile/resource-context-photo`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${accessToken}` },
          body: form,
        });
      };

      let response = await request(creds.access_token);
      if (response.status === 401) {
        creds = await MobileStorage.refreshCredentials();
        if (creds?.access_token) response = await request(creds.access_token);
      }
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || `Photo clinique non enregistrée (${response.status}).`);
      }
      const payload = await response.json();
      if (!payload?.success || payload?.document?.document_type !== 'PHOTO_CLINIQUE') {
        throw new Error('Réponse d’enregistrement de photo invalide.');
      }
      setPhotoPhase('saved');
    } catch (err: unknown) {
      setPhotoError(err instanceof TypeError
        ? 'Serveur du cabinet inaccessible. La photo reste en aperçu : vérifiez le poste cabinet puis réessayez.'
        : err instanceof Error
          ? err.message
          : 'Impossible d’enregistrer la photo clinique.');
      setPhotoPhase('preview');
    }
  };

'''
if handler_marker not in front:
    raise SystemExit('M6-A frontend handler marker missing')
front = front.replace(handler_marker, handlers + handler_marker, 1)

quick_old = '<div className="grid grid-cols-2 gap-3"><a data-m4a-touch href={patient!.telephone ? `tel:${patient!.telephone}` : undefined} aria-disabled={!patient!.telephone} className="min-h-[54px] rounded-2xl bg-card-bg border border-border-main inline-flex items-center justify-center gap-2 font-black text-sm text-text-main aria-disabled:opacity-40"><Phone size={18} /> Appeler</a><button data-m4a-touch type="button" onClick={() => navigate(\'/mobile/dashboard?tab=agenda\')} className="min-h-[54px] rounded-2xl bg-primary text-white inline-flex items-center justify-center gap-2 font-black text-sm"><Calendar size={18} /> Agenda</button></div>'
quick_new = r'''<div className="grid grid-cols-2 gap-3"><a data-m4a-touch href={patient!.telephone ? `tel:${patient!.telephone}` : undefined} aria-disabled={!patient!.telephone} className="min-h-[54px] rounded-2xl bg-card-bg border border-border-main inline-flex items-center justify-center gap-2 font-black text-sm text-text-main aria-disabled:opacity-40"><Phone size={18} /> Appeler</a><button data-m4a-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda')} className="min-h-[54px] rounded-2xl bg-primary text-white inline-flex items-center justify-center gap-2 font-black text-sm"><Calendar size={18} /> Agenda</button></div>
        <input ref={photoInputRef} data-m6a-photo-input type="file" accept="image/jpeg,image/png,image/webp" capture="environment" onChange={handleClinicalPhotoSelected} className="sr-only" tabIndex={-1} aria-hidden="true" />
        <button data-m6a-photo-action data-m6a-touch type="button" onClick={openClinicalPhotoPicker} className="mt-3 w-full min-h-[66px] rounded-2xl bg-primary text-white inline-flex items-center justify-start gap-3 px-4 text-left shadow-elite active:scale-[0.99] transition-transform focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white/15"><Camera size={20} /></span>
          <span><span className="block font-black text-sm">Photo clinique</span><span className="mt-0.5 block text-[11px] font-bold text-white/80">Prendre une photo au fauteuil</span></span>
        </button>'''
if quick_old not in front:
    raise SystemExit('M6-A quick actions baseline mismatch')
front = front.replace(quick_old, quick_new, 1)

close_old = "        <button data-m4a-touch type=\"button\" onClick={() => navigate('/mobile/dashboard?tab=agenda', { replace: true })} className=\"mt-6 w-full min-h-[54px] rounded-2xl bg-card-bg border border-border-main text-text-main font-black text-xs uppercase tracking-widest\">Retour au mobile</button>\n      </div>\n    </div>\n  );\n};"
close_new = r'''        <button data-m4a-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda', { replace: true })} className="mt-6 w-full min-h-[54px] rounded-2xl bg-card-bg border border-border-main text-text-main font-black text-xs uppercase tracking-widest">Retour au mobile</button>
      </div>

      {photoPreviewUrl && photoFile && (
        <div data-m6a-photo-sheet className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/30 backdrop-blur-sm sm:p-4">
          <section role="dialog" aria-modal="true" aria-labelledby="m6a-photo-title" className="w-full max-w-md rounded-t-[2rem] sm:rounded-[2rem] bg-card-bg border border-border-main shadow-elite p-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] relative">
            <div className="mx-auto mb-4 h-1.5 w-12 rounded-full bg-text-muted/20 sm:hidden" />
            <button data-m6a-touch type="button" aria-label="Fermer la photo clinique" onClick={clearClinicalPhoto} className="absolute right-4 top-4 min-h-[52px] min-w-[52px] rounded-2xl inline-flex items-center justify-center text-text-muted hover:bg-primary/5"><X size={20} /></button>
            <p className="text-[10px] font-black uppercase tracking-[0.16em] text-primary">Photo clinique</p>
            <h2 id="m6a-photo-title" className="mt-1 pr-14 text-xl font-black text-text-main">{photoPhase === 'saved' ? 'Photo enregistrée' : 'Nouvelle photo clinique'}</h2>
            <p className="mt-1 text-xs font-bold text-text-muted">{displayName} · Dossier {patient!.numero_dossier || 'sans numéro'}</p>
            <img data-m6a-photo-preview src={photoPreviewUrl} alt={`Aperçu de la photo clinique de ${displayName}`} className="mt-4 block w-full max-h-[42dvh] aspect-[4/3] object-contain rounded-2xl border border-border-main bg-slate-950/5" />

            {photoPhase === 'saved' ? (
              <div data-m6a-photo-success className="mt-4">
                <div className="min-h-[52px] rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 flex items-center gap-3 text-emerald-800"><CheckCircle2 size={20} className="shrink-0" /><p className="text-sm font-black">Photo clinique enregistrée dans le dossier</p></div>
                <button data-m6a-touch type="button" onClick={() => { clearClinicalPhoto(); setTimeout(() => photoInputRef.current?.click(), 0); }} className="mt-3 w-full min-h-[54px] rounded-2xl bg-primary text-white inline-flex items-center justify-center gap-2 font-black text-sm"><Camera size={18} /> Prendre une autre photo</button>
              </div>
            ) : (
              <>
                <p className="mt-3 text-[11px] font-bold text-text-muted">La photo n’est pas enregistrée avant votre confirmation.</p>
                {photoError && <div role="alert" className="mt-3 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-xs font-bold text-rose-700">{photoError}</div>}
                <div className="mt-4 grid grid-cols-2 gap-3">
                  <button data-m6a-touch type="button" disabled={photoPhase === 'uploading'} onClick={openClinicalPhotoPicker} className="min-h-[54px] rounded-2xl bg-card-bg border border-border-main text-text-main inline-flex items-center justify-center gap-2 font-black text-sm disabled:opacity-50"><RefreshCcw size={17} /> Reprendre</button>
                  <button data-m6a-touch type="button" disabled={photoPhase === 'uploading'} onClick={() => void uploadClinicalPhoto()} className="min-h-[54px] rounded-2xl bg-primary text-white inline-flex items-center justify-center gap-2 font-black text-sm disabled:opacity-60">{photoPhase === 'uploading' ? <><Loader2 size={17} className="animate-spin" /> Enregistrement…</> : 'Enregistrer'}</button>
                </div>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
};'''
if close_old not in front:
    raise SystemExit('M6-A patient closing marker mismatch')
front = front.replace(close_old, close_new, 1)
front_path.write_text(front.rstrip() + '\n', encoding='utf-8')

# -----------------------------------------------------------------------------
# Backend integration tests carried by the product commit
# -----------------------------------------------------------------------------
test_path = ROOT / 'backend/tests/test_mobile_m6a_clinical_photo.py'
test_path.write_text(r'''from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from PIL import Image

from backend import models
from backend.routers import mobile_resource_bridge
from backend.routers.mobile_resource_bridge import BRIDGE_CONTEXT_TABLE  # noqa: F401
from backend.security import get_password_hash
from backend.services import archive_service


@pytest.fixture(autouse=True)
def _isolate_mobile_photo_runtime(tmp_path, monkeypatch):
    from backend.main import _license_cache
    from backend.utils import rate_limit

    _license_cache.clear()
    monkeypatch.setattr(rate_limit, '_store_path', str(tmp_path / 'm6a-rate-limit.json'))
    monkeypatch.setattr(archive_service, 'MEDIA_DIR', tmp_path)
    monkeypatch.setattr(archive_service, 'ARCHIVE_BASE_DIR', tmp_path / 'archives')
    monkeypatch.setattr(mobile_resource_bridge._documents, 'MEDIA_DIR', tmp_path)
    yield
    _license_cache.clear()


def _user(db, *, email, role=models.UserRole.DENTISTE, employer_id=None, permissions=None):
    user = models.User(
        email=email,
        hashed_password=get_password_hash('TestPass123!'),
        role=role,
        nom_complet='M6A User',
        is_active=True,
        is_licensed=True,
        license_expires_at=datetime.utcnow() + timedelta(days=30),
        employer_id=employer_id,
        permissions=permissions or {},
        approval_status='approved',
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _patient(db, owner, *, dossier='M6A-001'):
    patient = models.Patient(
        numero_dossier=dossier,
        nom='BENNANI',
        prenom='Sara',
        date_naissance=datetime(1992, 5, 18),
        sexe='F',
        employer_id=owner.id,
        telephone='0612345678',
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _cabinet(db, owner, public_id='abcdef1234567890'):
    cfg = models.CabinetConfig(owner_id=owner.id, public_id=public_id)
    db.add(cfg)
    db.commit()
    return cfg


def _auth(client, user):
    response = client.post('/api/auth/login', data={'username': user.email, 'password': 'TestPass123!'})
    assert response.status_code == 200, response.text
    return {'Authorization': f"Bearer {response.json()['access_token']}"}


def _client_public_key():
    private_key = ec.generate_private_key(ec.SECP256R1())
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    ).hex()


def _mobile_patient_context(client, db, owner, patient, owner_headers, *, target_user_id=None):
    payload = {'resource_type': 'patient', 'resource_id': patient.id}
    if target_user_id is not None:
        payload['target_user_id'] = target_user_id
    issued = client.post('/api/mobile/resource-bridge-pairing', json=payload, headers=owner_headers)
    assert issued.status_code == 200, issued.text
    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    claimed = client.post('/api/mobile/claim-token', json={
        'token': pairing.token,
        'client_public_key_hex': _client_public_key(),
    })
    assert claimed.status_code == 200, claimed.text
    access = claimed.json()['access_token']
    destination = client.post(
        '/api/mobile/resource-bridge-destination',
        json={'credential': pairing.token},
        headers={'Authorization': f'Bearer {access}'},
    )
    assert destination.status_code == 200, destination.text
    return access, destination.json()['context']['key']


def _jpeg_bytes(*, with_exif=False):
    image = Image.new('RGB', (96, 64), color=(205, 225, 240))
    output = BytesIO()
    if with_exif:
        exif = Image.Exif()
        exif[274] = 6
        exif[270] = 'metadata-to-strip'
        image.save(output, format='JPEG', quality=95, exif=exif)
    else:
        image.save(output, format='JPEG', quality=95)
    return output.getvalue()


def _upload(client, access, context_key, content, *, filename='chairside.jpg', content_type='image/jpeg'):
    return client.post(
        '/api/mobile/resource-context-photo',
        data={'context_key': context_key},
        files={'file': (filename, content, content_type)},
        headers={'Authorization': f'Bearer {access}'},
    )


def test_mobile_clinical_photo_archives_exact_patient_and_strips_metadata(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.is_licensed = True
    dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.commit()
    _cabinet(db, dentiste)
    patient = _patient(db, dentiste)
    access, context_key = _mobile_patient_context(client, db, dentiste, patient, auth_headers)

    response = _upload(client, access, context_key, _jpeg_bytes(with_exif=True), filename='../../evil.php.jpg')
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload['success'] is True
    assert payload['document']['document_type'] == 'PHOTO_CLINIQUE'
    assert 'patient_id' not in payload
    assert 'file_path' not in payload['document']

    document = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == payload['document']['id']).one()
    assert document.patient_id == patient.id
    assert document.document_type == models.DocumentType.PHOTO_CLINIQUE
    assert document.uploaded_by_id == dentiste.id
    assert document.original_filename.startswith('photo-clinique-')
    assert document.original_filename.endswith('.jpg')
    assert '..' not in document.original_filename
    assert 'evil' not in document.original_filename

    relative = document.file_path.replace('static/archives/', '', 1)
    stored = Path(archive_service.ARCHIVE_BASE_DIR) / relative
    assert stored.is_file()
    assert archive_service.ARCHIVE_BASE_DIR.resolve() in stored.resolve().parents
    with Image.open(stored) as normalized:
        assert normalized.format == 'JPEG'
        assert normalized.getexif().get(274) is None
        assert normalized.getexif().get(270) is None


def test_mobile_clinical_photo_rejects_invalid_and_oversized_files(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.is_licensed = True
    dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.commit()
    _cabinet(db, dentiste)
    patient = _patient(db, dentiste)
    access, context_key = _mobile_patient_context(client, db, dentiste, patient, auth_headers)

    invalid = _upload(client, access, context_key, b'not-an-image', filename='fake.jpg')
    assert invalid.status_code == 422
    assert db.query(models.DocumentArchive).count() == 0

    oversized = _upload(client, access, context_key, b'x' * (12 * 1024 * 1024 + 1), filename='large.jpg')
    assert oversized.status_code == 413
    assert db.query(models.DocumentArchive).count() == 0


def test_mobile_clinical_photo_revalidates_permission_at_upload_time(client, db, dentiste, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.is_licensed = True
    dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.commit()
    _cabinet(db, dentiste)
    secretary = _user(
        db,
        email='m6a-secretary@cabinet.ma',
        role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id,
        permissions={'patients': True, 'agenda': True},
    )
    patient = _patient(db, dentiste)
    owner_headers = _auth(client, dentiste)
    access, context_key = _mobile_patient_context(client, db, dentiste, patient, owner_headers, target_user_id=secretary.id)

    secretary.permissions = {'patients': False, 'agenda': True}
    db.commit()
    denied = _upload(client, access, context_key, _jpeg_bytes())
    assert denied.status_code == 403
    assert db.query(models.DocumentArchive).count() == 0


def test_mobile_clinical_photo_rejects_deleted_patient_and_non_patient_context(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.is_licensed = True
    dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.commit()
    _cabinet(db, dentiste)
    patient = _patient(db, dentiste)
    access, context_key = _mobile_patient_context(client, db, dentiste, patient, auth_headers)

    patient.deleted_at = datetime.utcnow()
    db.commit()
    deleted = _upload(client, access, context_key, _jpeg_bytes())
    assert deleted.status_code == 404
    assert db.query(models.DocumentArchive).count() == 0

    patient.deleted_at = None
    db.commit()
    appointment = models.Appointment(
        patient_id=patient.id,
        patient_name='BENNANI Sara',
        datetime_start=datetime.utcnow() + timedelta(hours=1),
        duration_minutes=30,
        employer_id=dentiste.id,
    )
    db.add(appointment)
    db.commit()
    issued = client.post('/api/mobile/resource-bridge-pairing', json={
        'resource_type': 'appointment',
        'resource_id': appointment.id,
    }, headers=auth_headers)
    assert issued.status_code == 200, issued.text
    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    claimed = client.post('/api/mobile/claim-token', json={
        'token': pairing.token,
        'client_public_key_hex': _client_public_key(),
    })
    assert claimed.status_code == 200
    appointment_access = claimed.json()['access_token']
    destination = client.post('/api/mobile/resource-bridge-destination', json={'credential': pairing.token}, headers={'Authorization': f'Bearer {appointment_access}'})
    assert destination.status_code == 200
    wrong = _upload(client, appointment_access, destination.json()['context']['key'], _jpeg_bytes())
    assert wrong.status_code == 422
    assert db.query(models.DocumentArchive).count() == 0
'''.rstrip() + '\n', encoding='utf-8')

print('M6-A product patch materialized: backend context upload + frontend preview + tests')
