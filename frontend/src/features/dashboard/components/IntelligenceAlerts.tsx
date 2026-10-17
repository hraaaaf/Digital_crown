import { BarChart2, Bell, CheckCheck, Clock } from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '../../../utils/cn';
import { dashboardItemVariants } from '../animations';
import type { ForecastData, ProactiveAlert } from '../types';

export const IntelligenceAlerts = ({
  forecast,
  alerts,
  showForecast,
  showAlerts,
  onNavigatePatient,
  onSnooze,
  onMarkRead,
}: {
  forecast: ForecastData | null;
  alerts: ProactiveAlert[];
  showForecast: boolean;
  showAlerts: boolean;
  onNavigatePatient: (patientId: number) => void;
  onSnooze: (alertId: number) => void;
  onMarkRead: (alertId: number) => void;
}) => {
  const hasForecast = showForecast && Boolean(forecast);
  const hasAlerts = showAlerts && alerts.length > 0;
  if (!hasForecast && !hasAlerts) return null;

  return (
    <motion.section
      variants={dashboardItemVariants}
      className={cn('grid grid-cols-1 gap-8', hasForecast && hasAlerts && 'lg:grid-cols-2')}
    >
      {hasForecast && forecast && (
        <div className="relative overflow-hidden bg-card-bg/65 backdrop-blur-2xl rounded-elite-lg border border-border-main shadow-elite p-6">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 via-white/5 to-transparent pointer-events-none" />
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-9 h-9 bg-emerald-500/10 backdrop-blur-md rounded-elite-sm flex items-center justify-center border border-emerald-500/20">
                <BarChart2 size={18} className="text-emerald-400" />
              </div>
              <div>
                <h3 className="text-sm font-black text-primary font-outfit uppercase tracking-tight">Forecast Semaine</h3>
                <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest">{forecast.rdv_count} RDV planifiés</p>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-end gap-2">
                <span className="text-3xl font-black text-emerald-400 font-outfit">{forecast.forecast_revenue.toLocaleString('fr-FR')}</span>
                <span className="text-sm text-text-muted font-bold mb-1">MAD estimés</span>
              </div>
              <p className="text-[11px] text-text-muted font-medium">
                Basé sur {forecast.rdv_count} RDV × {forecast.avg_per_rdv.toFixed(0)} MAD moyen/RDV (30 derniers jours)
              </p>
            </div>
          </div>
        </div>
      )}

      {hasAlerts && (
        <div className="relative overflow-hidden bg-card-bg/65 backdrop-blur-2xl rounded-elite-lg border border-border-main shadow-elite p-6">
          <div className="absolute inset-0 bg-gradient-to-br from-amber-500/5 via-white/5 to-transparent pointer-events-none" />
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-amber-500/10 backdrop-blur-md rounded-elite-sm flex items-center justify-center border border-amber-500/20">
                  <Bell size={18} className="text-amber-400" />
                </div>
                <div>
                  <h3 className="text-sm font-black text-primary font-outfit uppercase tracking-tight">Alertes à traiter</h3>
                  <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest">
                    {alerts.length} alerte{alerts.length > 1 ? 's' : ''} active{alerts.length > 1 ? 's' : ''}
                  </p>
                </div>
              </div>
              <span className="w-6 h-6 bg-amber-500 text-white rounded-full text-[10px] font-black flex items-center justify-center shadow-sm shadow-amber-500/20">
                {alerts.length}
              </span>
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {alerts.map(alert => (
                <article key={alert.id} data-testid="dashboard-proactive-alert" className="flex items-start gap-3 p-3 bg-card-bg border border-border-main rounded-elite-sm transition-all">
                  <span className={cn(
                    'w-2 h-2 rounded-full shrink-0 mt-2.5',
                    alert.priority === 1 ? 'bg-red-500' : 'bg-amber-400',
                  )} aria-hidden="true" />
                  <div className="flex-1 min-w-0 space-y-1">
                    <p className="text-xs font-black text-text-main">
                      {alert.priority === 1 ? 'Priorité élevée' : 'À traiter'}
                    </p>
                    {alert.patient_id !== null ? (
                      <button
                        type="button"
                        onClick={() => onNavigatePatient(alert.patient_id!)}
                        aria-label={`Ouvrir le dossier pour l’alerte : ${alert.title}`}
                        className="block w-full rounded-md text-left text-sm font-bold text-text-main hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                      >
                        {alert.nom ? <>{alert.nom} {alert.prenom} — </> : null}{alert.title}
                      </button>
                    ) : (
                      <p className="text-sm font-bold text-text-main">{alert.title}</p>
                    )}
                    <p className="text-sm leading-relaxed text-text-main/90 break-words">{alert.action || alert.message}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => onSnooze(alert.id)}
                    className="min-h-10 min-w-10 inline-flex items-center justify-center rounded-lg text-text-main hover:bg-primary/5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                    title="Reporter 24h"
                    aria-label={`Reporter l’alerte ${alert.title} de 24h`}
                  >
                    <Clock size={18} aria-hidden="true" />
                  </button>
                  <button
                    type="button"
                    onClick={() => onMarkRead(alert.id)}
                    className="min-h-10 min-w-10 inline-flex items-center justify-center rounded-lg text-text-main hover:bg-primary/5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                    title="Marquer comme lu"
                    aria-label={`Marquer l’alerte ${alert.title} comme lue`}
                  >
                    <CheckCheck size={18} aria-hidden="true" />
                  </button>
                </article>
              ))}
            </div>
          </div>
        </div>
      )}
    </motion.section>
  );
};