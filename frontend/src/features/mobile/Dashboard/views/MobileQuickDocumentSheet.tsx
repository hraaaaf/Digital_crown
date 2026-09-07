import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, ArrowLeft, CheckCircle2, ExternalLink, FileText, Loader2, Plus, Trash2, X } from 'lucide-react';
import { MobileStorage } from '../../../../services/zka/MobileStorage';
import { mobileFetch } from '../../../../services/zka/mobileFetch';
import { CryptoService } from '../../../../services/zka/CryptoService';

export type MobileQuickDocumentType = 'ordonnance' | 'certificat' | 'devis' | 'honoraires' | 'libre';

interface PatientIdentity {
  id: number;
  name: string;
  medicalAlert?: string | null;
}

interface DocumentLine {
  id: number;
  label: string;
  detail: string;
  amount: string;
}

interface DocumentCapabilities {
  can_create_prescription: boolean;
  can_create_certificate: boolean;
  can_create_devis: boolean;
  can_create_honoraires: boolean;
  can_create_free_document: boolean;
}

const ALL_CAPABILITIES: DocumentCapabilities = {
  can_create_prescription: true,
  can_create_certificate: true,
  can_create_devis: true,
  can_create_honoraires: true,
  can_create_free_document: true,
};

const TYPES: Array<{ value: MobileQuickDocumentType; label: string; hint: string; capability: keyof DocumentCapabilities }> = [
  { value: 'ordonnance', label: 'Ordonnance', hint: 'Médicament + posologie', capability: 'can_create_prescription' },
  { value: 'certificat', label: 'Certificat', hint: 'Présence, arrêt ou certificat médical', capability: 'can_create_certificate' },
  { value: 'devis', label: 'Devis', hint: 'Actes et montants', capability: 'can_create_devis' },
  { value: 'honoraires', label: 'Honoraires', hint: 'Note d’honoraires', capability: 'can_create_honoraires' },
  { value: 'libre', label: 'Document libre', hint: 'Courrier ou note clinique simple', capability: 'can_create_free_document' },
];

function resolveApiBaseUrl(stored: string): string {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return stored.replace(/\/$/, '');
  if (stored.includes('localhost') || stored.includes('127.0.0.1')) return `${window.location.protocol}//${hostname}:8005`;
  return stored.replace(/\/$/, '');
}

