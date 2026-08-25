import { useEffect, useMemo, useRef, useState } from 'react';
import { AlertTriangle, ArrowLeft, Calendar, FileText, Image as ImageIcon, Loader2, Phone, RefreshCcw, ShieldCheck } from 'lucide-react';
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

interface MobilePanoramic {
  patient_name: string;
  created_at?: string | null;
  landmarks_count: number;
  report_saved: boolean;
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

function formatDate(value?: string | null): string {
  if (!value) return 'Date non renseignée';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Date non renseignée';
  return date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export const MobileContext = () => {
  const navigate = useNavigate();
  const [context, setContext] = useState<MobileBridgeContext | null>(null);
  const [patient, setPatient] = useState<MobilePatient | null>(null);
  const [panoramic, setPanoramic] = useState<MobilePanoramic | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const imageUrlRef = useRef<string | null>(null);
  const [phase, setPhase] = useState<'loading' | 'ready' | 'error'>('loading');
  const [error, setError] = useState('');

  const clearImage = () => {
    if (imageUrlRef.current) URL.revokeObjectURL(imageUrlRef.current);
    imageUrlRef.current = null;
    setImageUrl(null);
  };

  const load = async () => {
    setPhase('loading');
    setError('');
    setPatient(null);
    setPanoramic(null);
    clearImage();
    const stored = await MobileStorage.getBridgeContext().catch(() => null);
    setContext(stored);
    if (!stored || !['patient', 'panoramic'].includes(stored.type)) {
      setError('Aucun contexte clinique compatible n’est disponible sur cet appareil.');
      setPhase('error');
      return;
    }
    if (stored.state !== 'ready') {
      setError(stored.reason || 'Ce contexte clinique n’est plus disponible.');
      setPhase('error');
      return;
    }

    let creds = await MobileStorage.getCredentials();
    if (!creds?.access_token) {
      setError('Session mobile non disponible. Régénérez le pont depuis le poste cabinet.');
      setPhase('error');
      return;
    }

    const request = async (path: string, accessToken: string) => fetch(`${creds!.api_base_url.replace(/\/$/, '')}/api/mobile/${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` },
      body: JSON.stringify({ context_key: stored.key }),
    });

    try {
      let response = await request('resource-context', creds.access_token);
      if (response.status === 401) {
        creds = await MobileStorage.refreshCredentials();
        if (creds?.access_token) response = await request('resource-context', creds.access_token);
      }
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || `Contexte indisponible (${response.status}).`);
      }
      const payload = await response.json();

      if (payload.type === 'patient' && payload.patient && stored.type === 'patient') {
        setPatient(payload.patient as MobilePatient);
        setPhase('ready');
        return;
      }

      if (payload.type === 'panoramic' && payload.panoramic && stored.type === 'panoramic') {
        if (!creds?.access_token) throw new Error('Session mobile expirée.');
        let mediaResponse = await request('resource-context-media', creds.access_token);
        if (mediaResponse.status === 401) {
          creds = await MobileStorage.refreshCredentials();
          if (creds?.access_token) mediaResponse = await request('resource-context-media', creds.access_token);
        }
        if (!mediaResponse.ok) {
          const mediaError = await mediaResponse.json().catch(() => ({}));
          throw new Error(mediaError.detail || `Image indisponible (${mediaResponse.status}).`);
        }
        const blob = await mediaResponse.blob();
        if (!blob.type.startsWith('image/')) throw new Error('Le média panoramique reçu n’est pas une image valide.');
        const nextUrl = URL.createObjectURL(blob);
        imageUrlRef.current = nextUrl;
        setImageUrl(nextUrl);
        setPanoramic(payload.panoramic as MobilePanoramic);
        setPhase('ready');
        return;
      }

