from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f'{label}: expected one match, got {text.count(old)}')
    return text.replace(old, new, 1)


backend_path = Path('backend/routers/mobile_resource_bridge.py')
backend = backend_path.read_text()

scan_helpers = r'''

_DOCUMENT_SCAN_MAX_PAGES = 8
_DOCUMENT_SCAN_MAX_PAGE_BYTES = 12 * 1024 * 1024
_DOCUMENT_SCAN_MAX_TOTAL_BYTES = 48 * 1024 * 1024
_DOCUMENT_SCAN_MAX_PIXELS = 50_000_000
_DOCUMENT_SCAN_SOURCE_FORMATS = {'JPEG', 'PNG', 'WEBP'}


def _normalize_document_scan_page(raw: bytes) -> bytes:
    """Validate and rewrite one scan page as a metadata-free JPEG."""
    if not raw:
        raise HTTPException(status_code=422, detail="La page scannée est vide.")
    if len(raw) > _DOCUMENT_SCAN_MAX_PAGE_BYTES:
        raise HTTPException(status_code=413, detail="Une page scannée dépasse la limite de 12 MiB.")

    try:
        with Image.open(BytesIO(raw)) as probe:
            source_format = str(probe.format or '').upper()
            width, height = probe.size
            if source_format not in _DOCUMENT_SCAN_SOURCE_FORMATS:
                raise HTTPException(status_code=422, detail="Format de page non pris en charge. Utilisez JPEG, PNG ou WebP.")
            if width <= 0 or height <= 0 or width * height > _DOCUMENT_SCAN_MAX_PIXELS:
                raise HTTPException(status_code=413, detail="La résolution d'une page scannée est trop élevée.")
            probe.verify()

        with Image.open(BytesIO(raw)) as image:
            image = ImageOps.exif_transpose(image)
            image.load()
            if image.width <= 0 or image.height <= 0 or image.width * image.height > _DOCUMENT_SCAN_MAX_PIXELS:
                raise HTTPException(status_code=413, detail="La résolution d'une page scannée est trop élevée.")
            if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
                rgba = image.convert('RGBA')
                normalized_image = Image.new('RGB', rgba.size, 'white')
                normalized_image.paste(rgba, mask=rgba.getchannel('A'))
            else:
                normalized_image = image.convert('RGB')
            output = BytesIO()
            normalized_image.save(output, format='JPEG', quality=90, optimize=True)
            normalized = output.getvalue()
            if not normalized:
                raise HTTPException(status_code=422, detail="Impossible de normaliser une page scannée.")
            return normalized
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise HTTPException(status_code=422, detail="Le fichier sélectionné n'est pas une page de document valide.") from exc


def _document_scan_pdf(normalized_pages: list[bytes]) -> bytes:
    if not normalized_pages:
        raise HTTPException(status_code=422, detail="Le scan ne contient aucune page.")
    images: list[Image.Image] = []
    try:
        for raw in normalized_pages:
            with Image.open(BytesIO(raw)) as image:
                images.append(image.convert('RGB').copy())
        output = BytesIO()
        images[0].save(
            output,
            format='PDF',
            save_all=True,
            append_images=images[1:],
            resolution=150.0,
        )
        pdf = output.getvalue()
        if not pdf.startswith(b'%PDF'):
            raise HTTPException(status_code=422, detail="Impossible de générer le PDF scanné.")
        return pdf
    finally:
        for image in images:
            image.close()
'''
backend = replace_once(
    backend,
    "\n\n@router.get('/resource-bridge-options', summary='Cibles autorisées pour un pont mobile de ressource')",
    scan_helpers + "\n\n@router.get('/resource-bridge-options', summary='Cibles autorisées pour un pont mobile de ressource')",
    'backend scan helpers',
)

