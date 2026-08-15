from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 1) CertificatePolicy: separate document issue date from work-stop start date.
path = ROOT / 'frontend/src/features/admin/DocumentStudio/CertificatePolicy.ts'
text = path.read_text(encoding='utf-8')
old = '''export function buildCertificatePayload(
  certifType: string,
  customContent: string,
  certifDays: number,
  startDate: string,
) {
  const normalized = normalizeCertificateSelection(certifType, customContent);
  return {
    reason: normalized.type,
    days: certificateRequiresDuration(normalized.type) ? Number(certifDays) : 0,
    start_date: startDate,
    ...(normalized.type === CERTIFICATE_TYPE_FREE
      ? { content: normalized.content.trim() }
      : {}),
  };
}'''
new = '''export function buildCertificatePayload(
  certifType: string,
  customContent: string,
  certifDays: number,
  docDate: string,
  startDate: string,
) {
  const normalized = normalizeCertificateSelection(certifType, customContent);
  const requiresDuration = certificateRequiresDuration(normalized.type);
  return {
    reason: normalized.type,
    days: requiresDuration ? Number(certifDays) : 0,
    doc_date: docDate,
    ...(requiresDuration ? { start_date: startDate || docDate } : {}),
    ...(normalized.type === CERTIFICATE_TYPE_FREE
      ? { content: normalized.content.trim() }
      : {}),
  };
}'''
assert old in text, 'CertificatePolicy build payload anchor missing'
path.write_text(text.replace(old, new, 1), encoding='utf-8')

# 2) Update policy tests for explicit issue/start dates.
path = ROOT / 'frontend/src/features/admin/DocumentStudio/CertificatePolicy.test.ts'
text = path.read_text(encoding='utf-8')
text = text.replace(
'''      5,
      '2026-08-15',
    );''',
'''      5,
      '2026-08-15',
      '2026-08-17',
    );''',
1,
)
text = text.replace(
'''      days: 0,
      start_date: '2026-08-15',
      content: 'Contrôle post-opératoire sans complication.',
''',
'''      days: 0,
      doc_date: '2026-08-15',
      content: 'Contrôle post-opératoire sans complication.',
''',
1,
)
insert = '''
  it('sépare la date d’émission du début du repos pour un arrêt de travail', () => {
    expect(buildCertificatePayload('Arrêt de travail', '', 3, '2026-08-15', '2026-08-17')).toEqual({
      reason: 'Arrêt de travail',
      days: 3,
      doc_date: '2026-08-15',
      start_date: '2026-08-17',
    });
  });

  it('fait suivre le début du repos sur la date d’émission tant qu’aucune date distincte n’est choisie', () => {
    expect(buildCertificatePayload('Arrêt de travail', '', 2, '2026-08-15', '')).toEqual({
      reason: 'Arrêt de travail',
      days: 2,
      doc_date: '2026-08-15',
      start_date: '2026-08-15',
    });
  });
'''
anchor = "\n  it('ne demande une durée que pour l’arrêt de travail', () => {"
assert anchor in text, 'CertificatePolicy test insertion anchor missing'
text = text.replace(anchor, insert + anchor, 1)
path.write_text(text, encoding='utf-8')

# 3) CertificateForm: explicit start-date control only for work stops.
path = ROOT / 'frontend/src/features/admin/DocumentStudio/Forms/CertificateForm.tsx'
text = path.read_text(encoding='utf-8')
old = '''  certifDays: number;
  setCertifDays: (days: number) => void;
  certifCustomMotif: string;'''
new = '''  certifDays: number;
  setCertifDays: (days: number) => void;
  docDate: string;
  certifStartDate: string;
  setCertifStartDate: (date: string) => void;
  certifCustomMotif: string;'''
assert old in text, 'CertificateForm props interface anchor missing'
text = text.replace(old, new, 1)
old = '''  certifDays,
  setCertifDays,
  certifCustomMotif,'''
new = '''  certifDays,
  setCertifDays,
  docDate,
  certifStartDate,
  setCertifStartDate,
  certifCustomMotif,'''
