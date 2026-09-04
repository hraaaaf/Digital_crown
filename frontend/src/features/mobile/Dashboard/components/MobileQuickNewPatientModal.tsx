import { Loader2, UserPlus, X } from 'lucide-react';
import { useState } from 'react';
import toast from 'react-hot-toast';
import { MobileStorage } from '../../../../services/zka/MobileStorage';
import { mobileFetch } from '../../../../services/zka/mobileFetch';

type CreatedPatient = { id: number; nom: string; prenom: string; telephone?: string | null };

export function MobileQuickNewPatientModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [form, setForm] = useState({
    nom: '',
    prenom: '',
    date_naissance: '',
    sexe: '' as '' | 'F' | 'M',
    telephone: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const submit = async () => {
    if (!form.nom.trim() || !form.prenom.trim()) {
      setError('Nom et prénom requis.');
      return;
    }
    if (!form.date_naissance) {
      setError('Date de naissance requise.');
      return;
    }
    if (!form.sexe) {
      setError('Sexe F ou M requis.');
      return;
    }

    setSubmitting(true);
    setError('');
    try {
      const creds = await MobileStorage.getCredentials();
      if (!creds) throw new Error('Session mobile indisponible.');
      const response = await mobileFetch(`${creds.api_base_url.replace(/\/$/, '')}/api/patients/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nom: form.nom.trim(),
          prenom: form.prenom.trim(),
          date_naissance: form.date_naissance,
          sexe: form.sexe,
          telephone: form.telephone.trim() || null,
        }),
        signal: AbortSignal.timeout(6000),
      });
      const payload = await response.json().catch(() => ({}));
      if (response.status === 409) {
        const existing = payload?.detail?.existing_patient;
        if (existing?.id) throw new Error('Un dossier patient correspondant existe déjà. Utilisez la recherche patient.');
      }
      if (!response.ok) {
        const detail = typeof payload?.detail === 'string' ? payload.detail : `Création patient refusée (${response.status}).`;
        throw new Error(detail);
      }
      const created = payload as CreatedPatient;
      if (!created?.id) throw new Error('Réponse patient invalide.');
      toast.success('Patient créé');
      onCreated();
      onClose();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Création patient impossible.');
    } finally {
      setSubmitting(false);
    }
  };

  const controlClass = 'min-h-12 w-full rounded-[16px] border border-glass-border bg-background px-3 text-sm font-bold text-text-main outline-none focus:border-primary/40';

  return (
    <div className="fixed inset-0 z-[100] flex items-end bg-slate-950/30 backdrop-blur-sm sm:items-center sm:justify-center sm:p-4" data-mobile-quick-new-patient>
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="mobile-quick-new-patient-title"
        className="w-full max-h-[88dvh] overflow-y-auto rounded-t-[28px] border border-glass-border bg-card p-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] shadow-elite sm:max-w-md sm:rounded-[28px]"
        style={{
          backgroundColor: 'var(--glass-bg)',
          fontFamily: 'var(--app-font-family, "Inter", system-ui, sans-serif)',
        }}
      >
        <div className="mb-5 flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-[14px] bg-primary/10 text-primary"><UserPlus size={19} /></span>
            <div>
              <p className="text-[9px] font-black uppercase tracking-[0.16em] text-text-muted">Action rapide</p>
              <h2 id="mobile-quick-new-patient-title" className="mt-0.5 text-lg font-black text-text-main">Nouveau patient</h2>
            </div>
          </div>
          <button type="button" onClick={onClose} aria-label="Fermer" className="flex h-11 w-11 items-center justify-center rounded-[15px] border border-glass-border bg-background text-text-muted"><X size={18} /></button>
        </div>

        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <input autoFocus type="text" autoComplete="family-name" placeholder="Nom" value={form.nom} onChange={(event) => setForm({ ...form, nom: event.target.value })} className={controlClass} />
            <input type="text" autoComplete="given-name" placeholder="Prénom" value={form.prenom} onChange={(event) => setForm({ ...form, prenom: event.target.value })} className={controlClass} />
          </div>
          <div>
            <label className="text-[10px] font-black uppercase tracking-[0.14em] text-text-muted">Date de naissance</label>
            <input type="date" value={form.date_naissance} onChange={(event) => setForm({ ...form, date_naissance: event.target.value })} className={`${controlClass} mt-1`} />
          </div>
          <div>
            <label className="text-[10px] font-black uppercase tracking-[0.14em] text-text-muted">Sexe</label>
            <div className="mt-1 grid grid-cols-2 gap-2">
              {(['F', 'M'] as const).map((sexe) => (
                <button
                  key={sexe}
                  type="button"
                  aria-pressed={form.sexe === sexe}
                  onClick={() => setForm({ ...form, sexe })}
                  className={`min-h-12 rounded-[16px] border text-sm font-black ${form.sexe === sexe ? 'border-primary bg-primary text-white' : 'border-glass-border bg-background text-text-main'}`}
                >
                  {sexe === 'F' ? 'Féminin' : 'Masculin'}
                </button>
              ))}
            </div>
          </div>
          <input type="tel" autoComplete="tel" placeholder="Téléphone (optionnel)" value={form.telephone} onChange={(event) => setForm({ ...form, telephone: event.target.value })} className={controlClass} />
          {error && <p className="text-xs font-bold text-rose-600">{error}</p>}
          <button type="button" disabled={submitting} onClick={() => void submit()} className="flex min-h-[54px] w-full items-center justify-center gap-2 rounded-[18px] bg-primary px-4 text-sm font-black text-white shadow-sm disabled:opacity-50">
            {submitting && <Loader2 size={17} className="animate-spin" />} Créer le patient
          </button>
        </div>
      </section>
    </div>
  );
}
