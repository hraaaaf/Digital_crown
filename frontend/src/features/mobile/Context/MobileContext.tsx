import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, ArrowLeft, Calendar, Loader2, Phone, RefreshCcw, ShieldCheck } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { MobileStorage, type MobileBridgeContext } from '../../../services/zka/MobileStorage';

interface MobilePatient {
  id: number;
  numero_dossier?: string | null;
  nom: string;
  prenom: string;
  date_naissance?: string | null;
  telephone?: string | null;
  assurance?: string | null;
  has_medical_alert: boolean;
  motif_consultation?: string | null;
}

function ageFromBirth(value?: string | null): number | null {
  if (!value) return null;
  const birth = new Date(value);
  if (Number.isNaN(birth.getTime())) return null;
  const now = new Date();
  let age = now.getFullYear() - birth.getFullYear();
  const beforeBirthday = now.getMonth() < birth.getMonth() || (now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate());
  if (beforeBirthday) age -= 1;
  return age >= 0 && age < 130 ? age : null;
}

export const MobileContext = () => {
  const navigate = useNavigate();
  const [context, setContext] = useState<MobileBridgeContext | null>(null);
  const [patient, setPatient] = useState<MobilePatient | null>(null);
  const [phase, setPhase] = useState<'loading' | 'ready' | 'error'>('loading');
  const [error, setError] = useState('');

  const load = async () => {
    setPhase('loading');
    setError('');
    setPatient(null);
    const stored = await MobileStorage.getBridgeContext().catch(() => null);
    setContext(stored);
    if (!stored || stored.type !== 'patient') {
      setError("Aucun dossier patient contextuel n’est disponible sur cet appareil.");
      setPhase('error');
      return;
    }
    if (stored.state !== 'ready') {
      setError(stored.reason || 'Ce dossier patient n’est plus disponible.');
      setPhase('error');
      return;
    }

    let creds = await MobileStorage.getCredentials();
    if (!creds?.access_token) {
      setError('Session mobile non disponible. Régénérez le pont depuis le poste cabinet.');
      setPhase('error');
      return;
    }

    const request = async (accessToken: string) => fetch(`${creds!.api_base_url.replace(/\/$/, '')}/api/mobile/resource-context`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` },
      body: JSON.stringify({ context_key: stored.key }),
    });

    try {
      let response = await request(creds.access_token);
      if (response.status === 401) {
        creds = await MobileStorage.refreshCredentials();
        if (creds?.access_token) response = await request(creds.access_token);
      }
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || `Dossier indisponible (${response.status}).`);
      }
      const payload = await response.json();
      if (payload.type !== 'patient' || !payload.patient) throw new Error('Réponse patient mobile invalide.');
      setPatient(payload.patient as MobilePatient);
      setPhase('ready');
    } catch (err: any) {
      setError(err?.message || 'Impossible de charger le dossier patient.');
      setPhase('error');
    }
  };

  useEffect(() => { void load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const age = useMemo(() => ageFromBirth(patient?.date_naissance), [patient?.date_naissance]);

  if (phase === 'loading') {
    return (
      <div data-m4a-context className="min-h-[100dvh] bg-background text-text-main flex flex-col items-center justify-center gap-4 p-6 font-outfit relative" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}><div className="document-watermark absolute inset-0 pointer-events-none opacity-40" />
        <Loader2 size={38} className="animate-spin text-primary relative z-10" />
        <p className="relative z-10 text-xs font-black uppercase tracking-widest text-text-muted">Ouverture sécurisée du dossier…</p>
      </div>
    );
  }

  if (phase === 'error' || !patient) {
    return (
      <div data-m4a-context className="min-h-[100dvh] bg-background text-text-main p-5 font-outfit flex items-center justify-center relative" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}><div className="document-watermark absolute inset-0 pointer-events-none opacity-40" />
        <div className="w-full max-w-md bg-card-bg border border-rose-200 rounded-[2rem] p-6 shadow-elite text-center relative z-10">
          <AlertTriangle className="mx-auto text-rose-500" size={42} />
          <h1 className="mt-4 text-xl font-black text-text-main">Dossier indisponible</h1>
          <p className="mt-2 text-sm font-bold leading-relaxed text-text-muted">{error || context?.reason}</p>
          <button data-m4a-touch type="button" onClick={() => void load()} className="mt-5 w-full min-h-[52px] rounded-2xl border border-border-main bg-card-bg font-black text-xs uppercase tracking-widest text-text-main inline-flex items-center justify-center gap-2">
            <RefreshCcw size={16} /> Réessayer
          </button>
          <button data-m4a-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda', { replace: true })} className="mt-3 w-full min-h-[52px] rounded-2xl bg-primary text-white font-black text-xs uppercase tracking-widest">
            Retour au mobile
          </button>
        </div>
      </div>
    );
  }

  const displayName = `${patient.nom.toUpperCase()} ${patient.prenom}`;
  return (
    <div data-m4a-context className="min-h-[100dvh] bg-background text-text-main font-outfit relative px-5 pt-[max(1.25rem,env(safe-area-inset-top))] pb-[max(1.5rem,env(safe-area-inset-bottom))]" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}>
      <div className="document-watermark absolute inset-0 pointer-events-none opacity-40" />
      <div className="max-w-md mx-auto relative z-10">
        <button data-m4a-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda')} className="min-h-11 inline-flex items-center gap-2 text-sm font-black text-text-muted">
          <ArrowLeft size={17} /> Retour
        </button>

        <div className="mt-4 flex items-center gap-2 text-primary">
          <ShieldCheck size={18} />
          <p className="text-[10px] font-black uppercase tracking-[0.18em]">Contexte cabinet vérifié</p>
        </div>
        <h1 className="mt-2 text-3xl font-black tracking-tight text-text-main">Dossier patient</h1>

        <section className="mt-5 rounded-[1.75rem] bg-card-bg border border-border-main p-5 shadow-elite">
          <h2 className="text-2xl font-black tracking-tight text-text-main">{displayName}</h2>
          <p className="mt-1 text-sm font-bold text-text-muted">Dossier {patient.numero_dossier || 'sans numéro'}</p>
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-sm font-bold text-text-muted">
            {age !== null && <span>{age} ans</span>}
            {patient.telephone && <span>{patient.telephone}</span>}
          </div>
          {patient.has_medical_alert && (
            <div className="mt-4 inline-flex min-h-11 items-center gap-2 px-3 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 text-xs font-black uppercase tracking-wide">
              <AlertTriangle size={15} /> Alerte médicale
            </div>
          )}
        </section>

        <p className="mt-7 mb-3 text-sm font-black text-text-main">Actions rapides</p>
        <div className="grid grid-cols-2 gap-3">
          <a data-m4a-touch href={patient.telephone ? `tel:${patient.telephone}` : undefined} aria-disabled={!patient.telephone} className="min-h-[54px] rounded-2xl bg-card-bg border border-border-main inline-flex items-center justify-center gap-2 font-black text-sm text-text-main aria-disabled:opacity-40">
            <Phone size={18} /> Appeler
          </a>
          <button data-m4a-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda')} className="min-h-[54px] rounded-2xl bg-primary text-white inline-flex items-center justify-center gap-2 font-black text-sm">
            <Calendar size={18} /> Agenda
          </button>
        </div>

        <section className="mt-6 rounded-[1.75rem] bg-card-bg border border-border-main p-5 shadow-elite space-y-4">
          <div>
            <p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Assurance</p>
            <p className="mt-1 font-black text-text-main">{patient.assurance || 'Non renseignée'}</p>
          </div>
          <div>
            <p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Motif</p>
            <p className="mt-1 font-bold text-text-main">{patient.motif_consultation || 'Non renseigné'}</p>
          </div>
          <p className="pt-2 border-t border-border-main text-[11px] font-bold text-text-muted">Contexte chargé depuis le serveur · aucun identifiant patient dans l’URL</p>
        </section>

        <button data-m4a-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda', { replace: true })} className="mt-6 w-full min-h-[54px] rounded-2xl bg-card-bg border border-border-main text-text-main font-black text-xs uppercase tracking-widest">
          Retour au mobile
        </button>
      </div>
    </div>
  );
};