function resolvePdfUrl(baseUrl: string, value: string): string {
  const raw = value.trim();
  if (/^https?:\/\//i.test(raw)) return raw;
  if (raw.startsWith('/')) return `${baseUrl}${raw}`;
  if (raw.startsWith('api/')) return `${baseUrl}/${raw}`;
  return `${baseUrl}/api/${raw}`;
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

async function decryptCapabilities(response: Response, masterKey: string): Promise<DocumentCapabilities> {
  const raw = await response.json();
  const payload = raw?.payload ? CryptoService.decryptPayload(raw.payload, masterKey) : raw;
  return {
    can_create_prescription: payload?.can_create_prescription === true,
    can_create_certificate: payload?.can_create_certificate === true,
    can_create_devis: payload?.can_create_devis === true,
    can_create_honoraires: payload?.can_create_honoraires === true,
    can_create_free_document: payload?.can_create_free_document === true,
  };
}

export function MobileQuickDocumentSheet({ patient, preview = false, onClose }: { patient: PatientIdentity; preview?: boolean; onClose: () => void }) {
  const [capabilities, setCapabilities] = useState<DocumentCapabilities | null>(preview ? ALL_CAPABILITIES : null);
  const [type, setType] = useState<MobileQuickDocumentType | null>(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [certificateType, setCertificateType] = useState('Certificat de Présence');
  const [certificateDays, setCertificateDays] = useState('1');
  const [lines, setLines] = useState<DocumentLine[]>([{ id: 1, label: '', detail: '', amount: '' }]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [previewPayload, setPreviewPayload] = useState<Record<string, unknown> | null>(null);
  const [previewPdfUrl, setPreviewPdfUrl] = useState<string | null>(null);

  useEffect(() => {
    if (preview) return;
    let cancelled = false;
    const load = async () => {
      try {
        const creds = await MobileStorage.getCredentials();
        if (!creds) throw new Error('Session mobile indisponible.');
        const baseUrl = resolveApiBaseUrl(creds.api_base_url);
        const response = await mobileFetch(`${baseUrl}/api/mobile/quick-actions/capabilities`, {
          headers: { Authorization: `Bearer ${creds.access_token}` },
          signal: AbortSignal.timeout(5000),
        });
        if (!response.ok) throw new Error(`Permissions indisponibles (${response.status}).`);
        const next = await decryptCapabilities(response, creds.masterKey);
        if (!cancelled) setCapabilities(next);
      } catch (failure) {
        if (!cancelled) {
          setCapabilities({
            can_create_prescription: false,
            can_create_certificate: false,
            can_create_devis: false,
            can_create_honoraires: false,
            can_create_free_document: false,
          });
          setError(failure instanceof Error ? failure.message : 'Permissions documentaires indisponibles.');
        }
      }
    };
    void load();
    return () => { cancelled = true; };
  }, [preview]);

  const availableTypes = useMemo(
    () => capabilities ? TYPES.filter((entry) => capabilities[entry.capability]) : [],
    [capabilities],
  );
  const selected = useMemo(() => TYPES.find((entry) => entry.value === type), [type]);
  const updateLine = (id: number, patch: Partial<DocumentLine>) => setLines((current) => current.map((line) => line.id === id ? { ...line, ...patch } : line));
  const addLine = () => setLines((current) => [...current, { id: Date.now(), label: '', detail: '', amount: '' }]);
  const removeLine = (id: number) => setLines((current) => current.length > 1 ? current.filter((line) => line.id !== id) : current);

  const buildPayload = (): Record<string, unknown> => {
    const docDate = todayIso();
    if (type === 'ordonnance') {
      const medications = lines.filter((line) => line.label.trim()).map((line) => ({ nom: line.label.trim(), dosage: line.detail.trim(), forme: 'Comprimés', posologie: content.trim(), type: 'MEDICAMENT' }));
      if (!medications.length || !content.trim()) throw new Error('Ajoutez au moins un médicament et sa posologie.');
      return { type, patient_id: patient.id, data: { medications, doc_date: docDate, show_legal_annotations: true } };
    }
    if (type === 'certificat') {
      const days = Number.parseInt(certificateDays, 10);
      if (certificateType === 'Arrêt de travail' && (!Number.isInteger(days) || days < 1 || days > 365)) throw new Error('La durée doit être comprise entre 1 et 365 jours.');
      if (certificateType === 'Certificat médical' && !content.trim()) throw new Error('Le contenu du certificat médical est requis.');
      return { type, patient_id: patient.id, data: { reason: certificateType, days: certificateType === 'Arrêt de travail' ? days : 0, doc_date: docDate, ...(certificateType === 'Arrêt de travail' ? { start_date: docDate } : {}), ...(certificateType === 'Certificat médical' ? { content: content.trim() } : {}) } };
    }
    if (type === 'devis' || type === 'honoraires') {
      const entries = lines.filter((line) => line.label.trim()).map((line) => {
        const amount = Number.parseFloat(line.amount.replace(',', '.'));
        const invalid = !Number.isFinite(amount) || amount < 0 || (type === 'honoraires' && amount <= 0) || amount > 1_000_000;
        if (invalid) throw new Error(type === 'honoraires' ? `Le montant de « ${line.label || 'acte'} » doit être strictement positif et ≤ 1 000 000 MAD.` : `Le montant de « ${line.label || 'acte'} » doit être compris entre 0 et 1 000 000 MAD.`);
        return { acte: line.label.trim(), dent: line.detail.trim() || '0', dents: [], ...(type === 'devis' ? { prix_unitaire: amount } : { montant: amount, date: docDate }) };
      });
      if (!entries.length) throw new Error('Ajoutez au moins un acte.');
      return { type: type === 'honoraires' ? 'note' : 'devis', patient_id: patient.id, data: type === 'honoraires' ? { payments: entries, doc_date: docDate, teeth_data: [], installments: [], is_global_note: false } : { items: entries, doc_date: docDate, teeth_data: [], installments: [] }, is_accounted: true, payment_status: 'EN_ATTENTE' };
    }
    if (type === 'libre') {
      if (!title.trim() || !content.trim()) throw new Error('Le titre et le contenu sont requis.');
      return { type: 'libre', patient_id: patient.id, data: { title: title.trim(), content: content.trim(), doc_date: docDate, custom_patient: '', custom_date: '', hide_patient_header: false, page_size: 'A4', alignment: 'left' } };
    }
    throw new Error('Choisissez un type de document.');
  };

  const requestDocument = async (payload: Record<string, unknown>, archive: boolean) => {
    const creds = await MobileStorage.getCredentials();
    if (!creds) throw new Error('Session mobile indisponible.');
    const baseUrl = resolveApiBaseUrl(creds.api_base_url);
    const response = await mobileFetch(`${baseUrl}/api/documents/generate?archive=${archive ? 'true' : 'false'}&preview=${archive ? 'false' : 'true'}&force=false`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${creds.access_token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(20000),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = body?.detail;
      throw new Error((typeof detail === 'string' ? detail : detail?.message) || `Génération indisponible (${response.status}).`);
    }
    return { body, baseUrl };
  };

  const previewDocument = async () => {
    setError(''); setSuccess('');
    let payload: Record<string, unknown>;
    try { payload = buildPayload(); } catch (failure) { setError(failure instanceof Error ? failure.message : 'Document incomplet.'); return; }
    if (preview) {
      setPreviewPayload(payload);
      setPreviewPdfUrl(null);
      setSuccess('Aperçu isolé prêt. Aucun appel cabinet effectué.');
      return;
    }
    setBusy(true);
    try {
      const { body, baseUrl } = await requestDocument(payload, false);
      setPreviewPayload(payload);
      setPreviewPdfUrl(body?.pdf_url ? resolvePdfUrl(baseUrl, String(body.pdf_url)) : null);
      setSuccess('Aperçu validé. Vérifiez puis archivez.');
    } catch (failure) { setError(failure instanceof Error ? failure.message : 'Impossible de prévisualiser le document.'); } finally { setBusy(false); }
  };

  const archiveDocument = async () => {
    if (!previewPayload) return;
    setError(''); setSuccess('');
    if (preview) {
      setSuccess('Aperçu isolé : archivage simulé sans réseau.');
      return;
    }
    setBusy(true);
    try {
      const { body, baseUrl } = await requestDocument(previewPayload, true);
      setSuccess('Document généré et archivé dans le dossier patient.');
      if (body?.pdf_url) window.open(resolvePdfUrl(baseUrl, String(body.pdf_url)), '_blank', 'noopener,noreferrer');
    } catch (failure) { setError(failure instanceof Error ? failure.message : 'Impossible d’archiver le document.'); } finally { setBusy(false); }
  };

  return <div data-mobile-quick-document className="fixed inset-0 z-[80] bg-black/35 backdrop-blur-sm flex items-end sm:items-center justify-center">
    <section className="w-full max-w-2xl max-h-[92dvh] overflow-y-auto rounded-t-[30px] sm:rounded-[30px] border border-glass-border bg-card p-4 sm:p-5 shadow-2xl" style={{ backgroundColor: 'var(--glass-bg)' }}>
      <div className="sticky top-0 z-10 -mx-1 mb-4 flex items-center gap-3 rounded-[20px] bg-card/95 px-1 py-2 backdrop-blur" style={{ backgroundColor: 'var(--glass-bg)' }}>
        {type ? <button type="button" onClick={() => { setType(null); setPreviewPayload(null); setPreviewPdfUrl(null); setError(''); setSuccess(''); }} className="h-11 w-11 rounded-[14px] border border-glass-border flex items-center justify-center text-primary" aria-label="Retour aux types"><ArrowLeft size={18} /></button> : <div className="h-11 w-11 rounded-[14px] bg-primary/10 text-primary flex items-center justify-center"><FileText size={19} /></div>}
        <div className="min-w-0 flex-1"><p className="text-[10px] font-black uppercase tracking-[0.16em] text-text-muted">Quick Document Studio</p><h2 className="truncate text-lg font-black text-text-main">{selected?.label || patient.name}</h2></div>
        <button type="button" onClick={onClose} className="h-11 w-11 rounded-[14px] border border-glass-border flex items-center justify-center text-text-muted" aria-label="Fermer"><X size={18} /></button>
      </div>

      {!type ? <div className="space-y-2">
        {!capabilities && <div className="min-h-28 flex items-center justify-center"><Loader2 size={22} className="animate-spin text-primary" /></div>}
        {capabilities && availableTypes.length === 0 && <div className="rounded-[18px] border border-glass-border bg-background p-4 text-xs font-bold text-text-muted">Aucun type documentaire autorisé pour cette session.</div>}
        {availableTypes.map((entry) => <button key={entry.value} type="button" onClick={() => { setType(entry.value); setError(''); setSuccess(''); }} className="w-full min-h-16 rounded-[20px] border border-glass-border bg-background px-4 py-3 text-left active:scale-[0.99] transition-transform"><p className="text-sm font-black text-text-main">{entry.label}</p><p className="mt-1 text-[11px] font-bold text-text-muted">{entry.hint}</p></button>)}
        {error && <div className="rounded-[16px] border border-rose-500/20 bg-rose-500/5 p-3 text-xs font-bold text-rose-700">{error}</div>}
      </div> : previewPayload ? <div className="space-y-4">
        <div className="rounded-[20px] border border-primary/20 bg-primary/5 p-4"><p className="text-[10px] font-black uppercase tracking-[0.14em] text-primary">Aperçu prêt</p><p className="mt-1 text-base font-black text-text-main">{selected?.label} · {patient.name}</p><p className="mt-1 text-xs font-bold text-text-muted">Contenu verrouillé pour cette confirmation. Modifiez pour régénérer un aperçu.</p></div>
        {previewPdfUrl && <a href={previewPdfUrl} target="_blank" rel="noreferrer" className="w-full min-h-12 rounded-[16px] border border-glass-border bg-background text-primary flex items-center justify-center gap-2 text-xs font-black"><ExternalLink size={16} /> Ouvrir l’aperçu PDF</a>}
        {success && <div className="rounded-[16px] border border-emerald-500/20 bg-emerald-500/5 p-3 text-xs font-bold text-emerald-700 flex items-center gap-2"><CheckCircle2 size={16} /> {success}</div>}
        {error && <div className="rounded-[16px] border border-rose-500/20 bg-rose-500/5 p-3 text-xs font-bold text-rose-700">{error}</div>}
        <div className="grid grid-cols-2 gap-2"><button type="button" onClick={() => { setPreviewPayload(null); setPreviewPdfUrl(null); setSuccess(''); setError(''); }} className="min-h-14 rounded-[18px] border border-glass-border bg-background text-xs font-black text-text-main">Modifier</button><button type="button" onClick={() => void archiveDocument()} disabled={busy} className="min-h-14 rounded-[18px] bg-primary text-primary-foreground text-xs font-black flex items-center justify-center gap-2 disabled:opacity-50">{busy ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />} Archiver le document</button></div>
      </div> : <div className="space-y-4">
        {type === 'ordonnance' && patient.medicalAlert && <div className="rounded-[18px] border border-rose-500/20 bg-rose-500/5 p-3 flex items-start gap-2"><AlertTriangle size={16} className="mt-0.5 shrink-0 text-rose-600" /><div><p className="text-[10px] font-black uppercase tracking-[0.12em] text-rose-600">Alerte médicale</p><p className="mt-1 text-xs font-bold leading-relaxed text-text-main">{patient.medicalAlert}</p></div></div>}
        {type === 'certificat' && <><label className="block"><span className="text-[11px] font-black text-text-muted">Nature</span><select value={certificateType} onChange={(event) => setCertificateType(event.target.value)} className="mt-1 w-full min-h-12 rounded-[16px] border border-glass-border bg-background px-3 text-sm font-bold text-text-main"><option>Certificat de Présence</option><option>Arrêt de travail</option><option>Certificat médical</option></select></label>{certificateType === 'Arrêt de travail' && <label className="block"><span className="text-[11px] font-black text-text-muted">Durée (jours)</span><input inputMode="numeric" value={certificateDays} onChange={(event) => setCertificateDays(event.target.value)} className="mt-1 w-full min-h-12 rounded-[16px] border border-glass-border bg-background px-3 text-sm font-bold text-text-main" /></label>}</>}
        {type === 'libre' && <label className="block"><span className="text-[11px] font-black text-text-muted">Titre</span><input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Courrier d’orientation" className="mt-1 w-full min-h-12 rounded-[16px] border border-glass-border bg-background px-3 text-sm font-bold text-text-main" /></label>}
        {(type === 'ordonnance' || type === 'devis' || type === 'honoraires') && <div className="space-y-2"><div className="flex items-center justify-between"><span className="text-[11px] font-black text-text-muted">{type === 'ordonnance' ? 'Médicaments' : 'Actes'}</span><button type="button" onClick={addLine} className="min-h-10 px-3 rounded-[13px] bg-primary/10 text-primary text-[11px] font-black flex items-center gap-1.5"><Plus size={14} /> Ajouter</button></div>{lines.map((line) => <div key={line.id} className="rounded-[18px] border border-glass-border bg-background p-3 space-y-2"><input value={line.label} onChange={(event) => updateLine(line.id, { label: event.target.value })} placeholder={type === 'ordonnance' ? 'Médicament' : 'Acte'} className="w-full min-h-11 rounded-[13px] border border-glass-border bg-card px-3 text-sm font-bold text-text-main" /><div className="grid grid-cols-[1fr_auto] gap-2"><input value={line.detail} onChange={(event) => updateLine(line.id, { detail: event.target.value })} placeholder={type === 'ordonnance' ? 'Dosage' : 'Dent (optionnel)'} className="min-w-0 min-h-11 rounded-[13px] border border-glass-border bg-card px-3 text-sm font-bold text-text-main" />{(type === 'devis' || type === 'honoraires') && <input inputMode="decimal" value={line.amount} onChange={(event) => updateLine(line.id, { amount: event.target.value })} placeholder="MAD" className="w-24 min-h-11 rounded-[13px] border border-glass-border bg-card px-3 text-sm font-bold text-text-main" />}{lines.length > 1 && <button type="button" onClick={() => removeLine(line.id)} className="h-11 w-11 rounded-[13px] border border-rose-500/20 text-rose-600 flex items-center justify-center" aria-label="Supprimer la ligne"><Trash2 size={16} /></button>}</div></div>)}</div>}
        {(type === 'ordonnance' || type === 'libre' || (type === 'certificat' && certificateType === 'Certificat médical')) && <label className="block"><span className="text-[11px] font-black text-text-muted">{type === 'ordonnance' ? 'Posologie' : 'Contenu'}</span><textarea value={content} onChange={(event) => setContent(event.target.value)} rows={5} placeholder={type === 'ordonnance' ? 'Ex. 1 comprimé matin et soir pendant 5 jours' : 'Saisir le contenu du document'} className="mt-1 w-full rounded-[16px] border border-glass-border bg-background p-3 text-sm font-bold leading-relaxed text-text-main resize-none" /></label>}
        {error && <div className="rounded-[16px] border border-rose-500/20 bg-rose-500/5 p-3 text-xs font-bold text-rose-700">{error}</div>}{success && <div className="rounded-[16px] border border-emerald-500/20 bg-emerald-500/5 p-3 text-xs font-bold text-emerald-700 flex items-center gap-2"><CheckCircle2 size={16} /> {success}</div>}
        <button type="button" onClick={() => void previewDocument()} disabled={busy} className="w-full min-h-14 rounded-[18px] bg-primary text-primary-foreground text-sm font-black flex items-center justify-center gap-2 disabled:opacity-50">{busy ? <Loader2 size={17} className="animate-spin" /> : <FileText size={17} />} Prévisualiser</button>
        <p className="text-center text-[10px] font-bold leading-relaxed text-text-muted">Même moteur documentaire, mêmes permissions et même dossier patient que sur desktop.</p>
      </div>}
    </section>
  </div>;
}