scan_endpoint = r'''

@router.post('/resource-context-document-scan', summary='Archiver un scan multi-page depuis le contexte Patient mobile')
async def upload_resource_context_document_scan(
    context_key: str = Form(...),
    pages: list[UploadFile] = File(...),
    authorization: str = Header(...),
    db: Session = Depends(database.get_db),
):
    mobile_user, context = _validated_mobile_context(db, authorization, context_key)
    if str(context['resource_type']).lower() != 'patient':
        raise HTTPException(status_code=422, detail="Le scan de document exige un contexte Patient.")
    patient = _patient_resource(db, mobile_user, int(context['resource_id']))

    if not pages:
        raise HTTPException(status_code=422, detail="Ajoutez au moins une page au document.")
    if len(pages) > _DOCUMENT_SCAN_MAX_PAGES:
        raise HTTPException(status_code=413, detail="Un document scanné est limité à 8 pages.")

    normalized_pages: list[bytes] = []
    total_raw_bytes = 0
    for page in pages:
        claimed_type = str(page.content_type or '').strip().lower()
        if claimed_type and not claimed_type.startswith('image/'):
            await page.close()
            raise HTTPException(status_code=422, detail="Chaque page doit être une image JPEG, PNG ou WebP.")
        try:
            raw = await page.read(_DOCUMENT_SCAN_MAX_PAGE_BYTES + 1)
        finally:
            await page.close()
        total_raw_bytes += len(raw)
        if total_raw_bytes > _DOCUMENT_SCAN_MAX_TOTAL_BYTES:
            raise HTTPException(status_code=413, detail="Le scan dépasse la limite cumulée de 48 MiB.")
        normalized_pages.append(_normalize_document_scan_page(raw))

    pdf = _document_scan_pdf(normalized_pages)
    filename = f"document-scanne-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(4)}.pdf"
    archive_service = _documents.get_archive_service(db)
    document, _ = archive_service.archive_document(
        patient_id=patient.id,
        file_content=pdf,
        filename=filename,
        doc_type=models.DocumentType.AUTRE,
        uploaded_by_id=mobile_user.id,
        title='Document scanné',
        description=f'Scan mobile contextuel · {len(normalized_pages)} page(s)',
        tags=['mobile', 'document-scan'],
        is_accounted=False,
    )
    _documents.audit_service.log(
        db=db,
        user_id=mobile_user.id,
        employer_id=mobile_user.get_employer_id(),
        action='DOCUMENT_SCANNED',
        resource_type='AUTRE',
        resource_id=str(document.id),
        severity='INFO',
        details=f"Document mobile scanné document_id={document.id} pages={len(normalized_pages)}",
    )
    return {
        'success': True,
        'pages': len(normalized_pages),
        'document': {
            'id': document.id,
            'document_type': models.DocumentType.AUTRE.value,
            'title': document.title or 'Document scanné',
            'created_at': document.created_at.isoformat() if document.created_at else None,
        },
    }
'''
backend = replace_once(
    backend,
    "\n\n@router.post('/resource-context-media', summary='Charger le média protégé du contexte mobile')",
    scan_endpoint + "\n\n@router.post('/resource-context-media', summary='Charger le média protégé du contexte mobile')",
    'backend scan endpoint',
)
backend_path.write_text(backend)


