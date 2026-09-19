import { useEffect, useMemo, useState } from 'react';
import { KeyRound, Loader2, ShieldCheck, Smartphone } from 'lucide-react';
import { API_BASE } from '../../services/api';

type Context = {
  access_id: string;
  patient: { nom?: string; prenom?: string; numero_dossier?: string | null };
  relationship_type: string;
};

const tokenFromUrl = () => new URLSearchParams(window.location.search).get('token')?.trim() || '';

export const PatientCompanionApp = () => {
  const [idToken, setIdToken] = useState('');
  const [manualCode, setManualCode] = useState('');
  const [contexts, setContexts] = useState<Context[]>([]);
  const [selected, setSelected] = useState<Context | null>(null);
  const [phase, setPhase] = useState<'identity'|'activation'|'loading'|'home'|'error'>('identity');
  const [error, setError] = useState('');
  const qrToken = useMemo(tokenFromUrl, []);

  useEffect(() => {
    if (qrToken) setPhase('identity');
  }, [qrToken]);

  const request = async (path: string, init?: RequestInit) => {
    const response = await fetch(`${API_BASE}/patient-companion${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${idToken.trim()}`, ...(init?.headers || {}) },
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || 'Action impossible.');
    return payload;
  };

  const loadContexts = async () => {
    setPhase('loading'); setError('');
    try {
      const payload = await request('/me');
      const items = Array.isArray(payload.contexts) ? payload.contexts : [];
      if (!items.length) { setPhase('activation'); return; }
      setContexts(items);
      if (items.length === 1) { setSelected(items[0]); setPhase('home'); }
      else setPhase('home');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Identité patient invalide.');
      setPhase('error');
    }
  };

  const continueIdentity = () => {
    if (!idToken.trim()) { setError('Jeton Firebase vérifié requis.'); setPhase('error'); return; }
    void loadContexts();
  };

  const activate = async () => {
    if (!manualCode.trim() && !qrToken) { setError('Saisissez le code remis par le cabinet.'); setPhase('error'); return; }
    setPhase('loading'); setError('');
    try {
      await request('/activate', { method: 'POST', body: JSON.stringify(qrToken ? { token: qrToken } : { manual_code: manualCode.trim() }) });
      window.history.replaceState({}, '', '/companion');
      await loadContexts();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Invitation invalide ou expirée.');
      setPhase('error');
    }
  };

  const reset = () => { setSelected(null); setContexts([]); setManualCode(''); setError(''); setPhase('identity'); };

  return <main data-pc00-shell className="min-h-[100dvh] bg-background text-text-main font-outfit px-4 py-[max(1rem,env(safe-area-inset-top))]">
    <div className="mx-auto max-w-md">
      <header className="pt-5 pb-6"><div className="flex items-center gap-2 text-primary"><ShieldCheck size={19}/><span className="text-[10px] font-black uppercase tracking-[0.18em]">Digital Crown</span></div><h1 className="mt-2 text-3xl font-black tracking-tight">Patient Companion</h1><p className="mt-2 text-sm font-bold text-text-muted">Votre espace sécurisé, relié directement à votre cabinet.</p></header>
      {phase === 'identity' && <Card title="Accès sécurisé" icon={<Smartphone size={20}/>}>
        <p className="text-sm font-medium text-text-muted">Identifiez-vous avec le compte Firebase vérifié associé à l’invitation du cabinet.</p>
        <label className="mt-5 block"><span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Jeton Firebase</span><input data-pc00-id-token type="password" autoComplete="off" value={idToken} onChange={e=>setIdToken(e.target.value)} className="mt-2 h-12 w-full rounded-2xl border border-border-main bg-background px-4 text-sm font-bold outline-none focus:ring-2 focus:ring-primary/20" /></label>
        <button data-pc00-continue onClick={continueIdentity} className="mt-4 min-h-[54px] w-full rounded-2xl bg-primary text-white font-black">Continuer</button>
        <p className="mt-3 text-center text-[11px] font-bold text-text-muted">Le jeton n’est pas enregistré par Patient Companion.</p>
      </Card>}
      {phase === 'activation' && <Card title="Activer mon accès" icon={<KeyRound size={20}/>}>
        {qrToken ? <p className="text-sm font-bold text-emerald-700">Invitation QR détectée. Confirmez pour activer votre accès.</p> : <label className="block"><span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Code remis par le cabinet</span><input data-pc00-manual-code value={manualCode} onChange={e=>setManualCode(e.target.value)} autoComplete="one-time-code" className="mt-2 h-12 w-full rounded-2xl border border-border-main bg-background px-4 text-center text-lg font-black tracking-[0.12em] uppercase" /></label>}
        <button data-pc00-activate onClick={()=>void activate()} className="mt-4 min-h-[54px] w-full rounded-2xl bg-primary text-white font-black">Activer Patient Companion</button>
      </Card>}
      {phase === 'loading' && <Card title="Vérification" icon={<Loader2 className="animate-spin" size={20}/>}><p className="text-sm font-bold text-text-muted">Vérification sécurisée de votre accès…</p></Card>}
      {phase === 'error' && <Card title="Accès non validé" icon={<ShieldCheck size={20}/>}><p role="alert" className="text-sm font-bold text-rose-700">{error}</p><button onClick={()=>setPhase(idToken.trim()?'activation':'identity')} className="mt-4 min-h-[52px] w-full rounded-2xl border border-border-main font-black">Réessayer</button></Card>}
      {phase === 'home' && !selected && contexts.length > 1 && <Card title="Choisir un dossier" icon={<ShieldCheck size={20}/>}>{contexts.map(c=><button key={c.access_id} data-pc00-context onClick={()=>setSelected(c)} className="mb-2 min-h-[62px] w-full rounded-2xl border border-border-main bg-card-bg px-4 text-left"><span className="block font-black">{c.patient?.prenom} {c.patient?.nom}</span><span className="text-xs font-bold text-text-muted">{c.relationship_type}</span></button>)}</Card>}
      {phase === 'home' && selected && <><Card title="Bonjour" icon={<ShieldCheck size={20}/>}><p className="text-xl font-black">{selected.patient?.prenom} {selected.patient?.nom}</p><p className="mt-1 text-xs font-bold text-text-muted">{selected.relationship_type}</p></Card><section className="mt-4 grid grid-cols-2 gap-3" aria-label="Fonctions Patient Companion"><Placeholder label="Mes rendez-vous" /><Placeholder label="Mes documents" /></section><button onClick={reset} className="mt-6 min-h-[48px] w-full text-xs font-black uppercase tracking-widest text-text-muted">Changer de compte</button></>}
    </div>
  </main>;
};

const Card=({title,icon,children}:{title:string;icon:React.ReactNode;children:React.ReactNode})=><section className="rounded-[1.75rem] border border-border-main bg-card-bg p-5 shadow-elite"><div className="flex items-center gap-2 text-primary">{icon}<h2 className="font-black text-text-main">{title}</h2></div><div className="mt-4">{children}</div></section>;
const Placeholder=({label}:{label:string})=><div className="min-h-[92px] rounded-2xl border border-border-main bg-card-bg p-4 opacity-70"><p className="font-black">{label}</p><p className="mt-1 text-[10px] font-black uppercase tracking-widest text-text-muted">Bientôt disponible</p></div>;
