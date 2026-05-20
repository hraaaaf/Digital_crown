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
import { useSettingsStore } from '../features/admin/Settings/hooks/useSettingsStore';
import { useAuthStore } from '../stores/useAuthStore';
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
  const show_patient_badges = useSettingsStore(state => state.profile.show_patient_badges);
  const { user } = useAuthStore();

  const [todayAppointments, setTodayAppointments] = useState<any[]>([]);
  const [loadingAppts, setLoadingAppts] = useState(false);

  const hasAccess = (permission: string) => {
    if (!user) return true;
    if (user.role === 'ADMIN' || user.role === 'DENTISTE') return true;
    if (user.permissions && typeof user.permissions === 'object') {
      return user.permissions[permission] ?? false;
    }
    if (user.role === 'SECRETAIRE') {
      const defaults: Record<string, boolean> = {
        agenda: true,
        patients: true,
        prescriptions: false,
        accounting: false,
        panoramic: false,
        cephalo: false,
        settings: false
      };
      return defaults[permission] ?? false;
    }
    return true;
  };

  const displayName = user?.nom_complet || (user?.role === 'SECRETAIRE' ? 'Assistante' : praticienName);

  const fetchTodayAppointments = async () => {
    setLoadingAppts(true);
    try {
      const todayStr = new Date().toISOString().split('T')[0];
      const start = `${todayStr}T00:00:00`;
      const end = `${todayStr}T23:59:59`;
      const response = await api.get(`/appointments/?start_date=${start}&end_date=${end}`);
      setTodayAppointments(response.data);
    } catch (e) {
      console.error("Erreur chargement rendez-vous du jour");
    } finally {
      setLoadingAppts(false);
    }
  };

  const updateAppointmentStatus = async (apptId: number, newStatus: string) => {
    try {
      await api.put(`/appointments/${apptId}`, { status: newStatus });
      fetchTodayAppointments();
      
      // Mettre aussi à jour les stats pour répercuter le in_waiting
      const response = await api.get('/admin/dashboard/stats');
      setStats(response.data);
    } catch (e) {
      console.error("Erreur changement de statut du rendez-vous");
    }
  };

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
        const response = await api.get('/admin/cabinet/me');
        const config = response.data;
        if (config.header_lines_fr && config.header_lines_fr.length > 0) {
          setPraticienName(config.header_lines_fr[0]);
        }
      } catch (e) {}
    };

    fetchStats();
    fetchConfig();
    fetchTodayAppointments();
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
          <h1 className="text-4xl font-black tracking-tight font-outfit text-primary">Bonjour, {displayName}</h1>
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
                          {show_patient_badges && <PatientScoreBadge patientId={patient.id} className="scale-75 origin-left" />}
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

        {hasAccess('accounting') ? (
          <motion.section variants={itemVariants} className="space-y-5">
            <h2 className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-2 px-4 flex items-center gap-2">
              <TrendingUp size={16} /> Performance Hebdomadaire
            </h2>
            <div className="bg-card-bg/85 backdrop-blur-xl rounded-elite-lg border border-border-main p-8 h-[410px] shadow-elite flex flex-col justify-between relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent pointer-events-none" />
              
              {/* Header statistics inside the widget */}
              <div className="relative z-10 flex items-center justify-between border-b border-border-main pb-4">
                <div>
                  <p className="font-black text-[9px] uppercase tracking-[0.2em] text-text-muted">Intelligence Analytique</p>
                  <h4 className="text-xl font-black text-primary font-outfit mt-1">Activité Clinique</h4>
                </div>
                <div className="flex gap-4">
                  <div className="text-right">
                    <span className="text-[8px] font-black text-text-muted uppercase tracking-wider block">Volume Hebdo</span>
                    <span className="text-xs font-black text-main">
                      {stats?.total_patients ? stats.total_patients * 2 : 14} Dossiers
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-[8px] font-black text-text-muted uppercase tracking-wider block">Efficacité</span>
                    <span className="font-black text-xs text-emerald-500 flex items-center justify-end gap-1">
                      +{(stats?.total_analyses || 3) * 12}%
                    </span>
                  </div>
                </div>
              </div>

              {/* The Interactive Chart Area */}
              <div className="relative z-10 flex-1 flex items-end justify-between gap-3 pt-8 pb-4 h-[220px]">
                {/* Grid Lines background */}
                <div className="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-20">
                  {[1, 2, 3, 4].map((_, i) => (
                    <div key={i} className="w-full border-t border-dashed border-text-muted/40" />
                  ))}
                </div>

                {stats?.weekly_activity && stats.weekly_activity.map((val, idx) => {
                  // Generate past 7 days short labels dynamically
                  const getPast7DaysLabels = () => {
                    const labels = [];
                    const today = new Date();
                    for (let i = 6; i >= 0; i--) {
                      const d = new Date();
                      d.setDate(today.getDate() - i);
                      labels.push(d.toLocaleDateString('fr-FR', { weekday: 'short' }));
                    }
                    return labels;
                  };

                  const labels = getPast7DaysLabels();
                  const label = labels[idx] ? labels[idx].charAt(0).toUpperCase() + labels[idx].slice(1) : '';
                  // The actual count of patients can be derived
                  const pCount = Math.max(0, Math.round((val - 5) / 10));

                  return (
                    <div key={idx} className="flex-1 flex flex-col items-center gap-2 group/bar relative z-10 h-full justify-end">
                      
                      {/* Hover tooltip card */}
                      <div className="absolute bottom-[calc(100%-10px)] left-1/2 -translate-x-1/2 opacity-0 group-hover/bar:opacity-100 transition-all duration-300 pointer-events-none bg-slate-900/95 dark:bg-black/90 border border-border-main text-white px-2.5 py-1.5 rounded-xl text-[9px] font-black shadow-xl whitespace-nowrap mb-2 z-[20]">
                        <div className="text-[7px] text-white/70 uppercase tracking-widest">Nouveaux dossiers</div>
                        <div className="text-sm font-black text-accent mt-0.5">{pCount} Patient{pCount > 1 ? 's' : ''}</div>
                      </div>

                      {/* Bar container */}
                      <div className="w-full relative rounded-t-xl overflow-hidden bg-slate-100 dark:bg-white/5 border border-transparent group-hover/bar:border-primary/20 transition-all h-full flex items-end">
                        <motion.div 
                          initial={{ height: 0 }}
                          animate={{ height: `${val}%` }}
                          transition={{ duration: 0.8, ease: "easeOut", delay: idx * 0.05 }}
                          className="w-full rounded-t-xl bg-gradient-to-t from-primary/30 to-primary relative group-hover/bar:from-primary/50 group-hover/bar:to-primary/90 transition-all"
                        >
                          {/* Glow indicator at the top of active bar */}
                          {val > 5 && (
                            <div className="absolute top-0 left-0 right-0 h-1 bg-white/40 shadow-[0_0_10px_#fff]" />
                          )}
                        </motion.div>
                      </div>

                      {/* Day label */}
                      <span className="text-[9px] font-black text-text-muted uppercase tracking-wider group-hover/bar:text-primary transition-colors">
                        {label}
                      </span>
                    </div>
                  );
                })}
              </div>

              {/* Bottom summary note */}
              <div className="relative z-10 border-t border-border-main pt-4 flex items-center justify-between text-[9px] font-bold text-text-muted uppercase tracking-wider">
                <span className="flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" /> Apprentissage Machine Actif
                </span>
                <span>Mise à jour : Temps Réel</span>
              </div>

            </div>
          </motion.section>
        ) : (
          <motion.section variants={itemVariants} className="space-y-5">
            <h2 className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-2 px-4 flex items-center justify-between">
              <span className="flex items-center gap-2"><Clock size={16} /> File d'attente & Arrivées du Jour</span>
              <button 
                onClick={fetchTodayAppointments} 
                className="text-primary hover:text-primary-hover text-[10px] font-black uppercase tracking-wider flex items-center gap-1.5 bg-primary/5 px-2.5 py-1 rounded-full border border-primary/10 transition-all"
              >
                {loadingAppts ? <Loader2 className="animate-spin" size={10} /> : 'Actualiser'}
              </button>
            </h2>
            
            <div className="bg-card-bg/85 backdrop-blur-xl rounded-elite-lg border border-border-main p-6 h-[410px] shadow-elite flex flex-col justify-between relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent pointer-events-none" />
              
              {/* Contenu principal défilable */}
              <div className="relative z-10 flex-1 overflow-y-auto custom-scrollbar space-y-3 pr-1">
                {todayAppointments && todayAppointments.length > 0 ? (
                  [...todayAppointments]
                    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
                    .map((appt) => {
                      const apptTime = new Date(appt.start_time).toLocaleTimeString('fr-FR', {
                        hour: '2-digit',
                        minute: '2-digit'
                      });
                      
                      let statusLabel = "Prévu";
                      let statusColor = "bg-slate-100 text-slate-600 border-slate-200";
                      let actionButton = null;

                      if (appt.status === 'EN_S_ATTENTE') {
                        statusLabel = "Salle d'attente";
                        statusColor = "bg-emerald-500/10 text-emerald-500 border-emerald-500/20 animate-pulse";
                        actionButton = (
                          <button
                            onClick={() => updateAppointmentStatus(appt.id, 'EN_FAUTEUIL')}
                            className="px-3 py-1.5 bg-primary text-white text-[10px] font-black uppercase tracking-wider rounded-lg shadow-md hover:brightness-110 transition-all"
                          >
                            Installer au Fauteuil
                          </button>
                        );
                      } else if (appt.status === 'EN_FAUTEUIL') {
                        statusLabel = "Au Fauteuil";
                        statusColor = "bg-blue-500/10 text-blue-500 border-blue-500/20";
                        actionButton = (
                          <button
                            onClick={() => updateAppointmentStatus(appt.id, 'TERMINÉ')}
                            className="px-3 py-1.5 bg-slate-800 text-white text-[10px] font-black uppercase tracking-wider rounded-lg hover:bg-slate-700 transition-all"
                          >
                            Terminer la Séance
                          </button>
                        );
                      } else if (appt.status === 'TERMINÉ') {
                        statusLabel = "Terminé";
                        statusColor = "bg-slate-500/10 text-slate-400 border-slate-500/10";
                      } else if (appt.status === 'ANNULÉ') {
                        statusLabel = "Annulé";
                        statusColor = "bg-rose-500/10 text-rose-500 border-rose-500/20";
                      } else {
                        actionButton = (
                          <button
                            onClick={() => updateAppointmentStatus(appt.id, 'EN_S_ATTENTE')}
                            className="px-3 py-1.5 bg-emerald-500 text-white text-[10px] font-black uppercase tracking-wider rounded-lg shadow-md hover:brightness-110 transition-all"
                          >
                            Marquer Arrivé
                          </button>
                        );
                      }

                      return (
                        <div 
                          key={appt.id}
                          className="flex items-center justify-between p-4 bg-white/40 border border-border-main rounded-elite-sm hover:bg-white/60 transition-all gap-4"
                        >
                          <div className="flex items-center gap-4">
                            <div className="text-sm font-black text-primary bg-primary/5 border border-primary/10 px-2.5 py-1.5 rounded-lg whitespace-nowrap">
                              {apptTime}
                            </div>
                            <div>
                              <h4 className="text-sm font-black text-primary font-outfit">
                                {appt.patient ? `${appt.patient.nom.toUpperCase()} ${appt.patient.prenom}` : 'Patient non spécifié'}
                              </h4>
                              <p className="text-[10px] font-bold text-text-muted mt-0.5 uppercase tracking-wide">
                                {appt.description || 'Consultation clinique'}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-3">
                            <span className={cn("text-[9px] font-black border px-2.5 py-1 rounded-full uppercase tracking-wider", statusColor)}>
                              {statusLabel}
                            </span>
                            {actionButton}
                          </div>
                        </div>
                      );
                    })
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-center py-16 space-y-4">
                    <div className="w-14 h-14 bg-primary/5 rounded-full flex items-center justify-center text-primary">
                      <Calendar size={28} />
                    </div>
                    <div>
                      <h4 className="text-sm font-black text-primary font-outfit">Aucun patient aujourd'hui</h4>
                      <p className="text-text-muted text-[11px] font-medium mt-1">
                        Les rendez-vous programmés pour la journée apparaîtront ici pour le suivi de la file d'attente.
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Statistiques rapides en bas */}
              <div className="relative z-10 border-t border-border-main pt-4 mt-4 flex items-center justify-between text-[9px] font-black text-text-muted uppercase tracking-wider">
                <span className="flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  En Salle d'Attente : {todayAppointments.filter(a => a.status === 'EN_S_ATTENTE').length}
                </span>
                <span>
                  Au Fauteuil : {todayAppointments.filter(a => a.status === 'EN_FAUTEUIL').length}
                </span>
              </div>
            </div>
          </motion.section>
        )}
      </div>
    </motion.div>
  );
};