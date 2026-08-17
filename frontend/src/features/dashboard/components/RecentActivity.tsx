import { AlertTriangle, ChevronRight, Clock, FileText, UserPlus } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { cn } from '../../../utils/cn';
import { PatientScoreBadge } from '../../patients/components/PatientScoreBadge';
import { dashboardItemVariants } from '../animations';
import type { DashboardStats } from '../types';

export const RecentActivity = ({
  visible,
  stats,
  showPatientBadges,
}: {
  visible: boolean;
  stats: DashboardStats | null;
  showPatientBadges: boolean;
}) => {
  if (!visible) return null;

  return (
    <motion.section variants={dashboardItemVariants} data-tour="dashboard-agenda" className="space-y-5">
      <h2 className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-2 px-4 flex items-center gap-2">
        <Clock size={16} aria-hidden="true" /> Activité Récente
      </h2>
      <div data-tour="dashboard-activity" className="bg-card-bg/80 backdrop-blur-xl border border-border-main rounded-elite-lg p-4 shadow-elite">
        {stats === null ? (
          <div role="status" className="py-14 flex flex-col items-center justify-center text-center">
            <div className="w-20 h-20 bg-amber-500/10 rounded-full flex items-center justify-center mb-6 border border-amber-500/15">
              <AlertTriangle className="text-amber-500 w-9 h-9" aria-hidden="true" />
            </div>
            <h3 className="text-xl font-black text-primary font-outfit mb-2">Activité indisponible</h3>
            <p className="text-text-muted font-medium text-sm max-w-[300px] leading-relaxed">
              Les données récentes n'ont pas pu être vérifiées. Aucun état vide n'est supposé.
            </p>
          </div>
        ) : stats.recent_patients && stats.recent_patients.length > 0 ? (
          stats.recent_patients.map((patient, index) => {
            if (!patient || !patient.nom) return null;
            return (
              <Link
                key={patient.id}
                to={`/patients/${patient.id}`}
                className={cn(
                  'flex items-center justify-between p-4 hover:bg-primary/5 rounded-elite-sm transition-elite group',
                  index !== stats.recent_patients.length - 1 && 'border-b border-border-main',
                )}
              >
                <div className="flex items-center gap-5">
                  <div className="w-14 h-14 bg-primary/10 text-primary rounded-elite-sm flex items-center justify-center font-black text-xl border border-primary/20 group-hover:bg-primary group-hover:text-white transition-elite shadow-sm">
                    {(patient.nom || '?').charAt(0)}
                  </div>
                  <div>
                    <div className="flex items-center gap-3">
                      <h4 className="font-black text-primary text-lg leading-none font-outfit">
                        {(patient.nom || '').toUpperCase()} {patient.prenom || ''}
                      </h4>
                      {showPatientBadges && <PatientScoreBadge patientId={patient.id} className="scale-75 origin-left" />}
                    </div>
                    <p className="text-xs font-bold text-text-muted mt-2 flex items-center gap-2">
                      <FileText size={14} className="text-blue-400" aria-hidden="true" /> {patient.acte || 'Consultation'}
                      <span className="text-border-main">·</span>
                      <span>{patient.time || 'Récemment'}</span>
                    </p>
                  </div>
                </div>
                <ChevronRight size={18} className="text-text-muted group-hover:text-primary transition-elite group-hover:translate-x-1" aria-hidden="true" />
              </Link>
            );
          })
        ) : (
          <div className="py-14 flex flex-col items-center justify-center text-center">
            <div className="w-20 h-20 bg-primary/5 rounded-full flex items-center justify-center mb-6">
              <UserPlus className="text-primary w-10 h-10" aria-hidden="true" />
            </div>
            <h3 className="text-xl font-black text-primary font-outfit mb-2">Aucune activité récente</h3>
            <p className="text-text-muted font-medium text-sm max-w-[280px] leading-relaxed mb-8">
              Aucun dossier patient récent n'est disponible pour le moment.
            </p>
            <Link
              to="/patients/new"
              className="min-h-11 px-6 py-3 bg-primary text-white rounded-elite-sm text-xs font-black uppercase tracking-widest hover:brightness-110 transition-all shadow-md shadow-primary/20 flex items-center gap-2"
            >
              Créer un patient <ChevronRight size={14} aria-hidden="true" />
            </Link>
          </div>
        )}
      </div>
    </motion.section>
  );
};
