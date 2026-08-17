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
                <div key={alert.id} className="flex items-center gap-3 p-3 bg-white/25 backdrop-blur-md border border-border-main rounded-elite-sm hover:bg-white/40 transition-all group">
                  <div className={cn(
                    'w-2 h-2 rounded-full flex-shrink-0',
                    alert.priority === 1 ? 'bg-red-500' : 'bg-amber-400',
                  )} />
                  <div
                    className={cn('flex-1 min-w-0', alert.patient_id !== null && 'cursor-pointer')}
                    onClick={() => alert.patient_id !== null && onNavigatePatient(alert.patient_id)}
                  >
                    <p className="text-[11px] font-black text-primary truncate">
                      {alert.nom
                        ? <>{alert.nom} {alert.prenom} — <span className="text-amber-500">{alert.title}</span></>
                        : alert.title}
                    </p>
                    <p className="text-[10px] text-text-muted font-medium truncate">{alert.action}</p>
                  </div>
                  <button
                    onClick={() => onSnooze(alert.id)}
                    className="p-1 rounded text-text-muted hover:text-amber-500"
                    title="Reporter 24h"
                    aria-label="Reporter cette alerte de 24h"
                  >
                    <Clock size={14} />
                  </button>
                  <button
                    onClick={() => onMarkRead(alert.id)}
                    className="p-1 rounded text-text-muted hover:text-emerald-400"
                    title="Marquer comme lu"
                    aria-label="Marquer cette alerte comme lue"
                  >
                    <CheckCheck size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </motion.section>
  );
};