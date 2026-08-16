import { AlertTriangle, Calendar, Clock, Loader2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { cn } from '../../../utils/cn';
import { dashboardItemVariants } from '../animations';
import type { DashboardAppointment } from '../types';

export const WaitingRoom = ({
  visible,
  appointments,
  loading,
  onRefresh,
  onStatusChange,
}: {
  visible: boolean;
  appointments: DashboardAppointment[] | null;
  loading: boolean;
  onRefresh: () => void;
  onStatusChange: (appointmentId: number, status: string) => void;
}) => {
  if (!visible) return null;

  const isUnavailable = appointments === null;
  const safeAppointments = appointments ?? [];

  return (
    <motion.section variants={dashboardItemVariants} className="space-y-5 min-w-0">
      <h2 className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-2 px-2 sm:px-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <span className="flex items-center gap-2 min-w-0"><Clock size={16} className="shrink-0" aria-hidden="true" /> File d'attente & Arrivées du Jour</span>
        <button
          type="button"
          onClick={onRefresh}
          aria-label="Actualiser la file d'attente"
          className="min-h-11 self-start sm:self-auto text-primary hover:text-primary-hover text-[10px] font-black uppercase tracking-wider flex items-center gap-1.5 bg-primary/5 px-3 rounded-full border border-primary/10 transition-all"
        >
          {loading ? <Loader2 className="animate-spin" size={12} aria-hidden="true" /> : 'Actualiser'}
        </button>
      </h2>

      <div className="bg-card-bg/85 backdrop-blur-xl rounded-elite-lg border border-border-main p-4 sm:p-6 min-h-[410px] sm:h-[410px] shadow-elite flex flex-col justify-between relative overflow-hidden group">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent pointer-events-none" />

        <div className="relative z-10 flex-1 overflow-y-auto custom-scrollbar space-y-3 pr-1 min-w-0">
          {isUnavailable ? (
            <div role="status" className="h-full flex flex-col items-center justify-center text-center py-16 space-y-4">
              <div className="w-16 h-16 bg-amber-500/10 rounded-full flex items-center justify-center border border-amber-500/15">
                <AlertTriangle size={28} className="text-amber-500" aria-hidden="true" />
              </div>
              <div>
                <h4 className="text-lg font-black text-primary font-outfit mb-2">Rendez-vous indisponibles</h4>
                <p className="text-text-muted text-xs font-medium mt-1 max-w-[280px] mx-auto leading-relaxed">
                  La file d'attente n'a pas pu être vérifiée. Aucun état vide n'est supposé.
                </p>
              </div>
              <button
                type="button"
                onClick={onRefresh}
                className="min-h-11 mt-4 px-5 py-2.5 bg-amber-500/10 text-amber-700 dark:text-amber-300 rounded-lg text-xs font-black uppercase tracking-widest hover:bg-amber-500/20 transition-all"
              >
                Réessayer
              </button>
            </div>
          ) : safeAppointments.length > 0 ? (
            [...safeAppointments]
              .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
              .map(appointment => {
                const appointmentTime = new Date(appointment.start_time).toLocaleTimeString('fr-FR', {
                  hour: '2-digit',
                  minute: '2-digit',
                });

                let statusLabel = 'Prévu';
                let statusColor = 'bg-slate-100 text-slate-600 border-slate-200';
                let actionButton = null;

                if (appointment.status === 'EN_S_ATTENTE') {
                  statusLabel = "Salle d'attente";
                  statusColor = 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20 animate-pulse';
                  actionButton = (
                    <button
                      type="button"
                      onClick={() => onStatusChange(appointment.id, 'EN_FAUTEUIL')}
                      className="w-full sm:w-auto min-h-11 px-3 py-2 bg-primary text-white text-[10px] font-black uppercase tracking-wider rounded-lg shadow-md hover:brightness-110 transition-all"
                    >
                      Installer au Fauteuil
                    </button>
                  );
                } else if (appointment.status === 'EN_FAUTEUIL') {
                  statusLabel = 'Au Fauteuil';
                  statusColor = 'bg-blue-500/10 text-blue-500 border-blue-500/20';
                  actionButton = (
                    <button
                      type="button"
                      onClick={() => onStatusChange(appointment.id, 'TERMINÉ')}
                      className="w-full sm:w-auto min-h-11 px-3 py-2 bg-slate-800 text-white text-[10px] font-black uppercase tracking-wider rounded-lg hover:bg-slate-700 transition-all"
                    >
                      Terminer la Séance
                    </button>
                  );
                } else if (appointment.status === 'TERMINÉ') {
                  statusLabel = 'Terminé';
                  statusColor = 'bg-slate-500/10 text-slate-400 border-slate-500/10';
                } else if (appointment.status === 'ANNULÉ') {
                  statusLabel = 'Annulé';
                  statusColor = 'bg-rose-500/10 text-rose-500 border-rose-500/20';
                } else {
                  actionButton = (
                    <button
                      type="button"
                      onClick={() => onStatusChange(appointment.id, 'EN_S_ATTENTE')}
                      className="w-full sm:w-auto min-h-11 px-3 py-2 bg-emerald-500 text-white text-[10px] font-black uppercase tracking-wider rounded-lg shadow-md hover:brightness-110 transition-all"
                    >
                      Marquer Arrivé
                    </button>
                  );
                }

                return (
                  <div
                    key={appointment.id}
                    className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-3 sm:p-4 bg-white/40 border border-border-main rounded-elite-sm hover:bg-white/60 transition-all gap-3 sm:gap-4 min-w-0"
                  >
                    <div className="flex items-start sm:items-center gap-3 sm:gap-4 min-w-0 w-full sm:w-auto">
                      <div className="shrink-0 text-sm font-black text-primary bg-primary/5 border border-primary/10 px-2.5 py-1.5 rounded-lg whitespace-nowrap">
                        {appointmentTime}
                      </div>
                      <div className="min-w-0">
                        <h4 className="text-sm font-black text-primary font-outfit break-words">
                          {appointment.patient ? `${appointment.patient.nom.toUpperCase()} ${appointment.patient.prenom}` : 'Patient non spécifié'}
                        </h4>
                        <p className="text-[10px] font-bold text-text-muted mt-0.5 uppercase tracking-wide break-words">
                          {appointment.description || 'Consultation clinique'}
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-wrap sm:flex-nowrap items-center gap-2 sm:gap-3 w-full sm:w-auto min-w-0">
                      <span className={cn('shrink-0 text-[9px] font-black border px-2.5 py-1 rounded-full uppercase tracking-wider', statusColor)}>
                        {statusLabel}
                      </span>
                      <div className="w-full sm:w-auto">{actionButton}</div>
                    </div>
                  </div>
                );
              })
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center py-16 space-y-4">
              <div className="w-16 h-16 bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 rounded-full flex items-center justify-center">
                <Calendar size={28} className="text-emerald-500" aria-hidden="true" />
              </div>
              <div>
                <h4 className="text-lg font-black text-primary font-outfit mb-2">Aucun patient aujourd'hui</h4>
                <p className="text-text-muted text-xs font-medium mt-1 max-w-[250px] mx-auto leading-relaxed">
                  Les rendez-vous programmés pour la journée apparaîtront ici pour le suivi de la file d'attente.
                </p>
              </div>
              <Link
                to="/agenda"
                className="min-h-11 mt-4 px-5 py-2.5 bg-emerald-500/10 text-emerald-600 rounded-lg text-xs font-black uppercase tracking-widest hover:bg-emerald-500/20 transition-all inline-flex items-center"
              >
                Ouvrir l'agenda
              </Link>
            </div>
          )}
        </div>

        <div className="relative z-10 border-t border-border-main pt-4 mt-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-[9px] font-black text-text-muted uppercase tracking-wider">
          {isUnavailable ? (
            <span className="text-amber-600 dark:text-amber-300">État non vérifié</span>
          ) : (
            <>
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" aria-hidden="true" />
                En Salle d'Attente : {safeAppointments.filter(item => item.status === 'EN_S_ATTENTE').length}
              </span>
              <span>Au Fauteuil : {safeAppointments.filter(item => item.status === 'EN_FAUTEUIL').length}</span>
            </>
          )}
        </div>
      </div>
    </motion.section>
  );
};