test_path = Path('backend/tests/test_mobile_m6b_document_scan.py')
test_path.write_text(r'''from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

import fitz
import pytest
from PIL import Image

from backend import models
from backend.routers import mobile_resource_bridge
from backend.routers.mobile_resource_bridge import BRIDGE_CONTEXT_TABLE  # noqa: F401
from backend.services import archive_service
from backend.tests.test_mobile_m6a_clinical_photo import (
    _auth,
    _cabinet,
    _client_public_key,
    _jpeg_bytes,
    _mobile_patient_context,
    _patient,
    _user,
)


@pytest.fixture(autouse=True)
def _isolate_mobile_scan_runtime(tmp_path, monkeypatch):
    from backend.main import _license_cache
    from backend.utils import rate_limit

    _license_cache.clear()
    monkeypatch.setattr(rate_limit, '_store_path', str(tmp_path / 'm6b-rate-limit.json'))
    monkeypatch.setattr(archive_service, 'MEDIA_DIR', tmp_path)
    monkeypatch.setattr(archive_service, 'ARCHIVE_BASE_DIR', tmp_path / 'archives')
    monkeypatch.setattr(mobile_resource_bridge._documents, 'MEDIA_DIR', tmp_path)
    yield
    _license_cache.clear()


def _scan(client, access, context_key, pages):
    files = [
        ('pages', (filename, content, content_type))
        for filename, content, content_type in pages
    ]
    return client.post(
        '/api/mobile/resource-context-document-scan',
        data={'context_key': context_key},
        files=files,
        headers={'Authorization': f'Bearer {access}'},
    )


def _setup(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.is_licensed = True
    dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.commit()
    _cabinet(db, dentiste)
    patient = _patient(db, dentiste, dossier='M6B-001')
    access, context_key = _mobile_patient_context(client, db, dentiste, patient, auth_headers)
    return patient, access, context_key


def test_mobile_document_scan_archives_one_exact_patient_pdf(client, db, dentiste, auth_headers, monkeypatch):
    patient, access, context_key = _setup(client, db, dentiste, auth_headers, monkeypatch)
    response = _scan(client, access, context_key, [
        ('../../page-1.php.jpg', _jpeg_bytes(with_exif=True), 'image/jpeg'),
        ('page-2.jpg', _jpeg_bytes(), 'image/jpeg'),
    ])
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload['success'] is True
    assert payload['pages'] == 2
    assert payload['document']['document_type'] == 'AUTRE'
    assert 'patient_id' not in payload
    assert 'file_path' not in payload['document']

    documents = db.query(models.DocumentArchive).all()
    assert len(documents) == 1
    document = documents[0]
    assert document.patient_id == patient.id
    assert document.document_type == models.DocumentType.AUTRE
    assert document.uploaded_by_id == dentiste.id
    assert document.title == 'Document scanné'
    assert document.original_filename.startswith('document-scanne-')
    assert document.original_filename.endswith('.pdf')
    assert '..' not in document.original_filename
    assert 'page-1' not in document.original_filename

    relative = document.file_path.replace('static/archives/', '', 1)
    stored = Path(archive_service.ARCHIVE_BASE_DIR) / relative
    assert stored.is_file()
    assert archive_service.ARCHIVE_BASE_DIR.resolve() in stored.resolve().parents
    pdf = fitz.open(stream=stored.read_bytes(), filetype='pdf')
    try:
        assert pdf.page_count == 2
    finally:
        pdf.close()


def test_mobile_document_scan_rejects_bad_content_mime_and_limits(client, db, dentiste, auth_headers, monkeypatch):
    _patient_row, access, context_key = _setup(client, db, dentiste, auth_headers, monkeypatch)

    invalid = _scan(client, access, context_key, [('fake.jpg', b'not-an-image', 'image/jpeg')])
    assert invalid.status_code == 422
    assert db.query(models.DocumentArchive).count() == 0

    wrong_mime = _scan(client, access, context_key, [('page.pdf', _jpeg_bytes(), 'application/pdf')])
    assert wrong_mime.status_code == 422
    assert db.query(models.DocumentArchive).count() == 0

    too_many = _scan(client, access, context_key, [
        (f'page-{index}.jpg', _jpeg_bytes(), 'image/jpeg') for index in range(9)
    ])
    assert too_many.status_code == 413
    assert db.query(models.DocumentArchive).count() == 0

    page = _jpeg_bytes()
    monkeypatch.setattr(mobile_resource_bridge, '_DOCUMENT_SCAN_MAX_TOTAL_BYTES', len(page) + 8)
    aggregate = _scan(client, access, context_key, [
        ('one.jpg', page, 'image/jpeg'),
        ('two.jpg', page, 'image/jpeg'),
    ])
    assert aggregate.status_code == 413
    assert db.query(models.DocumentArchive).count() == 0

    monkeypatch.setattr(mobile_resource_bridge, '_DOCUMENT_SCAN_MAX_TOTAL_BYTES', 48 * 1024 * 1024)
    monkeypatch.setattr(mobile_resource_bridge, '_DOCUMENT_SCAN_MAX_PIXELS', 100)
    pixels = _scan(client, access, context_key, [('pixels.jpg', page, 'image/jpeg')])
    assert pixels.status_code == 413
    assert db.query(models.DocumentArchive).count() == 0


def test_mobile_document_scan_revalidates_permission_and_deleted_patient(client, db, dentiste, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.is_licensed = True
    dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.commit()
    _cabinet(db, dentiste)
    secretary = _user(
        db,
        email='m6b-secretary@cabinet.ma',
        role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id,
        permissions={'patients': True, 'agenda': True},
    )
    patient = _patient(db, dentiste, dossier='M6B-REVOKE')
    owner_headers = _auth(client, dentiste)
    access, context_key = _mobile_patient_context(client, db, dentiste, patient, owner_headers, target_user_id=secretary.id)

    secretary.permissions = {'patients': False, 'agenda': True}
    db.commit()
    denied = _scan(client, access, context_key, [('page.jpg', _jpeg_bytes(), 'image/jpeg')])
    assert denied.status_code == 403
    assert db.query(models.DocumentArchive).count() == 0

    secretary.permissions = {'patients': True, 'agenda': True}
    patient.deleted_at = datetime.utcnow()
    db.commit()
    deleted = _scan(client, access, context_key, [('page.jpg', _jpeg_bytes(), 'image/jpeg')])
    assert deleted.status_code == 404
    assert db.query(models.DocumentArchive).count() == 0


def test_mobile_document_scan_rejects_cross_tenant_and_non_patient_context(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.is_licensed = True
    dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.commit()
    _cabinet(db, dentiste)

    other_owner = _user(db, email='m6b-other@cabinet.ma')
    other_patient = _patient(db, other_owner, dossier='M6B-OTHER')
    cross = client.post('/api/mobile/resource-bridge-pairing', json={
        'resource_type': 'patient', 'resource_id': other_patient.id,
    }, headers=auth_headers)
    assert cross.status_code == 404

    patient = _patient(db, dentiste, dossier='M6B-LOCAL')
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
        'resource_type': 'appointment', 'resource_id': appointment.id,
    }, headers=auth_headers)
    assert issued.status_code == 200
    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    claimed = client.post('/api/mobile/claim-token', json={
        'token': pairing.token, 'client_public_key_hex': _client_public_key(),
    })
    assert claimed.status_code == 200
    appointment_access = claimed.json()['access_token']
    destination = client.post('/api/mobile/resource-bridge-destination', json={'credential': pairing.token}, headers={'Authorization': f'Bearer {appointment_access}'})
    assert destination.status_code == 200
    wrong = _scan(client, appointment_access, destination.json()['context']['key'], [('page.jpg', _jpeg_bytes(), 'image/jpeg')])
    assert wrong.status_code == 422
    assert db.query(models.DocumentArchive).count() == 0
''')


