import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  UserPlus, 
  Calendar, 
  Clock, 
  FileText, 
  ChevronRight,
  TrendingUp,
  Loader2,
  Users
} from 'lucide-react';
import { cn } from '../utils/cn';
import { api } from '../services/api';
import { PatientScoreBadge } from '../features/patients/components/PatientScoreBadge';
import { motion, type Variants } from 'framer-motion';

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.1 }
  }
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.5, ease: "easeOut" }
  }
};

interface RecentPatient {
  id: number;
  nom: string;
  prenom: string;
  acte: string;
  time: string;
  type: string;
}

interface DashboardStats {
  total_patients: number;
  total_analyses: number;
  in_waiting: number;
  recent_patients: RecentPatient[];
  weekly_activity: number[];
}

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [praticienName, setPraticienName] = useState('Praticien');

  const today = new Date().toLocaleDateString('fr-FR', { 
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' 
  });

  const formatDate = (dateStr: string) => {
    return dateStr.charAt(0).toUpperCase() + dateStr.slice(1);
  };

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await api.get('/admin/dashboard/stats');
        setStats(response.data);
      } catch (err) {
        console.warn("Route API manquante ou invalide, injection des données de secours.");
        setStats({
          total_patients: 0,
          total_analyses: 0,
          in_waiting: 0,
          weekly_activity: [0, 0, 0, 0, 0, 0, 0],
          recent_patients: []
        });
      } finally {
        setLoading(false);
      }
    };

    const fetchConfig = async () => {
      try {
        const response = await api.get('/admin/cabinet/mine');
        const config = response.data;
        if (config.header_lines_fr && config.header_lines_fr.length > 0) {
          setPraticienName(config.header_lines_fr[0]);
        }
      } catch (e) {}
    };

    fetchStats();
    fetchConfig();
  }, []);

  if (loading) return (
    <div className="h-full flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <Loader2 className="w-12 h-12 animate-spin text-primary" />
        <p className="text-slate-400 font-black uppercase tracking-widest text-xs text-primary">Initialisation de votre cabinet...</p>
      </div>
    </div>
  );

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-[1600px] mx-auto w-full px-6 py-8 md:px-10 md:py-10 space-y-12"
    >
      <motion.header variants={itemVariants} className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 className="text-4xl font-black tracking-tight font-outfit text-primary">Bonjour, {praticienName}</h1>
          <div className="flex items-center gap-3 mt-3 bg-card-bg/60 backdrop-blur-md px-4 py-2 rounded-elite-sm border border-border-main w-fit">
            <Calendar size={16} className="text-primary" />
            <p className="text-text-muted font-bold text-sm">{formatDate(today)}</p>
          </div>
        </div>

        
        <div className="flex items-center gap-4 bg-card-bg/40 p-2 rounded-elite-lg border border-border-main shadow-elite transition-elite hover:bg-card-bg/60">
          <div className="px-6 py-3 rounded-elite-sm flex flex-col items-end">
            <span className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-1">Status Système</span>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-sm font-black text-main uppercase tracking-tighter" style={{ color: 'var(--text-main)' }}>Elite Cloud Connecté</span>
            </div>
          </div>
        </div>
      </motion.header>

      <motion.section variants={containerVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        <motion.div variants={itemVariants}>
          <Link to="/patients/new" data-tour="quick-action-new-patient" className="group block p-8 rounded-elite-lg shadow-elite hover:shadow-elite-hover hover:-translate-y-1 transition-elite relative overflow-hidden h-full" style={{ backgroundImage: 'linear-gradient(135deg, var(--primary), var(--secondary, #1e3a8a))' }}>
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

        <motion.div variants={itemVariants}>
          <Link to="/patients" className="group bg-card-bg block p-8 rounded-elite-lg border border-border-main shadow-elite hover:shadow-elite-hover hover:-translate-y-1 transition-elite relative overflow-hidden h-full">
            <div className="w-14 h-14 bg-primary/5 rounded-elite-sm flex items-center justify-center mb-6 border border-primary/10 group-hover:bg-primary group-hover:text-white transition-elite text-primary">
              <Users size={28} />
            </div>
            <h3 className="text-xl font-black tracking-tight font-outfit text-primary">Dossiers Patients</h3>
            <p className="text-text-muted mt-1 font-medium italic">Gestion de la patientèle</p>
          </Link>
        </motion.div>

        <motion.div variants={itemVariants}>
          <Link to="/agenda" className="group bg-card-bg block p-8 rounded-elite-lg border border-border-main shadow-elite hover:shadow-elite-hover hover:-translate-y-1 transition-elite relative overflow-hidden h-full">
            <div className="w-14 h-14 bg-emerald-500/10 text-emerald-500 rounded-elite-sm flex items-center justify-center mb-6 border border-emerald-500/20 group-hover:bg-emerald-500 group-hover:text-white transition-elite">
              <Calendar size={28} />
            </div>
            <h3 className="text-xl font-black text-main tracking-tight font-outfit" style={{ color: 'var(--text-main)' }}>Agenda Clinique</h3>
            <p className="text-text-muted mt-1 font-medium italic">Suivi des rendez-vous</p>
          </Link>
        </motion.div>
      </motion.section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
        <motion.section variants={itemVariants} data-tour="dashboard-agenda" className="space-y-5">
          <h2 className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-2 px-4 flex items-center gap-2">
            <Clock size={16} /> Activité Récente
          </h2>
          <div data-tour="dashboard-activity" className="bg-card-bg/80 backdrop-blur-xl border border-border-main rounded-elite-lg p-4 shadow-elite">
            {stats?.recent_patients && stats.recent_patients.length > 0 ? (
              stats.recent_patients.map((patient, index) => {
                if (!patient || !patient.nom) return null;
                return (
                  <Link 
                    key={patient.id} 
                    to={`/patients/${patient.id}`}
                    className={cn(
                      "flex items-center justify-between p-4 hover:bg-primary/5 rounded-elite-sm transition-elite group",
                      index !== (stats.recent_patients.length - 1) && "border-b border-border-main"
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
                          <PatientScoreBadge patientId={patient.id} className="scale-75 origin-left" />
                        </div>
                        <p className="text-xs font-bold text-text-muted mt-2 flex items-center gap-2">
                          <FileText size={14} className="text-blue-400" /> {patient.acte || 'Consultation'}
                          <span className="text-border-main">·</span>
                          <span>{patient.time || 'Récemment'}</span>
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center">
                      <ChevronRight size={18} className="text-text-muted group-hover:text-primary transition-elite group-hover:translate-x-1" />
                    </div>
                  </Link>
                );
              })
            ) : (
              <div className="py-12 text-center">
                <p className="text-text-muted font-bold italic text-xs uppercase tracking-widest">Aucun patient récent à afficher.</p>
              </div>
            )}
          </div>
        </motion.section>

        <motion.section variants={itemVariants} className="space-y-5">
          <h2 className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-2 px-4 flex items-center gap-2">
            <TrendingUp size={16} /> Performance Hebdomadaire
          </h2>
          <div className="bg-card-bg rounded-elite-lg border border-border-main p-8 h-[410px] shadow-elite flex items-center justify-center relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent pointer-events-none" />
            <div className="flex flex-col items-center gap-4 text-text-muted relative z-10">
               <TrendingUp size={48} className="animate-pulse text-primary/40" />
               <p className="font-black text-[10px] uppercase tracking-[0.2em] text-text-muted">Intelligence Analytique</p>
               <p className="text-xs text-text-muted font-bold italic">Données en cours de synchronisation...</p>
            </div>
          </div>
        </motion.section>
      </div>
    </motion.div>
  );
};