assert old in text, 'CertificateForm destructuring anchor missing'
text = text.replace(old, new, 1)
old = '''          {certificateRequiresDuration(certifType) && (
            <div className="pt-8 border-t border-slate-100/50">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <label htmlFor="certificate-rest-days" className={labelClass + " mb-1"}>Durée du repos</label>
                  <p className="text-[9px] font-bold text-slate-400 italic">À déterminer et valider par le praticien.</p>
                </div>
                <span className="text-3xl font-black text-primary tracking-tighter" style={{ color: 'var(--primary)' }}>
                  {certifDays} <span className="text-[10px] uppercase tracking-widest ml-1 opacity-40">jours</span>
                </span>
              </div>

              <input
                id="certificate-rest-days"
                type="range"
                min="1"
                max="30"
                step="1"
                value={certifDays}
                onChange={(e) => setCertifDays(parseInt(e.target.value))}
                className="w-full h-2.5 bg-slate-100 rounded-full appearance-none cursor-pointer accent-primary"
                style={{ accentColor: 'var(--primary)' }}
                aria-label="Durée du repos en jours"
              />
            </div>
          )}'''
new = '''          {certificateRequiresDuration(certifType) && (
            <div className="pt-8 border-t border-slate-100/50 space-y-6">
              <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_220px] sm:items-end">
                <div>
                  <label htmlFor="certificate-rest-days" className={labelClass + " mb-1"}>Durée du repos</label>
                  <p className="text-[9px] font-bold text-slate-400 italic">À déterminer et valider par le praticien.</p>
                </div>
                <div>
                  <label htmlFor="certificate-rest-start" className={labelClass + " mb-1"}>Début du repos</label>
                  <input
                    id="certificate-rest-start"
                    type="date"
                    value={certifStartDate || docDate}
                    onChange={(e) => setCertifStartDate(e.target.value)}
                    className="w-full rounded-xl border border-slate-100 bg-white/70 px-4 py-3 text-sm font-bold text-slate-700 shadow-sm outline-none transition-all focus:border-primary focus:ring-4 focus:ring-primary/5"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between gap-4">
                <input
                  id="certificate-rest-days"
                  type="range"
                  min="1"
                  max="30"
                  step="1"
                  value={certifDays}
                  onChange={(e) => setCertifDays(parseInt(e.target.value))}
                  className="min-w-0 flex-1 h-2.5 bg-slate-100 rounded-full appearance-none cursor-pointer accent-primary"
                  style={{ accentColor: 'var(--primary)' }}
                  aria-label="Durée du repos en jours"
                />
                <span className="shrink-0 text-3xl font-black text-primary tracking-tighter" style={{ color: 'var(--primary)' }}>
                  {certifDays} <span className="text-[10px] uppercase tracking-widest ml-1 opacity-40">jours</span>
                </span>
              </div>
            </div>
          )}'''
assert old in text, 'CertificateForm duration block anchor missing'
path.write_text(text.replace(old, new, 1), encoding='utf-8')

# 4) Form tests: provide new props and verify start date is work-stop-only.
path = ROOT / 'frontend/src/features/admin/DocumentStudio/Forms/CertificateForm.p3a.test.tsx'
text = path.read_text(encoding='utf-8')
text = text.replace(
'''        certifDays={1}
        setCertifDays={setCertifDays}
        certifCustomMotif=""''',
'''        certifDays={1}
        setCertifDays={setCertifDays}
        docDate="2026-08-15"
        certifStartDate=""
        setCertifStartDate={vi.fn()}
        certifCustomMotif=""''',
1,
)
text = text.replace(
'''        certifDays={2}
        setCertifDays={vi.fn()}
        certifCustomMotif=""''',
'''        certifDays={2}
        setCertifDays={vi.fn()}
        docDate="2026-08-15"
        certifStartDate=""
        setCertifStartDate={vi.fn()}
        certifCustomMotif=""''',
1,
)
text = text.replace(
'''        certifDays={2}
        setCertifDays={vi.fn()}
        certifCustomMotif="Texte rédigé par le praticien"''',
'''        certifDays={2}
        setCertifDays={vi.fn()}
        docDate="2026-08-15"
        certifStartDate=""
        setCertifStartDate={vi.fn()}
        certifCustomMotif="Texte rédigé par le praticien"''',
1,
)
insert = '''

  it('affiche un début du repos distinct uniquement pour un arrêt de travail', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: null } as never);
    render(
      <CertificateForm
        patientId=""
        certifType="Arrêt de travail"
        setCertifType={vi.fn()}
        certifDays={3}
        setCertifDays={vi.fn()}
        docDate="2026-08-15"
        certifStartDate="2026-08-17"
        setCertifStartDate={vi.fn()}
        certifCustomMotif=""
        setCertifCustomMotif={vi.fn()}
      />,
    );

    expect((screen.getByLabelText(/Début du repos/i) as HTMLInputElement).value).toBe('2026-08-17');
  });
'''
anchor = '\n});\n'
idx = text.rfind(anchor)
assert idx != -1, 'CertificateForm test closing anchor missing'
text = text[:idx] + insert + text[idx:]
path.write_text(text, encoding='utf-8')