frontend_path = Path('frontend/src/features/mobile/Context/MobileContext.tsx')
frontend = frontend_path.read_text()
frontend = replace_once(
    frontend,
    "import { AlertTriangle, ArrowLeft, Calendar, Camera, CheckCircle2, Download, ExternalLink, FileText, Image as ImageIcon, Loader2, Phone, RefreshCcw, ShieldCheck, X } from 'lucide-react';",
    "import { AlertTriangle, ArrowLeft, Calendar, Camera, CheckCircle2, Download, ExternalLink, FileText, Image as ImageIcon, Loader2, Phone, Plus, RefreshCcw, ShieldCheck, Trash2, X } from 'lucide-react';",
    'frontend icons',
)
frontend = replace_once(
    frontend,
    "interface MobileAppointment {\n  patient_name: string;\n  datetime_start?: string | null;\n  duration_minutes: number;\n  motif: string;\n  status: string;\n  scheduling_type: string;\n  notes?: string | null;\n}\n",
    "interface MobileAppointment {\n  patient_name: string;\n  datetime_start?: string | null;\n  duration_minutes: number;\n  motif: string;\n  status: string;\n  scheduling_type: string;\n  notes?: string | null;\n}\n\ninterface DocumentScanPage {\n  key: string;\n  file: File;\n  previewUrl: string;\n}\n",
    'frontend scan page type',
)
frontend = replace_once(
    frontend,
    "  const [photoPhase, setPhotoPhase] = useState<'idle' | 'preview' | 'uploading' | 'saved'>('idle');\n  const [photoError, setPhotoError] = useState('');\n",
    "  const [photoPhase, setPhotoPhase] = useState<'idle' | 'preview' | 'uploading' | 'saved'>('idle');\n  const [photoError, setPhotoError] = useState('');\n  const scanInputRef = useRef<HTMLInputElement | null>(null);\n  const scanPagesRef = useRef<DocumentScanPage[]>([]);\n  const [scanPages, setScanPages] = useState<DocumentScanPage[]>([]);\n  const [scanActiveIndex, setScanActiveIndex] = useState(0);\n  const [scanPhase, setScanPhase] = useState<'idle' | 'preview' | 'uploading' | 'saved'>('idle');\n  const [scanError, setScanError] = useState('');\n",
    'frontend scan state',
)
scan_clear = r'''

  const setDocumentScanPages = (pages: DocumentScanPage[]) => {
    scanPagesRef.current = pages;
    setScanPages(pages);
  };

  const clearDocumentScan = () => {
    scanPagesRef.current.forEach(page => URL.revokeObjectURL(page.previewUrl));
    setDocumentScanPages([]);
    setScanActiveIndex(0);
    setScanPhase('idle');
    setScanError('');
    if (scanInputRef.current) scanInputRef.current.value = '';
  };
'''
frontend = replace_once(frontend, "\n\n  const load = async () => {", scan_clear + "\n\n  const load = async () => {", 'frontend scan clear')
frontend = replace_once(frontend, "    clearMedia();\n    clearClinicalPhoto();\n", "    clearMedia();\n    clearClinicalPhoto();\n    clearDocumentScan();\n", 'frontend load reset')
frontend = replace_once(
    frontend,
    "      if (mediaUrlRef.current) URL.revokeObjectURL(mediaUrlRef.current);\n      if (photoPreviewUrlRef.current) URL.revokeObjectURL(photoPreviewUrlRef.current);\n",
    "      if (mediaUrlRef.current) URL.revokeObjectURL(mediaUrlRef.current);\n      if (photoPreviewUrlRef.current) URL.revokeObjectURL(photoPreviewUrlRef.current);\n      scanPagesRef.current.forEach(page => URL.revokeObjectURL(page.previewUrl));\n",
    'frontend cleanup',
)
frontend = replace_once(
    frontend,
    "  const openClinicalPhotoPicker = () => {\n    setPhotoError('');\n    photoInputRef.current?.click();\n  };",
    "  const openClinicalPhotoPicker = () => {\n    clearDocumentScan();\n    setPhotoError('');\n    photoInputRef.current?.click();\n  };",
    'frontend photo/scan exclusivity',
)

