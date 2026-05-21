import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Calendar, TrendingUp, ShieldCheck, Phone, MessageSquare,
  Clock, Wallet, ArrowUpRight, ArrowDownRight, RefreshCw,
  Wifi, WifiOff, LogOut, Users, AlertTriangle, CheckCircle2,
  PlayCircle, XCircle, ChevronRight, Stethoscope, FileText,
} from 'lucide-react';
import { MobileStorage } from '../../../services/zka/MobileStorage';
import { cn } from '../../../utils/cn';

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

const STATUS_META: Record<ApptStatus, { label: string; className: string; icon: React.ReactNode }> = {
  PLANIFIE: {
    label: 'Planifié',
    className: 'bg-slate-100 text-slate-600 border-slate-200',
    icon: <Clock size={11} />,
  },
  EN_COURS: {
    label: 'En cours',
    className: 'bg-primary/10 text-primary border-primary/20 animate-pulse',
    icon: <PlayCircle size={11} />,
  },
  TERMINE: {
    label: 'Terminé',
    className: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20',
    icon: <CheckCircle2 size={11} />,
  },
  ANNULE: {
    label: 'Annulé',
    className: 'bg-rose-500/10 text-rose-500 border-rose-500/20',
    icon: <XCircle size={11} />,
  },
};

// ── MINI BAR CHART ────────────────────────────────────────────────────────────

