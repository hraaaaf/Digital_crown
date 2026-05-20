import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Calendar, TrendingUp, ShieldCheck, Phone, MessageSquare,
  Clock, Wallet, ArrowUpRight, ArrowDownRight, RefreshCw,
  Wifi, WifiOff, LogOut, Users, AlertTriangle, CheckCircle2,
  PlayCircle, XCircle, ChevronRight, Stethoscope,
} from 'lucide-react';
import { MobileStorage } from '../../../services/zka/MobileStorage';

type Tab = 'agenda' | 'finance' | 'securite';
type SyncStatus = 'idle' | 'loading' | 'success' | 'error';
type ApptStatus = 'PLANIFIE' | 'EN_COURS' | 'TERMINE' | 'ANNULE';

interface WeekDay { date: string; amount: number }
interface Appointment {
  id: number; time: string; patient_name: string;
  phone: string | null; motif: string;
  status: ApptStatus | null; duration_minutes: number;
}
interface Snapshot {
  generated_at: string;
  appointments: Appointment[];
  finance: {
    today_revenue: number; month_revenue: number;
    month_variation: number | null; appointments_count: number;
    weekly_revenue: WeekDay[]; total_patients: number; total_debt: number;
  };
  debtors: { id: number; name: string; amount: number; phone: string | null }[];
}

// ── HELPERS ──────────────────────────────────────────────────────────────────

function greeting(): string {
  const h = new Date().getHours();
  if (h < 12) return 'Bonjour';
  if (h < 18) return 'Bon après-midi';
  return 'Bonsoir';
}

function fmt(n: number) { return new Intl.NumberFormat('fr-FR').format(Math.round(n)); }

function dayLabel(dateStr: string, idx: number, total: number): string {
  if (idx === total - 1) return 'Auj.';
  const d = new Date(dateStr);
  return ['D', 'L', 'M', 'M', 'J', 'V', 'S'][d.getDay()];
}