scan_functions = r'''

  const startDocumentScan = () => {
    clearClinicalPhoto();
    clearDocumentScan();
    scanInputRef.current?.click();
  };

  const addDocumentScanPage = () => {
    setScanError('');
    if (scanPagesRef.current.length >= 8) {
      setScanError('Le document est limité à 8 pages.');
      return;
    }
    scanInputRef.current?.click();
  };

  const handleDocumentScanSelected = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] || null;
    if (!file) return;
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (file.type && !allowedTypes.includes(file.type)) {
      setScanError('Sélectionnez une page JPEG, PNG ou WebP.');
      event.target.value = '';
      return;
    }
    if (file.size > 12 * 1024 * 1024) {
      setScanError('Une page dépasse la limite de 12 MiB.');
      event.target.value = '';
      return;
    }
    if (scanPagesRef.current.reduce((total, page) => total + page.file.size, 0) + file.size > 48 * 1024 * 1024) {
      setScanError('Le scan dépasse la limite cumulée de 48 MiB.');
      event.target.value = '';
      return;
    }
    if (scanPagesRef.current.length >= 8) {
      setScanError('Le document est limité à 8 pages.');
      event.target.value = '';
      return;
    }
    const previewUrl = URL.createObjectURL(file);
    const next = [...scanPagesRef.current, {
      key: `${Date.now()}-${scanPagesRef.current.length}-${file.name}`,
      file,
      previewUrl,
    }];
    setDocumentScanPages(next);
    setScanActiveIndex(next.length - 1);
    setScanPhase('preview');
    setScanError('');
    event.target.value = '';
  };

  const removeDocumentScanPage = (index: number) => {
    const current = scanPagesRef.current;
    const removed = current[index];
    if (removed) URL.revokeObjectURL(removed.previewUrl);
    const next = current.filter((_page, pageIndex) => pageIndex !== index);
    setDocumentScanPages(next);
    if (!next.length) {
      setScanActiveIndex(0);
      setScanPhase('idle');
      setScanError('');
      return;
    }
    setScanActiveIndex(Math.min(index, next.length - 1));
    setScanPhase('preview');
    setScanError('');
  };

  const uploadDocumentScan = async () => {
    if (!scanPagesRef.current.length || !context || context.type !== 'patient') return;
    setScanPhase('uploading');
    setScanError('');
    try {
      let creds = await MobileStorage.getCredentials();
      if (!creds?.access_token) throw new Error('Session mobile non disponible. Régénérez le pont depuis le poste cabinet.');
      const request = async (accessToken: string) => {
        const form = new FormData();
        form.append('context_key', context.key);
        scanPagesRef.current.forEach((page, index) => form.append('pages', page.file, page.file.name || `scan-page-${index + 1}.jpg`));
        return fetch(`${creds!.api_base_url.replace(/\/$/, '')}/api/mobile/resource-context-document-scan`, {
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
        throw new Error(payload.detail || `Document non enregistré (${response.status}).`);
      }
      const payload = await response.json();
      if (!payload?.success || payload?.document?.document_type !== 'AUTRE' || payload?.pages !== scanPagesRef.current.length) {
        throw new Error('Réponse d’enregistrement du document invalide.');
      }
      setScanPhase('saved');
    } catch (err: unknown) {
      setScanError(err instanceof TypeError
        ? 'Serveur du cabinet inaccessible. Les pages restent en aperçu : vérifiez le poste cabinet puis réessayez.'
        : err instanceof Error
          ? err.message
          : 'Impossible d’enregistrer le document scanné.');
      setScanPhase('preview');
    }
  };
'''
frontend = replace_once(frontend, "\n\n  if (phase === 'loading') {", scan_functions + "\n\n  if (phase === 'loading') {", 'frontend scan functions')

