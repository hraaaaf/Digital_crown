import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  UserPlus, 
  Search, 
  Calendar, 
  Clock, 
  FileText, 
  ChevronRight,
  TrendingUp,
  Loader2
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

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await api.get('/dashboard/stats');
        setStats(response.data);
      } catch (err) {
        console.warn("Route API manquante ou invalide, injection des données de secours.");
        // Rigueur CTO : Fallback Premium pour garantir la continuité de service
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

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full w-full gap-4">
        <Loader2 className="w-12 h-12 text-[#003380] animate-spin" />
        <p className="text-slate-500 font-bold tracking-widest uppercase text-xs animate-pulse">Chargement sécurisé...</p>
      </div>
    );
  }

  return (
    <div className="max-w-[1600px] mx-auto w-full px-6 py-8 md:px-10 md:py-10 space-y-10 animate-in fade-in duration-700">
      
      {/* 1. EN-TÊTE PREMIUM */}
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 bg-white/80 backdrop-blur-xl border border-slate-200/60 p-8 rounded-[2.5rem] shadow-[0_8px_40px_rgba(0,0,0,0.04)]">
        <div>
          <h1 className="text-4xl font-black text-[#003380] tracking-tight">Bonjour, Dr. Benmoussa</h1>
          <p className="text-slate-500 font-medium mt-2 capitalize flex items-center gap-2">
            <Calendar size={16} className="text-[#003380]" />
            {today}
          </p>
        </div>
        <div className="flex gap-4">
          <div className="bg-emerald-50 px-5 py-3 rounded-2xl border border-emerald-100 flex items-center gap-3 shadow-sm">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.6)]"></div>
            <span className="text-sm font-black text-emerald-700 uppercase tracking-wider">Système Opérationnel</span>
          </div>
        </div>
      </header>

      {/* 2. ACTIONS RAPIDES */}
      <section>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Link to="/patients/new" className="group bg-gradient-to-br from-[#003380] to-blue-900 p-8 rounded-[2.5rem] shadow-xl shadow-[#003380]/20 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 relative overflow-hidden">
            <div className="w-14 h-14 bg-white/10 text-white rounded-2xl flex items-center justify-center mb-6 backdrop-blur-md border border-white/20 shadow-inner">
              <UserPlus size={28} />
            </div>
            <h3 className="text-xl font-black text-white">Nouveau Patient</h3>
            <p className="text-blue-200 text-sm mt-2 font-medium">Créer une fiche clinique IA.</p>
          </Link>

          <Link to="/patients" className="group bg-white/80 backdrop-blur-md border border-slate-200/60 p-8 rounded-[2.5rem] shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
            <div className="w-14 h-14 bg-blue-50 text-[#003380] rounded-2xl flex items-center justify-center mb-6 border border-blue-100">
              <Search size={28} />
            </div>
            <h3 className="text-xl font-black text-[#003380]">Base de Données</h3>
            <p className="text-slate-500 text-sm mt-2 font-medium">Accéder aux dossiers patients.</p>
          </Link>

          <div className="group bg-white/40 backdrop-blur-md border border-slate-200/40 p-8 rounded-[2.5rem] shadow-sm flex flex-col justify-between">
            <div className="w-14 h-14 bg-slate-100 text-slate-400 rounded-2xl flex items-center justify-center mb-6 border border-slate-200">
              <Calendar size={28} />
            </div>
            <div>
              <h3 className="text-xl font-black text-slate-700">Agenda Clinique</h3>
              <p className="text-slate-400 text-xs font-bold uppercase tracking-widest mt-2">Mode Consultation Seul</p>
            </div>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        
        {/* SECTION SÉCURISÉE : ACTIVITÉ RÉCENTE */}
        <section className="xl:col-span-2 space-y-5">
          <div className="flex items-center justify-between mb-2 px-4">
            <h2 className="text-sm font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
              <Clock size={18} /> Activité Récente
            </h2>
          </div>
          
          <div className="bg-white/80 backdrop-blur-xl border border-slate-200/60 rounded-[2.5rem] p-4 shadow-sm">
            {stats?.recent_patients && stats.recent_patients.length > 0 ? (
              stats.recent_patients.map((patient, index) => {
                // SÉCURITÉ : Vérification de l'existence du patient et du nom
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
                      {/* SÉCURITÉ : charAt(0) protégé */}
                      <div className="w-14 h-14 bg-blue-50/50 text-[#003380] rounded-xl flex items-center justify-center font-black text-xl border border-blue-100/50 group-hover:bg-[#003380] group-hover:text-white transition-all duration-300 shadow-sm">
                        {(patient.nom || '?').charAt(0)}
                      </div>
                      <div>
                        {/* SÉCURITÉ : toUpperCase() protégé */}
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