      throw new Error('Réponse de contexte mobile invalide.');
    } catch (err: any) {
      setError(err?.message || 'Impossible de charger le contexte clinique.');
      setPhase('error');
    }
  };

  useEffect(() => {
    void load();
    return () => {
      if (imageUrlRef.current) URL.revokeObjectURL(imageUrlRef.current);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const age = useMemo(() => ageFromBirth(patient?.date_naissance), [patient?.date_naissance]);

  if (phase === 'loading') {
    return (
      <div data-mobile-context className="min-h-[100dvh] bg-background text-text-main flex flex-col items-center justify-center gap-4 p-6 font-outfit relative" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}><div className="document-watermark absolute inset-0 pointer-events-none opacity-40" />
        <Loader2 size={38} className="animate-spin text-primary relative z-10" />
        <p className="relative z-10 text-xs font-black uppercase tracking-widest text-text-muted">Ouverture sécurisée du contexte…</p>
      </div>
    );
  }

  if (phase === 'error' || (!patient && !panoramic)) {
    return (
      <div data-mobile-context className="min-h-[100dvh] bg-background text-text-main p-5 font-outfit flex items-center justify-center relative" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}><div className="document-watermark absolute inset-0 pointer-events-none opacity-40" />
        <div className="w-full max-w-md bg-card-bg border border-rose-200 rounded-[2rem] p-6 shadow-elite text-center relative z-10">
          <AlertTriangle className="mx-auto text-rose-500" size={42} />
          <h1 className="mt-4 text-xl font-black text-text-main">Contexte indisponible</h1>
          <p className="mt-2 text-sm font-bold leading-relaxed text-text-muted">{error || context?.reason}</p>
          <button data-m4b-touch type="button" onClick={() => void load()} className="mt-5 w-full min-h-[52px] rounded-2xl border border-border-main bg-card-bg font-black text-xs uppercase tracking-widest text-text-main inline-flex items-center justify-center gap-2">
            <RefreshCcw size={16} /> Réessayer
          </button>
          <button data-m4b-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda', { replace: true })} className="mt-3 w-full min-h-[52px] rounded-2xl bg-primary text-white font-black text-xs uppercase tracking-widest">
            Retour au mobile
          </button>
        </div>
      </div>
    );
  }

  if (panoramic) {
    return (
      <div data-m4b-context className="min-h-[100dvh] bg-background text-text-main font-outfit relative px-5 pt-[max(1.25rem,env(safe-area-inset-top))] pb-[max(1.5rem,env(safe-area-inset-bottom))]" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}>
        <div className="document-watermark absolute inset-0 pointer-events-none opacity-40" />
        <div className="max-w-md mx-auto relative z-10">
          <button data-m4b-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda')} className="min-h-11 inline-flex items-center gap-2 text-sm font-black text-text-muted">
            <ArrowLeft size={17} /> Retour
          </button>

          <div className="mt-4 flex items-center gap-2 text-primary">
            <ShieldCheck size={18} />
            <p className="text-[10px] font-black uppercase tracking-[0.18em]">Contexte cabinet vérifié</p>
          </div>
          <h1 className="mt-2 text-3xl font-black tracking-tight text-text-main">Radio panoramique</h1>
          <p className="mt-1 text-base font-black text-text-main">{panoramic.patient_name}</p>
          <p className="mt-1 text-sm font-bold text-text-muted">{formatDate(panoramic.created_at)}</p>

          <section className="mt-5 rounded-[1.75rem] overflow-hidden bg-slate-950 border border-slate-800 shadow-elite min-h-[230px] flex items-center justify-center">
            {imageUrl ? (
              <img src={imageUrl} alt="Radio panoramique contextuelle" className="block w-full max-h-[52dvh] object-contain bg-black" />
            ) : (
              <div className="text-slate-400 flex items-center gap-2 text-sm font-bold"><ImageIcon size={18} /> Image indisponible</div>
            )}
          </section>

          <section className="mt-4 rounded-[1.5rem] bg-card-bg border border-border-main p-4 shadow-elite">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Statut</p>
                <p className="mt-1 font-black text-text-main">{panoramic.report_saved ? 'Rapport enregistré' : 'Rapport non finalisé'}</p>
              </div>
              <FileText size={20} className="text-primary" />
            </div>
            <p className="mt-3 pt-3 border-t border-border-main text-[11px] font-bold text-text-muted">{panoramic.landmarks_count} repère{panoramic.landmarks_count > 1 ? 's' : ''} dentaire{panoramic.landmarks_count > 1 ? 's' : ''} · média chargé depuis le serveur sans identifiant dans l’URL</p>
          </section>

          <button data-m4b-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda', { replace: true })} className="mt-6 w-full min-h-[54px] rounded-2xl bg-card-bg border border-border-main text-text-main font-black text-xs uppercase tracking-widest">
            Retour au mobile
          </button>
        </div>
      </div>
    );
  }

  const displayName = `${patient!.nom.toUpperCase()} ${patient!.prenom}`;
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
          <p className="mt-1 text-sm font-bold text-text-muted">Dossier {patient!.numero_dossier || 'sans numéro'}</p>
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-sm font-bold text-text-muted">
            {age !== null && <span>{age} ans</span>}
            {patient!.telephone && <span>{patient!.telephone}</span>}
          </div>
          {patient!.has_medical_alert && (
            <div className="mt-4 inline-flex min-h-11 items-center gap-2 px-3 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 text-xs font-black uppercase tracking-wide">
              <AlertTriangle size={15} /> Alerte médicale
            </div>
          )}
        </section>

        <p className="mt-7 mb-3 text-sm font-black text-text-main">Actions rapides</p>
        <div className="grid grid-cols-2 gap-3">
          <a data-m4a-touch href={patient!.telephone ? `tel:${patient!.telephone}` : undefined} aria-disabled={!patient!.telephone} className="min-h-[54px] rounded-2xl bg-card-bg border border-border-main inline-flex items-center justify-center gap-2 font-black text-sm text-text-main aria-disabled:opacity-40">
            <Phone size={18} /> Appeler
          </a>
          <button data-m4a-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda')} className="min-h-[54px] rounded-2xl bg-primary text-white inline-flex items-center justify-center gap-2 font-black text-sm">
            <Calendar size={18} /> Agenda
          </button>
        </div>

        <section className="mt-6 rounded-[1.75rem] bg-card-bg border border-border-main p-5 shadow-elite space-y-4">
          <div>
            <p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Assurance</p>
            <p className="mt-1 font-black text-text-main">{patient!.assurance || 'Non renseignée'}</p>
          </div>
          <div>
            <p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Motif</p>
            <p className="mt-1 font-bold text-text-main">{patient!.motif_consultation || 'Non renseigné'}</p>
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