scan_action = r'''
        <input ref={scanInputRef} data-m6b-scan-input type="file" accept="image/jpeg,image/png,image/webp" capture="environment" onChange={handleDocumentScanSelected} className="sr-only" tabIndex={-1} aria-hidden="true" />
        <button data-m6b-scan-action data-m6b-touch type="button" onClick={startDocumentScan} className="mt-3 w-full min-h-[66px] rounded-2xl bg-card-bg border border-primary/25 text-text-main inline-flex items-center justify-start gap-3 px-4 text-left shadow-elite active:scale-[0.99] transition-transform focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary"><FileText size={20} /></span>
          <span><span className="block font-black text-sm">Scanner un document</span><span className="mt-0.5 block text-[11px] font-bold text-text-muted">Créer un PDF dans le dossier</span></span>
          <span aria-hidden="true" className="ml-auto text-xl font-black text-text-muted/70">›</span>
        </button>
'''
frontend = replace_once(
    frontend,
    "        <section className=\"mt-6 rounded-[1.75rem] bg-card-bg border border-border-main p-5 shadow-elite space-y-4\"><div><p className=\"text-[10px] font-black uppercase tracking-widest text-text-muted\">Assurance</p>",
    scan_action + "        <section className=\"mt-6 rounded-[1.75rem] bg-card-bg border border-border-main p-5 shadow-elite space-y-4\"><div><p className=\"text-[10px] font-black uppercase tracking-widest text-text-muted\">Assurance</p>",
    'frontend scan action',
)

