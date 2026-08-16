import { Banknote, BarChart2, Phone, TrendingUp } from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '../../../utils/cn';
import { dashboardItemVariants } from '../animations';
import type { ConversionData, LatentCashData, ProjectionData } from '../types';

export const BusinessInsights = ({
  visible,
  conversion,
  projection,
  latentCash,
  onNavigatePatient,
}: {
  visible: boolean;
  conversion: ConversionData | null;
  projection: ProjectionData | null;
  latentCash: LatentCashData | null;
  onNavigatePatient: (patientId: number) => void;
}) => {
  if (!visible || (!conversion && !projection && !latentCash)) return null;

  return (
    <motion.section variants={dashboardItemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {conversion && conversion.devis_count > 0 && (
        <div className="bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-9 h-9 bg-blue-500/10 rounded-elite-sm flex items-center justify-center border border-blue-500/20">
              <TrendingUp size={18} className="text-blue-400" />
            </div>
            <div>
              <h3 className="text-sm font-black text-primary font-outfit uppercase tracking-tight">Taux de Conversion</h3>
              <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest">{conversion.devis_count} devis émis</p>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-end gap-2">
              <span className={cn(
                'text-3xl font-black font-outfit',
                conversion.taux >= 60 ? 'text-emerald-400' : conversion.taux >= 40 ? 'text-amber-400' : 'text-red-400',
              )}>
                {conversion.taux}%
              </span>
              <span className="text-sm text-text-muted font-bold mb-1">de conversion</span>
            </div>
            <div className="w-full bg-slate-200/50 rounded-full h-2">
              <div
                className={cn(
                  'h-2 rounded-full transition-all',
                  conversion.taux >= 60 ? 'bg-emerald-400' : conversion.taux >= 40 ? 'bg-amber-400' : 'bg-red-400',
                )}
                style={{ width: `${Math.min(conversion.taux, 100)}%` }}
              />
            </div>
            <p className="text-[11px] text-text-muted font-medium">
              {conversion.converted_count} / {conversion.devis_count} devis suivis d'un acte
              {conversion.avg_days ? ` · délai moyen ${conversion.avg_days}j` : ''}
            </p>
          </div>
        </div>
      )}

      {projection && (
        <div className="bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-9 h-9 bg-violet-500/10 rounded-elite-sm flex items-center justify-center border border-violet-500/20">
              <BarChart2 size={18} className="text-violet-400" />
            </div>
            <div>
              <h3 className="text-sm font-black text-primary font-outfit uppercase tracking-tight">Projection Mensuelle</h3>
              <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest">Moy. {projection.avg_monthly.toLocaleString('fr-FR')} MAD/mois</p>
            </div>
          </div>
          <div className="space-y-1.5 max-h-52 overflow-y-auto">
            {[...projection.historical, ...projection.projections].map(entry => (
              <div key={entry.month} className="flex items-center justify-between text-[11px]">
                <span className="font-bold text-text-muted">{entry.month}</span>
                <div className="flex items-center gap-2">
                  <span className={cn('font-black', entry.type === 'actual' ? 'text-primary' : 'text-violet-400')}>
                    {entry.revenue.toLocaleString('fr-FR')} MAD
                  </span>
                  <span className={cn(
                    'text-[9px] font-black px-1.5 py-0.5 rounded-full uppercase tracking-wider',
                    entry.type === 'actual' ? 'bg-slate-100 text-slate-500' : 'bg-violet-500/10 text-violet-500',
                  )}>
                    {entry.type === 'actual' ? 'réel' : 'estimé'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {latentCash && latentCash.total_opportunites > 0 && (
        <div className="bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-purple-500/10 rounded-elite-sm flex items-center justify-center border border-purple-500/20">
                <Banknote size={18} className="text-purple-400" />
              </div>
              <div>
                <h3 className="text-sm font-black text-primary font-outfit uppercase tracking-tight">Ghost Re-Call (Cash Latent)</h3>
                <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest">{latentCash.total_opportunites} Opportunités</p>
              </div>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-end gap-2">
              <span className="text-3xl font-black text-purple-400 font-outfit">{latentCash.valeur_totale_latente.toLocaleString('fr-FR')}</span>
              <span className="text-sm text-text-muted font-bold mb-1">MAD récupérables</span>
            </div>
            <p className="text-[11px] text-text-muted font-medium mb-3">Devis signés de plus de 15 jours sans actes commencés.</p>
            <div className="space-y-2 max-h-40 overflow-y-auto pr-2 custom-scrollbar">
              {latentCash.opportunites.map((opportunity, index) => (
                <div
                  key={`${opportunity.patient_id}-${index}`}
                  className="flex items-center justify-between p-2.5 bg-slate-50 border border-slate-100 rounded-xl hover:bg-purple-50 hover:border-purple-200 transition-all cursor-pointer"
                  onClick={() => onNavigatePatient(opportunity.patient_id)}
                >
                  <div>
                    <p className="text-xs font-black text-slate-800">{opportunity.patient_name}</p>
                    <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mt-0.5">{opportunity.type} • {opportunity.date_devis}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-black text-purple-600">{opportunity.montant.toLocaleString('fr-FR')} <span className="text-[9px] text-purple-400">MAD</span></p>
                    <a
                      href={`tel:${opportunity.telephone}`}
                      onClick={event => event.stopPropagation()}
                      className="text-[10px] text-emerald-500 hover:text-emerald-600 font-bold flex items-center gap-1 justify-end mt-0.5"
                    >
                      <Phone size={10} /> Appeler
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </motion.section>
  );
};
