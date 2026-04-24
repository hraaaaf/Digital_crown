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
  weekly_activity: number[]; // Tableau de 7 valeurs pour le graphique
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
        const response = await api.get('/dashboard/stats');
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
      
      {/* HEADER GREETING */}
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

      {/* QUICK ACTIONS GRID */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        
        {/* ACTION: AJOUT PATIENT */}
        <Link to="/patients/new" className="group p-8 rounded-[2.5rem] shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 relative overflow-hidden" style={{ backgroundImage: 'linear-gradient(to bottom right, var(--primary), var(--secondary, #1e3a8a))', boxShadow: '0 20px 40px -15px var(--primary)' }}>
          <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16 blur-2xl group-hover:scale-150 transition-transform duration-700" />
          <div className="relative z-10">
            <div className="w-16 h-16 bg-white/20 backdrop-blur-md rounded-2xl flex items-center justify-center mb-8 border border-white/30 group-hover:rotate-12 transition-transform">
              <UserPlus className="text-white" size={32} />
            </div>
            <h3 className="text-2xl font-black text-white leading-none">Nouveau Patient</h3>
            <p className="text-white/70 mt-2 font-medium">Ouvrir un dossier clinique complet</p>
          </div>
        </Link>

        {/* ACTION: RECHERCHE / LISTE */}
        <Link to="/patients" className="group bg-white p-8 rounded-[2.5rem] border border-slate-200/60 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 relative overflow-hidden">
          <div className="w-14 h-14 bg-slate-50 rounded-2xl flex items-center justify-center mb-6 border border-slate-100 group-hover:bg-primary group-hover:text-white transition-all duration-300" style={{ color: 'var(--primary)' }}>
            <Users size={28} />
          </div>
          <h3 className="text-xl font-black tracking-tight" style={{ color: 'var(--primary)' }}>Base de Données</h3>
          <p className="text-slate-500 mt-1 font-medium italic">Gérez vos dossiers patients</p>
        </Link>

        {/* ACTION: AGENDA */}
        <Link to="/agenda" className="group bg-white p-8 rounded-[2.5rem] border border-slate-200/60 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 relative overflow-hidden">
          <div className="w-14 h-14 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center mb-6 border border-emerald-100 group-hover:bg-emerald-600 group-hover:text-white transition-all duration-300">
            <Calendar size={28} />
          </div>
          <h3 className="text-xl font-black text-slate-800 tracking-tight">Agenda Clinique</h3>
          <p className="text-slate-500 mt-1 font-medium italic">Suivi des rendez-vous</p>
        </Link>

      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
        {/* SECTION PATIENTS RÉCENTS */}
        <section className="space-y-5">
          <h2 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-2 px-4 flex items-center gap-2">
            <Clock size={18} /> Activité Récente
          </h2>
          
          <div className="bg-white/80 backdrop-blur-xl border border-slate-200/60 rounded-[2.5rem] p-4 shadow-sm">
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
                      <div className="w-14 h-14 bg-blue-50/50 text-[#003380] rounded-xl flex items-center justify-center font-black text-xl border border-blue-100/50 group-hover:bg-[#003380] group-hover:text-white transition-all duration-300 shadow-sm">
                        {(patient.nom || '?').charAt(0)}
                      </div>
                      <div>
                        <h4 className="font-black text-[#003380] text-lg leading-none">
                          {(patient.nom || '').toUpperCase()} {patient.prenom || ''}
                        </h4>
                        <p className="text-xs font-bold text-slate-400 mt-1.5 flex items-center gap-2">
                          <FileText size={14} className="text-blue-400" /> {patient.acte || 'Consultation'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-xs font-bold text-slate-400 bg-white px-3 py-1.5 rounded-lg border border-slate-100 shadow-sm">
                        {patient.time || 'Récemment'}
                      </span>
                      <ChevronRight size={18} className="text-slate-300 group-hover:text-[#003380] transition-colors" />
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

        {/* SECTION KPI & DATA VIZ */}
        <section className="space-y-5">
          <h2 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-2 px-4 flex items-center gap-2">
            <TrendingUp size={18} /> Statistiques
          </h2>
          
          <div className="bg-white/80 backdrop-blur-xl border border-slate-200/60 rounded-[2.5rem] p-8 shadow-sm flex flex-col gap-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-50 p-5 rounded-2xl border border-slate-100 text-center">
                <p className="text-[10px] font-black text-slate-400 uppercase mb-1">Patients</p>
                <p className="text-3xl font-black text-[#003380]">{stats?.total_patients ?? 0}</p>
              </div>
              <div className="bg-blue-50 p-5 rounded-2xl border border-blue-100 text-center">
                <p className="text-[10px] font-black text-blue-500 uppercase mb-1">Analyses</p>
                <p className="text-3xl font-black text-[#003380]">{stats?.total_analyses ?? 0}</p>
              </div>
            </div>
            
            <hr className="border-slate-100" />

            {/* GRAPHIQUE D'ACTIVITÉ SÉCURISÉ */}
            <div>
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Activité Hebdomadaire</p>
              <div className="h-32 flex items-end justify-between gap-2">
                {(stats?.weekly_activity || [0,0,0,0,0,0,0]).map((height, i) => (
                  <div key={i} className="w-full bg-slate-100 rounded-t-lg relative overflow-hidden h-full flex items-end">
                    <div 
                      className="w-full bg-gradient-to-t from-[#003380] to-blue-500 rounded-t-lg transition-all duration-500"
                      style={{ height: `${height || 5}%` }}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};