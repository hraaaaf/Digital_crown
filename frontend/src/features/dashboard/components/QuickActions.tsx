import { Calendar, UserPlus, Users } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { dashboardContainerVariants, dashboardItemVariants } from '../animations';

export const QuickActions = ({
  canReadPatients,
  canUseAgenda,
}: {
  canReadPatients: boolean;
  canUseAgenda: boolean;
}) => {
  if (!canReadPatients && !canUseAgenda) return null;

  return (
    <motion.section
      variants={dashboardContainerVariants}
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
    >
      {canReadPatients && (
        <motion.div variants={dashboardItemVariants}>
          <Link
            to="/patients/new"
            data-tour="quick-action-new-patient"
            data-guide="quick-action-new-patient"
            className="group block p-8 rounded-elite-lg shadow-elite hover:shadow-elite-hover hover:-translate-y-1 transition-elite relative overflow-hidden h-full border border-white/20 backdrop-blur-xl"
            style={{ backgroundImage: 'linear-gradient(135deg, color-mix(in srgb, var(--primary) 92%, transparent), color-mix(in srgb, var(--secondary, #1e3a8a) 88%, transparent))' }}
          >
            <div className="absolute inset-0 bg-white/[0.03] pointer-events-none" />
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16 blur-2xl group-hover:scale-150 transition-elite duration-700" />
            <div className="relative z-10">
              <div className="w-16 h-16 bg-white/20 backdrop-blur-md rounded-elite-sm flex items-center justify-center mb-8 border border-white/30 group-hover:rotate-12 transition-elite">
                <UserPlus className="text-white" size={32} />
              </div>
              <h3 className="text-2xl font-black text-white leading-none font-outfit">Nouveau Patient</h3>
              <p className="text-white/70 mt-2 font-medium">Ouvrir un dossier clinique complet</p>
            </div>
          </Link>
        </motion.div>
      )}

      {canReadPatients && (
        <motion.div variants={dashboardItemVariants}>
          <Link
            to="/patients"
            className="group bg-card-bg/65 backdrop-blur-2xl block p-8 rounded-elite-lg border border-border-main shadow-elite hover:shadow-elite-hover hover:-translate-y-1 transition-elite relative overflow-hidden h-full"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-white/10 via-transparent to-primary/5 pointer-events-none" />
            <div className="relative z-10">
              <div className="w-14 h-14 bg-primary/5 backdrop-blur-md rounded-elite-sm flex items-center justify-center mb-6 border border-primary/10 group-hover:bg-primary group-hover:text-white transition-elite text-primary">
                <Users size={28} />
              </div>
              <h3 className="text-xl font-black tracking-tight font-outfit text-primary">Dossiers Patients</h3>
              <p className="text-text-muted mt-1 font-medium italic">Gestion de la patientèle</p>
            </div>
          </Link>
        </motion.div>
      )}

      {canUseAgenda && (
        <motion.div variants={dashboardItemVariants}>
          <Link
            to="/agenda"
            data-guide="quick-action-agenda"
            className="group bg-card-bg/65 backdrop-blur-2xl block p-8 rounded-elite-lg border border-border-main shadow-elite hover:shadow-elite-hover hover:-translate-y-1 transition-elite relative overflow-hidden h-full"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-white/10 via-transparent to-emerald-500/5 pointer-events-none" />
            <div className="relative z-10">
              <div className="w-14 h-14 bg-emerald-500/10 backdrop-blur-md text-emerald-500 rounded-elite-sm flex items-center justify-center mb-6 border border-emerald-500/20 group-hover:bg-emerald-500 group-hover:text-white transition-elite">
                <Calendar size={28} />
              </div>
              <h3 className="text-xl font-black text-main tracking-tight font-outfit" style={{ color: 'var(--text-main)' }}>
                Agenda Clinique
              </h3>
              <p className="text-text-muted mt-1 font-medium italic">Suivi des rendez-vous</p>
            </div>
          </Link>
        </motion.div>
      )}
    </motion.section>
  );
};