# 5) DocumentHub: state, payload wiring, hydration and component props.
path = ROOT / 'frontend/src/features/admin/DocumentHub.tsx'
text = path.read_text(encoding='utf-8')
old = '''  const [certifType, setCertifType] = useState('Arrêt de travail');
  const [certifDays, setCertifDays] = useState(5);
  const [certifCustomMotif, setCertifCustomMotif] = useState('');'''
new = '''  const [certifType, setCertifType] = useState('Arrêt de travail');
  const [certifDays, setCertifDays] = useState(5);
  const [certifStartDate, setCertifStartDate] = useState('');
  const [certifCustomMotif, setCertifCustomMotif] = useState('');'''
assert old in text, 'DocumentHub certificate state anchor missing'
text = text.replace(old, new, 1)
old = '''    patientId, patientDetails, activeTab, drugs, certifType, certifDays, certifCustomMotif,
    items, paymentMode, libreTitle, libreContent, libreCustomPatient, libreCustomDate,'''
new = '''    patientId, patientDetails, activeTab, drugs, certifType, certifDays, certifStartDate, certifCustomMotif,
    items, paymentMode, libreTitle, libreContent, libreCustomPatient, libreCustomDate,'''
assert text.count(old) >= 2, 'DocumentHub generator param anchors missing'
text = text.replace(old, new, 2)
old = '''        setCertifType(d.reason || 'Arrêt de travail');
        setCertifDays(d.days ?? 0);
        setCertifCustomMotif(d.content || '');'''
new = '''        setCertifType(d.reason || 'Arrêt de travail');
        setCertifDays(d.days ?? 0);
        setCertifStartDate(d.start_date || '');
        setCertifCustomMotif(d.content || '');
        if (!d.doc_date && d.start_date) setDocDate(d.start_date);'''
assert old in text, 'DocumentHub certificate hydration anchor missing'
text = text.replace(old, new, 1)
old = '''              certifType={certifType} setCertifType={setCertifType}
              certifDays={certifDays} setCertifDays={setCertifDays}
              certifCustomMotif={certifCustomMotif} setCertifCustomMotif={setCertifCustomMotif}'''
new = '''              certifType={certifType} setCertifType={setCertifType}
              certifDays={certifDays} setCertifDays={setCertifDays}
              docDate={docDate}
              certifStartDate={certifStartDate} setCertifStartDate={setCertifStartDate}
              certifCustomMotif={certifCustomMotif} setCertifCustomMotif={setCertifCustomMotif}'''
assert old in text, 'DocumentHub CertificateForm props anchor missing'
text = text.replace(old, new, 1)
# Preview must refresh when start date changes.
old = '''    sideStudioType, drugs, items, certifType, certifDays, paymentMode, 
    libreTitle, libreContent, docDate, activeTab, '''
new = '''    sideStudioType, drugs, items, certifType, certifDays, certifStartDate, paymentMode, 
    libreTitle, libreContent, docDate, activeTab, '''
assert old in text, 'DocumentHub preview dependency anchor missing'
text = text.replace(old, new, 1)
# Generic archived clinical data contract.
old = '''  reason?: string;
  days?: number;
  title?: string;'''
new = '''  reason?: string;
  days?: number;
  start_date?: string;
  title?: string;'''
assert old in text, 'GenericClinicalData anchor missing'
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')