const STATUS_META: Record<ApptStatus, { label: string; color: string; bg: string; icon: React.ReactNode }> = {
  PLANIFIE:  { label: 'Planifié',  color: 'text-slate-400',   bg: 'bg-slate-500/10 border-slate-500/20',  icon: <Clock size={11} /> },
  EN_COURS:  { label: 'En cours',  color: 'text-indigo-400',  bg: 'bg-indigo-500/15 border-indigo-500/30', icon: <PlayCircle size={11} /> },
  TERMINE:   { label: 'Terminé',   color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20', icon: <CheckCircle2 size={11} /> },
  ANNULE:    { label: 'Annulé',    color: 'text-rose-400',    bg: 'bg-rose-500/10 border-rose-500/20',     icon: <XCircle size={11} /> },
};

// ── MINI BAR CHART ────────────────────────────────────────────────────────────

function MiniBarChart({ data }: { data: WeekDay[] }) {
  const max = Math.max(...data.map(d => d.amount), 1);
  return (
    <div className="flex items-end gap-1.5 h-16">
      {data.map((d, i) => {
        const pct = Math.max((d.amount / max) * 100, d.amount > 0 ? 8 : 3);
        const isToday = i === data.length - 1;
        return (
          <div key={d.date} className="flex-1 flex flex-col items-center gap-1">
            <div
              className={`w-full rounded-lg transition-all duration-700 ${isToday ? 'bg-indigo-400' : 'bg-white/15'}`}
              style={{ height: `${pct}%` }}
            />
            <span className={`text-[8px] font-black uppercase ${isToday ? 'text-indigo-400' : 'text-slate-600'}`}>
              {dayLabel(d.date, i, data.length)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ── APPOINTMENT CARD ──────────────────────────────────────────────────────────

function ApptCard({
  apt, onStatusChange, onWhatsApp,
}: {
  apt: Appointment;
  onStatusChange: (id: number, status: ApptStatus) => void;
  onWhatsApp: (phone: string | null, msg: string) => void;
}) {
  const meta = STATUS_META[apt.status as ApptStatus] ?? STATUS_META.PLANIFIE;
  const [expanded, setExpanded] = useState(false);

  const nextStatuses: ApptStatus[] = apt.status === 'PLANIFIE'
    ? ['EN_COURS', 'ANNULE']
    : apt.status === 'EN_COURS'
    ? ['TERMINE', 'ANNULE']
    : [];

  return (
    <div className="bg-white/[0.04] border border-white/[0.07] rounded-3xl overflow-hidden transition-all duration-300">
      {/* Main row */}
      <button
        className="w-full flex items-center gap-4 p-5 text-left"
        onClick={() => setExpanded(e => !e)}
      >
        {/* Time bubble */}
        <div className="w-14 h-14 bg-indigo-500/10 border border-indigo-500/20 rounded-2xl flex flex-col items-center justify-center shrink-0">
          <Stethoscope size={12} className="text-indigo-400 mb-0.5" />
          <span className="text-[11px] font-black text-indigo-300 leading-none">{apt.time}</span>
        </div>

        <div className="flex-1 min-w-0">
          <p className="font-black text-slate-100 truncate leading-tight">{apt.patient_name}</p>
          <p className="text-[10px] text-slate-500 font-bold mt-0.5 uppercase tracking-wider truncate">
            {apt.motif} · {apt.duration_minutes}min
          </p>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          <span className={`flex items-center gap-1 px-2 py-1 rounded-lg border text-[9px] font-black uppercase tracking-widest ${meta.bg} ${meta.color}`}>
            {meta.icon} {meta.label}
          </span>
          <ChevronRight size={14} className={`text-slate-600 transition-transform ${expanded ? 'rotate-90' : ''}`} />
        </div>
      </button>

      {/* Expanded actions */}
      {expanded && (
        <div className="px-5 pb-5 space-y-3 animate-in fade-in slide-in-from-top-2 duration-200">
          {/* Status actions */}
          {nextStatuses.length > 0 && (
            <div className="flex gap-2">
              {nextStatuses.map(s => {
                const sm = STATUS_META[s];
                return (
                  <button
                    key={s}
                    onClick={() => onStatusChange(apt.id, s)}
                    className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-2xl border text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 ${sm.bg} ${sm.color}`}
                  >
                    {sm.icon} {sm.label}
                  </button>
                );
              })}
            </div>
          )}
          {/* Contact */}
          {apt.phone && (
            <div className="flex gap-2">
              <a
                href={`tel:${apt.phone}`}
                className="flex-1 flex items-center justify-center gap-1.5 py-2.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-2xl text-[10px] font-black uppercase tracking-widest"
              >
                <Phone size={12} /> Appeler
              </a>
              <button
                onClick={() => onWhatsApp(apt.phone, `Bonjour ${apt.patient_name}, nous vous confirmons votre RDV de ${apt.time}.`)}
                className="flex-1 flex items-center justify-center gap-1.5 py-2.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-2xl text-[10px] font-black uppercase tracking-widest"
              >
                <MessageSquare size={12} /> WhatsApp
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── SKELETON ──────────────────────────────────────────────────────────────────

function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`bg-white/[0.06] rounded-2xl animate-pulse ${className}`} />;
}

// ── MAIN COMPONENT ────────────────────────────────────────────────────────────

export const MobileDashboard = () => {
  const [activeTab, setActiveTab] = useState<Tab>('agenda');
  const [syncStatus, setSyncStatus] = useState<SyncStatus>('idle');
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [now, setNow] = useState(new Date());
  const credsRef = useRef<{ access_token: string; api_base_url: string } | null>(null);

  // Live clock
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 30000);
    return () => clearInterval(t);
  }, []);

  // Online/offline
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
      credsRef.current = creds;

      const res = await fetch(`${creds.api_base_url}/api/mobile/snapshot`, {
        headers: { Authorization: `Bearer ${creds.access_token}` },
        signal: AbortSignal.timeout(8000),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? `Erreur ${res.status}`);

      const data: Snapshot = await res.json();
      setSnapshot(data);
      await MobileStorage.saveLastSnapshot(data);
      setError(null);
      setSyncStatus('success');
    } catch {
      const cached = await MobileStorage.getLastSnapshot();
      if (cached) { setSnapshot(cached); setSyncStatus('error'); setError('Hors réseau — données en cache'); }
      else { setError('Impossible de joindre le cabinet'); setSyncStatus('error'); }
    }
  }, []);

  useEffect(() => {
    MobileStorage.getLastSnapshot().then(c => { if (c) { setSnapshot(c); setSyncStatus('success'); } });
    fetchSnapshot();
  }, [fetchSnapshot]);

  const handleStatusChange = async (id: number, status: ApptStatus) => {
    const creds = credsRef.current || await MobileStorage.getCredentials();
    if (!creds) return;
    try {
      await fetch(`${creds.api_base_url}/api/mobile/appointments/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${creds.access_token}` },
        body: JSON.stringify({ status }),
      });
      setSnapshot(prev => prev ? {
        ...prev,
        appointments: prev.appointments.map(a => a.id === id ? { ...a, status } : a),
      } : prev);
    } catch { /* silent */ }
  };

  const openWhatsApp = (phone: string | null, msg: string) => {
    if (!phone) return;
    window.open(`https://wa.me/${phone.replace(/\D/g, '')}?text=${encodeURIComponent(msg)}`, '_blank');
  };

  const handleLogout = async () => {
    if (window.confirm('Révoquer cet accès ? La clé sera supprimée de ce téléphone.')) {
      await MobileStorage.clearAll();
      window.location.replace('/mobile/onboarding');
    }
  };

  const f = snapshot?.finance;
  const todayStr = now.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });
  const timeStr = now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });

  const termineCount = snapshot?.appointments.filter(a => a.status === 'TERMINE').length ?? 0;
  const totalCount = snapshot?.appointments.length ?? 0;

  // ── AGENDA VIEW ──────────────────────────────────────────────────────────────
  const AgendaView = () => (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-3 duration-400">
      {/* Progress bar */}
      {totalCount > 0 && (
        <div className="bg-white/[0.04] border border-white/[0.07] rounded-2xl p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Progression du jour</span>
            <span className="text-[10px] font-black text-indigo-400">{termineCount}/{totalCount}</span>
          </div>
          <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-indigo-400 rounded-full transition-all duration-700"
              style={{ width: `${(termineCount / totalCount) * 100}%` }}
            />
          </div>
        </div>
      )}

      {syncStatus === 'loading' && !snapshot ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-24 rounded-3xl" />)}
        </div>
      ) : !snapshot?.appointments.length ? (
        <div className="py-24 flex flex-col items-center gap-4 opacity-25">
          <Calendar size={52} />
          <p className="text-sm font-black uppercase tracking-widest">Aucun RDV aujourd'hui</p>
        </div>
      ) : (
        snapshot.appointments.map(apt => (
          <ApptCard key={apt.id} apt={apt} onStatusChange={handleStatusChange} onWhatsApp={openWhatsApp} />
        ))
      )}
    </div>
  );

  // ── FINANCE VIEW ─────────────────────────────────────────────────────────────
  const FinanceView = () => (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-3 duration-400">
      {/* KPI grid */}
      <div className="grid grid-cols-2 gap-3">
        {/* Today */}
        <div className="bg-gradient-to-br from-indigo-500/15 to-indigo-500/5 border border-indigo-500/20 rounded-3xl p-5">
          <div className="w-8 h-8 bg-indigo-500/20 rounded-xl flex items-center justify-center text-indigo-400 mb-3">
            <Wallet size={16} />
          </div>
          {syncStatus === 'loading' && !f
            ? <Skeleton className="h-8 w-24" />
            : <>
                <p className="text-xl font-black tracking-tight text-slate-100">{fmt(f?.today_revenue ?? 0)}</p>
                <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mt-1">Recettes Jour</p>
              </>
          }
        </div>
        {/* Month */}
        <div className="bg-gradient-to-br from-amber-500/15 to-amber-500/5 border border-amber-500/20 rounded-3xl p-5">
          <div className="w-8 h-8 bg-amber-500/20 rounded-xl flex items-center justify-center text-amber-400 mb-3">
            <TrendingUp size={16} />
          </div>
          {syncStatus === 'loading' && !f
            ? <Skeleton className="h-8 w-24" />
            : <>
                <div className="flex items-baseline gap-1.5">
                  <p className="text-xl font-black tracking-tight text-slate-100">{fmt(f?.month_revenue ?? 0)}</p>
                  {f?.month_variation != null && (
                    <span className={`text-[9px] font-black flex items-center ${f.month_variation >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {f.month_variation >= 0 ? <ArrowUpRight size={9} /> : <ArrowDownRight size={9} />}
                      {Math.abs(f.month_variation)}%
                    </span>
                  )}
                </div>
                <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mt-1">Recettes Mois</p>
              </>
          }
        </div>
        {/* Patients */}
        <div className="bg-white/[0.04] border border-white/[0.07] rounded-3xl p-5">
          <div className="w-8 h-8 bg-emerald-500/10 rounded-xl flex items-center justify-center text-emerald-400 mb-3">
            <Users size={16} />
          </div>
          <p className="text-xl font-black tracking-tight text-slate-100">{f?.total_patients ?? '—'}</p>
          <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mt-1">Patients</p>
        </div>
        {/* Total debt */}
        <div className="bg-white/[0.04] border border-white/[0.07] rounded-3xl p-5">
          <div className="w-8 h-8 bg-rose-500/10 rounded-xl flex items-center justify-center text-rose-400 mb-3">
            <AlertTriangle size={16} />
          </div>
          <p className="text-xl font-black tracking-tight text-rose-300">{fmt(f?.total_debt ?? 0)}</p>
          <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mt-1">Créances</p>
        </div>
      </div>

      {/* 7-day bar chart */}
      {f?.weekly_revenue && f.weekly_revenue.length > 0 && (
        <div className="bg-white/[0.04] border border-white/[0.07] rounded-3xl p-5">
          <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-4">Activité 7 jours (MAD)</p>
          <MiniBarChart data={f.weekly_revenue} />
        </div>
      )}

      {/* Debtors */}
      <div>
        <div className="flex items-center justify-between mb-3 px-1">
          <p className="text-[9px] font-black text-rose-400 uppercase tracking-widest flex items-center gap-1.5">
            <AlertTriangle size={12} /> Liste Rouge
          </p>
          <span className="text-[9px] text-slate-600 font-bold">{snapshot?.debtors.length ?? 0} dossiers</span>
        </div>
        {!snapshot?.debtors.length ? (
          <div className="py-10 text-center opacity-20">
            <CheckCircle2 size={32} className="mx-auto mb-2" />
            <p className="text-xs font-black uppercase tracking-widest">Aucun impayé</p>
          </div>
        ) : (
          <div className="space-y-2">
            {snapshot.debtors.map(d => (
              <div key={d.id} className="bg-rose-500/[0.05] border border-rose-500/[0.12] rounded-2xl p-4 flex items-center justify-between">
                <div>
                  <p className="text-xs font-black text-slate-200">{d.name}</p>
                  <p className="text-[10px] font-black text-rose-400 mt-0.5">{fmt(d.amount)} MAD</p>
                </div>
                {d.phone && (
                  <button
                    onClick={() => openWhatsApp(d.phone, `Bonjour ${d.name}, nous vous contactons concernant un solde en attente de ${fmt(d.amount)} MAD. Merci de nous contacter.`)}
                    className="w-10 h-10 bg-white/5 rounded-xl flex items-center justify-center text-slate-500 hover:text-indigo-400 transition-colors active:scale-95"
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

  // ── SECURITE VIEW ─────────────────────────────────────────────────────────────
  const SecuriteView = () => (
    <div className="animate-in fade-in slide-in-from-bottom-3 duration-400 space-y-5">
      {/* Shield card */}
      <div className="relative overflow-hidden bg-gradient-to-br from-indigo-500/10 to-indigo-500/5 border border-indigo-500/15 rounded-3xl p-8 flex flex-col items-center text-center gap-5">
        <div className="absolute -top-12 -right-12 w-40 h-40 bg-indigo-500/5 rounded-full blur-2xl" />
        <div className="w-20 h-20 bg-indigo-500/15 border border-indigo-500/25 rounded-3xl flex items-center justify-center text-indigo-400 shadow-xl shadow-indigo-500/10">
          <ShieldCheck size={40} />
        </div>
        <div>
          <p className="font-black text-slate-200 text-lg">Terminal Appairé</p>
          <p className="text-[11px] text-slate-500 mt-2 leading-relaxed max-w-xs">
            Accès direct au cabinet via réseau local. Aucune donnée ne transite par un serveur cloud.
          </p>
        </div>
        <div className="w-full flex items-center justify-center gap-2 py-2.5 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[10px] font-black text-emerald-400 uppercase tracking-widest">Zero-Knowledge · AES-256</span>
        </div>
      </div>

      {/* Status cards */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white/[0.04] border border-white/[0.07] rounded-2xl p-4">
          <div className="flex items-center gap-2 mb-2">
            {isOnline ? <Wifi size={14} className="text-emerald-400" /> : <WifiOff size={14} className="text-rose-400" />}
            <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Réseau</span>
          </div>
          <p className={`text-xs font-black ${isOnline ? 'text-emerald-400' : 'text-rose-400'}`}>
            {isOnline ? 'En ligne' : 'Hors ligne'}
          </p>
          <p className="text-[9px] text-slate-600 mt-0.5">
            {isOnline ? 'Temps réel' : 'Cache local'}
          </p>
        </div>
        <div className="bg-white/[0.04] border border-white/[0.07] rounded-2xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <RefreshCw size={14} className="text-indigo-400" />
            <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Sync</span>
          </div>
          <p className="text-xs font-black text-slate-300">
            {syncStatus === 'success' ? 'À jour' : syncStatus === 'loading' ? 'En cours…' : 'En attente'}
          </p>
          <p className="text-[9px] text-slate-600 mt-0.5">
            {snapshot ? new Date(snapshot.generated_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : '—'}
          </p>
        </div>
      </div>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="w-full py-5 bg-rose-500/[0.08] border border-rose-500/20 text-rose-400 rounded-3xl font-black text-xs uppercase tracking-widest flex items-center justify-center gap-3 active:scale-95 transition-all"
      >
        <LogOut size={16} /> Révoquer cet accès
      </button>
    </div>
  );

  // ── MAIN LAYOUT ───────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col font-outfit pb-28 select-none">

      {/* ── HEADER ── */}
      <div className="px-6 pt-14 pb-6">
        {/* Top row */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-indigo-500/15 border border-indigo-500/20 flex items-center justify-center">
              <span className="text-indigo-400 font-black text-sm">DC</span>
            </div>
            <div>
              <p className="text-[9px] font-black text-slate-600 uppercase tracking-[0.2em]">Digital Crown Elite</p>
              <p className="text-[9px] font-bold text-slate-500">{timeStr}</p>
            </div>
          </div>

          <button
            onClick={fetchSnapshot}
            disabled={syncStatus === 'loading'}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white/[0.05] border border-white/[0.07] rounded-full disabled:opacity-40 active:scale-95 transition-all"
          >
            <div className={`w-1.5 h-1.5 rounded-full ${syncStatus === 'loading' ? 'bg-indigo-400 animate-pulse' : syncStatus === 'error' ? 'bg-rose-400' : 'bg-emerald-400'}`} />
            <RefreshCw size={10} className={`text-slate-500 ${syncStatus === 'loading' ? 'animate-spin' : ''}`} />
            <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">
              {syncStatus === 'loading' ? 'Sync…' : syncStatus === 'error' ? 'Offline' : 'Live'}
            </span>
          </button>
        </div>

        {/* Greeting */}
        <div>
          <p className="text-3xl font-black tracking-tight leading-none">
            {greeting()},
          </p>
          <p className="text-3xl font-black tracking-tight text-indigo-400 leading-tight capitalize mt-0.5">
            Docteur.
          </p>
          <div className="flex items-center gap-2 mt-3">
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-white/[0.04] border border-white/[0.07] rounded-full">
              <Calendar size={11} className="text-indigo-400" />
              <span className="text-[10px] font-bold text-slate-400 capitalize">{todayStr}</span>
            </div>
            {totalCount > 0 && (
              <div className="px-3 py-1.5 bg-indigo-500/10 border border-indigo-500/20 rounded-full">
                <span className="text-[10px] font-black text-indigo-400">{totalCount} RDV</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Error banner */}
      {error && syncStatus === 'error' && (
        <div className="mx-6 mb-4 p-3 bg-amber-500/10 border border-amber-500/20 rounded-2xl flex items-center gap-3">
          <WifiOff size={14} className="text-amber-400 shrink-0" />
          <p className="text-[10px] font-black text-amber-400 uppercase tracking-widest">{error}</p>
        </div>
      )}

      {/* Content */}
      <main className="flex-1 px-6 overflow-y-auto">
        {activeTab === 'agenda'   && <AgendaView />}
        {activeTab === 'finance'  && <FinanceView />}
        {activeTab === 'securite' && <SecuriteView />}
      </main>

      {/* ── BOTTOM NAV ── */}
      <nav className="fixed bottom-6 left-6 right-6 h-[68px] bg-slate-900/90 backdrop-blur-2xl border border-white/[0.07] rounded-[2rem] flex items-center justify-around px-6 shadow-2xl shadow-black/50">
        {([
          { id: 'agenda',   icon: Calendar,    label: 'Agenda',   accent: 'text-indigo-400', dot: totalCount > 0 && termineCount < totalCount },
          { id: 'finance',  icon: TrendingUp,  label: 'Finance',  accent: 'text-amber-400',  dot: false },
          { id: 'securite', icon: ShieldCheck, label: 'Sécurité', accent: 'text-indigo-400', dot: false },
        ] as const).map(({ id, icon: Icon, label, accent, dot }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`relative flex flex-col items-center gap-1 transition-all duration-200 ${activeTab === id ? `${accent} scale-105` : 'text-slate-600'}`}
          >
            {dot && (
              <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-indigo-400 rounded-full" />
            )}
            <Icon size={21} />
            <span className="text-[9px] font-black uppercase tracking-widest">{label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
};
