import { EliteGhostLoader } from '../../../components/EliteGhostLoader';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface InsightsPanelProps {
  loadingInsights: boolean;
  financialData: any;
}

export const InsightsPanel = ({ loadingInsights, financialData }: InsightsPanelProps) => (
  <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
    {loadingInsights ? (
      <div className="py-20 relative h-[400px]">
        <EliteGhostLoader text="Calcul des indicateurs financiers..." fullScreen={false} size="medium" />
      </div>
    ) : (
      <>
        {/* KPIs Financiers */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm flex flex-col gap-2 relative overflow-hidden group hover:border-primary/20 transition-all">
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Revenu Ce Mois</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-3xl font-black text-slate-800">
                {financialData?.revenue_this_month ? Math.round(financialData.revenue_this_month).toLocaleString('fr-FR') : 0}
              </span>
              <span className="text-xs font-bold text-slate-400 ml-1">MAD</span>
            </div>
          </div>

          <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm flex flex-col gap-2 relative overflow-hidden group hover:border-primary/20 transition-all">
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Revenu Mois Dernier</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-3xl font-black text-slate-800">
                {financialData?.revenue_last_month ? Math.round(financialData.revenue_last_month).toLocaleString('fr-FR') : 0}
              </span>
              <span className="text-xs font-bold text-slate-400 ml-1">MAD</span>
            </div>
          </div>

          <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm flex flex-col gap-2 relative overflow-hidden group hover:border-primary/20 transition-all">
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Taux de Recouvrement</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-3xl font-black text-slate-800">{financialData?.recovery_rate || 0}%</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden">
              <div 
                className="h-full rounded-full transition-all duration-1000" 
                style={{ width: `${financialData?.recovery_rate || 0}%`, backgroundColor: 'var(--primary)' }}
              />
            </div>
          </div>

          <div className="p-8 rounded-[2rem] shadow-xl shadow-primary/10 flex flex-col gap-2 text-white relative overflow-hidden group hover:brightness-105 transition-all" style={{ backgroundColor: 'var(--primary)' }}>
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16 blur-2xl group-hover:scale-125 transition-all duration-700" />
            <span className="text-[10px] font-black text-white/70 uppercase tracking-widest relative z-10">Total Facturé Global</span>
            <div className="flex items-baseline gap-2 mt-1 relative z-10">
              <span className="text-3xl font-black">
                {financialData?.total_billed ? Math.round(financialData.total_billed).toLocaleString('fr-FR') : 0}
              </span>
              <span className="text-xs font-bold text-white/80 ml-1">MAD</span>
            </div>
            <span className="text-[10px] font-medium text-white/70 mt-4 block relative z-10">
              Total encaissé : {financialData?.total_paid ? Math.round(financialData.total_paid).toLocaleString('fr-FR') : 0} MAD
            </span>
          </div>
        </div>

        {/* GRAPHIQUES */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
          {/* 1. Évolution Revenu */}
          <div className="bg-white border border-slate-200/80 p-8 rounded-[2.5rem] shadow-sm flex flex-col h-[400px]">
            <div>
              <h3 className="text-base font-black tracking-tight" style={{ color: 'var(--primary)' }}>Évolution du Revenu</h3>
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-1">Chiffre d'Affaires Mensuel (6 derniers mois)</p>
            </div>
            <div className="flex-1 min-h-0 w-full mt-6">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={financialData?.monthly_revenue || []}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 9, fontWeight: 700, fill: '#94a3b8' }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 9, fontWeight: 700, fill: '#94a3b8' }} />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const item = payload[0];
                        return (
                          <div className="bg-white/95 backdrop-blur-md p-4 rounded-2xl border border-slate-200 shadow-2xl">
                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{item.payload.name}</p>
                            <p className="text-sm font-black text-primary" style={{ color: 'var(--primary)' }}>
                              {(item.value as number).toLocaleString('fr-FR')} MAD
                            </p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar dataKey="revenue" fill="var(--primary)" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 2. Top Actes */}
          <div className="bg-white border border-slate-200/80 p-8 rounded-[2.5rem] shadow-sm flex flex-col h-[400px]">
            <div>
              <h3 className="text-base font-black tracking-tight" style={{ color: 'var(--primary)' }}>Actes les plus rentables</h3>
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-1">Top 5 actes (Chiffre d'Affaires généré)</p>
            </div>
            <div className="flex-1 min-h-0 w-full mt-6">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart layout="vertical" data={financialData?.top_acts_revenue || []}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                  <XAxis type="number" axisLine={false} tickLine={false} tick={{ fontSize: 9, fontWeight: 700, fill: '#94a3b8' }} />
                  <YAxis type="category" dataKey="name" width={100} axisLine={false} tickLine={false} tick={{ fontSize: 9, fontWeight: 700, fill: '#94a3b8' }} />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const item = payload[0];
                        return (
                          <div className="bg-white/95 backdrop-blur-md p-4 rounded-2xl border border-slate-200 shadow-2xl">
                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{item.payload.name}</p>
                            <p className="text-sm font-black text-primary" style={{ color: 'var(--primary)' }}>
                              {(item.value as number).toLocaleString('fr-FR')} MAD
                            </p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar dataKey="value" fill="#8b5cf6" radius={[0, 8, 8, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </>
    )}
  </div>
);
