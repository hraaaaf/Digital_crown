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
  Lock,
  Clock,
  TrendingUp,
  CheckCheck,
  XCircle,
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
  approval_status?: string | null;
  approval_note?: string | null;
  created_at: string | null;
  permissions?: {
    agenda?: boolean;
    patients?: boolean;
    prescriptions?: boolean;
    accounting?: boolean;
    payments?: boolean;
    clinical?: boolean;
    panoramic?: boolean;
    cephalo?: boolean;
    settings?: boolean;
  } | null;
}

interface QuotaData {
  plan: string;
  dentistes_used: number;
  dentistes_max: number;
  secretaires_used: number;
  secretaires_max: number;
  pending_count: number;
  can_add_dentiste: boolean;
  can_add_secretaire: boolean;
}

interface CreateForm {
  email: string;
  password: string;
  nom_complet: string;
  telephone_mobile: string;
  role: string;
  permissions: {
    agenda: boolean;
    patients: boolean;
    prescriptions: boolean;
    accounting: boolean;
    payments: boolean;
    clinical: boolean;
    panoramic: boolean;
    cephalo: boolean;
    settings: boolean;
  };
}

// --- COMPOSANT PRINCIPAL ---

export const TeamManager: React.FC = () => {
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [quota, setQuota] = useState<QuotaData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [editingPermissionsMember, setEditingPermissionsMember] = useState<TeamMember | null>(null);
  const [approvingId, setApprovingId] = useState<number | null>(null);

  const [form, setForm] = useState<CreateForm>({
    email: '',
    password: '',
    nom_complet: '',
    telephone_mobile: '',
    role: 'SECRETAIRE',
    permissions: {
      agenda: true,
      patients: true,
      prescriptions: false,
      accounting: false,
      payments: false,
      clinical: false,
      panoramic: false,
      cephalo: false,
      settings: false
    }
  });

  const fetchMembers = useCallback(async () => {
    try {
      const [membersRes, quotaRes] = await Promise.all([
        api.get(`/team/?_t=${Date.now()}`),
        api.get('/team/quota'),
      ]);
      if (Array.isArray(membersRes.data)) {
        setMembers(membersRes.data);
      } else {
        setMembers([]);
      }
      setQuota(quotaRes.data);
    } catch {
      console.error("Erreur chargement équipe");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMembers();
  }, [fetchMembers]);

  const approveMember = async (member: TeamMember) => {
    setApprovingId(member.id);
    setError(null);
    try {
      await api.post(`/team/${member.id}/approve`);
      setSuccess(`${member.nom_complet || member.email} est maintenant actif.`);
      fetchMembers();
      setTimeout(() => setSuccess(null), 4000);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Erreur lors de l'approbation.");
    } finally {
      setApprovingId(null);
    }
  };

  const rejectMember = async (member: TeamMember) => {
    if (!confirm(`Refuser l'accès de ${member.nom_complet || member.email} ?`)) return;
    setError(null);
    try {
      await api.post(`/team/${member.id}/reject`);
      setSuccess(`Demande de ${member.nom_complet || member.email} refusée.`);
      fetchMembers();
      setTimeout(() => setSuccess(null), 4000);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Erreur lors du refus.");
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError(null);
    setSuccess(null);

    try {
      await api.post('/team/', form);
      setSuccess(`Compte créé pour ${form.nom_complet} !`);
      setForm({
        email: '',
        password: '',
        nom_complet: '',
        telephone_mobile: '',
        role: 'SECRETAIRE',
        permissions: {
          agenda: true,
          patients: true,
          prescriptions: false,
          accounting: false,
          payments: false,
          clinical: false,
          panoramic: false,
          cephalo: false,
          settings: false
        }
      });
      setShowForm(false);
      fetchMembers();
      setTimeout(() => setSuccess(null), 4000);
    } catch (err: any) {
      let errorMessage = "Erreur lors de la création du compte.";
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          // FastAPI Validation Error
          const msgs = detail.map(d => {
            if (d.loc?.includes('password') && (d.type === 'string_too_short' || d.type === 'string_too_long')) {
              return "Le mot de passe doit contenir entre 8 et 128 caractères.";
            }
            if (d.loc?.includes('email')) {
              return "L'adresse email est invalide.";
            }
            if (d.loc?.includes('nom_complet') && d.type === 'string_too_short') {
              return "Le nom complet est trop court.";
            }
            return "Vérifiez vos informations.";
          });
          errorMessage = msgs[0]; // On affiche la première erreur pour ne pas surcharger
        } else if (typeof detail === 'string') {
          errorMessage = detail;
        }
      }
      setError(errorMessage);
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
    <div className="min-w-0 space-y-8 animate-in slide-in-from-right-4 duration-500">
      
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100">
        <div className="flex items-center gap-4 min-w-0">
          <div className="w-16 h-16 shrink-0 bg-primary/5 rounded-2xl flex items-center justify-center shadow-inner border border-primary/10" style={{ color: 'var(--primary)' }}>
            <Users size={32} />
          </div>
          <div className="min-w-0">
            <h3 className="text-2xl font-black" style={{ color: 'var(--primary)' }}>Mon Équipe</h3>
            <p className="text-slate-500 text-sm font-medium mt-1 break-words">
              Gérez les sous-comptes de vos collaborateurs (Assistantes, Dentistes associés).
            </p>
          </div>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="self-start sm:self-auto shrink-0 px-6 py-3 text-white font-bold rounded-xl transition-all shadow-lg flex items-center gap-2 hover:brightness-110"
          style={{ backgroundColor: 'var(--primary)', boxShadow: '0 10px 25px -8px var(--primary)' }}
        >
          {showForm ? <X size={18} /> : <UserPlus size={18} />}
          {showForm ? 'Annuler' : 'Ajouter un membre'}
        </button>
      </div>

      {/* QUOTA BANNER */}
      {quota && (
        <div className="bg-slate-50 border border-slate-200 rounded-2xl p-5 flex flex-wrap items-center gap-4 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Plan</span>
            <span
              className="px-3 py-1 rounded-full text-xs font-black"
              style={{ backgroundColor: 'var(--primary)', color: '#fff' }}
            >
              {quota.plan}
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-sm font-bold text-slate-700">
            <Users size={15} className="text-slate-400" />
            Dentistes :
            <span className={cn("font-black", !quota.can_add_dentiste ? "text-rose-600" : "text-emerald-600")}>
              {quota.dentistes_used}/{quota.dentistes_max}
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-sm font-bold text-slate-700">
            <Shield size={15} className="text-slate-400" />
            Assistantes :
            <span className={cn("font-black", !quota.can_add_secretaire ? "text-rose-600" : "text-emerald-600")}>
              {quota.secretaires_used}/{quota.secretaires_max}
            </span>
          </div>
          {quota.pending_count > 0 && (
            <div className="flex items-center gap-1.5 text-sm font-bold text-amber-600">
              <Clock size={15} />
              {quota.pending_count} en attente
            </div>
          )}
          {(!quota.can_add_dentiste || !quota.can_add_secretaire) && (
            <div className="sm:ml-auto max-w-full flex items-center gap-2 px-4 py-2 bg-amber-50 border border-amber-200 rounded-xl text-amber-700 text-xs font-black">
              <TrendingUp size={14} className="shrink-0" />
              <span className="break-words">Quota atteint — passez au plan supérieur</span>
            </div>
          )}
        </div>
      )}

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
          className="min-w-0 bg-slate-50 border border-slate-200 rounded-2xl p-5 sm:p-8 space-y-6 animate-in slide-in-from-top-4 duration-300"
        >
          <h4 className="font-black text-lg text-slate-800 flex items-center gap-2">
            <UserPlus size={20} style={{ color: 'var(--primary)' }} />
            Nouveau sous-compte
          </h4>

          <div className="min-w-0 grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="min-w-0 md:col-span-2">
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1">
                Nom complet du collaborateur
              </label>
              <div className="relative min-w-0">
                <Users size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  value={form.nom_complet}
                  onChange={(e) => setForm(f => ({ ...f, nom_complet: e.target.value }))}
                  className="min-w-0 w-full pl-11 pr-5 py-4 bg-white border border-slate-200 rounded-xl text-sm outline-none focus:ring-4 transition-all font-bold text-slate-800"
                  style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)' } as any}
                  placeholder="Ex: Fatima Zahra"
                  required
                />
              </div>
            </div>

            <div className="min-w-0 md:col-span-2">
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1">
                Rôle du collaborateur
              </label>
              <select
                value={form.role}
                onChange={(e) => {
                  const role = e.target.value;
                  setForm(f => ({
                    ...f,
                    role,
                    permissions: role === 'DENTISTE' 
                      ? { agenda: true, patients: true, prescriptions: true, accounting: true, payments: true, clinical: true, panoramic: true, cephalo: true, settings: false }
                      : { agenda: true, patients: true, prescriptions: false, accounting: false, payments: false, clinical: false, panoramic: false, cephalo: false, settings: false }
                  }));
                }}
                className="min-w-0 w-full px-5 py-4 bg-white border border-slate-200 rounded-xl text-sm outline-none focus:ring-4 transition-all font-bold text-slate-800"
                style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)' } as any}
              >
                <option value="SECRETAIRE">Assistante (Accès restreint par défaut)</option>
                <option value="DENTISTE">Dentiste Associé (Accès complet par défaut)</option>
              </select>
            </div>

            <div className="min-w-0">
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1">
                Email de connexion
              </label>
              <div className="relative min-w-0">
                <Mail size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm(f => ({ ...f, email: e.target.value }))}
                  className="min-w-0 w-full pl-11 pr-5 py-4 bg-white border border-slate-200 rounded-xl text-sm outline-none focus:ring-4 transition-all font-bold text-slate-800"
                  style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)' } as any}
                  placeholder="assistante@cabinet.com"
                  required
                />
              </div>
            </div>

            <div className="min-w-0">
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1">
                Mot de passe provisoire
              </label>
              <div className="relative min-w-0">
                <Lock size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={form.password}
                  onChange={(e) => setForm(f => ({ ...f, password: e.target.value }))}
                  className="min-w-0 w-full pl-11 pr-12 py-4 bg-white border border-slate-200 rounded-xl text-sm outline-none focus:ring-4 transition-all font-bold text-slate-800"
                  style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)' } as any}
                  placeholder="••••••••"
                  minLength={8}
                  maxLength={128}
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
              <p className="mt-2 ml-1 text-[11px] font-bold text-slate-400">8 à 128 caractères</p>
            </div>

            <div className="min-w-0">
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1">
                Téléphone (optionnel)
              </label>
              <div className="relative min-w-0">
                <Phone size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="tel"
                  value={form.telephone_mobile}
                  onChange={(e) => setForm(f => ({ ...f, telephone_mobile: e.target.value }))}
                  className="min-w-0 w-full pl-11 pr-5 py-4 bg-white border border-slate-200 rounded-xl text-sm outline-none focus:ring-4 transition-all font-bold text-slate-800"
                  style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)' } as any}
                  placeholder="06 00 00 00 00"
                />
              </div>
            </div>

            <div className="min-w-0 md:col-span-2 border-t border-slate-200 pt-6">
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-4 ml-1">
                Permissions d'accès granulaires
              </label>
              <div className="min-w-0 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {[
                  { key: 'agenda', label: 'Studio Agenda', desc: 'Gestion des rendez-vous et plannings' },
                  { key: 'patients', label: 'Dossiers Patients', desc: 'Création, modification et fiches patients' },
                  { key: 'prescriptions', label: 'Studio Prescriptions', desc: 'Rédaction d\'ordonnances cliniques' },
                  { key: 'accounting', label: 'Comptabilité & Chiffres', desc: 'Statistiques financières et paiements' },
                  { key: 'payments', label: 'Encaissements', desc: 'Valider et enregistrer les paiements' },
                  { key: 'clinical', label: 'Examen Clinique & IA', desc: 'Diagnostic, plan de traitement, synthèses IA' },
                  { key: 'panoramic', label: 'Imagerie OPG IA', desc: 'Analyses radio panoramiques' },
                  { key: 'cephalo', label: 'Tracés Céphalométriques', desc: 'Analyses et rapports ortho' },
                  { key: 'settings', label: 'Réglages Cabinet', desc: 'Configuration de l\'en-tête et thèmes' }
                ].map((perm) => (
                  <label
                    key={perm.key}
                    className={cn(
                      "min-w-0 flex items-start gap-3 p-4 rounded-xl border transition-all cursor-pointer select-none",
                      form.permissions[perm.key as keyof typeof form.permissions]
                        ? "bg-primary/5 border-primary/20"
                        : "bg-white border-slate-200 hover:bg-slate-50"
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={form.permissions[perm.key as keyof typeof form.permissions]}
                      onChange={(e) => setForm(f => ({
                        ...f,
                        permissions: {
                          ...f.permissions,
                          [perm.key]: e.target.checked
                        }
                      }))}
                      className="mt-1 h-4 w-4 shrink-0 rounded border-slate-300 text-primary focus:ring-primary/20 accent-primary"
                    />
                    <div className="min-w-0">
                      <span className="block break-words text-sm font-black text-slate-800" style={form.permissions[perm.key as keyof typeof form.permissions] ? { color: 'var(--primary)' } : {}}>{perm.label}</span>
                      <span className="block break-words text-[11px] font-bold text-slate-400 mt-0.5">{perm.desc}</span>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center gap-3 pt-2 min-w-0">
            <button
              type="submit"
              disabled={creating}
              className="self-start shrink-0 px-8 py-4 text-white rounded-xl font-black transition-all shadow-xl flex items-center gap-3 disabled:opacity-70"
              style={{ backgroundColor: 'var(--primary)', boxShadow: '0 10px 30px -10px var(--primary)' }}
            >
              {creating ? <Loader2 className="animate-spin" size={20} /> : <UserPlus size={20} />}
              {creating ? 'Création en cours...' : 'Créer le compte'}
            </button>
            <p className="min-w-0 text-xs text-slate-400 font-medium max-w-xs break-words">
              L'accès de ce membre sera sécurisé avec cet email et ce mot de passe.
            </p>
          </div>
        </form>
      )}

      {/* SECTION EN ATTENTE */}
      {!loading && members.filter(m => m.approval_status === 'pending').length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-black uppercase tracking-widest text-amber-600 flex items-center gap-2">
            <Clock size={14} /> En attente d'approbation ({members.filter(m => m.approval_status === 'pending').length})
          </h4>
          {members.filter(m => m.approval_status === 'pending').map((member) => (
            <div
              key={member.id}
              className="flex items-center justify-between p-5 bg-amber-50 border border-amber-200 rounded-2xl shadow-sm"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-amber-200 text-amber-800 font-black text-lg">
                  {(member.nom_complet || 'A')[0].toUpperCase()}
                </div>
                <div>
                  <h4 className="font-black text-slate-800 flex items-center gap-2">
                    {member.nom_complet || 'Sans nom'}
                    <span className="text-[9px] font-black bg-amber-100 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full uppercase tracking-wider">
                      En attente
                    </span>
                    <span className="text-[9px] font-black bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full uppercase tracking-wider">
                      {member.role}
                    </span>
                  </h4>
                  <span className="text-xs text-slate-500 font-medium flex items-center gap-1 mt-1">
                    <Mail size={12} /> {member.email}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => approveMember(member)}
                  disabled={approvingId === member.id}
                  className="px-4 py-2 bg-emerald-600 text-white text-xs font-black rounded-xl shadow transition-all hover:brightness-110 flex items-center gap-2 disabled:opacity-60"
                >
                  {approvingId === member.id ? <Loader2 size={14} className="animate-spin" /> : <CheckCheck size={14} />}
                  Valider
                </button>
                <button
                  onClick={() => rejectMember(member)}
                  className="px-4 py-2 bg-rose-50 text-rose-600 border border-rose-200 text-xs font-black rounded-xl transition-all hover:bg-rose-100 flex items-center gap-2"
                >
                  <XCircle size={14} />
                  Refuser
                </button>
                <button
                  onClick={() => deleteMember(member)}
                  className="p-2.5 bg-slate-50 text-slate-400 hover:text-rose-500 hover:bg-rose-50 border border-slate-200 rounded-xl transition-all"
                  title="Supprimer définitivement"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
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
          <h4 className="text-xl font-black text-slate-700">Aucun membre dans l'équipe</h4>
          <p className="text-slate-500 text-sm mt-2 max-w-md mx-auto">
            Ajoutez un premier sous-compte pour permettre à votre équipe de gérer le cabinet.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {members.filter(m => m.approval_status !== 'pending').map((member) => (
            <div
              key={member.id}
              className={cn(
                "flex items-center justify-between p-5 bg-white border rounded-2xl shadow-sm transition-all hover:shadow-md group",
                member.approval_status === 'rejected'
                  ? "border-rose-200 bg-rose-50/20 opacity-60"
                  : member.is_active ? "border-slate-200" : "border-amber-200 bg-amber-50/20 opacity-75"
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
                    <span className="text-[9px] font-black bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full uppercase tracking-wider">
                      {member.role}
                    </span>
                    {member.approval_status === 'rejected' && (
                      <span className="text-[9px] font-black bg-rose-100 text-rose-600 px-2 py-0.5 rounded-full uppercase tracking-wider">
                        Refusé
                      </span>
                    )}
                    {!member.is_active && member.approval_status !== 'rejected' && (
                      <span className="text-[9px] font-black bg-amber-100 text-amber-600 px-2 py-0.5 rounded-full uppercase tracking-wider">
                        Suspendu
                      </span>
                    )}
                    {member.is_active && (
                      <span className="text-[9px] font-black bg-emerald-100 text-emerald-600 px-2 py-0.5 rounded-full uppercase tracking-wider">
                        Actif
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
                  onClick={() => setEditingPermissionsMember(member)}
                  className="p-2.5 bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200 rounded-xl transition-all text-xs font-bold flex items-center gap-2"
                  title="Gérer les permissions"
                >
                  <Lock size={14} />
                  <span className="hidden xl:inline">Permissions</span>
                </button>
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

      {/* MODAL D'ÉDITION DES PERMISSIONS */}
      {editingPermissionsMember && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[11000] flex items-center justify-center p-4 animate-in fade-in duration-300">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-2xl w-full p-8 shadow-2xl relative animate-in zoom-in-95 duration-300 space-y-6">
            <button
              onClick={() => setEditingPermissionsMember(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-2 hover:bg-slate-50 rounded-xl transition-all"
            >
              <X size={20} />
            </button>

            <div>
              <h3 className="text-xl font-black text-slate-800 flex items-center gap-2">
                <Lock size={22} style={{ color: 'var(--primary)' }} />
                Droits d'accès : {editingPermissionsMember.nom_complet || editingPermissionsMember.email}
              </h3>
              <p className="text-slate-500 text-xs font-medium mt-1">
                Configurez les accès précis de votre collaborateur aux modules cliniques et administratifs.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              {[
                { key: 'agenda', label: 'Studio Agenda', desc: 'Gestion des rendez-vous et plannings' },
                { key: 'patients', label: 'Dossiers Patients', desc: 'Création, modification et fiches patients' },
                { key: 'prescriptions', label: 'Studio Prescriptions', desc: 'Rédaction d\'ordonnances cliniques' },
                { key: 'accounting', label: 'Comptabilité & Chiffres', desc: 'Statistiques financières et paiements' },
                { key: 'payments', label: 'Encaissements', desc: 'Valider et enregistrer les paiements' },
                { key: 'clinical', label: 'Examen Clinique & IA', desc: 'Diagnostic, plan de traitement, synthèses IA' },
                { key: 'panoramic', label: 'Imagerie OPG IA', desc: 'Analyses radio panoramiques' },
                { key: 'cephalo', label: 'Tracés Céphalométriques', desc: 'Analyses et rapports ortho' },
                { key: 'settings', label: 'Réglages Cabinet', desc: 'Configuration de l\'en-tête et thèmes' }
              ].map((perm) => {
                const isChecked = editingPermissionsMember.permissions?.[perm.key as keyof typeof editingPermissionsMember.permissions] ?? false;
                return (
                  <label
                    key={perm.key}
                    className={cn(
                      "flex items-start gap-3 p-4 rounded-xl border transition-all cursor-pointer select-none",
                      isChecked ? "bg-primary/5 border-primary/20" : "bg-slate-50/50 border-slate-200 hover:bg-slate-50"
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={(e) => {
                        const newPerms = {
                          ...(editingPermissionsMember.permissions || {}),
                          [perm.key]: e.target.checked
                        };
                        setEditingPermissionsMember(prev => prev ? {
                          ...prev,
                          permissions: newPerms
                        } : null);
                      }}
                      className="mt-1 h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary/20 accent-primary"
                    />
                    <div>
                      <span className="block text-sm font-black text-slate-800" style={isChecked ? { color: 'var(--primary)' } : {}}>{perm.label}</span>
                      <span className="block text-[11px] font-bold text-slate-400 mt-0.5">{perm.desc}</span>
                    </div>
                  </label>
                );
              })}
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setEditingPermissionsMember(null)}
                className="px-5 py-2.5 text-xs font-bold text-slate-500 hover:text-slate-700 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-xl transition-all"
              >
                Annuler
              </button>
              <button
                type="button"
                onClick={async () => {
                  try {
                    await api.put(`/team/${editingPermissionsMember.id}`, {
                      permissions: editingPermissionsMember.permissions
                    });
                    setSuccess(`Permissions de ${editingPermissionsMember.nom_complet || editingPermissionsMember.email} mises à jour !`);
                    setEditingPermissionsMember(null);
                    fetchMembers();
                    setTimeout(() => setSuccess(null), 3000);
                  } catch (err: any) {
                    setError(err.response?.data?.detail || "Erreur de mise à jour.");
                  }
                }}
                className="px-6 py-2.5 text-xs font-black text-white rounded-xl shadow-md transition-all hover:brightness-110"
                style={{ backgroundColor: 'var(--primary)' }}
              >
                Enregistrer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};