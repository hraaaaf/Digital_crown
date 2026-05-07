import React, { useState, useEffect, useCallback } from 'react';
import {
  UserPlus,
  Shield,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Trash2,
  Eye,
  EyeOff,
  X,
  Users,
  Mail,
  Phone,
  Lock
} from 'lucide-react';
import { api } from '../../services/api';
import { cn } from '../../utils/cn';

// --- TYPES ---

interface TeamMember {
  id: number;
  email: string;
  role: string;
  nom_complet: string | null;
  telephone_mobile: string | null;
  is_active: boolean;
  created_at: string | null;
}

interface CreateForm {
  email: string;
  password: string;
  nom_complet: string;
  telephone_mobile: string;
}

// --- COMPOSANT PRINCIPAL ---

export const TeamManager: React.FC = () => {
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const [form, setForm] = useState<CreateForm>({
    email: '',
    password: '',
    nom_complet: '',
    telephone_mobile: ''
  });

  const fetchMembers = useCallback(async () => {
    try {
      const res = await api.get('/team/');
      setMembers(res.data);
    } catch {
      console.error("Erreur chargement équipe");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMembers();
  }, [fetchMembers]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError(null);
    setSuccess(null);

    try {
      await api.post('/team/', form);
      setSuccess(`Compte créé pour ${form.nom_complet} !`);
      setForm({ email: '', password: '', nom_complet: '', telephone_mobile: '' });
      setShowForm(false);
      fetchMembers();
      setTimeout(() => setSuccess(null), 4000);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Erreur lors de la création du compte.");
    } finally {
      setCreating(false);
    }
  };

  const toggleActive = async (member: TeamMember) => {
    try {
      await api.put(`/team/${member.id}`, { is_active: !member.is_active });
      fetchMembers();
    } catch {
      setError("Erreur lors de la modification du statut.");
    }
  };

  const deleteMember = async (member: TeamMember) => {
    if (!confirm(`Supprimer définitivement le compte de ${member.nom_complet || member.email} ?`)) return;
    try {
      await api.delete(`/team/${member.id}`);
      setSuccess("Compte supprimé.");
      fetchMembers();
      setTimeout(() => setSuccess(null), 3000);
    } catch {
      setError("Erreur lors de la suppression.");
    }
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-right-4 duration-500">
      
      {/* HEADER */}
      <div className="flex items-center justify-between pb-6 border-b border-slate-100">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-primary/5 rounded-2xl flex items-center justify-center shadow-inner border border-primary/10" style={{ color: 'var(--primary)' }}>
            <Users size={32} />
          </div>
          <div>
            <h3 className="text-2xl font-black" style={{ color: 'var(--primary)' }}>Mon Équipe</h3>
            <p className="text-slate-500 text-sm font-medium mt-1">
              Gérez les sous-comptes de vos assistantes. Elles auront un accès restreint (Agenda, Patients, Salle d'attente).
            </p>
          </div>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-6 py-3 text-white font-bold rounded-xl transition-all shadow-lg flex items-center gap-2 hover:brightness-110"
          style={{ backgroundColor: 'var(--primary)', boxShadow: '0 10px 25px -8px var(--primary)' }}
        >
          {showForm ? <X size={18} /> : <UserPlus size={18} />}
          {showForm ? 'Annuler' : 'Ajouter une assistante'}
        </button>
      </div>

      {/* NOTIFICATIONS */}
      {success && (
        <div className="flex items-center gap-3 p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-700 animate-in fade-in duration-300">
          <CheckCircle2 size={20} />
          <span className="font-bold text-sm">{success}</span>
        </div>
      )}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 animate-in fade-in duration-300">
          <AlertTriangle size={20} />
          <span className="font-bold text-sm">{error}</span>
          <button onClick={() => setError(null)} className="ml-auto"><X size={16} /></button>
        </div>
      )}

      {/* FORMULAIRE DE CRÉATION */}
      {showForm && (
        <form
          onSubmit={handleCreate}
          className="bg-slate-50 border border-slate-200 rounded-2xl p-8 space-y-6 animate-in slide-in-from-top-4 duration-300"
        >
          <h4 className="font-black text-lg text-slate-800 flex items-center gap-2">
            <UserPlus size={20} style={{ color: 'var(--primary)' }} />
            Nouveau sous-compte
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="md:col-span-2">
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1">
                Nom complet de l'assistante
              </label>
              <div className="relative">
                <Users size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  value={form.nom_complet}
                  onChange={(e) => setForm(f => ({ ...f, nom_complet: e.target.value }))}
                  className="w-full pl-11 pr-5 py-4 bg-white border border-slate-200 rounded-xl text-sm outline-none focus:ring-4 transition-all font-bold text-slate-800"
                  style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)' } as any}
                  placeholder="Ex: Fatima Zahra"
                  required
                />
              </div>
            </div>

            <div>
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1">
                Email de connexion
              </label>
              <div className="relative">
                <Mail size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm(f => ({ ...f, email: e.target.value }))}
                  className="w-full pl-11 pr-5 py-4 bg-white border border-slate-200 rounded-xl text-sm outline-none focus:ring-4 transition-all font-bold text-slate-800"
                  style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)' } as any}
                  placeholder="assistante@cabinet.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1">
                Mot de passe provisoire
              </label>
              <div className="relative">
                <Lock size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={form.password}
                  onChange={(e) => setForm(f => ({ ...f, password: e.target.value }))}
                  className="w-full pl-11 pr-12 py-4 bg-white border border-slate-200 rounded-xl text-sm outline-none focus:ring-4 transition-all font-bold text-slate-800"
                  style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)' } as any}
                  placeholder="••••••••"
                  minLength={4}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div>
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1">
                Téléphone (optionnel)
              </label>
              <div className="relative">
                <Phone size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="tel"
                  value={form.telephone_mobile}
                  onChange={(e) => setForm(f => ({ ...f, telephone_mobile: e.target.value }))}
                  className="w-full pl-11 pr-5 py-4 bg-white border border-slate-200 rounded-xl text-sm outline-none focus:ring-4 transition-all font-bold text-slate-800"
                  style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)' } as any}
                  placeholder="06 00 00 00 00"
                />
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={creating}
              className="px-8 py-4 text-white rounded-xl font-black transition-all shadow-xl flex items-center gap-3 disabled:opacity-70"
              style={{ backgroundColor: 'var(--primary)', boxShadow: '0 10px 30px -10px var(--primary)' }}
            >
              {creating ? <Loader2 className="animate-spin" size={20} /> : <UserPlus size={20} />}
              {creating ? 'Création en cours...' : 'Créer le compte'}
            </button>
            <p className="text-xs text-slate-400 font-medium max-w-xs">
              L'assistante pourra se connecter avec cet email et ce mot de passe.
            </p>
          </div>
        </form>
      )}

      {/* LISTE DES MEMBRES */}
      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="animate-spin" style={{ color: 'var(--primary)' }} size={40} />
        </div>
      ) : members.length === 0 ? (
        <div className="bg-slate-50 border border-dashed border-slate-200 rounded-2xl p-16 text-center">
          <div className="w-20 h-20 bg-primary/5 rounded-full flex items-center justify-center mx-auto mb-6" style={{ color: 'var(--primary)' }}>
            <Users size={36} />
          </div>
          <h4 className="text-xl font-black text-slate-700">Aucune assistante enregistrée</h4>
          <p className="text-slate-500 text-sm mt-2 max-w-md mx-auto">
            Ajoutez un premier sous-compte pour permettre à votre assistante de gérer l'agenda et la file d'attente des patients.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {members.map((member) => (
            <div
              key={member.id}
              className={cn(
                "flex items-center justify-between p-5 bg-white border rounded-2xl shadow-sm transition-all hover:shadow-md group",
                member.is_active ? "border-slate-200" : "border-rose-200 bg-rose-50/30 opacity-70"
              )}
            >
              {/* Infos du membre */}
              <div className="flex items-center gap-4">
                <div
                  className={cn(
                    "w-12 h-12 rounded-xl flex items-center justify-center text-white font-black text-lg shadow-md",
                    member.is_active ? "" : "bg-slate-400"
                  )}
                  style={member.is_active ? { backgroundColor: 'var(--primary)' } : undefined}
                >
                  {(member.nom_complet || 'A')[0].toUpperCase()}
                </div>
                <div>
                  <h4 className="font-black text-slate-800 flex items-center gap-2">
                    {member.nom_complet || 'Sans nom'}
                    {!member.is_active && (
                      <span className="text-[9px] font-black bg-rose-100 text-rose-600 px-2 py-0.5 rounded-full uppercase tracking-wider">
                        Suspendu
                      </span>
                    )}
                  </h4>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs text-slate-500 font-medium flex items-center gap-1">
                      <Mail size={12} /> {member.email}
                    </span>
                    {member.telephone_mobile && (
                      <span className="text-xs text-slate-500 font-medium flex items-center gap-1">
                        <Phone size={12} /> {member.telephone_mobile}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => toggleActive(member)}
                  className={cn(
                    "p-2.5 rounded-xl transition-all text-sm font-bold flex items-center gap-2",
                    member.is_active
                      ? "bg-amber-50 text-amber-600 hover:bg-amber-100 border border-amber-200"
                      : "bg-emerald-50 text-emerald-600 hover:bg-emerald-100 border border-emerald-200"
                  )}
                  title={member.is_active ? "Suspendre l'accès" : "Réactiver l'accès"}
                >
                  <Shield size={16} />
                  <span className="hidden xl:inline">{member.is_active ? 'Suspendre' : 'Réactiver'}</span>
                </button>
                <button
                  onClick={() => deleteMember(member)}
                  className="p-2.5 bg-rose-50 text-rose-500 hover:bg-rose-100 border border-rose-200 rounded-xl transition-all"
                  title="Supprimer définitivement"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
