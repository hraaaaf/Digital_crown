import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { Crown, CheckCircle2, XCircle, Shield, Clock, CalendarRange, UserPlus, Zap } from 'lucide-react';
import toast from 'react-hot-toast';
import { DigitalCrownLoader } from '../../components/DigitalCrownLoader';

interface Client {
  id: number;
  nom_complet: string;
  email: string;
  telephone: string;
  cabinet_name: string;
  total_patients: number;
  is_licensed: boolean;
  license_expires_at: string | null;
  created_at: string;
}

export const SuperAdminDashboard: React.FC = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchClients = async () => {
    setLoading(true);
    try {
      const res = await api.get('/superadmin/clients');
      setClients(res.data);
    } catch (err: any) {
      if (err.response?.status === 403) {
        toast.error("Accès refusé. Réservé au SuperAdmin.");
      } else {
        toast.error("Erreur lors de la récupération des clients.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClients();
  }, []);

  const handleGrantLicense = async (userId: number, action: string) => {
    try {
      await api.post(`/superadmin/clients/${userId}/grant-license`, null, { params: { action } });
      toast.success(action === 'revoke' ? 'Licence révoquée' : 'Licence mise à jour avec succès');
      fetchClients();
    } catch (err) {
      toast.error("Erreur lors de la mise à jour de la licence.");
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "N/A";
    const d = new Date(dateString);
    return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  const isExpired = (dateString: string | null) => {
    if (!dateString) return true;
    return new Date(dateString) < new Date();
  };

  if (loading) {
    return <DigitalCrownLoader text="Vérification Sécurité..." textColor="text-[#003380]" spinnerColor="border-[#003380]" />;
  }

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      {/* HEADER */}
      <div className="bg-[#003380] text-white py-12 px-6 shadow-xl relative overflow-hidden">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-white via-transparent to-transparent"></div>
        <div className="max-w-7xl mx-auto relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center gap-6">
            <div className="w-16 h-16 bg-white/10 rounded-2xl flex items-center justify-center border border-white/20 shadow-lg backdrop-blur-sm">
              <Shield className="text-amber-400" size={32} />
            </div>
            <div>
              <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
                Digital Crown <span className="bg-amber-400 text-amber-950 px-3 py-1 rounded-lg text-sm font-black uppercase tracking-widest border border-amber-300">SuperAdmin</span>
              </h1>
              <p className="text-blue-200 font-medium mt-1">Gestion Globale des Licences SaaS</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="bg-white/10 border border-white/20 rounded-2xl px-6 py-4 flex flex-col items-center">
              <span className="text-3xl font-black text-amber-400">{clients.length}</span>
              <span className="text-[10px] uppercase tracking-widest font-bold text-blue-200">Cabinets Inscrits</span>
            </div>
            <div className="bg-white/10 border border-white/20 rounded-2xl px-6 py-4 flex flex-col items-center">
              <span className="text-3xl font-black text-emerald-400">
                {clients.filter(c => c.is_licensed && !isExpired(c.license_expires_at)).length}
              </span>
              <span className="text-[10px] uppercase tracking-widest font-bold text-blue-200">Licences Actives</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 mt-8 space-y-6">
        
        {/* CARDS POUR MOBILE & DESKTOP (Responsive) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {clients.map(client => {
            const active = client.is_licensed && !isExpired(client.license_expires_at);
            return (
              <div key={client.id} className="bg-white border border-slate-200 rounded-[2rem] shadow-sm hover:shadow-xl transition-all overflow-hidden flex flex-col group relative">
                
                {/* Header Card */}
                <div className={`p-6 border-b flex justify-between items-start transition-colors ${active ? 'bg-emerald-50/50 border-emerald-100' : 'bg-rose-50/50 border-rose-100'}`}>
                  <div>
                    <h3 className="text-lg font-black text-slate-800">{client.nom_complet}</h3>
                    <p className="text-sm font-bold text-slate-500">{client.cabinet_name}</p>
                    <p className="text-xs text-slate-400 mt-1">{client.email} • {client.telephone}</p>
                  </div>
                  <div className={`px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider flex items-center gap-2 border ${active ? 'bg-emerald-100 text-emerald-700 border-emerald-200 shadow-sm shadow-emerald-500/10' : 'bg-rose-100 text-rose-700 border-rose-200 shadow-sm shadow-rose-500/10'}`}>
                    {active ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
                    {active ? 'Actif' : 'Expiré'}
                  </div>
                </div>

                {/* Body Card */}
                <div className="p-6 flex-grow flex flex-col sm:flex-row justify-between gap-6">
                  
                  {/* Stats */}
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 text-sm">
                      <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center"><CalendarRange size={16} /></div>
                      <div>
                        <p className="text-slate-400 text-xs font-bold uppercase tracking-wider">Expiration</p>
                        <p className={`font-black ${active ? 'text-slate-700' : 'text-rose-600'}`}>{formatDate(client.license_expires_at)}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                      <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center"><UserPlus size={16} /></div>
                      <div>
                        <p className="text-slate-400 text-xs font-bold uppercase tracking-wider">Patients gérés</p>
                        <p className="font-black text-slate-700">{client.total_patients} dossiers</p>
                      </div>
                    </div>
                  </div>

                  {/* Actions (Boutons de temps) */}
                  <div className="flex flex-col gap-2 min-w-[200px]">
                    <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Actions Licence</p>
                    <div className="grid grid-cols-2 gap-2">
                      <button onClick={() => handleGrantLicense(client.id, '1m')} className="px-3 py-2 bg-blue-50 hover:bg-blue-600 hover:text-white text-blue-700 rounded-xl text-xs font-black transition-all border border-blue-100">
                        + 1 Mois
                      </button>
                      <button onClick={() => handleGrantLicense(client.id, '3m')} className="px-3 py-2 bg-blue-50 hover:bg-blue-600 hover:text-white text-blue-700 rounded-xl text-xs font-black transition-all border border-blue-100">
                        + 3 Mois
                      </button>
                      <button onClick={() => handleGrantLicense(client.id, '6m')} className="px-3 py-2 bg-blue-50 hover:bg-blue-600 hover:text-white text-blue-700 rounded-xl text-xs font-black transition-all border border-blue-100">
                        + 6 Mois
                      </button>
                      <button onClick={() => handleGrantLicense(client.id, '1y')} className="px-3 py-2 bg-indigo-50 hover:bg-indigo-600 hover:text-white text-indigo-700 rounded-xl text-xs font-black transition-all border border-indigo-100 flex items-center justify-center gap-1">
                        <Zap size={14} /> + 1 An
                      </button>
                    </div>
                    {active && (
                      <button onClick={() => { if(window.confirm("Révoquer l'accès de ce cabinet ?")) handleGrantLicense(client.id, 'revoke'); }} className="mt-2 w-full px-3 py-2 bg-rose-50 hover:bg-rose-600 hover:text-white text-rose-600 rounded-xl text-xs font-black transition-all border border-rose-100">
                        Révoquer l'accès
                      </button>
                    )}
                  </div>

                </div>
              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
};
