import { useMemo, useState } from 'react';
import { ArrowLeft, CheckCircle2, FileText, Loader2, Plus, Trash2, X } from 'lucide-react';
import { MobileStorage } from '../../../../services/zka/MobileStorage';
import { mobileFetch } from '../../../../services/zka/mobileFetch';

export type MobileQuickDocumentType = 'ordonnance' | 'certificat' | 'devis' | 'honoraires' | 'libre';

interface PatientIdentity {
  id: number;
  name: string;
}

interface DocumentLine {
  id: number;
  label: string;
  detail: string;
  amount: string;
}

const TYPES: Array<{ value: MobileQuickDocumentType; label: string; hint: string }> = [
  { value: 'ordonnance', label: 'Ordonnance', hint: 'Médicament + posologie' },
  { value: 'certificat', label: 'Certificat', hint: 'Présence, arrêt ou certificat médical' },
  { value: 'devis', label: 'Devis', hint: 'Actes et montants' },
  { value: 'honoraires', label: 'Honoraires', hint: 'Note d’honoraires' },
  { value: 'libre', label: 'Document libre', hint: 'Courrier ou note clinique simple' },
];

function resolveApiBaseUrl(stored: string): string {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return stored;
  if (stored.includes('localhost') || stored.includes('127.0.0.1')) {
    return `${window.location.protocol}//${hostname}:8005`;
  }
  return stored.replace(/\/$/, '');
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

export function MobileQuickDocumentSheet({
  patient,
  preview = false,
  onClose,
}: {
  patient: PatientIdentity;
  preview?: boolean;
  onClose: () => void;
}) {
  const [type, setType] = useState<MobileQuickDocumentType | null>(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [certificateType, setCertificateType] = useState('Certificat de Présence');
  const [certificateDays, setCertificateDays] = useState('1');
  const [lines, setLines] = useState<DocumentLine[]>([{ id: 1, label: '', detail: '', amount: '' }]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const selected = useMemo(() => TYPES.find((entry) => entry.value === type), [type]);

  const updateLine = (id: number, patch: Partial<DocumentLine>) => {
    setLines((current) => current.map((line) => line.id === id ? { ...line, ...patch } : line));
  };

  const addLine = () => setLines((current) => [
    ...current,
    { id: Date.now(), label: '', detail: '', amount: '' },
  ]);

  const removeLine = (id: number) => setLines((current) => current.length > 1 ? current.filter((line) => line.id !== id) : current);

  const buildPayload = () => {
    const docDate = todayIso();
    if (type === 'ordonnance') {
      const medications = lines.filter((line) => line.label.trim()).map((line) => ({
        nom: line.label.trim(),
        dosage: line.detail.trim(),
        forme: 'Comprimés',
        posologie: content.trim(),
        type: 'MEDICAMENT',
        non_substituable: false,
      }));
      if (!medications.length || !content.trim()) throw new Error('Ajoutez au moins un médicament et sa posologie.');
      return { type, patient_id: patient.id, data: { medications, doc_date: docDate, show_legal_annotations: true } };
    }

    if (type === 'certificat') {
      const days = Number.parseInt(certificateDays, 10);
      if (certificateType === 'Arrêt de travail' && (!Number.isInteger(days) || days < 1 || days > 365)) {
        throw new Error('La durée doit être comprise entre 1 et 365 jours.');
      }
      if (certificateType === 'Certificat médical' && !content.trim()) throw new Error('Le contenu du certificat médical est requis.');
      return {
        type,
        patient_id: patient.id,
        data: {
          reason: certificateType,
          days: certificateType === 'Arrêt de travail' ? days : 0,
          doc_date: docDate,
          ...(certificateType === 'Arrêt de travail' ? { start_date: docDate } : {}),
          ...(certificateType === 'Certificat médical' ? { content: content.trim() } : {}),
        },
      };
    }

    if (type === 'devis' || type === 'honoraires') {
      const entries = lines.filter((line) => line.label.trim()).map((line) => {
        const amount = Number.parseFloat(line.amount.replace(',', '.'));
        if (!Number.isFinite(amount) || amount < 0) throw new Error(`Montant invalide pour « ${line.label || 'acte'} ».`);
        return {
          acte: line.label.trim(),
          dent: line.detail.trim() || '0',
          dents: [],
          prix_unitaire: amount,
          montant: amount,
          date: docDate,
        };
      });
      if (!entries.length) throw new Error('Ajoutez au moins un acte.');
      return {
        type: type === 'honoraires' ? 'note' : 'devis',
        patient_id: patient.id,
        data: type === 'honoraires'
          ? { payments: entries, doc_date: docDate, installments: [], is_global_note: false }
          : { items: entries, doc_date: docDate, teeth_data: {} },
        is_accounted: true,
        payment_status: 'EN_ATTENTE',
      };
    }

    if (type === 'libre') {
      if (!title.trim() || !content.trim()) throw new Error('Le titre et le contenu sont requis.');
      return {
        type: 'libre',
        patient_id: patient.id,
        data: {
          title: title.trim(),
          content: content.trim(),
          doc_date: docDate,
          custom_patient: '',
          custom_date: '',
          hide_patient_header: false,
          page_size: 'A4',
          alignment: 'left',
        },
      };
    }

    throw new Error('Choisissez un type de document.');
  };

  const generate = async () => {
    setError('');
    setSuccess('');
    let payload: ReturnType<typeof buildPayload>;
    try {
      payload = buildPayload();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Document incomplet.');
      return;
    }

    if (preview) {
      setSuccess('Aperçu isolé : document prêt à générer.');
      return;
    }

    setBusy(true);
    try {
      const creds = await MobileStorage.getCredentials();
      if (!creds) throw new Error('Session mobile indisponible.');
      const baseUrl = resolveApiBaseUrl(creds.api_base_url);
      const response = await mobileFetch(`${baseUrl}/api/documents/generate?archive=true&preview=false&force=false`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${creds.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(20000),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = body?.detail;
        const message = typeof detail === 'string' ? detail : detail?.message;
        throw new Error(message || `Génération indisponible (${response.status}).`);
      }
      setSuccess('Document généré et archivé dans le dossier patient.');
      if (body?.pdf_url) {
        const clean = String(body.pdf_url).replace(/^\//, '');
        window.open(`${baseUrl}/api/${clean}`, '_blank', 'noopener,noreferrer');
      }
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Impossible de générer le document.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div data-mobile-quick-document className="fixed inset-0 z-[80] bg-black/35 backdrop-blur-sm flex items-end sm:items-center justify-center">
      <section className="w-full max-w-2xl max-h-[92dvh] overflow-y-auto rounded-t-[30px] sm:rounded-[30px] border border-glass-border bg-card p-4 sm:p-5 shadow-2xl" style={{ backgroundColor: 'var(--glass-bg)' }}>
        <div className="sticky top-0 z-10 -mx-1 mb-4 flex items-center gap-3 rounded-[20px] bg-card/95 px-1 py-2 backdrop-blur" style={{ backgroundColor: 'var(--glass-bg)' }}>
          {type ? (
            <button type="button" onClick={() => { setType(null); setError(''); setSuccess(''); }} className="h-11 w-11 rounded-[14px] border border-glass-border flex items-center justify-center text-primary" aria-label="Retour aux types">
              <ArrowLeft size={18} />
            </button>
          ) : <div className="h-11 w-11 rounded-[14px] bg-primary/10 text-primary flex items-center justify-center"><FileText size={19} /></div>}
          <div className="min-w-0 flex-1">
            <p className="text-[10px] font-black uppercase tracking-[0.16em] text-text-muted">Quick Document Studio</p>
            <h2 className="truncate text-lg font-black text-text-main">{selected?.label || patient.name}</h2>
          </div>
          <button type="button" onClick={onClose} className="h-11 w-11 rounded-[14px] border border-glass-border flex items-center justify-center text-text-muted" aria-label="Fermer">
            <X size={18} />
          </button>
        </div>

        {!type ? (
          <div className="space-y-2">
            {TYPES.map((entry) => (
              <button key={entry.value} type="button" onClick={() => setType(entry.value)} className="w-full min-h-16 rounded-[20px] border border-glass-border bg-background px-4 py-3 text-left active:scale-[0.99] transition-transform">
                <p className="text-sm font-black text-text-main">{entry.label}</p>
                <p className="mt-1 text-[11px] font-bold text-text-muted">{entry.hint}</p>
              </button>
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {type === 'certificat' && (
              <>
                <label className="block">
                  <span className="text-[11px] font-black text-text-muted">Nature</span>
                  <select value={certificateType} onChange={(event) => setCertificateType(event.target.value)} className="mt-1 w-full min-h-12 rounded-[16px] border border-glass-border bg-background px-3 text-sm font-bold text-text-main">
                    <option>Certificat de Présence</option>
                    <option>Arrêt de travail</option>
                    <option>Certificat médical</option>
                  </select>
                </label>
                {certificateType === 'Arrêt de travail' && (
                  <label className="block">
                    <span className="text-[11px] font-black text-text-muted">Durée (jours)</span>
                    <input inputMode="numeric" value={certificateDays} onChange={(event) => setCertificateDays(event.target.value)} className="mt-1 w-full min-h-12 rounded-[16px] border border-glass-border bg-background px-3 text-sm font-bold text-text-main" />
                  </label>
                )}
              </>
            )}

            {type === 'libre' && (
              <label className="block">
                <span className="text-[11px] font-black text-text-muted">Titre</span>
                <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Courrier d’orientation" className="mt-1 w-full min-h-12 rounded-[16px] border border-glass-border bg-background px-3 text-sm font-bold text-text-main" />
              </label>
            )}

            {(type === 'ordonnance' || type === 'devis' || type === 'honoraires') && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-black text-text-muted">{type === 'ordonnance' ? 'Médicaments' : 'Actes'}</span>
                  <button type="button" onClick={addLine} className="min-h-10 px-3 rounded-[13px] bg-primary/10 text-primary text-[11px] font-black flex items-center gap-1.5"><Plus size={14} /> Ajouter</button>
                </div>
                {lines.map((line) => (
                  <div key={line.id} className="rounded-[18px] border border-glass-border bg-background p-3 space-y-2">
                    <input value={line.label} onChange={(event) => updateLine(line.id, { label: event.target.value })} placeholder={type === 'ordonnance' ? 'Médicament' : 'Acte'} className="w-full min-h-11 rounded-[13px] border border-glass-border bg-card px-3 text-sm font-bold text-text-main" />
                    <div className="grid grid-cols-[1fr_auto] gap-2">
                      <input value={line.detail} onChange={(event) => updateLine(line.id, { detail: event.target.value })} placeholder={type === 'ordonnance' ? 'Dosage' : 'Dent (optionnel)'} className="min-w-0 min-h-11 rounded-[13px] border border-glass-border bg-card px-3 text-sm font-bold text-text-main" />
                      {(type === 'devis' || type === 'honoraires') && <input inputMode="decimal" value={line.amount} onChange={(event) => updateLine(line.id, { amount: event.target.value })} placeholder="MAD" className="w-24 min-h-11 rounded-[13px] border border-glass-border bg-card px-3 text-sm font-bold text-text-main" />}
                      {lines.length > 1 && <button type="button" onClick={() => removeLine(line.id)} className="h-11 w-11 rounded-[13px] border border-rose-500/20 text-rose-600 flex items-center justify-center" aria-label="Supprimer la ligne"><Trash2 size={16} /></button>}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {(type === 'ordonnance' || type === 'libre' || (type === 'certificat' && certificateType === 'Certificat médical')) && (
              <label className="block">
                <span className="text-[11px] font-black text-text-muted">{type === 'ordonnance' ? 'Posologie' : 'Contenu'}</span>
                <textarea value={content} onChange={(event) => setContent(event.target.value)} rows={5} placeholder={type === 'ordonnance' ? 'Ex. 1 comprimé matin et soir pendant 5 jours' : 'Saisir le contenu du document'} className="mt-1 w-full rounded-[16px] border border-glass-border bg-background p-3 text-sm font-bold leading-relaxed text-text-main resize-none" />
              </label>
            )}

            {error && <div className="rounded-[16px] border border-rose-500/20 bg-rose-500/5 p-3 text-xs font-bold text-rose-700">{error}</div>}
            {success && <div className="rounded-[16px] border border-emerald-500/20 bg-emerald-500/5 p-3 text-xs font-bold text-emerald-700 flex items-center gap-2"><CheckCircle2 size={16} /> {success}</div>}

            <button type="button" onClick={() => void generate()} disabled={busy} className="w-full min-h-14 rounded-[18px] bg-primary text-primary-foreground text-sm font-black flex items-center justify-center gap-2 disabled:opacity-50">
              {busy ? <Loader2 size={17} className="animate-spin" /> : <FileText size={17} />}
              Générer et archiver
            </button>
            <p className="text-center text-[10px] font-bold leading-relaxed text-text-muted">Même moteur documentaire, mêmes permissions et même dossier patient que sur desktop.</p>
          </div>
        )}
      </section>
    </div>
  );
}
