import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Save, User, Phone, Mail, Activity, AlertTriangle, UserCheck, FileDigit, RefreshCw, Search, FolderOpen, CheckCircle2 } from 'lucide-react';
import { api } from '../../services/api';
import type { Patient } from '../../types';
import { cn } from '../../utils/cn';
import { MotifSelector } from './components/MotifSelector';
import { createPatientIdentityFormData, patientIdentityToApiPayload, validatePatientIdentity, type DossierStatus } from './PatientIdentityContract';

// Types pour la gestion des doublons
interface DuplicateInfo {
  has_duplicate: boolean;
  existing_patient?: {
    id: number;
    nom: string;
    prenom: string;
    date_naissance: string;
    created_at: string;
  };
}

export const AddPatientForm = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const submissionBusyRef = useRef(false);
  const [createOutcomeUnknown, setCreateOutcomeUnknown] = useState(false);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const globalErrorRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (errors.global) {
      globalErrorRef.current?.scrollIntoView({ block: 'start', behavior: 'auto' });
      globalErrorRef.current?.focus({ preventScroll: true });
    }
  }, [errors.global]);

  const [isOrtho, setIsOrtho] = useState(false);
  
  // Gestion des doublons
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);
  const [duplicateInfo, setDuplicateInfo] = useState<DuplicateInfo | null>(null);
  const [forceCreate, setForceCreate] = useState(false);

  const prefillNom = searchParams.get('nom') || '';
  const prefillPrenom = searchParams.get('prenom') || '';

  // État pour la validation du numéro de dossier
  const [dossierStatus, setDossierStatus] = useState<DossierStatus>({ status: 'idle' });

  const [formData, setFormData] = useState(() => createPatientIdentityFormData({
    nom: prefillNom,
    prenom: prefillPrenom,
  }));

  const [showPhone2, setShowPhone2] = useState(false);
  const [showPhone3, setShowPhone3] = useState(false);

  const fetchNextDossierNumber = async () => {
    try {
      const response = await api.get('/patients/next-dossier-number');
      setFormData((prev: any) => (
        prev.numero_dossier
          ? prev
          : { ...prev, numero_dossier: response.data.next_number }
      ));
    } catch (err) {
      console.error("Erreur lors de la récupération du prochain numéro:", err);
    }
  };

  // Charger le prochain numéro de dossier disponible au chargement
  useEffect(() => {
     
    fetchNextDossierNumber();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Check availability when numero_dossier changes
  useEffect(() => {
    if (!formData.numero_dossier || formData.numero_dossier.length < 2) {
       
      setDossierStatus({ status: 'idle' });
      return;
    }

    const timer = setTimeout(async () => {
      setDossierStatus({ status: 'checking' });
      try {
        const res = await api.get(`/patients/check-dossier/${formData.numero_dossier}`);
        if (res.data.exists) {
          setDossierStatus({ status: 'taken', owner: res.data.patient_name });
        } else {
          setDossierStatus({ status: 'available' });
        }
      } catch (err) {
        console.error('Erreur vérification numéro de dossier:', err);
        setDossierStatus({ status: 'error' });
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [formData.numero_dossier]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    let finalValue: any = value;
    if (type === 'checkbox') {
      finalValue = (e.target as HTMLInputElement).checked;
    } else if (name === 'nom') {
      finalValue = value.toUpperCase();
    }
    
    setFormData((prev: any) => ({ 
      ...prev, 
      [name]: finalValue 
    }));
    if (errors[name]) setErrors({ ...errors, [name]: '' });
    // Réinitialiser le modal doublon si modif
    if (showDuplicateModal) {
      setShowDuplicateModal(false);
      setForceCreate(false);
    }
  };

  const handleNumeroDossierChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.toUpperCase().trim();
    setFormData((prev: any) => ({ ...prev, numero_dossier: value }));
    if (errors.numero_dossier) setErrors({ ...errors, numero_dossier: '' });
  };

  const validate = () => {
    const newErrors = validatePatientIdentity(formData);
    setErrors(newErrors);
    const firstInvalid = ['nom', 'prenom', 'date_naissance', 'sexe', 'numero_dossier'].find(name => newErrors[name]);
    if (firstInvalid) {
      requestAnimationFrame(() => {
        const input = document.querySelector<HTMLInputElement | HTMLSelectElement>(`[name="${firstInvalid}"]`);
        input?.focus();
        input?.scrollIntoView({ block: 'center', behavior: 'auto' });
      });
    }
    return Object.keys(newErrors).length === 0;
  };

  // Vérification préalable des doublons
  const checkDuplicate = async (): Promise<boolean | null> => {
    try {
      const response = await api.post('/patients/check-duplicate', {
        numero_dossier: formData.numero_dossier || null,
        nom: formData.nom,
        prenom: formData.prenom,
        date_naissance: formData.date_naissance,
        sexe: formData.sexe,
        telephone: formData.telephone || null,
        email: formData.email || null,
        adresse: formData.adresse || null,
        antecedents_medicaux: formData.antecedents_medicaux || null
      });
      
      const data: DuplicateInfo = response.data;
      
      if (data.has_duplicate && data.existing_patient) {
        setDuplicateInfo(data);
        setShowDuplicateModal(true);
        return true; // Doublon trouvé
      }
      
      return false; // Pas de doublon
    } catch (err: any) {
      console.warn("Vérification anti-doublon indisponible (statut HTTP uniquement)", { status: err?.response?.status ?? null });
      setErrors(previous => ({ ...previous, global: "Vérification anti-doublon indisponible. Réessayez avant de créer le patient." }));
      return null;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submissionBusyRef.current || !validate()) return;
    submissionBusyRef.current = true;
    setLoading(true);
    setCreateOutcomeUnknown(false);
    try {
      if (!forceCreate && !showDuplicateModal) {
        const hasDuplicate = await checkDuplicate();
        if (hasDuplicate !== false) return;
      }
      await performSubmit(forceCreate);
    } finally {
      submissionBusyRef.current = false;
      setLoading(false);
    }
  };

  const performSubmit = async (isForced: boolean) => {
    setLoading(true);

    const payload = {
      ...patientIdentityToApiPayload(formData),
      is_ortho_active: isOrtho,
    };
    try {
      // Si isForced est true, on ajoute le paramètre force_create
      const url = isForced ? '/patients/?force_create=true' : '/patients/';
      const { data } = await api.post(url, payload);
      navigate(`/patients/${data.id}`);
    } catch (err: any) {
      console.error("Échec création dossier patient (statut HTTP uniquement)", { status: err?.response?.status ?? null });
      
      // Gérer l'erreur 409 (doublon) du backend
      if (err.response?.status === 409) {
        const detail = err.response.data.detail;
        if (detail?.existing_patient) {
          setDuplicateInfo({
            has_duplicate: true,
            existing_patient: detail.existing_patient
          });
          setShowDuplicateModal(true);
          setLoading(false);
          return;
        }
      }
      
      setCreateOutcomeUnknown(true);
      setErrors({ global: "Création non confirmée. Vérifiez dans la liste des patients avant de réessayer pour éviter un doublon." });
      setLoading(false);
    }
  };

  const inputClass = "w-full px-5 py-4 bg-white/60 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-[#003380]/15 focus:border-[#003380] outline-none transition-all duration-300 shadow-sm text-slate-800 font-medium";
  const labelClass = "text-xs sm:text-sm font-bold text-slate-600 tracking-wide block mb-2 ml-1";

  // Formatage de la date pour affichage
  const formatDate = (dateStr: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR');
  };

  return (
    <div className="w-full min-w-0 max-w-4xl mx-auto px-3 sm:px-6 lg:px-10 py-6 lg:py-10">
      <div className="w-full min-w-0 bg-white/70 backdrop-blur-xl rounded-[2.5rem] shadow-[0_20px_60px_rgba(0,0,0,0.05)] border border-white/80 overflow-hidden">
        
        {/* Header Premium */}
        <div className="@container bg-[#003380] px-3 sm:px-10 py-6 sm:py-8 flex justify-between items-center relative overflow-hidden">
          <div className="flex w-full min-w-0 flex-wrap items-center gap-3 sm:gap-5 relative z-10">
            <div className="shrink-0 p-4 bg-white/10 rounded-2xl border border-white/20 backdrop-blur-md">
              <User className="text-white w-8 h-8" />
            </div>
            <div className="min-w-0 flex-[1_1_12rem]">
              <h2 className="break-normal text-[clamp(0.875rem,6cqw,1.5rem)] font-black text-white tracking-tight leading-tight">Nouveau Patient</h2>
              <p className="break-words text-blue-200 text-sm font-medium mt-1">Digital Crown — Vérification anti-doublon activée</p>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} aria-busy={loading} aria-describedby="patient-required-info" className="p-5 sm:p-10 space-y-8 sm:space-y-10">
          <p id="patient-required-info" className="text-sm font-medium text-slate-700">Renseignez le nom, le prénom, la date de naissance et le sexe. Les autres informations sont facultatives.</p>
          <p role="status" aria-live="polite" className="sr-only">{loading ? "Vérification et création du dossier en cours…" : ""}</p>
          {errors.global && (
            <div role="alert" tabIndex={-1} ref={globalErrorRef} className="p-4 bg-red-50 text-red-700 rounded-2xl border border-red-100 flex items-center gap-2 font-bold text-sm">
              <Activity className="w-5 h-5 shrink-0" aria-hidden="true" />
              <span>{errors.global}</span>
              {createOutcomeUnknown && <button type="button" onClick={() => navigate("/patients")} className="ml-auto underline underline-offset-4 rounded focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-800">Consulter les dossiers</button>}
            </div>
          )}
          
          {/* Info pré-remplissage depuis recherche */}
          {(prefillNom || prefillPrenom) && (
            <div className="p-4 bg-blue-50 text-[#003380] rounded-2xl border border-blue-100 flex items-center gap-3 text-sm">
              <Search className="w-5 h-5" />
              <span className="font-medium">
                Patient "<strong>{prefillNom} {prefillPrenom}</strong>" introuvable. 
                Vérifiez les informations et complétez le formulaire ci-dessous.
              </span>
            </div>
          )}

          {/* Section Numéro de Dossier */}
          <div className="space-y-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="h-px flex-1 bg-gradient-to-r from-transparent via-slate-300 to-transparent" />
              <span className="text-xs font-black text-slate-400 uppercase tracking-widest">Numéro de Dossier</span>
              <div className="h-px flex-1 bg-gradient-to-r from-transparent via-slate-300 to-transparent" />
            </div>

            {/* Champ Numéro de dossier Unique */}
            <div className="relative">
              <label htmlFor="patient-numero_dossier" className={labelClass}>Numéro de dossier (Code Patient)</label>
              <div className="relative">
                <FileDigit className={cn(
                  "absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5",
                  dossierStatus.status === 'taken' ? "text-red-500" : "text-[#003380]"
                )} />
                <input 
                  type="text" 
                  id="patient-numero_dossier" 
                  name="numero_dossier" 
                  value={formData.numero_dossier || ''} 
                  onChange={handleNumeroDossierChange}
                  className={cn(
                    inputClass, 
                    "pl-14 font-mono text-lg tracking-wider",
                    dossierStatus.status === 'taken' && "border-red-400 focus:ring-red-100",
                    dossierStatus.status === 'available' && "border-emerald-400 focus:ring-emerald-100"
                  )}
                  placeholder="P-XXXXXX"
                />
                <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-2">
                  {dossierStatus.status === 'checking' && <RefreshCw className="w-4 h-4 text-slate-400 animate-spin" />}
                  {dossierStatus.status === 'taken' && <AlertTriangle className="w-4 h-4 text-red-500" />}
                  {dossierStatus.status === 'available' && <UserCheck className="w-4 h-4 text-emerald-500" />}
                </div>
              </div>
              
              {dossierStatus.status === 'taken' && (
                <p className="text-red-500 text-[10px] font-black uppercase tracking-widest mt-2 ml-1 flex items-center gap-1">
                  <AlertTriangle size={12} /> Ce numéro appartient déjà à : <span className="underline">{dossierStatus.owner}</span>
                </p>
              )}
              {dossierStatus.status === 'available' && (
                <p className="text-emerald-600 text-[10px] font-black uppercase tracking-widest mt-2 ml-1 flex items-center gap-1">
                  <UserCheck size={12} /> Numéro disponible
                </p>
              )}
              {dossierStatus.status === 'error' && (
                <p className="text-amber-600 text-[10px] font-black uppercase tracking-widest mt-2 ml-1 flex items-center gap-1">
                  <AlertTriangle size={12} /> Disponibilité non vérifiée
                </p>
              )}
            </div>

            {/* Champs Nom et Prénom - nécessaires dans les deux cas */}
            <div className="grid md:grid-cols-2 gap-6 pt-4 border-t border-slate-200">
              <div>
                <label htmlFor={"patient-nom"} className={labelClass}>Nom de famille *</label>
                <input 
                  type="text" 
                  id="patient-nom"
                  name="nom"
                  aria-invalid={Boolean(errors.nom)}
                  aria-describedby={errors.nom ? "patient-nom-error" : undefined}
                  value={formData.nom} 
                  onChange={handleChange}
                  className={cn(inputClass, errors.nom && "border-red-400 focus:border-red-400 focus:ring-red-100")}
                  placeholder="BENMOUSSA"
                />
                {errors.nom && <span id="patient-nom-error" className="text-red-500 text-xs mt-1 ml-1">{errors.nom}</span>}
              </div>

              <div>
                <label htmlFor={"patient-prenom"} className={labelClass}>Prénom *</label>
                <input 
                  type="text" 
                  id="patient-prenom"
                  name="prenom"
                  aria-invalid={Boolean(errors.prenom)}
                  aria-describedby={errors.prenom ? "patient-prenom-error" : undefined}
                  value={formData.prenom} 
                  onChange={handleChange}
                  className={cn(inputClass, errors.prenom && "border-red-400 focus:border-red-400 focus:ring-red-100")}
                  placeholder="Yazan"
                />
                {errors.prenom && <span id="patient-prenom-error" className="text-red-500 text-xs mt-1 ml-1">{errors.prenom}</span>}
              </div>
            </div>
          </div>

          {/* Section Identité */}
          <div className="space-y-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="h-px flex-1 bg-gradient-to-r from-transparent via-slate-300 to-transparent" />
              <span className="text-xs font-black text-slate-400 uppercase tracking-widest">Identité Civile</span>
              <div className="h-px flex-1 bg-gradient-to-r from-transparent via-slate-300 to-transparent" />
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label htmlFor={"patient-date_naissance"} className={labelClass}>Date de naissance *</label>
                <input 
                  type="date" 
                  id="patient-date_naissance"
                  name="date_naissance"
                  aria-invalid={Boolean(errors.date_naissance)}
                  aria-describedby={errors.date_naissance ? "patient-date_naissance-error" : undefined}
                  value={formData.date_naissance} 
                  onChange={handleChange}
                  className={cn(inputClass, errors.date_naissance && "border-red-400 focus:border-red-400 focus:ring-red-100")}
                />
                {errors.date_naissance && <span id="patient-date_naissance-error" className="text-red-500 text-xs mt-1 ml-1">{errors.date_naissance}</span>}
              </div>

              <div>
                <label htmlFor={"patient-sexe"} className={labelClass}>Sexe *</label>
                <select 
                  id="patient-sexe"
                  name="sexe"
                  aria-invalid={Boolean(errors.sexe)}
                  aria-describedby={errors.sexe ? "patient-sexe-error" : undefined}
                  value={formData.sexe} 
                  onChange={handleChange}
                  className={cn(inputClass, errors.sexe && "border-red-400 focus:border-red-400 focus:ring-red-100")}
                >
                  <option value="">Choisir…</option>
                  <option value="F">Féminin</option>
                  <option value="M">Masculin</option>
                </select>
                {errors.sexe && <span id="patient-sexe-error" className="text-red-500 text-xs mt-1 ml-1">{errors.sexe}</span>}
              </div>

              <div>
                <label htmlFor="patient-assurance" className={labelClass}>Assurance / Couverture Médicale</label>
                <select 
                  id="patient-assurance" 
                  name="assurance" 
                  value={formData.assurance} 
                  onChange={handleChange}
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
                    <label htmlFor="patient-assurance_privee_nom" className={labelClass}>Nom de l'Assurance Privée</label>
                    <input 
                      type="text" 
                      id="patient-assurance_privee_nom" 
                      name="assurance_privee_nom" 
                      value={formData.assurance_privee_nom} 
                      onChange={handleChange}
                      className={inputClass}
                      placeholder="Ex: Sanlam, Wafa Assurance..."
                    />
                  </div>
                )}
                
                {/* Assurance Complémentaire */}
                <div className="mt-4 pt-4 border-t border-slate-200">
                  <label className="flex items-center gap-3 cursor-pointer mb-3">
                    <input type="checkbox" name="assurance_complementaire" checked={formData.assurance_complementaire} onChange={handleChange} className="peer sr-only" />
                    <div aria-hidden="true" className={cn(
                      "w-10 h-5 shrink-0 rounded-full transition-all duration-300 relative peer-focus-visible:ring-2 peer-focus-visible:ring-offset-2 peer-focus-visible:ring-[#003380]",
                      formData.assurance_complementaire ? "bg-[#003380]" : "bg-slate-300"
                    )}>
                      <div className={cn(
                        "absolute top-1 w-3 h-3 rounded-full bg-white shadow-md transition-all duration-300",
                        formData.assurance_complementaire ? "left-6" : "left-1"
                      )} />
                    </div>
                    <span className="font-bold text-slate-700 text-sm">Assurance Complémentaire</span>
                  </label>
                  
                  {formData.assurance_complementaire && (
                    <div>
                      <label htmlFor="patient-assurance_complementaire_nom" className={labelClass}>Nom de l'Assurance Complémentaire</label>
                      <input 
                        type="text" 
                        id="patient-assurance_complementaire_nom" 
                        name="assurance_complementaire_nom" 
                        value={formData.assurance_complementaire_nom} 
                        onChange={handleChange}
                        className={inputClass}
                        placeholder="Ex: Mutuelle interne..."
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Section Contact */}
          <div className="space-y-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="h-px flex-1 bg-gradient-to-r from-transparent via-slate-300 to-transparent" />
              <span className="text-xs font-black text-slate-400 uppercase tracking-widest">Contact</span>
              <div className="h-px flex-1 bg-gradient-to-r from-transparent via-slate-300 to-transparent" />
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="patient-telephone" className={labelClass}>Téléphone Principal</label>
                <div className="relative mb-2">
                  <Phone className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input 
                    type="tel" 
                    id="patient-telephone" 
                    name="telephone" 
                    value={formData.telephone} 
                    onChange={handleChange}
                    className={cn(inputClass, "pl-14")}
                    placeholder="06 12 34 56 78"
                  />
                </div>
                
                {showPhone2 && (
                  <div className="relative mb-2 mt-2">
                    <Phone className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300" />
                    <input 
                      type="tel" 
                      name="telephone_2" 
                      value={formData.telephone_2} 
                      onChange={handleChange}
                      className={cn(inputClass, "pl-14 py-3")}
                      placeholder="Téléphone secondaire"
                    />
                  </div>
                )}
                
                {showPhone3 && (
                  <div className="relative mb-2 mt-2">
                    <Phone className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300" />
                    <input 
                      type="tel" 
                      name="telephone_3" 
                      value={formData.telephone_3} 
                      onChange={handleChange}
                      className={cn(inputClass, "pl-14 py-3")}
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
                <label htmlFor="patient-email" className={labelClass}>Email</label>
                <div className="relative">
                  <Mail className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input 
                    type="email" 
                    id="patient-email" 
                    name="email" 
                    aria-invalid={Boolean(errors.email)}
                  aria-describedby={errors.email ? "patient-email-error" : undefined}
                  value={formData.email} 
                    onChange={handleChange}
                    className={cn(inputClass, "pl-14", errors.email && "border-red-400 focus:border-red-400 focus:ring-red-100")}
                    placeholder="yazan.benmoussa@email.com"
                  />
                </div>
                {errors.email && <span id="patient-email-error" className="text-red-500 text-xs mt-1 ml-1">{errors.email}</span>}
              </div>

              <div className="md:col-span-2">
                <label htmlFor="patient-adresse" className={labelClass}>Adresse</label>
                <input 
                  type="text" 
                  id="patient-adresse" 
                  name="adresse" 
                  value={formData.adresse} 
                  onChange={handleChange}
                  className={inputClass}
                  placeholder="Avenue Mohammed V, Rabat"
                />
              </div>
            </div>
          </div>

          {/* Section Antécédents Médicaux */}
          <div className="space-y-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="h-px flex-1 bg-gradient-to-r from-transparent via-slate-300 to-transparent" />
              <span className="text-xs font-black text-slate-400 uppercase tracking-widest">Antécédents Médicaux</span>
              <div className="h-px flex-1 bg-gradient-to-r from-transparent via-slate-300 to-transparent" />
            </div>

            <div>
              <span className={labelClass}>Motif(s) de première consultation</span>
              <MotifSelector
                selected={formData.motif_consultation}
                onChange={(ids) => setFormData((prev: any) => ({ ...prev, motif_consultation: ids }))}
              />
            </div>

            <div className="mt-6">
              <label htmlFor="patient-antecedents_medicaux" className={labelClass}>Historique médical et allergies</label>
              <textarea 
                id="patient-antecedents_medicaux" 
                name="antecedents_medicaux" 
                value={formData.antecedents_medicaux} 
                onChange={handleChange}
                rows={4}
                className={inputClass}
                placeholder="Ex: Diabète, hypertension, allergie à la pénicilline, traitement en cours..."
              />
            </div>
          </div>

          <div className="p-6 bg-gradient-to-r from-blue-50/50 to-indigo-50/50 rounded-2xl border border-blue-100">
            <label className="flex items-center gap-4 cursor-pointer">
              <input type="checkbox" id="patient-is-ortho" checked={isOrtho} onChange={e => setIsOrtho(e.target.checked)} className="peer sr-only" />
              <div aria-hidden="true" className={cn(
                "w-14 h-8 shrink-0 rounded-full transition-all duration-300 relative peer-focus-visible:ring-2 peer-focus-visible:ring-offset-2 peer-focus-visible:ring-[#003380]",
                isOrtho ? "bg-[#003380]" : "bg-slate-300"
              )}>
                <div className={cn(
                  "absolute top-1 w-6 h-6 rounded-full bg-white shadow-md transition-all duration-300",
                  isOrtho ? "left-7" : "left-1"
                )} />
              </div>
              <div>
                <span className="font-bold text-slate-800">Suivi Orthodontique</span>
                <span className="block text-xs text-slate-500">Activer le suivi orthodontique pour ce patient</span>
              </div>
            </label>
          </div>

          {/* Actions */}
          <div className="flex flex-wrap items-center justify-end gap-3 pt-6 border-t border-slate-200">
            <button 
              type="button" 
              onClick={() => navigate('/patients')}
              className="min-h-11 px-5 sm:px-8 py-3 sm:py-4 rounded-2xl font-bold text-slate-600 hover:bg-slate-100 transition-all focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#003380]"
            >
              Annuler
            </button>
            <button 
              type="submit" 
              disabled={loading}
              className="min-h-11 px-5 sm:px-8 py-3 sm:py-4 bg-[#003380] text-white rounded-2xl font-bold hover:bg-[#002266] transition-all shadow-lg shadow-blue-900/20 flex items-center gap-3 disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#003380]"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Vérification...
                </>
              ) : (
                <>
                  <Save className="w-5 h-5" />
                  Créer le dossier
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Modal de détection de doublon */}
      {showDuplicateModal && duplicateInfo?.existing_patient && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-3xl shadow-2xl max-w-lg w-full p-8 animate-in fade-in zoom-in duration-200">
            <div className="flex items-center gap-4 mb-6">
              <div className="p-3 bg-amber-100 rounded-2xl">
                <AlertTriangle className="w-8 h-8 text-amber-600" />
              </div>
              <div>
                <h3 className="text-xl font-black text-slate-800">Patient similaire trouvé</h3>
                <p className="text-slate-500 text-sm">Un dossier avec les mêmes informations existe déjà.</p>
              </div>
            </div>

            <div className="bg-slate-50 rounded-2xl p-6 mb-6 border border-slate-200">
              <div className="flex items-center gap-3 mb-4">
                <UserCheck className="w-5 h-5 text-[#003380]" />
                <span className="font-bold text-slate-800">Dossier existant :</span>
              </div>
              <div className="space-y-2 text-sm">
                <p><span className="text-slate-500">Nom :</span> <span className="font-bold">{duplicateInfo.existing_patient.nom} {duplicateInfo.existing_patient.prenom}</span></p>
                <p><span className="text-slate-500">Né(e) le :</span> <span className="font-bold">{formatDate(duplicateInfo.existing_patient.date_naissance)}</span></p>
                <p><span className="text-slate-500">Créé le :</span> <span className="text-slate-600">{formatDate(duplicateInfo.existing_patient.created_at)}</span></p>
              </div>
            </div>

            <div className="space-y-3">
              <button
                onClick={() => navigate(`/patients/${duplicateInfo.existing_patient!.id}`)}
                className="w-full py-4 bg-[#003380] text-white rounded-2xl font-bold hover:bg-[#002266] transition-all flex items-center justify-center gap-2"
              >
                <FolderOpen className="w-5 h-5" />
                Ouvrir le dossier existant
              </button>

              <button
                onClick={() => {
                  setForceCreate(true);
                  setShowDuplicateModal(false);
                  performSubmit(true);
                }}
                className="w-full py-4 bg-white border-2 border-slate-200 text-slate-700 rounded-2xl font-bold hover:bg-slate-50 transition-all flex items-center justify-center gap-2"
              >
                <CheckCircle2 className="w-5 h-5" />
                Créer quand même (doublon autorisé)
              </button>

              <button
                onClick={() => {
                  setShowDuplicateModal(false);
                  setForceCreate(false);
                }}
                className="w-full py-3 text-slate-500 hover:text-slate-700 transition-colors"
              >
                Modifier les informations
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AddPatientForm;