function MiniBarChart({ data }: { data: WeekDay[] }) {
  const max = Math.max(...data.map(d => d.amount), 1);
  return (
    <div className="flex items-end gap-1.5 h-20">
      {data.map((d, i) => {
        const pct = Math.max((d.amount / max) * 100, d.amount > 0 ? 8 : 3);
        const isToday = i === data.length - 1;
        return (
          <div key={d.date} className="flex-1 flex flex-col items-center gap-1.5">
            <div
              className={cn(
                'w-full rounded-lg transition-all duration-700',
                isToday ? 'bg-primary' : 'bg-primary/20'
              )}
              style={{ height: `${pct}%` }}
            />
            <span className={cn(
              'text-[8px] font-black uppercase',
              isToday ? 'text-primary' : 'text-text-muted'
            )}>
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
    <div className="bg-card border border-border-main rounded-[24px] overflow-hidden shadow-elite transition-all duration-300">
      <button
        className="w-full flex items-center gap-4 p-5 text-left hover:bg-primary/[0.02] transition-colors"
        onClick={() => setExpanded(e => !e)}
      >
        {/* Time bubble */}
        <div className="w-14 h-14 bg-primary/5 border border-primary/10 rounded-[16px] flex flex-col items-center justify-center shrink-0">
          <Stethoscope size={12} className="text-primary mb-0.5" />
          <span className="text-[11px] font-black text-primary leading-none">{apt.time}</span>
        </div>

        <div className="flex-1 min-w-0">
          <p className="font-black text-text-main font-outfit truncate leading-tight">{apt.patient_name}</p>
          <p className="text-[10px] text-text-muted font-bold mt-0.5 uppercase tracking-wider truncate">
            {apt.motif} · {apt.duration_minutes}min
          </p>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          <span className={cn(
            'flex items-center gap-1 px-2 py-1 rounded-lg border text-[9px] font-black uppercase tracking-widest',
            meta.className
          )}>
            {meta.icon} {meta.label}
          </span>
          <ChevronRight size={14} className={cn('text-text-muted transition-transform', expanded ? 'rotate-90' : '')} />
        </div>
      </button>

      {expanded && (
        <div className="px-5 pb-5 space-y-3 border-t border-border-main pt-4">
          {nextStatuses.length > 0 && (
            <div className="flex gap-2">
              {nextStatuses.map(s => {
                const sm = STATUS_META[s];
                return (
                  <button
                    key={s}
                    onClick={() => onStatusChange(apt.id, s)}
                    className={cn(
                      'flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-[16px] border text-[10px] font-black uppercase tracking-widest transition-all active:scale-95',
                      sm.className
                    )}
                  >
                    {sm.icon} {sm.label}
                  </button>
                );
              })}
            </div>
          )}

          {apt.phone && (
            <div className="flex gap-2">
              <a
                href={`tel:${apt.phone}`}
                className="flex-1 flex items-center justify-center gap-1.5 py-2.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 rounded-[16px] text-[10px] font-black uppercase tracking-widest"
              >
                <Phone size={12} /> Appeler
              </a>
              <button
                onClick={() => onWhatsApp(apt.phone, `Bonjour ${apt.patient_name}, nous vous confirmons votre RDV de ${apt.time}.`)}
                className="flex-1 flex items-center justify-center gap-1.5 py-2.5 bg-primary/5 border border-primary/10 text-primary rounded-[16px] text-[10px] font-black uppercase tracking-widest"
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
  return <div className={cn('bg-border-main/40 rounded-[16px] animate-pulse', className)} />;
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

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 30000);
    return () => clearInterval(t);
  }, []);

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
    <div className="space-y-4">
      {/* Progress bar */}
      {totalCount > 0 && (
        <div className="bg-card border border-border-main rounded-[20px] p-4 shadow-elite">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-black text-text-muted uppercase tracking-widest flex items-center gap-1.5">
              <Clock size={12} /> Progression du jour
            </span>
            <span className="text-[10px] font-black text-primary">{termineCount}/{totalCount} terminés</span>
          </div>
          <div className="h-1.5 bg-border-main rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary to-secondary rounded-full transition-all duration-700"
              style={{ width: `${(termineCount / totalCount) * 100}%` }}
            />
          </div>
        </div>
      )}

      {syncStatus === 'loading' && !snapshot ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-24" />)}
        </div>
      ) : !snapshot?.appointments.length ? (
        <div className="bg-card border border-border-main rounded-[24px] py-20 text-center shadow-elite">
          <div className="w-16 h-16 bg-primary/5 border border-primary/10 rounded-[20px] flex items-center justify-center mx-auto mb-4 text-primary">
            <Calendar size={32} />
          </div>
          <h4 className="font-black text-primary font-outfit">Aucun RDV aujourd'hui</h4>
          <p className="text-text-muted text-[11px] font-medium mt-1">L'agenda est libre.</p>
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
    <div className="space-y-6">
      {/* KPI grid */}
      <div className="grid grid-cols-2 gap-3">
        {/* Today */}
        <div className="bg-card border border-border-main rounded-[24px] p-5 shadow-elite" style={{ background: 'linear-gradient(135deg, var(--primary), var(--secondary))' }}>
          <div className="w-8 h-8 bg-white/20 backdrop-blur-md rounded-[12px] flex items-center justify-center text-white mb-3 border border-white/30">
            <Wallet size={16} />
          </div>
          {syncStatus === 'loading' && !f
            ? <Skeleton className="h-8 w-24 bg-white/20" />
            : <>
                <p className="text-xl font-black tracking-tight text-white font-outfit">{fmt(f?.today_revenue ?? 0)}</p>
                <p className="text-[9px] font-black text-white/70 uppercase tracking-widest mt-1">Recettes Jour</p>
              </>
          }
        </div>
        {/* Month */}
        <div className="bg-card border border-border-main rounded-[24px] p-5 shadow-elite">
          <div className="w-8 h-8 bg-amber-500/10 rounded-[12px] flex items-center justify-center text-amber-600 mb-3 border border-amber-500/20">
            <TrendingUp size={16} />
          </div>
          {syncStatus === 'loading' && !f
            ? <Skeleton className="h-8 w-24" />
            : <>
                <div className="flex items-baseline gap-1.5">
                  <p className="text-xl font-black tracking-tight text-text-main font-outfit">{fmt(f?.month_revenue ?? 0)}</p>
                  {f?.month_variation != null && (
                    <span className={cn('text-[9px] font-black flex items-center', f.month_variation >= 0 ? 'text-emerald-500' : 'text-rose-500')}>
                      {f.month_variation >= 0 ? <ArrowUpRight size={9} /> : <ArrowDownRight size={9} />}
                      {Math.abs(f.month_variation)}%
                    </span>
                  )}
                </div>
                <p className="text-[9px] font-black text-text-muted uppercase tracking-widest mt-1">Recettes Mois</p>
              </>
          }
        </div>
        {/* Patients */}
        <div className="bg-card border border-border-main rounded-[24px] p-5 shadow-elite">
          <div className="w-8 h-8 bg-emerald-500/10 rounded-[12px] flex items-center justify-center text-emerald-600 mb-3 border border-emerald-500/20">
            <Users size={16} />
          </div>
          <p className="text-xl font-black tracking-tight text-text-main font-outfit">{f?.total_patients ?? '—'}</p>
          <p className="text-[9px] font-black text-text-muted uppercase tracking-widest mt-1">Patients</p>
        </div>
        {/* Total debt */}
        <div className="bg-card border border-border-main rounded-[24px] p-5 shadow-elite">
          <div className="w-8 h-8 bg-rose-500/10 rounded-[12px] flex items-center justify-center text-rose-500 mb-3 border border-rose-500/20">
            <AlertTriangle size={16} />
          </div>
          <p className="text-xl font-black tracking-tight text-rose-500 font-outfit">{fmt(f?.total_debt ?? 0)}</p>
          <p className="text-[9px] font-black text-text-muted uppercase tracking-widest mt-1">Créances</p>
        </div>
      </div>

      {/* 7-day bar chart */}
      {f?.weekly_revenue && f.weekly_revenue.length > 0 && (
        <div className="bg-card border border-border-main rounded-[24px] p-6 shadow-elite">
          <div className="flex items-center justify-between mb-4 border-b border-border-main pb-4">
            <div>
              <p className="text-[9px] font-black text-text-muted uppercase tracking-[0.2em]">Intelligence Analytique</p>
              <h4 className="text-lg font-black text-primary font-outfit mt-0.5">Activité 7 Jours</h4>
            </div>
            <span className="text-[9px] font-black text-text-muted uppercase tracking-wider">MAD</span>
          </div>
          <MiniBarChart data={f.weekly_revenue} />
        </div>
      )}

      {/* Debtors */}
      <div>
        <h2 className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-3 px-1 flex items-center gap-2">
          <AlertTriangle size={14} className="text-rose-500" /> Liste Rouge
          <span className="ml-auto">{snapshot?.debtors.length ?? 0} dossiers</span>
        </h2>
        {!snapshot?.debtors.length ? (
          <div className="bg-card border border-border-main rounded-[24px] py-12 text-center shadow-elite">
            <CheckCircle2 size={32} className="mx-auto mb-3 text-emerald-500" />
            <p className="text-sm font-black text-text-main font-outfit">Aucun impayé</p>
            <p className="text-text-muted text-[11px] mt-1">Tous les comptes sont à jour.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {snapshot.debtors.map(d => (
              <div
                key={d.id}
                className="bg-card border border-border-main rounded-[20px] p-4 flex items-center justify-between shadow-elite hover:border-rose-200 transition-all"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-primary/10 border border-primary/20 rounded-[12px] flex items-center justify-center font-black text-primary font-outfit">
                    {d.name.charAt(0)}
                  </div>
                  <div>
                    <p className="text-sm font-black text-text-main">{d.name}</p>
                    <p className="text-[10px] font-black text-rose-500 mt-0.5">{fmt(d.amount)} MAD</p>
                  </div>
                </div>
                {d.phone && (
                  <button
                    onClick={() => openWhatsApp(d.phone, `Bonjour ${d.name}, nous vous contactons concernant un solde en attente de ${fmt(d.amount)} MAD.`)}
                    className="w-10 h-10 bg-primary/5 border border-primary/10 rounded-[12px] flex items-center justify-center text-primary hover:bg-primary hover:text-white transition-all active:scale-95"
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
    <div className="space-y-5">
      {/* Shield card */}
      <div className="relative overflow-hidden rounded-[32px] p-8 flex flex-col items-center text-center gap-5 shadow-elite-hover" style={{ backgroundImage: 'linear-gradient(135deg, var(--primary), var(--secondary))' }}>
        <div className="absolute top-0 right-0 w-48 h-48 bg-white/10 rounded-full -mr-24 -mt-24 blur-3xl" />
        <div className="w-20 h-20 bg-white/20 backdrop-blur-md border border-white/30 rounded-[24px] flex items-center justify-center text-white shadow-xl z-10">
          <ShieldCheck size={40} />
        </div>
        <div className="z-10">
          <p className="font-black text-white text-xl font-outfit">Terminal Appairé</p>
          <p className="text-[11px] text-white/70 mt-2 leading-relaxed max-w-xs">
            Accès direct au cabinet via réseau local. Aucune donnée ne transite par un serveur cloud.
          </p>
        </div>
        <div className="w-full flex items-center justify-center gap-2 py-2.5 bg-white/10 border border-white/20 rounded-[16px] z-10">
          <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
          <span className="text-[10px] font-black text-white uppercase tracking-widest">Zero-Knowledge · AES-256</span>
        </div>
      </div>

      {/* Status cards */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-card border border-border-main rounded-[20px] p-4 shadow-elite">
          <div className="flex items-center gap-2 mb-3">
            {isOnline
              ? <Wifi size={14} className="text-emerald-500" />
              : <WifiOff size={14} className="text-rose-500" />
            }
            <span className="text-[9px] font-black text-text-muted uppercase tracking-widest">Réseau</span>
          </div>
          <p className={cn('text-xs font-black', isOnline ? 'text-emerald-600' : 'text-rose-500')}>
            {isOnline ? 'En ligne' : 'Hors ligne'}
          </p>
          <p className="text-[9px] text-text-muted mt-0.5 font-bold">
            {isOnline ? 'Temps réel' : 'Cache local'}
          </p>
        </div>
        <div className="bg-card border border-border-main rounded-[20px] p-4 shadow-elite">
          <div className="flex items-center gap-2 mb-3">
            <RefreshCw size={14} className="text-primary" />
            <span className="text-[9px] font-black text-text-muted uppercase tracking-widest">Sync</span>
          </div>
          <p className="text-xs font-black text-text-main">
            {syncStatus === 'success' ? 'À jour' : syncStatus === 'loading' ? 'En cours…' : 'En attente'}
          </p>
          <p className="text-[9px] text-text-muted mt-0.5 font-bold">
            {snapshot ? new Date(snapshot.generated_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : '—'}
          </p>
        </div>
      </div>

      {/* Status system pill */}
      <div className="bg-card border border-border-main rounded-[20px] p-4 shadow-elite flex items-center gap-3">
        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        <div>
          <p className="text-[10px] font-black text-text-muted uppercase tracking-widest">Status Système</p>
          <p className="text-sm font-black text-text-main">Elite Cloud Connecté</p>
        </div>
        <FileText size={16} className="ml-auto text-text-muted" />
      </div>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="w-full py-5 bg-rose-500/5 border border-rose-200 text-rose-500 rounded-[24px] font-black text-xs uppercase tracking-widest flex items-center justify-center gap-3 active:scale-95 transition-all hover:bg-rose-50"
      >
        <LogOut size={16} /> Révoquer cet accès
      </button>
    </div>
  );

  // ── MAIN LAYOUT ───────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-background text-text-main flex flex-col font-outfit pb-28 select-none">

      {/* ── HEADER ── */}
      <div className="px-6 pt-14 pb-6">
        {/* Top row */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3 bg-card/60 backdrop-blur-md px-4 py-2 rounded-[16px] border border-border-main shadow-elite">
            <Calendar size={16} className="text-primary" />
            <p className="text-text-muted font-bold text-sm capitalize">{todayStr}</p>
          </div>

          <button
            onClick={fetchSnapshot}
            disabled={syncStatus === 'loading'}
            className="flex items-center gap-1.5 px-3 py-2 bg-card border border-border-main rounded-[12px] shadow-elite disabled:opacity-40 active:scale-95 transition-all hover:bg-primary/5"
          >
            <div className={cn(
              'w-1.5 h-1.5 rounded-full',
              syncStatus === 'loading' ? 'bg-primary animate-pulse'
              : syncStatus === 'error' ? 'bg-rose-500'
              : 'bg-emerald-500'
            )} />
            <RefreshCw size={10} className={cn('text-text-muted', syncStatus === 'loading' ? 'animate-spin' : '')} />
            <span className="text-[9px] font-black text-text-muted uppercase tracking-widest">
              {syncStatus === 'loading' ? 'Sync…' : syncStatus === 'error' ? 'Offline' : 'Live'}
            </span>
          </button>
        </div>

        {/* Greeting */}
        <div>
          <h1 className="text-4xl font-black tracking-tight text-primary font-outfit leading-none">
            {greeting()},
          </h1>
          <p className="text-lg font-bold text-text-muted mt-1">{timeStr}</p>
          {totalCount > 0 && (
            <div className="flex items-center gap-2 mt-3">
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/5 border border-primary/10 rounded-full">
                <span className="text-[10px] font-black text-primary">{totalCount} RDV aujourd'hui</span>
              </div>
              {termineCount > 0 && (
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/5 border border-emerald-500/20 rounded-full">
                  <span className="text-[10px] font-black text-emerald-600">{termineCount} terminé{termineCount > 1 ? 's' : ''}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Error banner */}
      {error && syncStatus === 'error' && (
        <div className="mx-6 mb-4 p-3 bg-amber-500/5 border border-amber-200 rounded-[16px] flex items-center gap-3">
          <WifiOff size={14} className="text-amber-500 shrink-0" />
          <p className="text-[10px] font-black text-amber-600 uppercase tracking-widest">{error}</p>
        </div>
      )}

      {/* Content */}
      <main className="flex-1 px-6 overflow-y-auto">
        {activeTab === 'agenda'   && <AgendaView />}
        {activeTab === 'finance'  && <FinanceView />}
        {activeTab === 'securite' && <SecuriteView />}
      </main>

      {/* ── BOTTOM NAV ── */}
      <nav className="fixed bottom-6 left-6 right-6 h-[68px] bg-card/90 backdrop-blur-2xl border border-border-main rounded-[32px] flex items-center justify-around px-6 shadow-elite-hover">
        {([
          {
            id: 'agenda' as Tab,
            icon: Calendar,
            label: 'Agenda',
            dot: totalCount > 0 && termineCount < totalCount,
          },
          {
            id: 'finance' as Tab,
            icon: TrendingUp,
            label: 'Finance',
            dot: false,
          },
          {
            id: 'securite' as Tab,
            icon: ShieldCheck,
            label: 'Sécurité',
            dot: false,
          },
        ]).map(({ id, icon: Icon, label, dot }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={cn(
              'relative flex flex-col items-center gap-1 transition-all duration-200',
              activeTab === id ? 'text-primary scale-105' : 'text-text-muted'
            )}
          >
            {dot && (
              <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />
            )}
            <Icon size={21} />
            <span className="text-[9px] font-black uppercase tracking-widest">{label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
};
