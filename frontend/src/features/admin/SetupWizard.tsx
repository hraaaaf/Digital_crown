import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Stethoscope,
  Phone,
  Palette,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  MapPin,
  Image as ImageIcon,
  Check,
  FileImage,
  Upload,
  Sparkles,
  Type,
  MousePointer2,
  Camera,
  X,
  Plus,
  Moon,
  Sun
} from 'lucide-react';
import { cabinetApi } from '../../services/templateApi';
import { cn } from '../../utils/cn';
import {
  SPECIALTIES_DICT,
  STEPS,
  CROWN_MESSAGES,
  PREMIUM_FONTS,
  DESIGN_VARIANTS,
  BRAND_IDENTITIES
} from './constants';
import type {
  IdentityState,
  HeaderOption,
  TemplateOption,
  ContactType,
  ContactConfig
} from './types';
import { LiveDocumentStudio } from './components/LiveDocumentStudio';
import { CrownGuide } from './components/CrownGuide';
import { ArabicKeyboard } from './components/ArabicKeyboard';
import Logo from '../../assets/logo.png';

export const SetupWizard: React.FC = () => {
  const navigate = useNavigate();
  const logoInputRef = useRef<HTMLInputElement>(null);
  const letterheadInputRef = useRef<HTMLInputElement>(null);

  // Navigation
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isDemoMode, setIsDemoMode] = useState(() => localStorage.getItem('appMode') === 'demo');

  const toggleDemoMode = useCallback(() => {
    setIsDemoMode(prev => {
      const next = !prev;
      localStorage.setItem('appMode', next ? 'demo' : 'live');
      return next;
    });
  }, []);

  // État du cabinet
  const [cabinetType, setCabinetType] = useState<'PRIVE' | 'CLINIQUE'>('PRIVE');
  const [identity, setIdentity] = useState<IdentityState>({ nomCabinet: '', nomPraticien: '', nomPraticienAR: '', adresse: '', ice: '', if: '', inpe: '' });
  const [selectedSpecialties, setSelectedSpecialties] = useState<string[]>([]);
  const [customSpecialty, setCustomSpecialty] = useState({ fr: '', ar: '' });
  const [showCustomModal, setShowCustomModal] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [contacts, setContacts] = useState<ContactConfig>({
    fixe: { enabled: true, value: '' },
    mobile: { enabled: false, value: '' },
    whatsapp: { enabled: false, value: '' },
    instagram: { enabled: false, value: '' }
  });

  // État Design & Ambiance
  const [headerOption, setHeaderOption] = useState<HeaderOption>('auto');
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateOption>('classic');
  const [selectedTheme, setSelectedTheme] = useState<'elite' | 'emerald' | 'prestige'>(() => {
    return (localStorage.getItem('digitalcrown_theme') as any) || 'elite';
  });
  const [selectedIdentity, setSelectedIdentity] = useState<string>(BRAND_IDENTITIES[0].id);
  const [selectedFont, setSelectedFont] = useState<string>(PREMIUM_FONTS[0].id);
  const [showArKeyboard, setShowArKeyboard] = useState<{ show: boolean, target: 'identity' | 'custom_spec' }>({ show: false, target: 'identity' });

  // Persistance du thème
  useEffect(() => {
    document.body.dataset.theme = selectedTheme;
    localStorage.setItem('digitalcrown_theme', selectedTheme);
  }, [selectedTheme]);

  // Médias
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [letterheadFile, setLetterheadFile] = useState<File | null>(null);
  const [letterheadPreview, setLetterheadPreview] = useState<string | null>(null);
  const [margins, setMargins] = useState({ top: 3.0, bottom: 2.5 });

  // Effet pour appliquer le thème visuel dynamiquement
  useEffect(() => {
    const brandIdentity = BRAND_IDENTITIES.find(i => i.id === selectedIdentity) || BRAND_IDENTITIES[0];
    document.body.dataset.theme = selectedTheme === 'elite' ? '' : selectedTheme;

    const root = document.documentElement;
    root.style.setProperty('--primary', brandIdentity.primary);
    root.style.setProperty('--secondary', brandIdentity.secondary);
    root.style.setProperty('--accent', brandIdentity.accent);

    return () => {
      document.body.dataset.theme = '';
      root.style.removeProperty('--primary');
      root.style.removeProperty('--secondary');
      root.style.removeProperty('--accent');
    };
  }, [selectedTheme, selectedIdentity]);

  // Handler d'extraction IA
  const handleCardImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const hasExistingData = identity.nomCabinet || identity.nomPraticien;
    if (hasExistingData) {
      const confirmed = window.confirm("Des données d'identité existent déjà. Les remplacer par l'extraction IA ?");
      if (!confirmed) return;
    }

    setIsExtracting(true);
    try {
      const data = await cabinetApi.extractCard(file);
      if (data && !data.error) {
        setIdentity({
          ...identity,
          nomCabinet: data.nom_cabinet || identity.nomCabinet,
          nomPraticien: data.nom_praticien || identity.nomPraticien,
          nomPraticienAR: data.nom_praticien_ar || identity.nomPraticienAR,
          adresse: data.adresse || identity.adresse
        });

        if (data.specialites && Array.isArray(data.specialites)) {
          // Mapper les spécialités extraites aux IDs existants si possible
          const matched = SPECIALTIES_DICT.filter(s =>
            data.specialites?.some((ext: string) => ext.toLowerCase().includes(s.fr.toLowerCase()))
          ).map(s => s.id);

          if (matched.length > 0) setSelectedSpecialties(prev => Array.from(new Set([...prev, ...matched])));
        }

        // Notification succès (Crown Guide)
        // On pourrait ajouter un message spécifique
      }
    } catch (err) {
      console.error("Erreur extraction:", err);
    } finally {
      setIsExtracting(false);
    }
  };

  // Utilitaires
  const specialtyStrings = useMemo(() => {
    const frArr: string[] = [];
    const arArr: string[] = [];
    selectedSpecialties.forEach(id => {
      const s = SPECIALTIES_DICT.find(x => x.id === id);
      if (s) { frArr.push(s.fr); arArr.push(s.ar); }
    });
    if (customSpecialty.fr) frArr.push(customSpecialty.fr);
    if (customSpecialty.ar) arArr.push(customSpecialty.ar);

    return { fr: frArr.join(' - '), ar: arArr.join(' - ') };
  }, [selectedSpecialties, customSpecialty]);

  const contactString = useMemo(() => {
    const parts: string[] = [];
    (Object.keys(contacts) as ContactType[]).forEach(type => {
      const c = contacts[type];
      if (c.enabled && c.value.trim()) {
        const icon = type === 'fixe' ? '📞' : type === 'mobile' ? '📱' : type === 'whatsapp' ? '💬' : '📸';
        parts.push(`${icon} ${c.value.trim()}`);
      }
    });
    return parts.join(' | ');
  }, [contacts]);

  // Handlers
  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.size <= 2 * 1024 * 1024) {
      setLogoFile(file);
      const r = new FileReader();
      r.onloadend = () => setLogoPreview(r.result as string);
      r.readAsDataURL(file);
    }
  };

  const handleLetterheadChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.size <= 5 * 1024 * 1024) {
      setLetterheadFile(file);
      const r = new FileReader();
      r.onloadend = () => setLetterheadPreview(r.result as string);
      r.readAsDataURL(file);
    }
  };

  const validateStep = (step: number) => {
    const errs: Record<string, string> = {};
    if (step === 1) {
      if (!identity.nomCabinet) errs.nomCabinet = "Requis";
      if (!identity.nomPraticien) errs.nomPraticien = "Requis";
      if (!identity.adresse) errs.adresse = "Requis";
    }
    if (step === 2 && selectedSpecialties.length === 0) errs.specialties = "Choisissez au moins une spécialité";
    if (step === 3 && !Object.values(contacts).some(c => c.enabled && c.value.trim())) errs.contacts = "Renseignez au moins un contact";

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleNext = () => {
    if (currentStep === 3) {
      const hasValid = Object.values(contacts).some(c => c.enabled && c.value.trim());
      if (!hasValid) {
        setErrors({ contacts: "Activez et renseignez au moins un contact" });
        return;
      }
    }
    validateStep(currentStep) && setCurrentStep(prev => Math.min(prev + 1, 6));
  };

  const handleBack = () => setCurrentStep(prev => Math.max(prev - 1, 1));

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const sanitizedMargins = {
        top: Math.max(1, Math.min(8, margins.top)),
        bottom: Math.max(1, Math.min(6, margins.bottom))
      };

      const identityData = BRAND_IDENTITIES.find(i => i.id === selectedIdentity) || BRAND_IDENTITIES[0];
      const payload = {
        nom_cabinet: identity.nomCabinet,
        header_lines_fr: [identity.nomPraticien, 'Chirurgien Dentiste', specialtyStrings.fr],
        header_lines_ar: [identity.nomPraticienAR, 'طبيب جراح للأسنان', specialtyStrings.ar],
        footer_address: identity.adresse,
        footer_phones: contactString,
        ice: identity.ice,
        if_: identity.if,
        inpe: identity.inpe,
        cabinet_type: cabinetType,
        selected_theme: selectedTheme,
        selected_template: selectedTemplate,
        selected_font: selectedFont,
        primary_color: identityData.primary,
        secondary_color: identityData.secondary,
        accent_color: identityData.accent,
        watermark_enabled: headerOption === 'auto',
        contacts_json: contacts
      };

      if (isDemoMode) {
        await new Promise(r => setTimeout(r, 1200));
        sessionStorage.setItem('demoConfig', JSON.stringify(payload));
        navigate('/dashboard');
      } else {
        await cabinetApi.create(payload as any);
        if (logoFile) await cabinetApi.uploadLogo(logoFile);

        if (headerOption === 'letterhead' && letterheadFile) {
          await cabinetApi.uploadLetterhead(letterheadFile, sanitizedMargins.top, sanitizedMargins.bottom);
        }

        navigate('/dashboard');
      }
    } catch (e) {
      setErrors({ submit: "Échec de l'initialisation. Réessayez." });
    } finally {
      setLoading(false);
    }
  };

  // =============================================================================
  // RENDU DES ÉTAPES
  // =============================================================================

  const renderStep1 = () => (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-black text-slate-900">Structure du Cabinet</h2>
        <p className="text-sm text-slate-500">Définissez le mode d'exercice de votre cabinet.</p>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-8">
        <button
          onClick={() => setCabinetType('PRIVE')}
          className={cn(
            "p-6 rounded-3xl border-2 transition-all flex flex-col items-center gap-3",
            cabinetType === 'PRIVE' ? "border-primary bg-primary/5 shadow-lg" : "border-slate-100 opacity-60 grayscale hover:grayscale-0 hover:opacity-100"
          )}
        >
          <div className="w-12 h-12 rounded-2xl bg-blue-100 flex items-center justify-center text-blue-600"><Building2 size={24} /></div>
          <div className="text-center">
            <span className="block font-black text-slate-900 text-sm">Cabinet Privé</span>
            <span className="text-[10px] text-slate-500">Mono-praticien</span>
          </div>
        </button>

        <button
          onClick={() => setCabinetType('CLINIQUE')}
          className={cn(
            "p-6 rounded-3xl border-2 transition-all flex flex-col items-center gap-3",
            cabinetType === 'CLINIQUE' ? "border-emerald-500 bg-emerald-50 shadow-lg" : "border-slate-100 opacity-60 grayscale hover:grayscale-0 hover:opacity-100"
          )}
        >
          <div className="w-12 h-12 rounded-2xl bg-emerald-100 flex items-center justify-center text-emerald-600"><Stethoscope size={24} /></div>
          <div className="text-center">
            <span className="block font-black text-slate-900 text-sm">Clinique / Centre</span>
            <span className="text-[10px] text-slate-500">Multi-spécialistes</span>
          </div>
        </button>
      </div>

      <div className="space-y-4 pt-4 border-t border-slate-100">
        <div>
          <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">Nom de l'établissement *</label>
          <input
            type="text"
            value={identity.nomCabinet}
            onChange={e => setIdentity({ ...identity, nomCabinet: e.target.value })}
            className={cn("w-full p-4 rounded-xl border focus:ring-2 focus:ring-primary/20 transition-all font-bold text-slate-900 shadow-sm", errors.nomCabinet ? "border-red-300" : "border-slate-200")}
            placeholder={cabinetType === 'CLINIQUE' ? "Ex: Centre Dentaire Al Massira" : "Ex: Cabinet Dr. Alami"}
          />
        </div>
        <div>
          <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">Praticien Principal / Titulaire *</label>
          <div className="grid grid-cols-2 gap-4">
            <input
              type="text"
              value={identity.nomPraticien}
              onChange={e => setIdentity({ ...identity, nomPraticien: e.target.value })}
              className={cn("w-full p-4 rounded-xl border focus:ring-2 focus:ring-primary/20 transition-all font-bold text-slate-900 shadow-sm", errors.nomPraticien ? "border-red-300" : "border-slate-200")}
              placeholder="Dr. Jean Dupont"
            />
            <div className="relative">
              <input
                type="text"
                dir="rtl"
                value={identity.nomPraticienAR}
                onChange={e => setIdentity({ ...identity, nomPraticienAR: e.target.value })}
                onFocus={() => setShowArKeyboard({ show: true, target: 'identity' })}
                className={cn("w-full p-4 rounded-xl border focus:ring-2 focus:ring-primary/20 transition-all font-bold text-slate-900 shadow-sm font-arabic text-lg", errors.nomPraticien ? "border-red-300" : "border-slate-200")}
                placeholder="د. الإسم الكامل"
              />
              <button 
                onClick={() => setShowArKeyboard({ show: true, target: 'identity' })}
                className="absolute left-3 top-1/2 -translate-y-1/2 p-2 bg-slate-100 rounded-lg text-slate-400 hover:text-primary transition-colors"
              >
                <Type size={16} />
              </button>
            </div>
          </div>
        </div>
        <div>
          <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">Adresse Professionnelle *</label>
          <textarea
            value={identity.adresse}
            onChange={e => setIdentity({ ...identity, adresse: e.target.value })}
            className={cn("w-full p-4 rounded-xl border focus:ring-2 focus:ring-primary/20 transition-all font-medium text-slate-600 text-sm h-24 shadow-sm", errors.adresse ? "border-red-300" : "border-slate-200")}
            placeholder="Étage, Résidence, Rue, Ville..."
          />
        </div>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-black text-slate-900">Spécialités</h2>
        <p className="text-sm text-slate-500">Sélectionnez vos domaines d'expertise.</p>
      </div>

      <div className="flex flex-col gap-4">
        {/* Magic Import Button */}
        <div className="relative group">
          <input
            type="file"
            id="card-upload"
            className="hidden"
            accept="image/*,application/pdf"
            onChange={handleCardImport}
          />
          <label
            htmlFor="card-upload"
            className={cn(
              "flex items-center justify-center gap-3 p-4 rounded-2xl border-2 border-dashed border-primary/30 bg-primary/5 cursor-pointer transition-all hover:bg-primary/10 hover:border-primary group-hover:scale-[1.02]",
              isExtracting && "opacity-50 pointer-events-none animate-pulse"
            )}
          >
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
              <Camera size={20} />
            </div>
            <div className="text-left">
              <span className="block font-black text-xs text-primary uppercase tracking-tighter">
                {isExtracting ? "Extraction IA en cours..." : "Importer depuis une Carte de Visite"}
              </span>
              <span className="text-[10px] text-slate-500">Remplissage automatique intelligent</span>
            </div>
            <Sparkles className="ml-auto text-primary/40" size={16} />
          </label>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {SPECIALTIES_DICT.map((spec) => (
            <button
              key={spec.id}
              onClick={() => {
                const newSpecs = selectedSpecialties.includes(spec.id)
                  ? selectedSpecialties.filter(id => id !== spec.id)
                  : [...selectedSpecialties, spec.id];
                setSelectedSpecialties(newSpecs);
              }}
              className={cn(
                "p-4 rounded-2xl border-2 text-left transition-all relative overflow-hidden group",
                selectedSpecialties.includes(spec.id)
                  ? "border-primary bg-primary/5 shadow-md"
                  : "border-slate-100 bg-white hover:border-slate-200"
              )}
            >
              <div className="flex items-center gap-3 mb-1">
                <div className={cn(
                  "w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-300",
                  selectedSpecialties.includes(spec.id)
                    ? "bg-primary text-white shadow-xl shadow-primary/30 scale-105"
                    : "bg-slate-50 text-slate-400 group-hover:bg-slate-100 group-hover:scale-105"
                )}>
                  <spec.icon size={32} />
                </div>
                <span className={cn(
                  "font-black text-xs transition-colors",
                  selectedSpecialties.includes(spec.id) ? "text-primary" : "text-slate-900"
                )}>{spec.fr}</span>
              </div>
              <div className="text-[10px] text-slate-400 font-medium text-right font-arabic">{spec.ar}</div>

              {selectedSpecialties.includes(spec.id) && (
                <div className="absolute top-2 right-2 w-4 h-4 rounded-full bg-primary flex items-center justify-center">
                  <Check size={10} className="text-white" />
                </div>
              )}
            </button>
          ))}

          {/* Custom Specialty Toggle */}
          <button
            onClick={() => setShowCustomModal(true)}
            className="p-4 rounded-2xl border-2 border-dashed border-slate-200 flex items-center justify-center gap-2 text-slate-500 hover:border-primary hover:text-primary transition-all"
          >
            <Plus size={16} />
            <span className="font-bold text-xs">Autre spécialité...</span>
          </button>
        </div>
      </div>

      {/* Modal Specialty */}
      {showCustomModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
          <div className="bg-white w-full max-w-md rounded-[32px] overflow-hidden shadow-2xl border border-white/20 animate-in zoom-in-95 duration-200">
            <div className="p-8 space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-black text-slate-900">Spécialité Personnalisée</h3>
                <button onClick={() => setShowCustomModal(false)} className="p-2 rounded-full hover:bg-slate-100"><X size={20} /></button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">En Français</label>
                  <input
                    type="text"
                    value={customSpecialty.fr}
                    onChange={e => setCustomSpecialty({ ...customSpecialty, fr: e.target.value })}
                    className="w-full p-4 rounded-xl border border-slate-200 focus:ring-2 focus:ring-primary/20 transition-all font-bold text-slate-900"
                    placeholder="Ex: Pédodontie"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">En Arabe (Clavier)</label>
                  <div className="relative">
                    <input
                      type="text"
                      dir="rtl"
                      value={customSpecialty.ar}
                      onChange={e => setCustomSpecialty({ ...customSpecialty, ar: e.target.value })}
                      onFocus={() => setShowArKeyboard({ show: true, target: 'custom_spec' })}
                      className="w-full p-4 rounded-xl border border-slate-200 focus:ring-2 focus:ring-primary/20 transition-all font-bold text-slate-900 font-arabic text-lg"
                      placeholder="Ex: طب أسنان الأطفال"
                    />
                    <button 
                      onClick={() => setShowArKeyboard({ show: true, target: 'custom_spec' })}
                      className="absolute left-3 top-1/2 -translate-y-1/2 p-2 bg-slate-100 rounded-lg text-slate-400 hover:text-primary transition-colors"
                    >
                      <Type size={16} />
                    </button>
                  </div>
                </div>
              </div>

              <button
                onClick={() => setShowCustomModal(false)}
                className="w-full py-4 bg-primary text-white rounded-2xl font-black text-sm"
              >
                Valider
              </button>
            </div>
          </div>
        </div>
      )}
      {errors.specialties && <p className="text-[10px] text-red-500 font-bold text-center">{errors.specialties}</p>}
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-black text-slate-900">Coordonnées</h2>
        <p className="text-sm text-slate-500">Comment les patients peuvent-ils vous joindre ?</p>
      </div>
      <div className="space-y-3">
        {(['fixe', 'mobile', 'whatsapp', 'instagram'] as ContactType[]).map(type => (
          <div key={type} className={cn("p-4 rounded-2xl border-2 transition-all", contacts[type].enabled ? "border-primary bg-primary/5" : "border-slate-100 bg-white")}>
            <div className="flex items-center gap-3 mb-2">
              <button
                onClick={() => setContacts({ ...contacts, [type]: { ...contacts[type], enabled: !contacts[type].enabled } })}
                className={cn("w-5 h-5 rounded flex items-center justify-center border-2 transition-all", contacts[type].enabled ? "bg-primary border-primary" : "border-slate-200")}
              >
                {contacts[type].enabled && <Check size={12} className="text-white" />}
              </button>
              <span className="font-bold text-slate-800 text-sm capitalize">{type}</span>
            </div>
            {contacts[type].enabled && (
              <input
                type="text"
                value={contacts[type].value}
                onChange={e => setContacts({ ...contacts, [type]: { ...contacts[type], value: e.target.value } })}
                className="w-full p-2.5 rounded-xl border border-slate-200 bg-white text-xs font-bold"
                placeholder={`Numéro ou pseudo ${type}...`}
              />
            )}
          </div>
        ))}
      </div>

      <div className="pt-4 border-t border-slate-100">
        <h3 className="text-sm font-black text-slate-800 mb-4">Identifiants Légaux (Optionnel)</h3>
        <p className="text-[10px] text-slate-500 mb-3">Requis pour les notes d'honoraires et devis.</p>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">I.C.E</label>
            <input
              type="text"
              value={identity.ice || ''}
              onChange={e => setIdentity({ ...identity, ice: e.target.value })}
              className="w-full p-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-primary/20 transition-all font-bold text-slate-900 shadow-sm text-xs"
              placeholder="N° ICE"
            />
          </div>
          <div>
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">I.F</label>
            <input
              type="text"
              value={identity.if || ''}
              onChange={e => setIdentity({ ...identity, if: e.target.value })}
              className="w-full p-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-primary/20 transition-all font-bold text-slate-900 shadow-sm text-xs"
              placeholder="Id. Fiscal"
            />
          </div>
          <div>
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">I.N.P.E</label>
            <input
              type="text"
              value={identity.inpe || ''}
              onChange={e => setIdentity({ ...identity, inpe: e.target.value })}
              className="w-full p-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-primary/20 transition-all font-bold text-slate-900 shadow-sm text-xs"
              placeholder="N° INPE"
            />
          </div>
        </div>
      </div>
      {errors.contacts && <p className="text-[10px] text-red-500 font-bold text-center">{errors.contacts}</p>}
    </div>
  );

  const renderStep4 = () => (
    <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
      <div className="text-center">
        <h2 className="text-2xl font-black text-slate-900 tracking-tight">Studio de Design</h2>
        <p className="text-slate-500 text-sm mt-1">Personnalisez l'apparence de vos documents officiels.</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <button
          onClick={() => setHeaderOption('auto')}
          className={cn(
            "p-5 rounded-2xl border-2 text-left transition-all",
            headerOption === 'auto' ? "border-primary bg-primary/5 shadow-lg" : "border-slate-200 bg-white"
          )}
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600"><ImageIcon size={18} /></div>
            <span className="font-bold text-slate-900">Auto-Généré</span>
          </div>
          <p className="text-[10px] text-slate-500 leading-tight">Mise en page automatique avec votre logo et typo.</p>
        </button>

        <button
          onClick={() => setHeaderOption('letterhead')}
          className={cn(
            "p-5 rounded-2xl border-2 text-left transition-all",
            headerOption === 'letterhead' ? "border-emerald-500 bg-emerald-50 shadow-lg" : "border-slate-200 bg-white"
          )}
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-600"><FileImage size={18} /></div>
            <span className="font-bold text-slate-900">Papier A5</span>
          </div>
          <p className="text-[10px] text-slate-500 leading-tight">Uploadez votre propre papier à en-tête pré-imprimé.</p>
        </button>
      </div>

      {headerOption === 'auto' ? (
        <div className="space-y-6">
          <div className="bg-slate-50 p-6 rounded-3xl border border-slate-200/60">
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-4">Identité Visuelle & Harmonie</label>
            <div className="grid grid-cols-2 gap-3">
              {BRAND_IDENTITIES.map(id => (
                <button
                  key={id.id}
                  onClick={() => setSelectedIdentity(id.id)}
                  className={cn(
                    "p-4 rounded-2xl border-2 transition-all text-left flex flex-col gap-3 group relative overflow-hidden",
                    selectedIdentity === id.id ? "border-primary bg-white shadow-lg scale-[1.02]" : "border-slate-200 bg-slate-50 hover:border-slate-300"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <h5 className="text-[10px] font-black uppercase tracking-tighter text-slate-900">{id.name}</h5>
                    <div className="flex -space-x-2">
                      <div className="w-4 h-4 rounded-full border border-white" style={{ backgroundColor: id.primary }} />
                      <div className="w-4 h-4 rounded-full border border-white" style={{ backgroundColor: id.secondary }} />
                      <div className="w-4 h-4 rounded-full border border-white" style={{ backgroundColor: id.accent }} />
                    </div>
                  </div>
                  <p className="text-[9px] text-slate-500 leading-tight italic">{id.vibe}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-3">
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2"><Type size={12} /> Typographie Premium</label>
              <div className="space-y-2">
                {PREMIUM_FONTS.map(f => (
                  <button
                    key={f.id}
                    onClick={() => setSelectedFont(f.id)}
                    className={cn(
                      "w-full p-2.5 rounded-xl border text-left flex items-center justify-between transition-all",
                      selectedFont === f.id ? "border-primary bg-primary/5 ring-1 ring-primary/20" : "border-slate-200 bg-white hover:bg-slate-50"
                    )}
                  >
                    <div>
                      <span className={cn("block text-sm font-bold", f.class)}>{f.name}</span>
                      <span className="text-[9px] text-slate-400">{f.desc}</span>
                    </div>
                    {selectedFont === f.id && <MousePointer2 size={12} className="text-primary" />}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2"><Palette size={12} /> Modèle de mise en page</label>
              <div className="space-y-2">
                {DESIGN_VARIANTS.map((v: any) => (
                  <button
                    key={v.id}
                    onClick={() => setSelectedTemplate(v.id as any)}
                    className={cn(
                      "w-full p-2.5 rounded-xl border text-left flex items-center gap-3 transition-all",
                      selectedTemplate === v.id ? "border-primary bg-primary/5" : "border-slate-200 bg-white"
                    )}
                  >
                    <v.icon size={16} className={selectedTemplate === v.id ? "text-primary" : "text-slate-400"} />
                    <span className="text-xs font-bold text-slate-900">{v.name}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-24 h-12 flex items-center justify-center bg-white overflow-hidden p-1">
                {logoPreview ? <img src={logoPreview} className="w-full h-full object-contain" alt="Logo" /> : <img src={Logo} className="w-full h-full object-contain opacity-80" alt="Default Logo" />}
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900">Logo du cabinet</h4>
                <p className="text-[10px] text-slate-500">PNG ou SVG (Optionnel)</p>
              </div>
            </div>
            <button onClick={() => logoInputRef.current?.click()} className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-slate-50 transition-all shadow-sm">Uploader</button>
            <input ref={logoInputRef} type="file" className="hidden" accept="image/png,image/svg+xml" onChange={handleLogoChange} />
          </div>
        </div>
      ) : (
        <div className="p-8 bg-emerald-50 border border-emerald-200 rounded-[2rem] space-y-6">
          <div className="flex flex-col items-center">
            <div
              onClick={() => letterheadInputRef.current?.click()}
              className={cn(
                "w-full h-48 rounded-2xl border-2 border-dashed cursor-pointer flex flex-col items-center justify-center transition-all shadow-inner",
                letterheadPreview ? "border-emerald-500 bg-white" : "border-emerald-300 hover:bg-white"
              )}
            >
              {letterheadPreview ? (
                <img src={letterheadPreview} className="h-full object-contain p-4" alt="Letterhead" />
              ) : (
                <>
                  <Upload className="text-emerald-400 mb-2" size={32} />
                  <span className="text-xs font-bold text-emerald-600">Uploader votre Papier A5</span>
                </>
              )}
            </div>
            <input ref={letterheadInputRef} type="file" className="hidden" accept="image/png,image/jpeg" onChange={handleLetterheadChange} />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest block">Marge Haute ({margins.top} cm)</label>
              <input type="range" min="1" max="8" step="0.5" value={margins.top} onChange={e => setMargins(m => ({ ...m, top: parseFloat(e.target.value) }))} className="w-full h-1.5 bg-emerald-200 rounded-lg accent-emerald-600 cursor-pointer" />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest block">Marge Basse ({margins.bottom} cm)</label>
              <input type="range" min="1" max="6" step="0.5" value={margins.bottom} onChange={e => setMargins(m => ({ ...m, bottom: parseFloat(e.target.value) }))} className="w-full h-1.5 bg-emerald-200 rounded-lg accent-emerald-600 cursor-pointer" />
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderStep5 = () => (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-black text-slate-900">Atmosphère Élite</h2>
        <p className="text-sm text-slate-500">Choisissez l'univers visuel qui vous ressemble.</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[
          { id: 'elite', label: 'Lumière Pure', class: 'bg-white border-slate-200', desc: 'Clarté & Professionalisme' },
          { id: 'emerald', label: 'Escale Zen', class: 'bg-emerald-50 border-emerald-100', desc: 'Sérénité & Nature' },
          { id: 'prestige', label: 'Nuit Intense', class: 'bg-slate-900 border-slate-800 text-white', desc: 'Luxe & Autorité' }
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setSelectedTheme(t.id as any)}
            className={cn(
              "flex flex-col items-center gap-4 p-6 rounded-[2rem] border-2 transition-all group relative overflow-hidden",
              t.class,
              selectedTheme === t.id ? "ring-4 ring-primary/20 border-primary scale-[1.05] shadow-xl" : "opacity-60 grayscale hover:grayscale-0 hover:opacity-100"
            )}
          >
            <div className={cn("inline-flex w-16 h-16 rounded-[1.5rem] items-center justify-center transition-transform group-hover:rotate-12", t.id === 'prestige' ? 'bg-white/10' : 'bg-white shadow-inner')}>
              {t.id === 'elite' ? <Sun size={32} className="text-amber-500" /> : t.id === 'emerald' ? <Sparkles size={32} className="text-emerald-500" /> : <Moon size={32} className="text-white" />}
            </div>
            <div className="text-center">
              <span className="block text-[10px] font-black uppercase tracking-[0.2em] mb-1">{t.label}</span>
              <span className="text-[9px] opacity-60 font-medium">{t.desc}</span>
            </div>
            {selectedTheme === t.id && (
              <div className="absolute top-4 right-4 animate-bounce"><CheckCircle2 size={20} className="text-primary" /></div>
            )}
          </button>
        ))}
      </div>

      <div className="mt-8 p-6 rounded-3xl bg-slate-50 border border-slate-100 space-y-4">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
            <Sparkles size={18} />
          </div>
          <div>
            <h4 className="text-sm font-black text-slate-900">Aperçu en temps réel</h4>
            <p className="text-[10px] text-slate-500">L'application entière a adopté le thème <b>{selectedTheme}</b>.</p>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white shadow-sm border border-slate-100 flex items-center justify-between">
          <span className="text-xs font-bold text-slate-700">Définir comme thème par défaut ?</span>
          <div className="flex gap-2">
            <button onClick={() => setSelectedTheme('elite')} className="px-3 py-1.5 rounded-lg text-[10px] font-black hover:bg-slate-100 transition-colors">ANNULER</button>
            <button onClick={() => alert("Thème confirmé !")} className="px-3 py-1.5 rounded-lg bg-primary text-white text-[10px] font-black shadow-lg shadow-primary/20">CONFIRMER</button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderStep6 = () => {
    return (
      <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
        <div className="text-center">
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">C'est presque prêt !</h2>
          <p className="text-slate-500 text-sm mt-1">Vérifiez vos préférences finales avant l'activation.</p>
        </div>
        <div className="space-y-4">
          <div className="p-6 bg-slate-50 rounded-3xl border border-slate-200/60 shadow-inner">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-sm font-black text-slate-900 uppercase tracking-tighter">Votre Cabinet</h3>
                <p className="text-lg font-bold text-primary">Dr. {identity.nomPraticien || '...'}</p>
              </div>
              <div className="w-10 h-10 rounded-xl bg-primary/5 flex items-center justify-center"><Building2 size={20} className="text-primary" /></div>
            </div>
            <div className="space-y-3 pt-4 border-t border-slate-200/50">
              <div className="flex items-center gap-2 text-xs text-slate-600 font-medium"><MapPin size={14} className="text-slate-400" /> {identity.adresse || '...'}</div>
              <div className="flex items-center gap-2 text-xs text-slate-600 font-medium"><Stethoscope size={14} className="text-slate-400" /> {specialtyStrings.fr || '...'}</div>
              <div className="flex items-center gap-2 text-xs text-slate-600 font-medium"><Phone size={14} className="text-slate-400" /> {contactString || '...'}</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-primary/5 rounded-2xl border border-primary/10">
              <p className="text-[9px] font-black text-primary uppercase tracking-widest mb-1">Police & Identité</p>
              <p className="text-xs font-bold text-slate-800 capitalize">{selectedFont} / {BRAND_IDENTITIES.find(i => i.id === selectedIdentity)?.name}</p>
            </div>
            <div className="p-4 bg-emerald-50 rounded-2xl border border-emerald-100">
              <p className="text-[9px] font-black text-emerald-600 uppercase tracking-widest mb-1">Ambiance Applicative</p>
              <p className="text-xs font-bold text-slate-800 capitalize">{selectedTheme}</p>
            </div>
          </div>
        </div>
        {errors.submit && <div className="p-4 bg-red-50 text-red-600 text-xs font-bold rounded-2xl border border-red-100 text-center">{errors.submit}</div>}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 font-outfit text-slate-900 selection:bg-primary/20">
      <header className="bg-white/80 backdrop-blur-xl border-b border-slate-200/60 sticky top-0 z-[100]">
        <div className="max-w-[1400px] mx-auto px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-primary rounded-2xl flex items-center justify-center shadow-lg shadow-primary/20"><Building2 className="text-white" size={20} /></div>
            <div><h1 className="font-black text-slate-900 tracking-tight text-lg">Digital Crown</h1><p className="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-none mt-0.5">Setup Wizard v1.2</p></div>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3 px-4 py-2 bg-slate-100 rounded-xl border border-slate-200/40">
              <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Demo Sandbox</span>
              <button onClick={toggleDemoMode} className={cn("w-10 h-5 rounded-full relative transition-all", isDemoMode ? "bg-primary" : "bg-slate-300")}><div className={cn("absolute top-1 w-3 h-3 bg-white rounded-full shadow transition-all", isDemoMode ? "left-6" : "left-1")} /></button>
            </div>
            <button onClick={() => navigate('/welcome')} className="text-[10px] font-black text-slate-400 hover:text-primary transition-all uppercase tracking-widest flex items-center gap-2"><ArrowLeft size={14} /> Quitter</button>
          </div>
        </div>
      </header>

      <div className="max-w-[1400px] mx-auto px-8 py-10">
        <div className="flex items-center gap-4 mb-20 max-w-4xl mx-auto">
          {STEPS.map((s, i) => (
            <React.Fragment key={s.id}>
              <div className="flex flex-col items-center relative group">
                <div className={cn("w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-500", s.id === currentStep ? "bg-primary text-white scale-110 shadow-xl shadow-primary/30" : s.id < currentStep ? "bg-emerald-500 text-white" : "bg-white text-slate-300 border border-slate-200")}>
                  {s.id < currentStep ? <Check size={20} /> : <s.icon size={20} />}
                </div>
                <span className={cn("absolute -bottom-8 text-[9px] font-black uppercase tracking-widest transition-all", s.id === currentStep ? "text-primary translate-y-2 opacity-100" : "text-slate-400 opacity-60")}>{s.title}</span>
              </div>
              {i < STEPS.length - 1 && <div className={cn("flex-1 h-0.5 rounded-full transition-all duration-1000", s.id < currentStep ? "bg-emerald-500 scale-x-100" : "bg-slate-200 scale-x-100")} />}
            </React.Fragment>
          ))}
        </div>

        <div className={cn("grid grid-cols-1 gap-12 items-start transition-all", (currentStep >= 3 && currentStep <= 6) ? "lg:grid-cols-12" : "max-w-2xl mx-auto")}>
          <div className={cn("bg-white rounded-[2.5rem] border border-slate-200/60 shadow-2xl shadow-slate-900/5 p-12 relative overflow-hidden", (currentStep >= 3 && currentStep <= 6) ? "lg:col-span-7" : "")}>
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-bl-[4rem] pointer-events-none" />

            {currentStep === 1 && renderStep1()}
            {currentStep === 2 && renderStep2()}
            {currentStep === 3 && renderStep3()}
            {currentStep === 4 && renderStep4()}
            {currentStep === 5 && renderStep5()}
            {currentStep === 6 && renderStep6()}

            <div className="mt-16 pt-10 border-t border-slate-100 flex items-center justify-between">
              <button onClick={handleBack} disabled={currentStep === 1} className={cn("flex items-center gap-2 px-8 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all", currentStep === 1 ? "opacity-0 invisible" : "text-slate-400 hover:text-primary hover:bg-slate-50")}>
                <ArrowLeft size={16} /> Retour
              </button>
              {currentStep < 6 ? (
                <button onClick={handleNext} className="bg-primary text-white px-10 py-4 rounded-2xl text-[11px] font-black uppercase tracking-widest shadow-xl shadow-primary/20 hover:scale-[1.03] active:scale-95 transition-all flex items-center gap-3">
                  Continuer <ArrowRight size={18} />
                </button>
              ) : (
                <button onClick={handleSubmit} disabled={loading} className={cn("px-10 py-4 rounded-2xl text-[11px] font-black uppercase tracking-widest shadow-xl transition-all flex items-center gap-3", loading ? "bg-slate-300" : "bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/20")}>
                  {loading ? "Chargement..." : <><CheckCircle2 size={18} /> Finaliser l'Installation</>}
                </button>
              )}
            </div>
          </div>

          {(currentStep >= 3 && currentStep <= 6) && (
            <div className="lg:col-span-5 sticky top-28 animate-in fade-in slide-in-from-right-12 duration-1000">
              <div className="mb-6 flex items-center justify-between px-4">
                <div className="flex items-center gap-2"><Sparkles className="text-primary animate-pulse" size={16} /><span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Aperçu Live Studio</span></div>
                <div className="bg-white px-3 py-1 rounded-md border text-[9px] font-bold text-slate-400 shadow-sm">Document A5 Premium</div>
              </div>
              <LiveDocumentStudio
                identity={identity}
                selectedIdentity={selectedIdentity}
                selectedTemplate={selectedTemplate}
                selectedFont={selectedFont}
                headerOption={headerOption}
                logoPreview={logoPreview}
                letterheadPreview={letterheadPreview}
                margins={margins}
                cabinetType={cabinetType}
                specialtyStrings={specialtyStrings}
                contactString={contactString}
              />
            </div>
          )}
        </div>
      </div>
      <CrownGuide message={CROWN_MESSAGES[currentStep]} />
      {/* CLAVIER ARABE VIRTUEL */}
      <ArabicKeyboard 
        show={showArKeyboard.show}
        value={showArKeyboard.target === 'identity' ? identity.nomPraticienAR : customSpecialty.ar}
        onChange={(val) => {
          if (showArKeyboard.target === 'identity') {
            setIdentity({ ...identity, nomPraticienAR: val });
          } else {
            setCustomSpecialty({ ...customSpecialty, ar: val });
          }
        }}
        onClose={() => setShowArKeyboard({ ...showArKeyboard, show: false })}
      />
    </div>
  );
};

export default SetupWizard;