# 6) Generator hook: accept start date, validate it only for work stops, include both dates.
path = ROOT / 'frontend/src/features/admin/DocumentStudio/useDocumentGenerator.ts'
text = path.read_text(encoding='utf-8')
old = '''  certifType: string;
  certifDays: number;
  certifCustomMotif: string;'''
new = '''  certifType: string;
  certifDays: number;
  certifStartDate: string;
  certifCustomMotif: string;'''
assert old in text, 'Generator params certificate anchor missing'
text = text.replace(old, new, 1)
old = '''    if (certificateRequiresDuration(params.certifType)) {
      if (!Number.isInteger(certifDays) || certifDays < 1) {'''
new = '''    if (certificateRequiresDuration(params.certifType)) {
      const effectiveStartDate = params.certifStartDate || params.docDate;
      if (!effectiveStartDate || isNaN(new Date(effectiveStartDate).getTime())) {
        errors.push({ field: 'certifStartDate', message: 'La date de début du repos est invalide.' });
      }
      if (!Number.isInteger(certifDays) || certifDays < 1) {'''
assert old in text, 'Generator certificate validation anchor missing'
text = text.replace(old, new, 1)
old = '''      patientId, activeTab, drugs, certifType, certifDays, certifCustomMotif, items, paymentMode,'''
new = '''      patientId, activeTab, drugs, certifType, certifDays, certifStartDate, certifCustomMotif, items, paymentMode,'''
assert old in text, 'Generator buildPayload destructuring anchor missing'
text = text.replace(old, new, 1)
old = '''      payload.data = buildCertificatePayload(certifType, certifCustomMotif, certifDays, docDate);'''
new = '''      payload.data = buildCertificatePayload(certifType, certifCustomMotif, certifDays, docDate, certifStartDate);'''
assert old in text, 'Generator certificate payload call anchor missing'
text = text.replace(old, new, 1)
old = '''    params.patientId, params.activeTab, params.drugs, params.certifType, params.certifDays,
    params.certifCustomMotif, params.items, params.paymentMode, params.libreTitle,'''
new = '''    params.patientId, params.activeTab, params.drugs, params.certifType, params.certifDays,
    params.certifStartDate, params.certifCustomMotif, params.items, params.paymentMode, params.libreTitle,'''
assert old in text, 'Generator dependency anchor missing'
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')

# 7) Backend schema: persist issue date as well as rest start date.
path = ROOT / 'backend/schemas/documents.py'
text = path.read_text(encoding='utf-8')
old = '''    days: Optional[int] = 1
    start_date: Optional[datetime.date] = None
    content: Optional[str] = None'''
new = '''    days: Optional[int] = 1
    doc_date: Optional[datetime.date] = None
    start_date: Optional[datetime.date] = None
    content: Optional[str] = None'''
assert old in text, 'CertificatData date anchor missing'
path.write_text(text.replace(old, new, 1), encoding='utf-8')

# 8) Backend generator: resolve issue/start dates independently and use each for its role.
path = ROOT / 'backend/services/generators/certificat_gen.py'
text = path.read_text(encoding='utf-8')
anchor = '''def _format_free_certificate_content(content: str) -> str:
    cleaned = (content or '').strip()
    if not cleaned:
        raise ValueError('Le contenu du certificat médical est requis.')
    return '<br/>'.join(escape(line) for line in cleaned.splitlines())


class CertificatGenerator:'''
replacement = '''def _format_free_certificate_content(content: str) -> str:
    cleaned = (content or '').strip()
    if not cleaned:
        raise ValueError('Le contenu du certificat médical est requis.')
    return '<br/>'.join(escape(line) for line in cleaned.splitlines())


def _coerce_certificate_date(value, fallback: date) -> date:
    if not value:
        return fallback
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            return fallback
    return fallback


def _resolve_certificate_dates(data, today: date | None = None) -> tuple[date, date]:
    today = today or date.today()
    issue_date = _coerce_certificate_date(getattr(data, 'doc_date', None), today)
    rest_start_date = _coerce_certificate_date(getattr(data, 'start_date', None), issue_date)
    return issue_date, rest_start_date


class CertificatGenerator:'''
assert anchor in text, 'certificat_gen helper anchor missing'
text = text.replace(anchor, replacement, 1)
old = '''        doc_date = getattr(data, 'doc_date', None) or date.today()
        if isinstance(doc_date, str):
            try:
                doc_date = datetime.strptime(doc_date, '%Y-%m-%d').date()
            except Exception:
                doc_date = date.today()

        current_date = doc_date.strftime('%d/%m/%Y')'''
