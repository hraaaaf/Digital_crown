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

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

async function decryptMobileResponse<T>(response: Response, masterKey: string): Promise<T> {
  const raw = await response.json();
  return raw?.payload ? CryptoService.decryptPayload(raw.payload, masterKey) : raw;
}

async function decryptCapabilities(response: Response, masterKey: string): Promise<DocumentCapabilities> {
  const payload = await decryptMobileResponse<any>(response, masterKey);
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
  const [medicalAlert, setMedicalAlert] = useState<string | null>(patient.medicalAlert ?? null);
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
  const [archived, setArchived] = useState(false);
  const [uncertainArchive, setUncertainArchive] = useState(false);
  const [pendingArchiveKey, setPendingArchiveKey] = useState<string | null>(null);

  useEffect(() => {
    if (preview) return;
    let active = true;
    void MobileStorage.getPendingDocumentArchive().then((pending) => {
      if (!active || !pending || pending.patientId !== patient.id) return;
      setPendingArchiveKey(pending.intentKey);
      setType(pending.documentType);
      setUncertainArchive(true);
      setError('Archivage à vérifier : ne renvoyez pas le document avant confirmation du reçu.');
    }).catch(() => {
      if (active) setError('Impossible de vérifier un archivage local en attente.');
    });
    return () => { active = false; };
  }, [patient.id, preview]);
  useEffect(() => () => {
    if (previewPdfUrl?.startsWith('blob:') && typeof URL.revokeObjectURL === 'function') URL.revokeObjectURL(previewPdfUrl);
  }, [previewPdfUrl]);

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

  useEffect(() => {
    if (preview || patient.medicalAlert) return;
    let cancelled = false;
    const loadAlert = async () => {
      try {
        const creds = await MobileStorage.getCredentials();
        if (!creds) return;
        const baseUrl = resolveApiBaseUrl(creds.api_base_url);
        const response = await mobileFetch(`${baseUrl}/api/mobile/patient-cockpit/${patient.id}`, {
          headers: { Authorization: `Bearer ${creds.access_token}` },
          signal: AbortSignal.timeout(5000),
        });
        if (!response.ok) return;
        const payload = await decryptMobileResponse<any>(response, creds.masterKey);
        const p = payload?.patient;
        if (!cancelled && p?.has_medical_alert) {
          setMedicalAlert(String(p.medical_alert_summary || 'Antécédents médicaux renseignés dans le dossier.'));
        }
      } catch {
        // Non bloquant: le cockpit patient reste la source visible précédente.
      }
    };
    void loadAlert();
    return () => { cancelled = true; };
  }, [patient.id, patient.medicalAlert, preview]);

  const availableTypes = useMemo(() => capabilities ? TYPES.filter((entry) => capabilities[entry.capability]) : [], [capabilities]);
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

  const requestDocument = async (payload: Record<string, unknown>, archive: boolean, intentKey?: string) => {
    const creds = await MobileStorage.getCredentials();
    if (!creds) throw new Error('Session mobile indisponible.');
    const baseUrl = resolveApiBaseUrl(creds.api_base_url);
    const response = await mobileFetch(`${baseUrl}/api/mobile/documents/${archive ? 'archive' : 'preview'}`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${creds.access_token}`,
        'Content-Type': 'application/json',
        ...(archive && intentKey ? { 'Idempotency-Key': intentKey } : {}),
      },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(20000),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const detail = body?.detail;
      throw new Error((typeof detail === 'string' ? detail : detail?.message) || `Génération indisponible (${response.status}).`);
    }
    if (!(response.headers.get('content-type') || '').includes('application/pdf')) {
      throw new Error('Réponse PDF invalide.');
    }
    if (archive && !response.headers.get('x-document-id')) throw new Error('Confirmation serveur manquante.');
    const pdf = await response.blob();
    if (!pdf.size) throw new Error('PDF vide.');
    return URL.createObjectURL(pdf);
  };

  const reconcileArchive = async () => {
    setError(''); setSuccess('');
    setBusy(true);
    try {
      const pending = await MobileStorage.getPendingDocumentArchive();
      if (!pending || pending.patientId !== patient.id || pending.intentKey !== pendingArchiveKey) {
        throw new Error('Reçu local introuvable ou lié à un autre patient.');
      }
      const creds = await MobileStorage.getCredentials();
      if (!creds) throw new Error('Session Pocket indisponible.');
      const baseUrl = resolveApiBaseUrl(creds.api_base_url);
      // Recovery is GET-only. Never repeat the clinical archive POST.
      const response = await mobileFetch(`${baseUrl}/api/mobile/documents/archive/receipt/${pending.intentKey}`, {
        method: 'GET',
        headers: { Authorization: `Bearer ${creds.access_token}` },
        signal: AbortSignal.timeout(10000),
      });
      if (response.status === 202) {
        setError('Archivage encore en cours. Vérifiez à nouveau sans réenvoyer le document.');
        return;
      }
      if (response.status === 409) {
        setError('Résultat à vérifier au cabinet : aucune nouvelle écriture ne sera envoyée.');
        return;
      }
      if (!response.ok) {
        throw new Error(`Reçu indisponible (${response.status}). Conservez cette opération pour vérification.`);
      }
      if (!(response.headers.get('content-type') || '').includes('application/pdf')
        || !response.headers.get('x-document-id')) {
        throw new Error('Reçu PDF non authentifié par le serveur.');
      }
      const blob = await response.blob();
      if (!blob.size) throw new Error('Reçu PDF vide.');
      setPreviewPdfUrl(URL.createObjectURL(blob));
      setType(pending.documentType);
      setPreviewPayload({});
      setArchived(true);
      setUncertainArchive(false);
      setPendingArchiveKey(null);
      setSuccess('Archive retrouvée et confirmée par le registre du cabinet.');
      await MobileStorage.clearPendingDocumentArchive(pending.intentKey);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Reçu indisponible. Vérifiez au cabinet.');
    } finally {
      setBusy(false);
    }
  };

  const previewDocument = async () => {
    if (uncertainArchive) {
      setError('Une archive doit être vérifiée avant toute nouvelle préparation.');
      return;
    }
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
      const url = await requestDocument(payload, false);
      setPreviewPayload(payload);
      setArchived(false);
      setPreviewPdfUrl(url);
      setSuccess('Aperçu validé. Vérifiez puis archivez.');
    } catch (failure) { setError(failure instanceof Error ? failure.message : 'Impossible de prévisualiser le document.'); } finally { setBusy(false); }
  };

  const archiveDocument = async () => {
    if (!previewPayload || archived || busy || uncertainArchive) return;
    setError(''); setSuccess('');
    if (preview) {
      setSuccess('Aperçu isolé : archivage simulé sans réseau.');
      return;
    }
    if (type === 'honoraires') {
      setError('Archivage des notes d’honoraires indisponible sur Pocket : validation comptable requise.');
      return;
    }
    if (!type) return;
    setBusy(true);
    let archiveAttempted = false;
    try {
      const existing = await MobileStorage.getPendingDocumentArchive();
      if (existing) {
        throw new Error('Une archive précédente doit être vérifiée avant une nouvelle écriture.');
      }
      const intentKey = crypto.randomUUID();
      // Persist the opaque key BEFORE any network write. This is not an offline replay queue.
      await MobileStorage.savePendingDocumentArchive(intentKey, patient.id, type);
      setPendingArchiveKey(intentKey);
      archiveAttempted = true;
      const url = await requestDocument(previewPayload, true, intentKey);
      setPreviewPdfUrl(url);
      setArchived(true);
      setSuccess('Document archivé et reçu confirmé.');
      await MobileStorage.clearPendingDocumentArchive(intentKey);
      setPendingArchiveKey(null);
    } catch (failure) {
      if (archiveAttempted) {
        setUncertainArchive(true);
        setError('Résultat incertain : vérifiez le reçu, ne renvoyez pas le document.');
      } else {
        setError(failure instanceof Error ? failure.message : 'Impossible de préparer un archivage sûr.');
      }
    } finally { setBusy(false); }
  };

  return <div data-mobile-quick-document className="fixed inset-0 z-[80] bg-modal-scrim backdrop-blur-sm flex items-end sm:items-center justify-center">
    <section className="w-full max-w-2xl max-h-[92dvh] overflow-y-auto rounded-t-[30px] sm:rounded-[30px] border border-glass-border bg-card p-4 sm:p-5 shadow-2xl" style={{ backgroundColor: 'var(--glass-bg)' }}>
      <div className="sticky top-0 z-10 -mx-1 mb-4 flex flex-wrap items-center gap-3 rounded-[20px] bg-card/95 px-1 py-2 backdrop-blur sm:flex-nowrap" style={{ backgroundColor: 'var(--glass-bg)' }}>
        {type ? <button type="button" onClick={() => { if (uncertainArchive) return; setType(null); setPreviewPayload(null); setPreviewPdfUrl(null); setArchived(false); setError(''); setSuccess(''); }} disabled={uncertainArchive} className="h-11 w-11 rounded-[14px] border border-glass-border flex items-center justify-center text-primary" aria-label="Retour aux types"><ArrowLeft size={18} /></button> : <div className="h-11 w-11 rounded-[14px] bg-primary/10 text-primary flex items-center justify-center"><FileText size={19} /></div>}
        <div className="order-3 w-full min-w-0 sm:order-none sm:w-auto sm:flex-1"><p className="text-[10px] font-black uppercase tracking-[0.16em] text-text-muted">Document rapide</p><h2 className="break-words text-lg font-black leading-snug text-text-main">{selected?.label || patient.name}</h2></div>
        <button type="button" onClick={onClose} className="ml-auto h-11 w-11 shrink-0 rounded-[14px] border border-glass-border flex items-center justify-center text-text-muted sm:ml-0" aria-label="Fermer"><X size={18} /></button>
      </div>

      {uncertainArchive && <div role="status" className="mb-4 rounded-[16px] border border-danger-border bg-danger-surface p-3 text-xs text-danger">
        <p className="font-black">Archivage non confirmé</p>
        <p className="mt-1">Ne relancez pas la création : une réponse perdue peut cacher un document déjà archivé.</p>
        <button type="button" disabled={busy || !pendingArchiveKey} onClick={() => void reconcileArchive()}
          className="mt-3 min-h-11 rounded-[12px] border border-glass-border bg-background px-4 font-black text-text-main disabled:opacity-50">
          {busy ? 'Vérification…' : 'Vérifier le reçu'}
        </button>
      </div>}
      {!type ? <div className="space-y-2">
        {!capabilities && <div className="min-h-28 flex items-center justify-center"><Loader2 size={22} className="animate-spin text-primary" /></div>}
        {capabilities && availableTypes.length === 0 && <div className="rounded-[18px] border border-glass-border bg-background p-4 text-xs font-bold text-text-muted">Aucun type documentaire autorisé pour cette session.</div>}
        {availableTypes.map((entry) => <button key={entry.value} type="button" onClick={() => { setType(entry.value); setError(''); setSuccess(''); }} className="w-full min-h-16 rounded-[20px] border border-glass-border bg-background px-4 py-3 text-left active:scale-[0.99] transition-transform"><p className="text-sm font-black text-text-main">{entry.label}</p><p className="mt-1 text-[11px] font-bold text-text-muted">{entry.hint}</p></button>)}
        {error && <div className="rounded-[16px] border border-danger-border bg-danger-surface p-3 text-xs font-bold text-danger">{error}</div>}
      </div> : previewPayload ? <div className="space-y-4">
        <div className="rounded-[20px] border border-primary/20 bg-primary/5 p-4"><p className="text-[10px] font-black uppercase tracking-[0.14em] text-primary">{archived ? 'Archive confirmée' : 'Aperçu prêt'}</p><p className="mt-1 text-base font-black text-text-main">{selected?.label} · {patient.name}</p><p className="mt-1 text-xs font-bold text-text-muted">Contenu verrouillé pour cette confirmation. Modifiez pour régénérer un aperçu.</p></div>
        {previewPdfUrl && <a href={previewPdfUrl} target="_blank" rel="noreferrer" className="w-full min-h-12 rounded-[16px] border border-glass-border bg-background text-primary flex items-center justify-center gap-2 text-xs font-black"><ExternalLink size={16} /> {archived ? 'Ouvrir le PDF archivé' : 'Ouvrir l’aperçu PDF'}</a>}
        {success && <div className="rounded-[16px] border border-success-border bg-success-surface p-3 text-xs font-bold text-success flex items-center gap-2"><CheckCircle2 size={16} /> {success}</div>}
        {error && <div className="rounded-[16px] border border-danger-border bg-danger-surface p-3 text-xs font-bold text-danger">{error}</div>}
        {type === 'honoraires' && !preview && <p className="text-xs text-text-muted">Archivage des honoraires non disponible sur Pocket avant certification du contrat comptable.</p>}
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2"><button type="button" onClick={() => { if (uncertainArchive) return; setPreviewPayload(null); setPreviewPdfUrl(null); setArchived(false); setSuccess(''); setError(''); }} disabled={uncertainArchive} className="min-h-14 rounded-[18px] border border-glass-border bg-background text-xs font-black text-text-main">Modifier</button><button type="button" onClick={() => void archiveDocument()} disabled={busy || archived || uncertainArchive || (type === 'honoraires' && !preview)} className="min-h-14 rounded-[18px] bg-primary text-on-primary text-xs font-black flex items-center justify-center gap-2 disabled:opacity-50">{busy ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />} {archived ? 'Déjà archivé' : type === 'honoraires' && !preview ? 'Archivage indisponible' : 'Archiver le document'}</button></div>
      </div> : <div className="space-y-4">
        {type === 'ordonnance' && medicalAlert && <div className="rounded-[18px] border border-danger-border bg-danger-surface p-3 flex items-start gap-2"><AlertTriangle size={16} className="mt-0.5 shrink-0 text-danger" /><div><p className="text-[10px] font-black uppercase tracking-[0.12em] text-danger">Alerte médicale</p><p className="mt-1 text-xs font-bold leading-relaxed text-text-main">{medicalAlert}</p></div></div>}
        {type === 'certificat' && <><label className="block"><span className="text-[11px] font-black text-text-muted">Nature</span><select value={certificateType} onChange={(event) => setCertificateType(event.target.value)} className="mt-1 w-full min-h-12 rounded-[16px] border border-glass-border bg-background px-3 text-sm font-bold text-text-main"><option>Certificat de Présence</option><option>Arrêt de travail</option><option>Certificat médical</option></select></label>{certificateType === 'Arrêt de travail' && <label className="block"><span className="text-[11px] font-black text-text-muted">Durée (jours)</span><input inputMode="numeric" value={certificateDays} onChange={(event) => setCertificateDays(event.target.value)} className="mt-1 w-full min-h-12 rounded-[16px] border border-glass-border bg-background px-3 text-sm font-bold text-text-main" /></label>}</>}
        {type === 'libre' && <label className="block"><span className="text-[11px] font-black text-text-muted">Titre</span><input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Courrier d’orientation" className="mt-1 w-full min-h-12 rounded-[16px] border border-glass-border bg-background px-3 text-sm font-bold text-text-main" /></label>}
        {(type === 'ordonnance' || type === 'devis' || type === 'honoraires') && <div className="space-y-2"><div className="flex items-center justify-between"><span className="text-[11px] font-black text-text-muted">{type === 'ordonnance' ? 'Médicaments' : 'Actes'}</span><button type="button" onClick={addLine} className="min-h-10 px-3 rounded-[13px] bg-primary/10 text-primary text-[11px] font-black flex items-center gap-1.5"><Plus size={14} /> Ajouter</button></div>{lines.map((line) => <div key={line.id} className="rounded-[18px] border border-glass-border bg-background p-3 space-y-2"><input value={line.label} onChange={(event) => updateLine(line.id, { label: event.target.value })} placeholder={type === 'ordonnance' ? 'Médicament' : 'Acte'} className="w-full min-h-11 rounded-[13px] border border-glass-border bg-card px-3 text-sm font-bold text-text-main" /><div className="grid grid-cols-[1fr_auto] gap-2"><input value={line.detail} onChange={(event) => updateLine(line.id, { detail: event.target.value })} placeholder={type === 'ordonnance' ? 'Dosage' : 'Dent (optionnel)'} className="min-w-0 min-h-11 rounded-[13px] border border-glass-border bg-card px-3 text-sm font-bold text-text-main" />{(type === 'devis' || type === 'honoraires') && <input inputMode="decimal" value={line.amount} onChange={(event) => updateLine(line.id, { amount: event.target.value })} placeholder="MAD" className="w-24 min-h-11 rounded-[13px] border border-glass-border bg-card px-3 text-sm font-bold text-text-main" />}{lines.length > 1 && <button type="button" onClick={() => removeLine(line.id)} className="h-11 w-11 rounded-[13px] border border-danger-border text-danger flex items-center justify-center" aria-label="Supprimer la ligne"><Trash2 size={16} /></button>}</div></div>)}</div>}
        {(type === 'ordonnance' || type === 'libre' || (type === 'certificat' && certificateType === 'Certificat médical')) && <label className="block"><span className="text-[11px] font-black text-text-muted">{type === 'ordonnance' ? 'Posologie' : 'Contenu'}</span><textarea value={content} onChange={(event) => setContent(event.target.value)} rows={5} placeholder={type === 'ordonnance' ? 'Ex. 1 comprimé matin et soir pendant 5 jours' : 'Saisir le contenu du document'} className="mt-1 w-full rounded-[16px] border border-glass-border bg-background p-3 text-sm font-bold leading-relaxed text-text-main resize-none" /></label>}
        {error && <div className="rounded-[16px] border border-danger-border bg-danger-surface p-3 text-xs font-bold text-danger">{error}</div>}{success && <div className="rounded-[16px] border border-success-border bg-success-surface p-3 text-xs font-bold text-success flex items-center gap-2"><CheckCircle2 size={16} /> {success}</div>}
        <button type="button" onClick={() => void previewDocument()} disabled={busy || uncertainArchive} className="w-full min-h-14 rounded-[18px] bg-primary text-on-primary text-sm font-black flex items-center justify-center gap-2 disabled:opacity-50">{busy ? <Loader2 size={17} className="animate-spin" /> : <FileText size={17} />} Prévisualiser</button>
        <p className="text-center text-[10px] font-bold leading-relaxed text-text-muted">Même moteur documentaire, mêmes permissions et même dossier patient que sur desktop.</p>
      </div>}
    </section>
  </div>;
}
