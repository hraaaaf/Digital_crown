import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { cn } from '../../utils/cn';
import { api } from '../../services/api';
import {
  ArrowLeft,
  Save,
  Loader2,
  User,
  Phone,
  Calendar,
  UserCircle,
  MapPin,
  Activity,
  FileDigit,
  AlertCircle,
  RefreshCw,
  AlertTriangle,
  UserCheck,
  Mail
} from 'lucide-react';
import { MotifSelector } from './components/MotifSelector';


export const EditPatientForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [formData, setFormData] = useState({
    numero_dossier: '',
    nom: '',
    prenom: '',
    date_naissance: '',
    sexe: '',
    telephone: '',
    telephone_2: '',
    telephone_3: '',
    email: '',
    adresse: '',
    assurance: 'AUCUNE',
    assurance_privee_nom: '',
    assurance_complementaire: false,
    assurance_complementaire_nom: '',
    antecedents_medicaux: '',
    motif_consultation: [] as string[]
  });
  const [showPhone2, setShowPhone2] = useState(false);
  const [showPhone3, setShowPhone3] = useState(false);
  const [numeroError, setNumeroError] = useState('');
  const [dossierStatus, setDossierStatus] = useState<{ status: 'idle' | 'checking' | 'available' | 'taken' | 'unknown', owner?: string }>({ status: 'idle' });
  const [originalNumero, setOriginalNumero] = useState('');

  // Chargement initial des données du patient
  useEffect(() => {
    const fetchPatient = async () => {
      try {
        setLoading(true);
        const res = await api.get(`/patients/${id}`);
        const patient = res.data;

        // Formater la date de naissance pour l'input type="date" (YYYY-MM-DD)
        let dateFormatted = '';
        if (patient.date_naissance) {
          const date = new Date(patient.date_naissance);
          dateFormatted = date.toISOString().split('T')[0];
        }

        setFormData({
          numero_dossier: patient.numero_dossier || '',
          nom: patient.nom || '',
          prenom: patient.prenom || '',
          date_naissance: dateFormatted,
          sexe: patient.sexe || '',
          telephone: patient.telephone || '',
          telephone_2: patient.telephone_2 || '',
          telephone_3: patient.telephone_3 || '',
          email: patient.email || '',
          adresse: patient.adresse || '',
          assurance: patient.assurance || 'AUCUNE',
          assurance_privee_nom: patient.assurance_privee_nom || '',
          assurance_complementaire: patient.assurance_complementaire || false,
          assurance_complementaire_nom: patient.assurance_complementaire_nom || '',
          antecedents_medicaux: patient.antecedents_medicaux || '',
          motif_consultation: patient.motif_consultation || []
        });
        if (patient.telephone_2) setShowPhone2(true);
        if (patient.telephone_3) setShowPhone3(true);
        setOriginalNumero(patient.numero_dossier || '');
      } catch (err) {
        console.error("Erreur de récupération:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchPatient();
  }, [id]);

  // Check availability when numero_dossier changes
  useEffect(() => {
    if (!formData.numero_dossier || formData.numero_dossier === originalNumero) {
      setDossierStatus({ status: 'idle' });
      return;
    }

    if (formData.numero_dossier.length < 2) {
      setDossierStatus({ status: 'idle' });
      return;
    }

    const timer = setTimeout(async () => {
      setDossierStatus({ status: 'checking' });
      try {
        const res = await api.get(`/patients/check-dossier/${formData.numero_dossier}`);
        if (res.data.exists && res.data.patient_id !== parseInt(id || '0')) {
          setDossierStatus({ status: 'taken', owner: res.data.patient_name });
        } else {
          setDossierStatus({ status: 'available' });
        }
      } catch (err) {
        setDossierStatus({ status: 'unknown' });
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [formData.numero_dossier, originalNumero, id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setNumeroError('');
    if (!formData.sexe) {
      alert("Le sexe doit être sélectionné explicitement.");
      return;
    }
    if (formData.numero_dossier !== originalNumero && dossierStatus.status === 'unknown') {
      setNumeroError("Vérification du numéro de dossier indisponible. Réessayez avant d'enregistrer.");
      return;
    }
    setSaving(true);
    try {
      // Mise à jour via l'API
      await api.put(`/patients/${id}`, formData);
      // Retour immédiat à la fiche patient après succès
      navigate(`/patients/${id}`);
    } catch (err: any) {
      if (err.response?.status === 409) {
        const detail = err.response.data.detail;
        if (detail?.message?.includes('numéro de dossier')) {
          setNumeroError(detail.message);
        } else {
          alert(detail?.message || "Conflit avec un patient existant.");
        }
      } else {
        alert("Erreur lors de la sauvegarde.");
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) return (
    <div className="h-screen flex flex-col items-center justify-center gap-4 bg-slate-50">
      <Loader2 className="animate-spin text-[#003380]" size={48} />
      <p className="text-slate-400 font-black uppercase tracking-widest text-[10px]">Chargement du dossier...</p>
    </div>
  );

  const inputClass = "w-full px-6 py-4 bg-white/70 border border-slate-200 rounded-[1.5rem] focus:ring-4 focus:ring-[#003380]/10 focus:border-[#003380] outline-none transition-all font-bold text-[#003380] placeholder:text-slate-300";
  const labelClass = "text-[11px] font-black text-slate-400 uppercase tracking-[0.2em] ml-5 mb-2 flex items-center gap-2";

  return (
    <div className="max-w-2xl mx-auto p-3 sm:p-6 md:p-10 animate-in slide-in-from-bottom-6 duration-700">

      {/* BOUTON RETOUR : Cohérent avec PatientDetails */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-slate-400 hover:text-[#003380] font-black text-xs uppercase tracking-widest mb-8 transition-colors group"
      >
        <ArrowLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
        Retour au dossier
      </button>

      <div className="bg-white/70 backdrop-blur-2xl p-5 sm:p-8 md:p-12 rounded-[2.5rem] border border-white/80 shadow-[0_20px_50px_rgba(0,0,0,0.05)]">

        <div className="flex items-center gap-6 mb-12">
          <div className="w-16 h-16 bg-[#003380] text-white rounded-3xl flex items-center justify-center shadow-xl shadow-[#003380]/20">
            <UserCircle size={32} strokeWidth={2} />
          </div>
          <div>
            <h2 className="text-3xl font-black text-[#003380] tracking-tight leading-none">Mise à jour</h2>
            <p className="text-slate-400 font-bold text-sm mt-2">Dossier {formData.numero_dossier || `ID-${id}`}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">

          {/* Numéro de dossier - Section spéciale */}
          <div className="p-6 bg-blue-50/50 rounded-2xl border border-blue-100">
            <label className={cn(labelClass, "text-[#003380]")}><FileDigit size={12}/> Numéro de Dossier</label>
            <div className="relative">
              <input
                type="text"
                className={cn(
                  inputClass,
                  "font-mono text-lg tracking-wider",
                  (numeroError || dossierStatus.status === 'taken') && "border-red-400 focus:border-red-400"
                )}
                value={formData.numero_dossier}
                onChange={(e) => {
                  setFormData({...formData, numero_dossier: e.target.value.toUpperCase().trim()});
                  setNumeroError('');
                }}
                placeholder="P-XXXXXX"
              />
              <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-2">
                {dossierStatus.status === 'checking' && <RefreshCw className="w-4 h-4 text-slate-400 animate-spin" />}
                {dossierStatus.status === 'taken' && <AlertTriangle className="w-4 h-4 text-red-500" />}
                {dossierStatus.status === 'available' && <UserCheck className="w-4 h-4 text-emerald-500" />}
                {dossierStatus.status === 'unknown' && <AlertTriangle className="w-4 h-4 text-amber-500" />}
              </div>
            </div>
            {dossierStatus.status === 'taken' && (
              <p className="mt-2 text-sm text-red-600 flex items-center gap-1 font-bold uppercase tracking-tight">
                <AlertTriangle size={14} /> Déjà utilisé par : {dossierStatus.owner}
              </p>
            )}
            {numeroError && !dossierStatus.owner && (
              <p className="mt-2 text-sm text-red-600 flex items-center gap-1">
                <AlertCircle size={14} /> {numeroError}
              </p>
            )}
            {dossierStatus.status === 'available' && (
              <p className="mt-2 text-xs text-emerald-600 font-bold">✓ Numéro disponible</p>
            )}
            {dossierStatus.status === 'unknown' && (
              <p className="mt-2 text-xs text-amber-600 font-bold">Vérification indisponible — réessayez</p>
            )}
            <p className="mt-2 text-xs text-slate-500">
              ⚠️ Modifiez avec précaution - ce numéro est utilisé pour identifier le dossier physique
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className={labelClass}><User size={12}/> Nom</label>
              <input
                type="text"
                className={inputClass}
                value={formData.nom}
                onChange={(e) => setFormData({...formData, nom: e.target.value.toUpperCase()})}
                required
              />
            </div>
            <div>
              <label className={labelClass}><User size={12}/> Prénom</label>
              <input
                type="text"
                className={inputClass}
                value={formData.prenom}
                onChange={(e) => setFormData({...formData, prenom: e.target.value})}
                required
              />
            </div>
          </div>

          <div>
            <label className={labelClass}><Calendar size={12}/> Date de naissance</label>
            <input
              type="date"
              className={inputClass}
              value={formData.date_naissance}
              onChange={(e) => setFormData({...formData, date_naissance: e.target.value})}
              required
            />
          </div>

          <div>
            <label className={labelClass}><User size={12}/> Sexe</label>
            <select
              name="sexe"
              value={formData.sexe}
              onChange={(e) => setFormData({...formData, sexe: e.target.value})}
              className={inputClass}
              required
            >
              <option value="">Sélectionner</option>
              <option value="F">Féminin</option>
              <option value="M">Masculin</option>
            </select>
          </div>

          <div>
            <label className={labelClass}><Activity size={12}/> Assurance / Couverture</label>
            <select
              name="assurance"
              value={formData.assurance}
              onChange={(e) => setFormData({...formData, assurance: e.target.value})}
              className={inputClass}
            >
              <option value="AUCUNE">Aucune (Privé)</option>
              <option value="CNOPS">CNOPS</option>
              <option value="CNSS">CNSS</option>
              <option value="MUTUELLE_FAR">Mutuelle de FAR</option>
              <option value="PRIVEE">Assurance Privée</option>
            </select>

            {formData.assurance === 'PRIVEE' && (
              <div className="mt-3">
                <label className={labelClass}>Nom de l'Assurance Privée</label>
                <input
                  type="text"
                  name="assurance_privee_nom"
                  value={formData.assurance_privee_nom}
                  onChange={(e) => setFormData({...formData, assurance_privee_nom: e.target.value})}
                  className={inputClass}
                  placeholder="Ex: Sanlam, Wafa Assurance..."
                />
              </div>
            )}

            {/* Assurance Complémentaire */}
            <div className="mt-4 pt-4 border-t border-slate-200">
              <label className="flex items-center gap-3 cursor-pointer mb-3">
                <div className={cn(
                  "w-10 h-5 rounded-full transition-all duration-300 relative",
                  formData.assurance_complementaire ? "bg-[#003380]" : "bg-slate-300"
                )}>
                  <div className={cn(
                    "absolute top-1 w-3 h-3 rounded-full bg-white shadow-md transition-all duration-300",
                    formData.assurance_complementaire ? "left-6" : "left-1"
                  )} />
                </div>
                <input
                  type="checkbox"
                  name="assurance_complementaire"
                  checked={formData.assurance_complementaire}
                  onChange={(e) => setFormData({...formData, assurance_complementaire: e.target.checked})}
                  className="hidden"
                />
                <span className="font-bold text-slate-700 text-sm">Assurance Complémentaire</span>
              </label>

              {formData.assurance_complementaire && (
                <div>
                  <label className={labelClass}>Nom de l'Assurance Complémentaire</label>
                  <input
                    type="text"
                    name="assurance_complementaire_nom"
                    value={formData.assurance_complementaire_nom}
                    onChange={(e) => setFormData({...formData, assurance_complementaire_nom: e.target.value})}
                    className={inputClass}
                    placeholder="Ex: Mutuelle interne..."
                  />
                </div>
              )}
            </div>
          </div>

          <div>
            <label className={labelClass}><Phone size={12}/> Téléphone Principal</label>
            <div className="relative mb-2">
              <Phone className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="tel"
                className={cn(inputClass, "pl-14")}
                value={formData.telephone}
                onChange={(e) => setFormData({...formData, telephone: e.target.value})}
                required
              />
            </div>

            {showPhone2 && (
              <div className="relative mb-2 mt-2">
                <Phone className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300" />
                <input
                  type="tel"
                  className={cn(inputClass, "pl-14 py-3")}
                  value={formData.telephone_2}
                  onChange={(e) => setFormData({...formData, telephone_2: e.target.value})}
                  placeholder="Téléphone secondaire"
                />
              </div>
            )}

            {showPhone3 && (
              <div className="relative mb-2 mt-2">
                <Phone className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300" />
                <input
                  type="tel"
                  className={cn(inputClass, "pl-14 py-3")}
                  value={formData.telephone_3}
                  onChange={(e) => setFormData({...formData, telephone_3: e.target.value})}
                  placeholder="Autre numéro"
                />
              </div>
            )}

            {(!showPhone2 || !showPhone3) && (
              <button
                type="button"
                onClick={() => {
                  if (!showPhone2) setShowPhone2(true);
                  else if (!showPhone3) setShowPhone3(true);
                }}
                className="text-xs text-[#003380] font-bold hover:underline"
              >
                + Ajouter un numéro
              </button>
            )}
          </div>

          <div>
            <label className={labelClass}><Mail size={12}/> Email</label>
            <div className="relative">
              <Mail className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="email"
                className={cn(inputClass, "pl-14")}
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                placeholder="yazan.benmoussa@email.com"
              />
            </div>
          </div>

          <div>
            <label className={labelClass}><MapPin size={12}/> Adresse</label>
            <input
              type="text"
              className={inputClass}
              value={formData.adresse}
              onChange={(e) => setFormData({...formData, adresse: e.target.value})}
              placeholder="123 Rue de la Paix, 75000 Paris"
            />
          </div>

          <div>
            <label className={labelClass}><Activity size={12}/> Motif(s) de première consultation</label>
            <MotifSelector
              selected={formData.motif_consultation}
              onChange={(ids) => setFormData({...formData, motif_consultation: ids})}
            />
          </div>

          <div>
            <label className={labelClass}><Activity size={12}/> Historique médical et allergies</label>
            <textarea
              className={cn(inputClass, "min-h-[120px] resize-none")}
              value={formData.antecedents_medicaux}
              onChange={(e) => setFormData({...formData, antecedents_medicaux: e.target.value})}
              placeholder="Ex: Diabète, hypertension, allergie à la pénicilline, traitement en cours..."
              rows={4}
            />
          </div>

          <div className="pt-4">
            <button
              type="submit"
              disabled={saving}
              className="w-full py-5 bg-[#003380] text-white rounded-[1.5rem] font-black text-lg flex items-center justify-center gap-3 shadow-2xl shadow-[#003380]/30 hover:bg-blue-900 transition-all hover:-translate-y-1 active:scale-95 disabled:opacity-50"
            >
              {saving ? <Loader2 className="animate-spin" size={24} /> : <Save size={24} />}
              {saving ? "Enregistrement..." : "Valider les modifications"}
            </button>
          </div>

        </form>
      </div>
    </div>
  );
};
