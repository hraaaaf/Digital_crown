import { Wallet, TrendingUp, ArrowUpRight, ArrowDownRight, Users, AlertTriangle, CheckCircle2, MessageSquare, Download } from 'lucide-react';
import { AreaChart, Area, XAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { cn } from '../../../../utils/cn';
import { fmt, dayLabel } from '../utils';
import type { Snapshot, SyncStatus } from '../types';
import { Skeleton } from '../components/Skeleton';

export function FinanceView({
  snapshot,
  syncStatus,
  selectedDate,
  openWhatsApp,
  handleExportPDF
}: {
  snapshot: Snapshot | null;
  syncStatus: SyncStatus;
  selectedDate: string;
  openWhatsApp: (phone: string | null, msg: string) => void;
  handleExportPDF: () => void;
}) {
  const f = snapshot?.finance;

  return (
    <div className="space-y-6">
      {/* KPI grid */}
      <div className="grid grid-cols-2 gap-3">
        {/* Today */}
        <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[24px] p-5 shadow-elite" style={{ background: 'linear-gradient(135deg, var(--primary), var(--secondary))' }}>
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
        <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[24px] p-5 shadow-elite">
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
        <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[24px] p-5 shadow-elite">
          <div className="w-8 h-8 bg-emerald-500/10 rounded-[12px] flex items-center justify-center text-emerald-600 mb-3 border border-emerald-500/20">
            <Users size={16} />
          </div>
          <p className="text-xl font-black tracking-tight text-text-main font-outfit">{f?.total_patients ?? '—'}</p>
          <p className="text-[9px] font-black text-text-muted uppercase tracking-widest mt-1">Patients</p>
        </div>
        {/* Total debt */}
        <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[24px] p-5 shadow-elite">
          <div className="w-8 h-8 bg-rose-500/10 rounded-[12px] flex items-center justify-center text-rose-500 mb-3 border border-rose-500/20">
            <AlertTriangle size={16} />
          </div>
          <p className="text-xl font-black tracking-tight text-rose-500 font-outfit">{fmt(f?.total_debt ?? 0)}</p>
          <p className="text-[9px] font-black text-text-muted uppercase tracking-widest mt-1">Créances</p>
        </div>
      </div>

      {/* 7-day chart */}
      {f?.weekly_revenue && f.weekly_revenue.length > 0 && (
        <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[24px] p-6 shadow-elite">
          <div className="flex items-center justify-between mb-6 border-b border-border-main pb-4">
            <div>
              <p className="text-[9px] font-black text-text-muted uppercase tracking-[0.2em]">Intelligence Analytique</p>
              <h4 className="text-lg font-black text-primary font-outfit mt-0.5">Activité 7 Jours</h4>
            </div>
            <span className="text-[9px] font-black text-text-muted uppercase tracking-wider">MAD</span>
          </div>
          <div className="h-[140px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={f.weekly_revenue}>
                <defs>
                  <linearGradient id="colorAmountMobile" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis 
                  dataKey="date" 
                  axisLine={false} 
                  tickLine={false} 
                  tickFormatter={(val, i) => dayLabel(val, i, f.weekly_revenue.length)}
                  tick={{ fontSize: 9, fontWeight: 900, fill: '#94a3b8' }} 
                  dy={10} 
                />
                <Tooltip
                  cursor={{ stroke: 'var(--primary)', strokeWidth: 1, strokeDasharray: '4 4', opacity: 0.2 }}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="bg-white/95 backdrop-blur-md p-3 rounded-[16px] border border-border-main shadow-elite">
                          <p className="text-[9px] font-black text-text-muted uppercase tracking-widest mb-1">
                            {new Date(payload[0].payload.date).toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short' })}
                          </p>
                          <p className="text-sm font-black text-primary">{(payload[0].value as number).toLocaleString('fr-FR')} MAD</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Area type="monotone" dataKey="amount" stroke="var(--primary)" strokeWidth={3} fillOpacity={1} fill="url(#colorAmountMobile)" animationDuration={1000} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Debtors */}
      <div>
        <h2 className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-3 px-1 flex items-center gap-2">
          <AlertTriangle size={14} className="text-rose-500" /> Liste Rouge
          <span className="ml-auto">{snapshot?.debtors.length ?? 0} dossiers</span>
        </h2>
        {!snapshot?.debtors.length ? (
          <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[24px] py-12 text-center shadow-elite">
            <CheckCircle2 size={32} className="mx-auto mb-3 text-emerald-500" />
            <p className="text-sm font-black text-text-main font-outfit">Aucun impayé</p>
            <p className="text-text-muted text-[11px] mt-1">Tous les comptes sont à jour.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {snapshot.debtors.map(d => (
              <div
                key={d.id}
                className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[20px] p-4 flex items-center justify-between shadow-elite hover:border-rose-200 transition-all"
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

      <button
        onClick={handleExportPDF}
        className="w-full py-4 bg-primary border border-primary/20 text-white rounded-[24px] font-black text-[11px] uppercase tracking-widest flex items-center justify-center gap-2 active:scale-95 transition-all shadow-elite hover:bg-primary/90"
      >
        <Download size={16} /> Exporter le Bilan PDF du Mois
      </button>
    </div>
  );
}