scan_sheet = r'''
      {scanPages.length > 0 && (
        <div data-m6b-scan-sheet className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/30 backdrop-blur-sm sm:p-4">
          <section role="dialog" aria-modal="true" aria-labelledby="m6b-scan-title" className="w-full max-w-md rounded-t-[2rem] sm:rounded-[2rem] bg-card-bg border border-border-main shadow-elite p-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] relative">
            <div className="mx-auto mb-4 h-1.5 w-12 rounded-full bg-text-muted/20 sm:hidden" />
            <button data-m6b-touch type="button" aria-label="Annuler le scan" onClick={clearDocumentScan} className="absolute right-4 top-4 min-h-[52px] min-w-[52px] rounded-2xl inline-flex items-center justify-center text-text-muted hover:bg-primary/5"><X size={20} /></button>
            <p className="text-[10px] font-black uppercase tracking-[0.16em] text-primary">Scan document</p>
            <h2 id="m6b-scan-title" className="mt-1 pr-14 text-xl font-black text-text-main">{scanPhase === 'saved' ? 'Document enregistré' : `${scanPages.length} page${scanPages.length > 1 ? 's' : ''} prête${scanPages.length > 1 ? 's' : ''}`}</h2>
            <p className="mt-1 text-xs font-bold text-text-muted">{displayName} · Dossier {patient!.numero_dossier || 'sans numéro'}</p>

            {scanPhase === 'saved' ? (
              <div data-m6b-scan-success className="mt-5">
                <div className="min-h-[72px] rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 flex items-center gap-3 text-emerald-800"><CheckCircle2 size={22} className="shrink-0" /><div><p className="text-sm font-black">Document scanné enregistré</p><p className="mt-0.5 text-xs font-bold">{scanPages.length} page{scanPages.length > 1 ? 's' : ''} · PDF dans le dossier</p></div></div>
                <button data-m6b-touch type="button" onClick={startDocumentScan} className="mt-4 w-full min-h-[54px] rounded-2xl bg-primary text-white inline-flex items-center justify-center gap-2 font-black text-sm"><FileText size={18} /> Scanner un autre document</button>
              </div>
            ) : (
              <>
                {scanPages[scanActiveIndex] && <img data-m6b-scan-preview src={scanPages[scanActiveIndex].previewUrl} alt={`Page ${scanActiveIndex + 1} du document de ${displayName}`} className="mt-4 block w-full max-h-[36dvh] aspect-[4/3] object-contain rounded-2xl border border-border-main bg-slate-950/5" />}
                <div className="mt-3 flex items-center justify-between gap-3"><p className="text-xs font-black text-text-main">Page {scanActiveIndex + 1} sur {scanPages.length}</p><p className="text-[10px] font-bold text-text-muted">8 pages max.</p></div>
                <div data-m6b-scan-thumbnails className="mt-3 flex gap-2 overflow-x-auto pb-1">
                  {scanPages.map((page, index) => <button data-m6b-touch data-m6b-scan-thumbnail key={page.key} type="button" onClick={() => setScanActiveIndex(index)} aria-label={`Voir la page ${index + 1}`} className={`min-w-[56px] min-h-[56px] w-14 h-14 overflow-hidden rounded-xl border-2 ${scanActiveIndex === index ? 'border-primary' : 'border-border-main'}`}><img src={page.previewUrl} alt="" className="w-full h-full object-cover" /></button>)}
                  {scanPages.length < 8 && <button data-m6b-touch data-m6b-add-page type="button" onClick={addDocumentScanPage} className="min-w-[56px] min-h-[56px] w-14 h-14 rounded-xl border border-primary/30 bg-primary/5 text-primary inline-flex items-center justify-center" aria-label="Ajouter une page"><Plus size={20} /></button>}
                </div>
                <button data-m6b-touch type="button" disabled={scanPhase === 'uploading'} onClick={() => removeDocumentScanPage(scanActiveIndex)} className="mt-3 min-h-[52px] w-full rounded-2xl border border-rose-200 bg-rose-50 text-rose-700 inline-flex items-center justify-center gap-2 font-black text-xs disabled:opacity-50"><Trash2 size={16} /> Supprimer cette page</button>
                {scanError && <div role="alert" className="mt-3 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-xs font-bold text-rose-700">{scanError}</div>}
                <button data-m6b-touch type="button" disabled={scanPhase === 'uploading'} onClick={() => void uploadDocumentScan()} className="mt-4 w-full min-h-[56px] rounded-2xl bg-primary text-white inline-flex items-center justify-center gap-2 font-black text-sm disabled:opacity-60">{scanPhase === 'uploading' ? <><Loader2 size={17} className="animate-spin" /> Enregistrement…</> : `Enregistrer le PDF · ${scanPages.length} page${scanPages.length > 1 ? 's' : ''}`}</button>
                <p className="mt-3 text-center text-[10px] font-bold text-text-muted">Aucune page n’est archivée avant confirmation.</p>
              </>
            )}
          </section>
        </div>
      )}

'''
frontend = replace_once(frontend, "      {photoPreviewUrl && photoFile && (", scan_sheet + "      {photoPreviewUrl && photoFile && (", 'frontend scan sheet')
frontend_path.write_text(frontend)

print('M6-B product patch materialized')
