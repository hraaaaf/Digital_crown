import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { Shield, Clock, CalendarRange, UserPlus, Zap, CheckCircle2, XCircle, Mail, Archive, AlertTriangle, MessageSquare, History, Ban, MoreVertical, Search, Filter } from 'lucide-react';
import toast from 'react-hot-toast';
import { DigitalCrownLoader } from '../../components/DigitalCrownLoader';

interface ClientStats {
  total_patients: number;
  total_ia_panoramique: number;
  total_ia_cephalo: number;
}

interface Client {
  id: number;
  nom_complet: string;
  email: string;
  telephone: string;
  cabinet_name: string;
  is_licensed: boolean;
  license_expires_at: string | null;
  created_at: string;
  is_archived: boolean;
  is_suspended: boolean;
  internal_notes: string | null;
  last_login_at: string | null;
  stats: ClientStats;
}

export const SuperAdminDashboard: React.FC = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('ALL');
  
  // Modals state
  const [notesModal, setNotesModal] = useState<{isOpen: boolean, clientId: number | null, notes: string}>({isOpen: false, clientId: null, notes: ''});
  const [historyModal, setHistoryModal] = useState<{isOpen: boolean, clientId: number | null, history: any[]}>({isOpen: false, clientId: null, history: []});

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

  const handleToggleArchive = async (userId: number) => {
    try {
      await api.patch(`/superadmin/clients/${userId}/archive`);
      toast.success("Statut d'archivage mis à jour");
      fetchClients();
    } catch (err) {
      toast.error("Erreur lors de l'archivage");
    }
  };

  const handleToggleSuspend = async (userId: number) => {
    try {
      await api.patch(`/superadmin/clients/${userId}/suspend`);
      toast.success("Statut de suspension mis à jour");
      fetchClients();
    } catch (err) {
      toast.error("Erreur lors de la suspension");
    }
  };

  const handleSendRenewalEmail = async (userId: number) => {
    try {
      await api.post(`/superadmin/clients/${userId}/send-renewal-email`, { message: "Votre licence expire bientôt." });
      toast.success("Email de relance envoyé !");
    } catch (err) {
      toast.error("Erreur lors de l'envoi de l'email");
    }
  };

  const saveNotes = async () => {
    if(!notesModal.clientId) return;
    try {
      await api.patch(`/superadmin/clients/${notesModal.clientId}/notes`, { internal_notes: notesModal.notes });
      toast.success("Notes mises à jour");
      setNotesModal({isOpen: false, clientId: null, notes: ''});
      fetchClients();
    } catch (err) {
      toast.error("Erreur lors de la mise à jour des notes");
    }
  };

  const openHistory = async (userId: number) => {
    try {
      const res = await api.get(`/superadmin/clients/${userId}/license-history`);
      setHistoryModal({isOpen: true, clientId: userId, history: res.data});
    } catch (err) {
      toast.error("Erreur lors du chargement de l'historique");
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "N/A";
    const d = new Date(dateString);
    return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  const getExpirationStatus = (dateString: string | null) => {
    if (!dateString) return { expired: true, daysLeft: 0 };
    const diffTime = new Date(dateString).getTime() - new Date().getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return { expired: diffDays <= 0, daysLeft: diffDays };
  };

  const filteredClients = clients.filter(c => {
    if (search && !c.nom_complet?.toLowerCase().includes(search.toLowerCase()) && !c.email.toLowerCase().includes(search.toLowerCase())) {
      return false;
    }
    if (filterStatus === 'ACTIVE') return c.is_licensed && !getExpirationStatus(c.license_expires_at).expired && !c.is_suspended && !c.is_archived;
    if (filterStatus === 'EXPIRED') return getExpirationStatus(c.license_expires_at).expired && !c.is_archived;
    if (filterStatus === 'ARCHIVED') return c.is_archived;
    if (filterStatus === 'SUSPENDED') return c.is_suspended;
    return true; // ALL
  });

  if (loading) {
    return <DigitalCrownLoader text="Vérification Sécurité..." textColor="text-[#003380]" spinnerColor="border-[#003380]" />;
  }

  return (
    <div className="min-h-screen bg-slate-50 pb-20 relative">
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
              <p className="text-blue-200 font-medium mt-1">Gestion Globale des Licences & Clients</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="bg-white/10 border border-white/20 rounded-2xl px-6 py-4 flex flex-col items-center">
              <span className="text-3xl font-black text-amber-400">{clients.length}</span>
              <span className="text-[10px] uppercase tracking-widest font-bold text-blue-200">Total Clients</span>
            </div>
            <div className="bg-white/10 border border-white/20 rounded-2xl px-6 py-4 flex flex-col items-center">
              <span className="text-3xl font-black text-emerald-400">
                {clients.filter(c => c.is_licensed && !getExpirationStatus(c.license_expires_at).expired && !c.is_suspended && !c.is_archived).length}
              </span>
              <span className="text-[10px] uppercase tracking-widest font-bold text-blue-200">Actifs</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 mt-8 space-y-6">
        
        {/* Filters */}
        <div className="flex flex-col sm:flex-row justify-between gap-4 bg-white p-4 rounded-2xl shadow-sm border border-slate-200">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input 
              type="text" 
              placeholder="Rechercher un client (Nom, email)..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter size={18} className="text-slate-400" />
            <select 
              value={filterStatus} 
              onChange={(e) => setFilterStatus(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 font-bold text-slate-700 outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ALL">Tous les statuts</option>
              <option value="ACTIVE">Actifs</option>
              <option value="EXPIRED">Expirés</option>
              <option value="SUSPENDED">Suspendus</option>
              <option value="ARCHIVED">Archivés</option>
            </select>
          </div>
        </div>

        {/* CARDS */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredClients.map(client => {
            const expStatus = getExpirationStatus(client.license_expires_at);
            const active = client.is_licensed && !expStatus.expired && !client.is_suspended && !client.is_archived;
            
            // Badge color logic
            let badgeStyle = "bg-slate-100 text-slate-600 border-slate-200";
            let badgeText = "Inconnu";
            let BadgeIcon = AlertTriangle;

            if (client.is_archived) {
              badgeStyle = "bg-slate-100 text-slate-500 border-slate-300";
              badgeText = "Archivé";
              BadgeIcon = Archive;
            } else if (client.is_suspended) {
              badgeStyle = "bg-orange-100 text-orange-700 border-orange-200 shadow-orange-500/10";
              badgeText = "Suspendu";
              BadgeIcon = Ban;
            } else if (expStatus.expired) {
              badgeStyle = "bg-rose-100 text-rose-700 border-rose-200 shadow-rose-500/10";
              badgeText = "Expiré";
              BadgeIcon = XCircle;
            } else {
              badgeStyle = "bg-emerald-100 text-emerald-700 border-emerald-200 shadow-emerald-500/10";
              badgeText = "Actif";
              BadgeIcon = CheckCircle2;
              if (expStatus.daysLeft <= 7) {
                badgeStyle = "bg-rose-100 text-rose-700 border-rose-200 shadow-rose-500/10";
                badgeText = `Expire < 7j (${expStatus.daysLeft}j)`;
              } else if (expStatus.daysLeft <= 30) {
                badgeStyle = "bg-amber-100 text-amber-700 border-amber-200 shadow-amber-500/10";
                badgeText = `Expire < 30j (${expStatus.daysLeft}j)`;
              }
            }

            return (
              <div key={client.id} className={`bg-white border border-slate-200 rounded-[2rem] shadow-sm hover:shadow-xl transition-all overflow-hidden flex flex-col group relative ${client.is_archived ? 'opacity-60' : ''}`}>
                
                {/* Header Card */}
                <div className={`p-6 border-b flex justify-between items-start transition-colors ${active ? 'bg-emerald-50/50 border-emerald-100' : 'bg-slate-50 border-slate-100'}`}>
                  <div>
                    <h3 className="text-lg font-black text-slate-800 flex items-center gap-2">
                      {client.nom_complet || 'Sans Nom'}
                      {client.internal_notes && (
                        <div title={client.internal_notes} className="w-5 h-5 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center cursor-help">
                          <MessageSquare size={12} />
                        </div>
                      )}
                    </h3>
                    <p className="text-sm font-bold text-slate-500">{client.cabinet_name || 'Cabinet N/A'}</p>
                    <p className="text-xs text-slate-400 mt-1">{client.email} • {client.telephone}</p>
                  </div>
                  <div className={`px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider flex items-center gap-2 border shadow-sm ${badgeStyle}`}>
                    <BadgeIcon size={16} />
                    {badgeText}
                  </div>
                </div>

                {/* Body Card */}
                <div className="p-6 flex-grow flex flex-col sm:flex-row justify-between gap-6">
                  
                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-4 w-full sm:w-auto">
                    <div className="flex flex-col gap-1">
                      <p className="text-slate-400 text-[10px] font-bold uppercase tracking-wider flex items-center gap-1"><CalendarRange size={12}/> Expiration</p>
                      <p className={`font-black text-sm ${expStatus.expired ? 'text-rose-600' : 'text-slate-700'}`}>{formatDate(client.license_expires_at)}</p>
                    </div>
                    <div className="flex flex-col gap-1">
                      <p className="text-slate-400 text-[10px] font-bold uppercase tracking-wider flex items-center gap-1"><UserPlus size={12}/> Patients</p>
                      <p className="font-black text-sm text-slate-700">{client.stats?.total_patients || 0}</p>
                    </div>
                    <div className="flex flex-col gap-1">
                      <p className="text-slate-400 text-[10px] font-bold uppercase tracking-wider flex items-center gap-1"><Zap size={12}/> IA Pano</p>
                      <p className="font-black text-sm text-slate-700">{client.stats?.total_ia_panoramique || 0}</p>
                    </div>
                    <div className="flex flex-col gap-1">
                      <p className="text-slate-400 text-[10px] font-bold uppercase tracking-wider flex items-center gap-1"><Zap size={12}/> IA Ceph</p>
                      <p className="font-black text-sm text-slate-700">{client.stats?.total_ia_cephalo || 0}</p>
                    </div>
                  </div>

                  {/* Actions Rapides */}
                  <div className="flex flex-col gap-2 min-w-[200px] border-l border-slate-100 pl-0 sm:pl-6">
                    <div className="grid grid-cols-2 gap-2">
                      <button onClick={() => handleGrantLicense(client.id, '1m')} disabled={client.is_archived} className="px-3 py-2 bg-blue-50 hover:bg-blue-600 hover:text-white text-blue-700 rounded-xl text-[10px] font-black transition-all border border-blue-100 disabled:opacity-50">
                        + 1 MOIS
                      </button>
                      <button onClick={() => handleGrantLicense(client.id, '3m')} disabled={client.is_archived} className="px-3 py-2 bg-blue-50 hover:bg-blue-600 hover:text-white text-blue-700 rounded-xl text-[10px] font-black transition-all border border-blue-100 disabled:opacity-50">
                        + 3 MOIS
                      </button>
                      <button onClick={() => handleGrantLicense(client.id, '6m')} disabled={client.is_archived} className="px-3 py-2 bg-blue-50 hover:bg-blue-600 hover:text-white text-blue-700 rounded-xl text-[10px] font-black transition-all border border-blue-100 disabled:opacity-50">
                        + 6 MOIS
                      </button>
                      <button onClick={() => handleGrantLicense(client.id, '1y')} disabled={client.is_archived} className="px-3 py-2 bg-indigo-50 hover:bg-indigo-600 hover:text-white text-indigo-700 rounded-xl text-[10px] font-black transition-all border border-indigo-100 disabled:opacity-50 flex items-center justify-center gap-1">
                        <Zap size={12} /> + 1 AN
                      </button>
                    </div>
                    
                    {/* Admin Actions */}
                    <div className="flex flex-wrap gap-2 mt-2 pt-2 border-t border-slate-100">
                      <button onClick={() => setNotesModal({isOpen: true, clientId: client.id, notes: client.internal_notes || ''})} title="Notes internes" className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg transition-colors">
                        <MessageSquare size={14} />
                      </button>
                      <button onClick={() => openHistory(client.id)} title="Historique Licences" className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg transition-colors">
                        <History size={14} />
                      </button>
                      <button onClick={() => handleSendRenewalEmail(client.id)} title="Email de relance" disabled={client.is_archived} className="p-2 bg-slate-100 hover:bg-blue-100 hover:text-blue-600 text-slate-600 rounded-lg transition-colors disabled:opacity-50">
                        <Mail size={14} />
                      </button>
                      <button onClick={() => { if(window.confirm(`Voulez-vous ${client.is_suspended ? 'réactiver' : 'suspendre'} ce client ?`)) handleToggleSuspend(client.id); }} title={client.is_suspended ? 'Réactiver' : 'Suspendre'} className={`p-2 rounded-lg transition-colors ${client.is_suspended ? 'bg-orange-100 text-orange-600 hover:bg-orange-200' : 'bg-slate-100 text-slate-600 hover:bg-orange-100 hover:text-orange-600'}`}>
                        <Ban size={14} />
                      </button>
                      <button onClick={() => { if(window.confirm(`Voulez-vous ${client.is_archived ? 'désarchiver' : 'archiver'} ce client ?`)) handleToggleArchive(client.id); }} title={client.is_archived ? 'Désarchiver' : 'Archiver'} className={`p-2 rounded-lg transition-colors ${client.is_archived ? 'bg-rose-100 text-rose-600 hover:bg-rose-200' : 'bg-slate-100 text-slate-600 hover:bg-rose-100 hover:text-rose-600'}`}>
                        <Archive size={14} />
                      </button>
                    </div>
                  </div>

                </div>
              </div>
            );
          })}
        </div>

      </div>

      {/* NOTES MODAL */}
      {notesModal.isOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 w-full max-w-md shadow-2xl">
            <h3 className="text-xl font-black text-slate-800 mb-4 flex items-center gap-2"><MessageSquare size={20} className="text-blue-600"/> Notes Internes (SuperAdmin)</h3>
            <textarea 
              className="w-full h-32 p-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none resize-none"
              placeholder="Notes sur ce client (visibles uniquement par les super admins)..."
              value={notesModal.notes}
              onChange={(e) => setNotesModal({...notesModal, notes: e.target.value})}
            ></textarea>
            <div className="flex gap-3 mt-4">
              <button onClick={() => setNotesModal({isOpen: false, clientId: null, notes: ''})} className="flex-1 py-3 font-bold text-slate-600 bg-slate-100 rounded-xl hover:bg-slate-200 transition-colors">Annuler</button>
              <button onClick={saveNotes} className="flex-1 py-3 font-bold text-white bg-blue-600 rounded-xl hover:bg-blue-700 transition-colors">Enregistrer</button>
            </div>
          </div>
        </div>
      )}

      {/* HISTORY MODAL */}
      {historyModal.isOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 w-full max-w-2xl shadow-2xl max-h-[80vh] flex flex-col">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-black text-slate-800 flex items-center gap-2"><History size={20} className="text-blue-600"/> Historique Licences</h3>
              <button onClick={() => setHistoryModal({isOpen: false, clientId: null, history: []})} className="p-2 bg-slate-100 hover:bg-slate-200 rounded-full"><XCircle size={20} className="text-slate-500"/></button>
            </div>
            <div className="overflow-y-auto flex-1 pr-2 space-y-3">
              {historyModal.history.length === 0 ? (
                <p className="text-center text-slate-500 py-4">Aucun historique disponible.</p>
              ) : (
                historyModal.history.map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center p-3 bg-slate-50 rounded-xl border border-slate-100">
                    <div>
                      <p className="font-bold text-slate-700 capitalize">{item.action.replace('_', ' ')}</p>
                      <p className="text-xs text-slate-400">{formatDate(item.timestamp)}</p>
                    </div>
                    {item.duration && (
                      <div className="bg-emerald-100 text-emerald-700 px-2 py-1 rounded-lg text-xs font-black">
                        +{item.duration} jours
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
