import { Calendar, Clock, Loader2 } from 'lucide-react';
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
  appointments: DashboardAppointment[];
  loading: boolean;
  onRefresh: () => void;
  onStatusChange: (appointmentId: number, status: string) => void;
}) => {
  if (!visible) return null;

  return (
    <motion.section variants={dashboardItemVariants} className="space-y-5">
      <h2 className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-2 px-4 flex items-center justify-between">
        <span className="flex items-center gap-2"><Clock size={16} /> File d'attente & Arrivées du Jour</span>
        <button
          onClick={onRefresh}
          className="text-primary hover:text-primary-hover text-[10px] font-black uppercase tracking-wider flex items-center gap-1.5 bg-primary/5 px-2.5 py-1 rounded-full border border-primary/10 transition-all"
        >
          {loading ? <Loader2 className="animate-spin" size={10} /> : 'Actualiser'}
        </button>
      </h2>

      <div className="bg-card-bg/85 backdrop-blur-xl rounded-elite-lg border border-border-main p-6 h-[410px] shadow-elite flex flex-col justify-between relative overflow-hidden group">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent pointer-events-none" />

        {/* Contenu principal défilable */}
        <div className="relative z-10 flex-1 overflow-y-auto custom-scrollbar space-y-3 pr-1">
          {appointments.length > 0 ? (
            [...appointments]
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
                      onClick={() => onStatusChange(appointment.id, 'EN_FAUTEUIL')}
                      className="px-3 py-1.5 bg-primary text-white text-[10px] font-black uppercase tracking-wider rounded-lg shadow-md hover:brightness-110 transition-all"
                    >
                      Installer au Fauteuil
                    </button>
                  );
                } else if (appointment.status === 'EN_FAUTEUIL') {
                  statusLabel = 'Au Fauteuil';
                  statusColor = 'bg-blue-500/10 text-blue-500 border-blue-500/20';
                  actionButton = (
                    <button
                      onClick={() => onStatusChange(appointment.id, 'TERMINÉ')}
                      className="px-3 py-1.5 bg-slate-800 text-white text-[10px] font-black uppercase tracking-wider rounded-lg hover:bg-slate-700 transition-all"
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
                      onClick={() => onStatusChange(appointment.id, 'EN_S_ATTENTE')}
                      className="px-3 py-1.5 bg-emerald-500 text-white text-[10px] font-black uppercase tracking-wider rounded-lg shadow-md hover:brightness-110 transition-all"
                    >
                      Marquer Arrivé
                    </button>
                  );
                }

                return (
                  <div
                    key={appointment.id}
                    className="flex items-center justify-between p-4 bg-white/40 border border-border-main rounded-elite-sm hover:bg-white/60 transition-all gap-4"
                  >
                    <div className="flex items-center gap-4">
                      <div className="text-sm font-black text-primary bg-primary/5 border border-primary/10 px-2.5 py-1.5 rounded-lg whitespace-nowrap">
                        {appointmentTime}
                      </div>
                      <div>
                        <h4 className="text-sm font-black text-primary font-outfit">
                          {appointment.patient ? `${appointment.patient.nom.toUpperCase()} ${appointment.patient.prenom}` : 'Patient non spécifié'}
                        </h4>
                        <p className="text-[10px] font-bold text-text-muted mt-0.5 uppercase tracking-wide">
                          {appointment.description || 'Consultation clinique'}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className={cn('text-[9px] font-black border px-2.5 py-1 rounded-full uppercase tracking-wider', statusColor)}>
                        {statusLabel}
                      </span>
                      {actionButton}
                    </div>
                  </div>
                );
              })
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center py-16 space-y-4">
              <div className="w-16 h-16 bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 rounded-full flex items-center justify-center">
                <Calendar size={28} className="text-emerald-500" />
              </div>
              <div>
                <h4 className="text-lg font-black text-primary font-outfit mb-2">Aucun patient aujourd'hui</h4>
                <p className="text-text-muted text-xs font-medium mt-1 max-w-[250px] mx-auto leading-relaxed">
                  Les rendez-vous programmés pour la journée apparaîtront ici pour le suivi de la file d'attente.
                </p>
              </div>
              <Link
                to="/agenda"
                className="mt-4 px-5 py-2.5 bg-emerald-500/10 text-emerald-600 rounded-lg text-xs font-black uppercase tracking-widest hover:bg-emerald-500/20 transition-all"
              >
                Ouvrir l'agenda
              </Link>
            </div>
          )}
        </div>

        {/* Statistiques rapides en bas */}
        <div className="relative z-10 border-t border-border-main pt-4 mt-4 flex items-center justify-between text-[9px] font-black text-text-muted uppercase tracking-wider">
          <span className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            En Salle d'Attente : {appointments.filter(item => item.status === 'EN_S_ATTENTE').length}
          </span>
          <span>Au Fauteuil : {appointments.filter(item => item.status === 'EN_FAUTEUIL').length}</span>
        </div>
      </div>
    </motion.section>
  );
};
