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
  handleExportPDF,
  pocketSummaryOnly = false,
}: {
  snapshot: Snapshot | null;
  syncStatus: SyncStatus;
  selectedDate: string;
  openWhatsApp: (phone: string | null, msg: string) => void;
  handleExportPDF: () => void;
  pocketSummaryOnly?: boolean;
}) {
  const f = snapshot?.finance;

  return (
    <div data-mobile-finance className="space-y-6">
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-primary border border-primary rounded-[22px] p-4 shadow-sm" >
          <div className="w-8 h-8 bg-on-primary/15 backdrop-blur-md rounded-[12px] flex items-center justify-center text-on-primary mb-3 border border-on-primary/20">
            <Wallet size={16} />
          </div>
          {syncStatus === 'loading' && !f
            ? <Skeleton className="h-8 w-24 bg-on-primary/15" />
            : <>
                <p className="text-[21px] font-bold tracking-tight text-on-primary ">{fmt(f?.today_revenue ?? 0)}</p>
                <p className="text-[10px] font-semibold text-on-primary/80 uppercase tracking-widest mt-1">Recettes du jour</p>
              </>
          }
        </div>
        <div className="bg-card border border-border-main rounded-[22px] p-4 shadow-sm">
          <div className="w-8 h-8 bg-warning-surface rounded-[12px] flex items-center justify-center text-warning mb-3 border border-warning-border">
            <TrendingUp size={16} />
          </div>
          {syncStatus === 'loading' && !f
            ? <Skeleton className="h-8 w-24" />
            : <>
                <div className="flex items-baseline gap-1.5">
                  <p className="text-[21px] font-bold tracking-tight text-text-main ">{fmt(f?.month_revenue ?? 0)}</p>
                  {f?.month_variation != null && (
                    <span className={cn('text-[10px] font-semibold flex items-center', f.month_variation >= 0 ? 'text-success' : 'text-danger')}>
                      {f.month_variation >= 0 ? <ArrowUpRight size={9} /> : <ArrowDownRight size={9} />}
                      {Math.abs(f.month_variation)}%
                    </span>
                  )}
                </div>
                <p className="text-[10px] font-semibold text-text-muted uppercase tracking-widest mt-1">Recettes du mois</p>
              </>
          }
        </div>
        <div className="bg-card border border-border-main rounded-[22px] p-4 shadow-sm">
          <div className="w-8 h-8 bg-success-surface rounded-[12px] flex items-center justify-center text-success mb-3 border border-success-border">
            <Users size={16} />
          </div>
          <p className="text-[21px] font-bold tracking-tight text-text-main ">{f?.total_patients ?? '—'}</p>
          <p className="text-[10px] font-semibold text-text-muted uppercase tracking-widest mt-1">Patients</p>
        </div>
        <div className="bg-card border border-border-main rounded-[22px] p-4 shadow-sm">
          <div className="w-8 h-8 bg-danger-surface rounded-[12px] flex items-center justify-center text-danger mb-3 border border-danger-border">
            <AlertTriangle size={16} />
          </div>
          <p className="text-[21px] font-bold tracking-tight text-danger ">{fmt(f?.total_debt ?? 0)}</p>
          <p className="text-[10px] font-semibold text-text-muted uppercase tracking-widest mt-1">Créances</p>
        </div>
      </div>

      {pocketSummaryOnly && <div data-mobile-finance-summary className="rounded-[22px] border border-glass-border bg-card px-5 py-4">
        <p className="text-[11px] font-black text-primary">Aperçu financier · lecture seule</p>
        <p className="mt-2 text-[11px] font-semibold leading-relaxed text-text-muted">Rapprochement, édition des écritures, détails des créances et exports restent sur le poste de travail.</p>
      </div>}
      {!pocketSummaryOnly && f?.weekly_revenue && f.weekly_revenue.length > 0 && (
        <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[24px] p-6 shadow-elite">
          <div className="flex items-center justify-between mb-6 border-b border-border-main pb-4">
            <div>
              <p className="text-[10px] font-semibold text-text-muted uppercase tracking-[0.2em]">Activité</p>
              <h4 className="text-lg font-black text-primary  mt-0.5">7 derniers jours</h4>
            </div>
            <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">MAD</span>
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
                  tick={{ fontSize: 9, fontWeight: 900, fill: 'var(--text-muted)' }}
                  dy={10}
                />
                <Tooltip
                  cursor={{ stroke: 'var(--primary)', strokeWidth: 1, strokeDasharray: '4 4', opacity: 0.2 }}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="bg-card backdrop-blur-md p-3 rounded-[16px] border border-border-main shadow-elite">
                          <p className="text-[10px] font-semibold text-text-muted uppercase tracking-widest mb-1">
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

      {!pocketSummaryOnly && <div>
        <h2 className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-3 px-1 flex items-center gap-2">
          <AlertTriangle size={14} className="text-danger" /> Impayés
          <span className="ml-auto">{snapshot?.debtors.length ?? 0} dossiers</span>
        </h2>
        {!snapshot?.debtors.length ? (
          <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[24px] py-12 text-center shadow-elite">
            <CheckCircle2 size={32} className="mx-auto mb-3 text-success" />
            <p className="text-sm font-black text-text-main ">Aucun impayé</p>
            <p className="text-text-muted text-[11px] mt-1">Tous les comptes sont à jour.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {snapshot.debtors.map(d => (
              <div
                key={d.id}
                className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[20px] p-4 flex items-center justify-between shadow-elite hover:border-danger-border transition-all"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-primary/10 border border-primary/20 rounded-[12px] flex items-center justify-center font-black text-primary ">
                    {d.name.charAt(0)}
                  </div>
                  <div>
                    <p className="text-sm font-black text-text-main">{d.name}</p>
                    <p className="text-[10px] font-black text-danger mt-0.5">{fmt(d.amount)} MAD</p>
                  </div>
                </div>
                {d.phone && (
                  <button
                    onClick={() => openWhatsApp(d.phone, 'Bonjour, merci de contacter le cabinet lorsque vous serez disponible.')}
                    type="button"
                    aria-label="Contacter via WhatsApp sans données financières"
                    className="w-10 h-10 bg-primary/5 border border-primary/10 rounded-[12px] flex items-center justify-center text-primary hover:bg-primary hover:text-on-primary transition-all active:scale-95"
                  >
                    <MessageSquare size={16} />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>}

      {!pocketSummaryOnly && <button
        onClick={handleExportPDF}
        className="w-full py-4 bg-primary border border-primary/20 text-on-primary rounded-[24px] font-black text-[11px] uppercase tracking-widest flex items-center justify-center gap-2 active:scale-95 transition-all shadow-elite hover:bg-primary/90"
      >
        <Download size={16} /> Exporter le bilan mensuel en PDF
      </button>}
    </div>
  );
}