new = '''        doc_date, _ = _resolve_certificate_dates(data)
        current_date = doc_date.strftime('%d/%m/%Y')'''
assert old in text, 'certificate header date block missing'
text = text.replace(old, new, 1)
old = '''        from datetime import timedelta
        doc_date_obj = getattr(data, 'doc_date', None) or date.today()
        if isinstance(doc_date_obj, str):
            try:
                doc_date_obj = datetime.strptime(doc_date_obj, '%Y-%m-%d').date()
            except Exception:
                doc_date_obj = date.today()

        days_int = int(days or 0)'''
new = '''        from datetime import timedelta
        issue_date_obj, rest_start_date_obj = _resolve_certificate_dates(data)

        days_int = int(days or 0)'''
assert old in text, 'certificate body date block missing'
text = text.replace(old, new, 1)
text = text.replace("end_date = doc_date_obj + timedelta(days=days_int - 1)", "end_date = rest_start_date_obj + timedelta(days=days_int - 1)", 1)
text = text.replace("f\"du <b>{doc_date_obj.strftime('%d/%m/%Y')}</b> \"", "f\"du <b>{rest_start_date_obj.strftime('%d/%m/%Y')}</b> \"", 1)
text = text.replace("date_phrase = f\"le <b>{doc_date_obj.strftime('%d/%m/%Y')}</b>\"", "date_phrase = f\"le <b>{rest_start_date_obj.strftime('%d/%m/%Y')}</b>\"", 1)
text = text.replace("f\"le <b>{doc_date_obj.strftime('%d/%m/%Y')}</b> de façon effective, pour y recevoir des soins {spec}.<br/><br/>\"", "f\"le <b>{issue_date_obj.strftime('%d/%m/%Y')}</b> de façon effective, pour y recevoir des soins {spec}.<br/><br/>\"", 1)
path.write_text(text, encoding='utf-8')

# 9) Backend date tests.
path = ROOT / 'backend/tests/test_certificat_dates_p3.py'
path.write_text('''from datetime import date\nfrom types import SimpleNamespace\n\nfrom backend.schemas.documents import CertificatData\nfrom backend.services.generators.certificat_gen import _resolve_certificate_dates\n\n\ndef test_certificate_schema_keeps_issue_and_rest_start_dates_distinct():\n    data = CertificatData(\n        reason="Arrêt de travail",\n        days=3,\n        doc_date=date(2026, 8, 15),\n        start_date=date(2026, 8, 17),\n    )\n    assert data.doc_date == date(2026, 8, 15)\n    assert data.start_date == date(2026, 8, 17)\n\n\ndef test_generator_resolves_issue_and_rest_start_independently():\n    data = SimpleNamespace(doc_date="2026-08-15", start_date="2026-08-17")\n    issue_date, rest_start = _resolve_certificate_dates(data, today=date(2026, 1, 1))\n    assert issue_date == date(2026, 8, 15)\n    assert rest_start == date(2026, 8, 17)\n\n\ndef test_legacy_certificate_without_doc_date_falls_back_safely():\n    data = SimpleNamespace(doc_date=None, start_date="2026-08-17")\n    issue_date, rest_start = _resolve_certificate_dates(data, today=date(2026, 8, 15))\n    assert issue_date == date(2026, 8, 15)\n    assert rest_start == date(2026, 8, 17)\n\n\ndef test_new_certificate_without_explicit_start_uses_issue_date():\n    data = SimpleNamespace(doc_date="2026-08-15", start_date=None)\n    issue_date, rest_start = _resolve_certificate_dates(data, today=date(2026, 1, 1))\n    assert issue_date == date(2026, 8, 15)\n    assert rest_start == date(2026, 8, 15)\n''', encoding='utf-8')

# 10) Remove one-shot machinery from final branch diff.
for rel in ['scripts/p3_certificat_dates_once.py', '.github/workflows/p3-certificat-dates-once.yml']:
    target = ROOT / rel
    if target.exists():
        target.unlink()
