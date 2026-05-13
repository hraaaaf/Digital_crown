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

    fetchStats();
  }, []);

  if (loading) return (
    <div className="h-full flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <Loader2 className="w-12 h-12 animate-spin" style={{ color: 'var(--primary)' }} />
        <p className="text-slate-400 font-black uppercase tracking-widest text-xs">Initialisation de votre cabinet...</p>
      </div>
    </div>
  );

  return (
    <div className="max-w-[1600px] mx-auto w-full px-6 py-8 md:px-10 md:py-10 space-y-12 animate-in fade-in duration-700">
      
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 className="text-4xl font-black tracking-tight" style={{ color: 'var(--primary)' }}>Bonjour, Dr. Benmoussa</h1>
          <div className="flex items-center gap-3 mt-2 bg-white/60 backdrop-blur-md px-4 py-2 rounded-2xl border border-slate-200/60 w-fit">
            <Calendar size={16} style={{ color: 'var(--primary)' }} />
            <p className="text-slate-500 font-bold text-sm">{formatDate(today)}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4 bg-white/40 p-2 rounded-3xl border border-white/60 shadow-sm">
          <div className="px-6 py-3 rounded-2xl flex flex-col items-end">
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Status Système</span>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-sm font-black text-slate-700 uppercase tracking-tighter">Elite Cloud Connecté</span>
            </div>
          </div>
        </div>
      </header>

      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        <Link to="/patients/new" data-tour="quick-action-new-patient" className="group p-8 rounded-[2.5rem] shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 relative overflow-hidden" style={{ backgroundImage: 'linear-gradient(to bottom right, var(--primary), var(--secondary, #1e3a8a))', boxShadow: '0 20px 40px -15px var(--primary)' }}>
          <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16 blur-2xl group-hover:scale-150 transition-transform duration-700" />
          <div className="relative z-10">
            <div className="w-16 h-16 bg-white/20 backdrop-blur-md rounded-2xl flex items-center justify-center mb-8 border border-white/30 group-hover:rotate-12 transition-transform">
              <UserPlus className="text-white" size={32} />
            </div>
            <h3 className="text-2xl font-black text-white leading-none">Nouveau Patient</h3>
            <p className="text-white/70 mt-2 font-medium">Ouvrir un dossier clinique complet</p>
          </div>
        </Link>

        <Link to="/patients" className="group bg-white p-8 rounded-[2.5rem] border border-slate-200/60 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 relative overflow-hidden">
          <div className="w-14 h-14 bg-slate-50 rounded-2xl flex items-center justify-center mb-6 border border-slate-100 group-hover:bg-primary group-hover:text-white transition-all duration-300" style={{ color: 'var(--primary)' }}>
            <Users size={28} />
          </div>
          <h3 className="text-xl font-black tracking-tight" style={{ color: 'var(--primary)' }}>Dossiers Patients</h3>
          <p className="text-slate-500 mt-1 font-medium italic">Gestion de la patientèle</p>
        </Link>

        <Link to="/agenda" className="group bg-white p-8 rounded-[2.5rem] border border-slate-200/60 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 relative overflow-hidden">
          <div className="w-14 h-14 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center mb-6 border border-emerald-100 group-hover:bg-emerald-600 group-hover:text-white transition-all duration-300">
            <Calendar size={28} />
          </div>
          <h3 className="text-xl font-black text-slate-800 tracking-tight">Agenda Clinique</h3>
          <p className="text-slate-500 mt-1 font-medium italic">Suivi des rendez-vous</p>
        </Link>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
        <section data-tour="dashboard-agenda" className="space-y-5">
          <h2 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-2 px-4 flex items-center gap-2">
            <Clock size={18} /> Activité Récente
          </h2>
          
          <div data-tour="dashboard-activity" className="bg-card backdrop-blur-xl border border-border-main rounded-[2.5rem] p-4 shadow-sm">
            {stats?.recent_patients && stats.recent_patients.length > 0 ? (
              stats.recent_patients.map((patient, index) => {
                if (!patient || !patient.nom) return null;

                return (
                  <Link 
                    key={patient.id} 
                    to={`/patients/${patient.id}`}
                    className={cn(
                      "flex items-center justify-between p-4 hover:bg-slate-50/80 rounded-2xl transition-all duration-300 group",
                      index !== (stats.recent_patients.length - 1) && "border-b border-slate-100"
                    )}
                  >
                    <div className="flex items-center gap-5">
                      <div className="w-14 h-14 bg-primary/10 text-primary rounded-xl flex items-center justify-center font-black text-xl border border-primary/20 group-hover:bg-primary group-hover:text-white transition-all duration-300 shadow-sm">
                        {(patient.nom || '?').charAt(0)}
                      </div>
                      <div>
                        <div className="flex items-center gap-3">
                          <h4 className="font-black text-primary text-lg leading-none">
                            {(patient.nom || '').toUpperCase()} {patient.prenom || ''}
                          </h4>
                          <PatientScoreBadge patientId={patient.id} className="scale-75 origin-left" />
                        </div>
                        <p className="text-xs font-bold text-slate-500 mt-1.5 flex items-center gap-2">
                          <FileText size={14} className="text-blue-400" /> {patient.acte || 'Consultation'}
                          <span className="text-slate-300">·</span>
                          <span>{patient.time || 'Récemment'}</span>
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center">
                      <ChevronRight size={18} className="text-slate-300 group-hover:text-primary transition-colors group-hover:translate-x-0.5 transition-transform" />
                    </div>
                  </Link>
                );
              })
            ) : (
              <div className="py-12 text-center">
                <p className="text-slate-400 font-medium italic">Aucun patient récent à afficher.</p>
              </div>
            )}
          </div>
        </section>

        <section className="space-y-5">
          <h2 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-2 px-4 flex items-center gap-2">
            <TrendingUp size={18} /> Performance Hebdomadaire
          </h2>
          <div className="bg-white rounded-[2.5rem] border border-slate-200/60 p-8 h-[380px] shadow-sm flex items-center justify-center">
            <div className="flex flex-col items-center gap-4 text-slate-300">
               <TrendingUp size={48} />
               <p className="font-bold text-sm uppercase tracking-widest">Graphique d'activité bientôt disponible</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};