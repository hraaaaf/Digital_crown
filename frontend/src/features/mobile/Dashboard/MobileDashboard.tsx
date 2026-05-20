import { useState, useEffect, useCallback } from 'react';
import {
  Smartphone, LogOut, Calendar, TrendingUp,
  AlertTriangle, Phone, MessageSquare, ChevronRight,
  Clock, Wallet, ShieldCheck, ArrowUpRight, ArrowDownRight,
  RefreshCw, Wifi, WifiOff,
} from 'lucide-react';
import { MobileStorage } from '../../../services/zka/MobileStorage';

type Tab = 'agenda' | 'finance' | 'securite';
type SyncStatus = 'idle' | 'loading' | 'success' | 'error';

interface Snapshot {
  generated_at: string;
  appointments: {
    id: number;
    time: string;
    patient_name: string;
    phone: string | null;
    motif: string;
    status: string | null;
    duration_minutes: number;
  }[];
  finance: {
    today_revenue: number;
    month_revenue: number;
    month_variation: number | null;
    appointments_count: number;
  };
  debtors: { id: number; name: string; amount: number; phone: string | null }[];
}

export const MobileDashboard = () => {
  const [activeTab, setActiveTab] = useState<Tab>('agenda');
  const [syncStatus, setSyncStatus] = useState<SyncStatus>('idle');
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const on = () => setIsOnline(true);
    const off = () => setIsOnline(false);
    window.addEventListener('online', on);
    window.addEventListener('offline', off);
    return () => { window.removeEventListener('online', on); window.removeEventListener('offline', off); };
  }, []);

  const fetchSnapshot = useCallback(async () => {
    try {
      setSyncStatus('loading');
      const creds = await MobileStorage.getCredentials();
      if (!creds) throw new Error('Non appairé');

      const res = await fetch(`${creds.api_base_url}/api/mobile/snapshot`, {
        headers: { Authorization: `Bearer ${creds.access_token}` },
        signal: AbortSignal.timeout(8000),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `Erreur ${res.status}`);
      }

      const data: Snapshot = await res.json();
      setSnapshot(data);
      await MobileStorage.saveLastSnapshot(data);
      setError(null);
      setSyncStatus('success');
    } catch (err: any) {
      // Fallback sur le cache offline
      const cached = await MobileStorage.getLastSnapshot();
      if (cached) {
        setSnapshot(cached);
        setSyncStatus('error');
        setError('Hors réseau — données en cache');
      } else {
        setError(err.message ?? 'Impossible de joindre le cabinet');
        setSyncStatus('error');
      }
    }
  }, []);

  useEffect(() => {
    // Charger le cache immédiatement, puis rafraîchir
    MobileStorage.getLastSnapshot().then(cached => {
      if (cached) { setSnapshot(cached); setSyncStatus('success'); }
    });
    fetchSnapshot();
  }, [fetchSnapshot]);

  const openWhatsApp = (phone: string | null, message: string) => {
    if (!phone) return;
    window.open(`https://wa.me/${phone.replace(/\D/g, '')}?text=${encodeURIComponent(message)}`, '_blank');
  };

  const handleLogout = async () => {
    if (window.confirm('Révoquer cet accès ? La clé sera supprimée de ce téléphone.')) {
      await MobileStorage.clearAll();
      window.location.replace('/mobile/onboarding');
    }
  };

  // ── SKELETON ────────────────────────────────────────────────────────────────
  const SkeletonCard = () => (
    <div className="bg-white/5 border border-white/5 rounded-[2rem] p-5 space-y-3 animate-pulse">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-white/10 rounded-2xl" />
        <div className="space-y-2 flex-1">
          <div className="h-3 bg-white/10 rounded-full w-2/3" />
          <div className="h-2 bg-white/5 rounded-full w-1/3" />
        </div>
      </div>
      <div className="h-10 bg-white/5 rounded-2xl" />
    </div>
  );

  // ── AGENDA ──────────────────────────────────────────────────────────────────
  const AgendaView = () => (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between px-1 mb-6">
        <h2 className="text-2xl font-black">Agenda du Jour</h2>
        <span className="px-3 py-1 bg-indigo-500/10 text-indigo-400 rounded-full text-[10px] font-black uppercase tracking-widest">
          {snapshot?.appointments?.length ?? 0} RDV
        </span>
      </div>

      {syncStatus === 'loading' && !snapshot ? (
        <div className="space-y-4"><SkeletonCard /><SkeletonCard /><SkeletonCard /></div>
      ) : !snapshot?.appointments?.length ? (
        <div className="py-20 text-center opacity-30 flex flex-col items-center gap-4">
          <Calendar size={48} />
          <p className="text-sm font-bold">Aucun rendez-vous aujourd'hui</p>
        </div>
      ) : (
        snapshot.appointments.map((apt) => (
          <div key={apt.id} className="bg-white/5 border border-white/5 rounded-[2rem] p-5 flex flex-col gap-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-indigo-500/10 rounded-2xl flex flex-col items-center justify-center text-indigo-400 border border-indigo-500/20">
                  <Clock size={14} />
                  <span className="text-[10px] font-black mt-0.5">{apt.time}</span>
                </div>
                <div>
                  <h3 className="font-bold text-slate-100">{apt.patient_name}</h3>
                  <p className="text-[10px] text-slate-500 font-black uppercase tracking-wider mt-0.5">
                    {apt.motif} · {apt.duration_minutes}min
                  </p>
                </div>
              </div>
              <ChevronRight size={18} className="text-slate-700 mt-2" />
            </div>
            {apt.phone && (
              <div className="flex gap-3">
                <a
                  href={`tel:${apt.phone}`}
                  className="flex-1 py-3 bg-white/5 hover:bg-white/10 rounded-2xl flex items-center justify-center gap-2 transition-all border border-white/5"
                >
                  <Phone size={14} className="text-emerald-400" />
                  <span className="text-[10px] font-black uppercase tracking-widest">Appeler</span>
                </a>
                <button
                  onClick={() => openWhatsApp(apt.phone, `Bonjour ${apt.patient_name}, nous vous confirmons votre RDV de ${apt.time}.`)}
                  className="flex-1 py-3 bg-white/5 hover:bg-white/10 rounded-2xl flex items-center justify-center gap-2 transition-all border border-white/5"
                >
                  <MessageSquare size={14} className="text-indigo-400" />
                  <span className="text-[10px] font-black uppercase tracking-widest">WhatsApp</span>
                </button>
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );

  // ── FINANCE ─────────────────────────────────────────────────────────────────
  const FinanceView = () => {
    const f = snapshot?.finance;
    const debtors = snapshot?.debtors ?? [];
    return (
      <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="px-1">
          <h2 className="text-2xl font-black">Performance</h2>
          <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest mt-1">Cabinet Analytics · Temps réel</p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white/5 p-6 rounded-[2rem] border border-white/5 flex flex-col">
            <div className="w-10 h-10 bg-emerald-500/10 rounded-xl flex items-center justify-center text-emerald-400 mb-4">
              <Wallet size={20} />
            </div>
            {syncStatus === 'loading' && !f ? (
              <div className="h-8 bg-white/10 rounded-full animate-pulse" />
            ) : (
              <>
                <p className="text-2xl font-black tracking-tight">
                  {new Intl.NumberFormat('fr-FR').format(f?.today_revenue ?? 0)}
                </p>
                <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mt-1">Recettes Jour (MAD)</p>
              </>
            )}
          </div>
          <div className="bg-white/5 p-6 rounded-[2rem] border border-white/5 flex flex-col">
            <div className="w-10 h-10 bg-amber-500/10 rounded-xl flex items-center justify-center text-amber-400 mb-4">
              <TrendingUp size={20} />
            </div>
            {syncStatus === 'loading' && !f ? (
              <div className="h-8 bg-white/10 rounded-full animate-pulse" />
            ) : (
              <>
                <div className="flex items-baseline gap-2">
                  <p className="text-2xl font-black tracking-tight">
                    {new Intl.NumberFormat('fr-FR').format(f?.month_revenue ?? 0)}
                  </p>
                  {f?.month_variation != null && (
                    <span className={`text-[10px] font-black flex items-center ${f.month_variation >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {f.month_variation >= 0 ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}
                      {Math.abs(f.month_variation)}%
                    </span>
                  )}
                </div>
                <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mt-1">Recettes Mois</p>
              </>
            )}
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-4 px-1">
            <h3 className="text-sm font-black text-rose-400 uppercase tracking-widest flex items-center gap-2">
              <AlertTriangle size={14} /> Liste Rouge
            </h3>
            <span className="text-[10px] font-bold text-slate-500">{debtors.length} dossiers</span>
          </div>
          {!debtors.length ? (
            <div className="py-10 text-center opacity-20">
              <p className="text-sm font-bold">Aucun impayé</p>
            </div>
          ) : (
            <div className="space-y-3">
              {debtors.map((d) => (
                <div key={d.id} className="bg-rose-500/5 border border-rose-500/10 rounded-2xl p-4 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-200">{d.name}</p>
                    <p className="text-[10px] font-black text-rose-400/60 mt-0.5">
                      {new Intl.NumberFormat('fr-FR').format(d.amount)} MAD
                    </p>
                  </div>
                  {d.phone && (
                    <button
                      onClick={() => openWhatsApp(d.phone, `Bonjour ${d.name}, nous vous contactons concernant un solde en attente de ${d.amount} MAD.`)}
                      className="w-10 h-10 bg-white/5 rounded-xl flex items-center justify-center text-slate-400 hover:text-indigo-400 transition-colors"
                    >
                      <MessageSquare size={16} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  // ── SÉCURITÉ ─────────────────────────────────────────────────────────────────
  const SecuriteView = () => (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-8">
      <div className="px-1">
        <h2 className="text-2xl font-black">Sécurité</h2>
        <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest mt-1">Contrôle Local-First</p>
      </div>

      <div className="bg-indigo-500/5 border border-indigo-500/10 rounded-[2rem] p-8 flex flex-col items-center text-center gap-4">
        <div className="w-20 h-20 bg-indigo-500/10 rounded-3xl flex items-center justify-center text-indigo-400 shadow-xl shadow-indigo-500/10">
          <ShieldCheck size={40} />
        </div>
        <div>
          <p className="text-sm font-bold text-slate-200">Terminal Appairé</p>
          <p className="text-[10px] text-slate-500 mt-2 leading-relaxed">
            Ce téléphone accède directement au cabinet via WiFi local. Aucune donnée ne transite par un serveur cloud.
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 p-4 bg-white/5 rounded-2xl border border-white/5">
        {isOnline ? <Wifi size={18} className="text-emerald-400" /> : <WifiOff size={18} className="text-rose-400" />}
        <div>
          <p className="text-xs font-bold">{isOnline ? 'Réseau disponible' : 'Hors réseau'}</p>
          <p className="text-[10px] text-slate-500 mt-0.5">
            {isOnline ? 'Données en temps réel depuis le cabinet' : 'Affichage du dernier snapshot en cache'}
          </p>
        </div>
      </div>

      <button
        onClick={handleLogout}
        className="w-full py-5 bg-rose-500/10 border border-rose-500/20 text-rose-500 rounded-[2rem] font-black text-xs uppercase tracking-widest flex items-center justify-center gap-3 active:scale-95 transition-all"
      >
        <LogOut size={18} /> Révoquer cet accès
      </button>
    </div>
  );

  // ── LAYOUT PRINCIPAL ──────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col font-outfit pb-24">
      {/* Top Bar */}
      <div className="p-6 pb-0 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
            <Smartphone size={16} />
          </div>
          <span className="text-xs font-black uppercase tracking-[0.2em]">Elite Mobile</span>
        </div>

        <button
          onClick={fetchSnapshot}
          disabled={syncStatus === 'loading'}
          className="flex items-center gap-2 px-3 py-1.5 bg-white/5 rounded-full border border-white/5 disabled:opacity-50"
        >
          <div className={`w-1.5 h-1.5 rounded-full ${
            syncStatus === 'loading' ? 'bg-indigo-400 animate-pulse'
            : syncStatus === 'error' ? 'bg-rose-500'
            : 'bg-emerald-500'
          }`} />
          <RefreshCw size={10} className={`text-slate-400 ${syncStatus === 'loading' ? 'animate-spin' : ''}`} />
          <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">
            {syncStatus === 'loading' ? 'Sync…' : syncStatus === 'error' ? 'Offline' : 'À jour'}
          </span>
        </button>
      </div>

      {/* Error Banner */}
      {error && syncStatus === 'error' && (
        <div className="mx-6 mt-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-center gap-3">
          <WifiOff size={16} className="text-rose-400 shrink-0" />
          <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest">{error}</p>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 p-6 overflow-y-auto">
        {activeTab === 'agenda' && <AgendaView />}
        {activeTab === 'finance' && <FinanceView />}
        {activeTab === 'securite' && <SecuriteView />}
      </main>

      {/* Bottom Nav */}
      <nav className="fixed bottom-6 left-6 right-6 h-20 bg-slate-900/80 backdrop-blur-2xl border border-white/5 rounded-[2.5rem] flex items-center justify-around px-4 shadow-2xl shadow-black">
        {([
          { id: 'agenda', icon: Calendar, label: 'Agenda', activeColor: 'text-indigo-400' },
          { id: 'finance', icon: TrendingUp, label: 'Finance', activeColor: 'text-amber-400' },
          { id: 'securite', icon: ShieldCheck, label: 'Sécurité', activeColor: 'text-indigo-400' },
        ] as const).map(({ id, icon: Icon, label, activeColor }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex flex-col items-center gap-1 transition-all ${
              activeTab === id ? `${activeColor} scale-110` : 'text-slate-600'
            }`}
          >
            <Icon size={22} />
            <span className="text-[9px] font-black uppercase tracking-widest">{label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
};
