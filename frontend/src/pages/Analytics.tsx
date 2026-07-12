import React, { Suspense, lazy } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { Activity, TrendingUp, AlertTriangle, Users, MessageCircle, Clock, Download } from 'lucide-react';
import { DigitalCrownLoader } from '../components/DigitalCrownLoader';
import toast from 'react-hot-toast';

const downloadCSV = (rows: string[][], filename: string) => {
  const content = rows.map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(';')).join('\r\n');
  const blob = new Blob(['﻿' + content], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
};

// Code Splitting for Recharts (to avoid blocking the main thread)
const AnalyticsCharts = lazy(() => import('../features/analytics/AnalyticsCharts').then(m => ({ default: m.AnalyticsCharts })));

export const Analytics = () => {
  const [showWaModal, setShowWaModal] = React.useState(false);

  // Récupération des données Financières
  const { data: financialStats, isLoading: isFinLoading } = useQuery({
    queryKey: ['stats', 'financial'],
    queryFn: () => api.get('/stats/financial').then(res => res.data),
    staleTime: 5 * 60 * 1000, // Cache 5 minutes
  });

  // Récupération des données Opérationnelles
  const { data: operationalStats, isLoading: isOpLoading } = useQuery({
    queryKey: ['stats', 'operational'],
    queryFn: () => api.get('/stats/operational').then(res => res.data),
    staleTime: 5 * 60 * 1000,
  });

  if (isFinLoading || isOpLoading) {
    return <DigitalCrownLoader minHeight="min-h-[60vh]" />;
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      {/* HEADER GHOST BRAIN */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400">
            Analytics & Intelligence
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Indicateurs de performance et de rentabilité en temps réel.
          </p>
        </div>
        <button
          onClick={() => {
            if (!financialStats) return;
            const date = new Date().toLocaleDateString('fr-FR');
            const rows: string[][] = [
              ['Rapport Analytics Digital Crown', date],
              [],
              ['KPIs Financiers'],
              ['Indicateur', 'Valeur'],
              ['Revenus ce mois (MAD)', String(financialStats.revenue_this_month ?? 0)],
              ['Revenus mois précédent (MAD)', String(financialStats.revenue_last_month ?? 0)],
              ['Total facturé (MAD)', String(financialStats.total_billed ?? 0)],
              ['Total encaissé (MAD)', String(financialStats.total_paid ?? 0)],
              ['Taux de recouvrement (%)', String(financialStats.recovery_rate ?? 0)],
              [],
              ['Revenus Mensuels (6 derniers mois)'],
              ['Mois', 'Revenus (MAD)'],
              ...(financialStats.monthly_revenue ?? []).map((m: any) => [m.name, String(m.revenue)]),
              [],
              ['Top 5 Actes par Revenu'],
              ['Acte', 'Revenu Total (MAD)'],
              ...(financialStats.top_acts_revenue ?? []).map((a: any) => [a.name, String(a.value)]),
              [],
              ['Top 5 Actes par Fréquence'],
              ['Acte', 'Nombre'],
              ...(financialStats.top_acts_frequency ?? []).map((a: any) => [a.name, String(a.value)]),
            ];
            downloadCSV(rows, `Analytics_${date.replace(/\//g, '-')}.csv`);
            toast.success('Rapport CSV téléchargé');
          }}
          disabled={!financialStats}
          className="flex items-center gap-2 px-5 py-2.5 rounded-2xl text-white font-black uppercase text-[11px] tracking-widest shadow-lg transition-all hover:-translate-y-0.5 active:scale-95 disabled:opacity-50"
          style={{ backgroundColor: 'var(--primary)' }}
        >
          <Download size={15} />
          Exporter CSV
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* BLOC 1 : FINANCES (Latent Cash & Revenus) */}
        <section className="bg-white dark:bg-slate-800 rounded-3xl p-6 shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-green-100 dark:bg-green-900/30 text-green-600 rounded-2xl">
              <TrendingUp size={24} />
            </div>
            <h2 className="text-xl font-bold text-slate-800 dark:text-white">Trésorerie & Revenus</h2>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="p-5 bg-slate-50 dark:bg-slate-900/50 rounded-2xl border border-slate-100 dark:border-slate-700">
              <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Revenus du mois</p>
              <p className="text-2xl font-bold text-slate-800 dark:text-white mt-1">
                {financialStats?.revenu_mois?.toLocaleString('fr-FR')} MAD
              </p>
            </div>
            <div className="p-5 bg-blue-50 dark:bg-blue-900/20 rounded-2xl border border-blue-100 dark:border-blue-800/30 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/10 rounded-full -mr-8 -mt-8 blur-2xl"></div>
              <p className="text-sm font-bold text-blue-600 dark:text-blue-400">Latent Cash</p>
              <p className="text-3xl font-black text-blue-700 dark:text-blue-300 mt-1">
                {financialStats?.latent_cash?.toLocaleString('fr-FR')} MAD
              </p>
              <p className="text-xs font-medium text-blue-500/70 mt-1">Devis non encaissés</p>
            </div>
          </div>

          {/* ACTION BUTTON UX (Sofia) */}
          <div 
            onClick={() => setShowWaModal(true)}
            className="mt-4 p-4 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white flex items-center justify-between group cursor-pointer shadow-lg shadow-blue-600/20 hover:shadow-blue-600/40 transition-all"
          >
            <div>
              <p className="font-bold flex items-center gap-2">
                <MessageCircle size={18} />
                Générer relances WhatsApp (Top 5)
              </p>
              <p className="text-blue-100 text-sm mt-1">
                Le Ghost Brain rédigera des messages personnalisés pour les devis les plus élevés.
              </p>
            </div>
            <div className="bg-white/20 p-2 rounded-xl group-hover:scale-110 transition-transform">
              <TrendingUp size={20} />
            </div>
          </div>
        </section>

        {/* WhatsApp Recovery Modal */}
        {showWaModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in">
            <div className="bg-white dark:bg-slate-800 rounded-3xl p-6 shadow-2xl max-w-lg w-full relative">
              <h3 className="text-2xl font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
                <MessageCircle className="text-green-500" /> Relances intelligentes
              </h3>
              <p className="text-slate-600 dark:text-slate-400 mb-6">
                Le Ghost Brain a identifié {financialStats?.top_relances?.length || 0} patients à fort potentiel de conversion pour récupérer votre Latent Cash.
              </p>
              
              <div className="space-y-3 mb-6 max-h-60 overflow-y-auto pr-2">
                {financialStats?.top_relances?.map((patient: any, idx: number) => {
                  const message = `Bonjour ${patient.prenom}, c'est le cabinet dentaire. Suite à votre devis pour le soin "${patient.soin}" (${patient.montant} MAD), nous avons des créneaux disponibles cette semaine. Souhaitez-vous le planifier ?`;
                  const waLink = `https://wa.me/${patient.telephone.replace(/[^0-9]/g, '')}?text=${encodeURIComponent(message)}`;
                  
                  return (
                    <div key={idx} className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-xl border border-slate-200 dark:border-slate-600 flex items-center justify-between">
                      <div>
                        <p className="font-bold text-slate-800 dark:text-white">{patient.nom} {patient.prenom}</p>
                        <p className="text-sm text-slate-500">{patient.soin} — {patient.montant} MAD</p>
                      </div>
                      <a 
                        href={waLink} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="p-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors flex items-center gap-1 text-sm font-medium"
                      >
                        Envoyer
                      </a>
                    </div>
                  );
                })}
              </div>

              <button 
                onClick={() => setShowWaModal(false)}
                className="w-full py-3 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-white font-bold rounded-xl transition-colors"
              >
                Fermer
              </button>
            </div>
          </div>
        )}

        {/* BLOC 2 : OPERATIONS (Secrétariat & Flux) */}
        <section className="bg-white dark:bg-slate-800 rounded-3xl p-6 shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-amber-100 dark:bg-amber-900/30 text-amber-600 rounded-2xl">
              <Activity size={24} />
            </div>
            <h2 className="text-xl font-bold text-slate-800 dark:text-white">Opérations & Flux</h2>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="p-5 bg-rose-50 dark:bg-rose-900/20 rounded-2xl border border-rose-100 dark:border-rose-800/30">
              <div className="flex items-center gap-2 mb-1">
                <AlertTriangle size={16} className="text-rose-500" />
                <p className="text-sm font-bold text-rose-600 dark:text-rose-400">Taux d'Annulation</p>
              </div>
              <p className="text-3xl font-black text-rose-700 dark:text-rose-300">
                {operationalStats?.no_show_rate}%
              </p>
            </div>

            <div className="p-5 bg-slate-50 dark:bg-slate-900/50 rounded-2xl border border-slate-100 dark:border-slate-700 flex flex-col justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400 flex items-center gap-2">
                  <Clock size={16} /> Attente Estimée
                </p>
                <p className="text-2xl font-bold text-slate-800 dark:text-white mt-1">
                  {operationalStats?.estimated_wait_time_minutes} min
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400 flex items-center gap-2 mt-4">
                  <Users size={16} /> Flux du Jour
                </p>
                <p className="text-xl font-bold text-slate-800 dark:text-white mt-1">
                  {operationalStats?.flux_today} patients
                </p>
              </div>
            </div>
          </div>
        </section>

      </div>

      {/* CHARTS (Asynchronous Lazy Load) */}
      <Suspense fallback={<div className="h-[300px] w-full bg-slate-100 dark:bg-slate-800/50 rounded-3xl animate-pulse"></div>}>
        <AnalyticsCharts />
      </Suspense>

    </div>
  );
};
