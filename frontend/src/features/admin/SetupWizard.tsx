import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Building2, 
  Stethoscope,
  Phone,
  Palette,
  CheckCircle2, 
  ChevronRight, 
  ChevronLeft,
  MapPin,
  User,
  Image as ImageIcon,
  Check,
  Smartphone,
  MessageCircle,
  Instagram,
  FileImage,
  Upload,
  Settings2
} from 'lucide-react';
import { cabinetApi } from '../../services/templateApi';
import { cn } from '../../utils/cn';

// =============================================================================
// Dictionnaire des spécialités (FR/AR)
// =============================================================================
const SPECIALTIES_DICT = [
  { id: 'soins', fr: 'Soins', ar: 'علاج' },
  { id: 'endo', fr: 'Endodontie', ar: 'علاج العصب' },
  { id: 'paro', fr: 'Parodontologie', ar: 'أمراض اللثة' },
  { id: 'ortho', fr: 'Orthodontie', ar: 'تقويم الأسنان' },
  { id: 'prothese', fr: 'Prothèse', ar: 'تعويض الأسنان' },
  { id: 'chirurgie', fr: 'Chirurgie', ar: 'جراحة' },
  { id: 'implant', fr: 'Implantologie', ar: 'زراعة الأسنان' },
  { id: 'blanchiment', fr: 'Blanchiment', ar: 'تبييض الأسنان' },
  { id: 'esthetique', fr: 'Esthétique', ar: 'تجميل الأسنان' }
];

// =============================================================================
// Types pour les contacts conditionnels
// =============================================================================
type ContactType = 'fixe' | 'mobile' | 'whatsapp' | 'instagram';

interface ContactConfig {
  fixe: { enabled: boolean; value: string };
  mobile: { enabled: boolean; value: string };
  whatsapp: { enabled: boolean; value: string };
  instagram: { enabled: boolean; value: string };
}

// =============================================================================
// Configuration des étapes
// =============================================================================
interface WizardStep {
  id: number;
  title: string;
  description: string;
  icon: React.ElementType;
}

const STEPS: WizardStep[] = [
  {
    id: 1,
    title: "Identité",
    description: "Votre cabinet",
    icon: Building2
  },
  {
    id: 2,
    title: "Spécialités",
    description: "Vos domaines",
    icon: Stethoscope
  },
  {
    id: 3,
    title: "Contacts",
    description: "Vos coordonnées",
    icon: Phone
  },
  {
    id: 4,
    title: "Design",
    description: "Votre en-tête",
    icon: Palette
  },
  {
    id: 5,
    title: "Validation",
    description: "Confirmez tout",
    icon: CheckCircle2
  }
];

// =============================================================================
// Type pour l'option d'en-tête
// =============================================================================
type HeaderOption = 'auto' | 'letterhead';

export const SetupWizard: React.FC = () => {
  const navigate = useNavigate();
  const logoInputRef = useRef<HTMLInputElement>(null);
  const letterheadInputRef = useRef<HTMLInputElement>(null);
  
  // État de navigation
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  // =============================================================================
  // ÉTAPE 1: Identité
  // =============================================================================
  const [identity, setIdentity] = useState({
    nomCabinet: '',
    nomPraticien: '',
    adresse: ''
  });
  
  // =============================================================================
  // ÉTAPE 2: Spécialités (IDs cochés)
  // =============================================================================
  const [selectedSpecialties, setSelectedSpecialties] = useState<string[]>([]);
  
  // =============================================================================
  // ÉTAPE 3: Contacts conditionnels
  // =============================================================================
  const [contacts, setContacts] = useState<ContactConfig>({
    fixe: { enabled: true, value: '' },  // Coché par défaut
    mobile: { enabled: false, value: '' },
    whatsapp: { enabled: false, value: '' },
    instagram: { enabled: false, value: '' }
  });
  
  // =============================================================================
  // ÉTAPE 4: Design de l'en-tête
  // =============================================================================
  const [headerOption, setHeaderOption] = useState<HeaderOption>('auto');
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [letterheadFile, setLetterheadFile] = useState<File | null>(null);
  const [letterheadPreview, setLetterheadPreview] = useState<string | null>(null);
  const [margins, setMargins] = useState({
    top: 3.0,    // cm
    bottom: 2.5  // cm
  });
  
  // =============================================================================
  // Erreurs de validation
  // =============================================================================
  const [errors, setErrors] = useState<Record<string, string>>({});

  // =============================================================================
  // Handlers
  // =============================================================================
  const handleIdentityChange = (field: keyof typeof identity, value: string) => {
    setIdentity(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const toggleSpecialty = (id: string) => {
    setSelectedSpecialties(prev => 
      prev.includes(id) 
        ? prev.filter(s => s !== id)
        : [...prev, id]
    );
  };

  const toggleContact = (type: ContactType) => {
    setContacts(prev => ({
      ...prev,
      [type]: { ...prev[type], enabled: !prev[type].enabled }
    }));
  };

  const updateContactValue = (type: ContactType, value: string) => {
    setContacts(prev => ({
      ...prev,
      [type]: { ...prev[type], value }
    }));
  };

  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 2 * 1024 * 1024) {
        setErrors(prev => ({ ...prev, logo: 'Le fichier ne doit pas dépasser 2Mo' }));
        return;
      }
      if (!['image/png', 'image/svg+xml'].includes(file.type)) {
        setErrors(prev => ({ ...prev, logo: 'Format accepté : PNG ou SVG uniquement' }));
        return;
      }
      setLogoFile(file);
      const reader = new FileReader();
      reader.onloadend = () => setLogoPreview(reader.result as string);
      reader.readAsDataURL(file);
      setErrors(prev => ({ ...prev, logo: '' }));
    }
  };

  const handleLetterheadChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        setErrors(prev => ({ ...prev, letterhead: 'Le fichier ne doit pas dépasser 5Mo' }));
        return;
      }
      if (!['image/jpeg', 'image/png'].includes(file.type)) {
        setErrors(prev => ({ ...prev, letterhead: 'Format accepté : JPG ou PNG uniquement' }));
        return;
      }
      setLetterheadFile(file);
      const reader = new FileReader();
      reader.onloadend = () => setLetterheadPreview(reader.result as string);
      reader.readAsDataURL(file);
      setErrors(prev => ({ ...prev, letterhead: '' }));
    }
  };

  // =============================================================================
  // Validation par étape
  // =============================================================================
  const validateStep = (step: number): boolean => {
    const newErrors: Record<string, string> = {};
    
    switch (step) {
      case 1:
        if (!identity.nomPraticien.trim()) {
          newErrors.nomPraticien = 'Le nom du praticien est requis';
        }
        if (!identity.nomCabinet.trim()) {
          newErrors.nomCabinet = 'Le nom du cabinet est requis';
        }
        if (!identity.adresse.trim()) {
          newErrors.adresse = 'L\'adresse est requise';
        }
        break;
        
      case 2:
        if (selectedSpecialties.length === 0) {
          newErrors.specialties = 'Sélectionnez au moins une spécialité';
        }
        break;
        
      case 3:
        const hasEnabledContact = Object.values(contacts).some(c => c.enabled && c.value.trim());
        if (!hasEnabledContact) {
          newErrors.contacts = 'Renseignez au moins un contact';
        }
        // Vérifier que les contacts activés ont une valeur
        Object.entries(contacts).forEach(([type, config]) => {
          if (config.enabled && !config.value.trim()) {
            newErrors[`contact_${type}`] = 'Ce contact est activé mais vide';
          }
        });
        break;
        
      case 4:
        if (headerOption === 'auto' && !logoFile) {
          // Logo optionnel en mode auto
        }
        if (headerOption === 'letterhead' && !letterheadFile) {
          newErrors.letterhead = 'Veuillez uploader votre papier en-tête';
        }
        break;
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (!validateStep(currentStep)) {
      return;
    }
    if (currentStep < 5) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1);
    }
  };

  // =============================================================================
  // Construction des chaînes de spécialités (FR et AR séparés par -)
  // =============================================================================
  const buildSpecialtyStrings = () => {
    const frParts: string[] = [];
    const arParts: string[] = [];
    
    selectedSpecialties.forEach(id => {
      const spec = SPECIALTIES_DICT.find(s => s.id === id);
      if (spec) {
        frParts.push(spec.fr);
        arParts.push(spec.ar);
      }
    });
    
    return {
      fr: frParts.join(' - '),
      ar: arParts.join(' - ')
    };
  };

  // =============================================================================
  // Construction de la chaîne de contacts concaténée
  // =============================================================================
  const buildContactString = () => {
    const parts: string[] = [];
    
    const icons: Record<ContactType, string> = {
      fixe: '📞',
      mobile: '📱',
      whatsapp: '💬',
      instagram: '📸'
    };
    
    const labels: Record<ContactType, string> = {
      fixe: 'Fixe',
      mobile: 'Mobile',
      whatsapp: 'WhatsApp',
      instagram: 'Instagram'
    };
    
    (Object.keys(contacts) as ContactType[]).forEach(type => {
      const config = contacts[type];
      if (config.enabled && config.value.trim()) {
        parts.push(`${icons[type]} ${labels[type]}: ${config.value.trim()}`);
      }
    });
    
    return parts.join(' - ');
  };

  // =============================================================================
  // Soumission finale
  // =============================================================================
  const handleSubmit = async () => {
    setLoading(true);
    try {
      const specialties = buildSpecialtyStrings();
      const contactString = buildContactString();
      
      // Construction du payload CabinetConfigCreate
      const configData = {
        header_lines_fr: [
          identity.nomPraticien,
          'Chirurgien Dentiste',
          specialties.fr
        ],
        header_lines_ar: [
          '', // Sera rempli côté backend si besoin
          'طبيب جراح للأسنان',
          specialties.ar
        ],
        footer_address: identity.adresse,
        footer_phones: contactString,
        primary_color: '#003380',
        font_fr: 'Helvetica',
        font_ar: 'Amiri',
        watermark_enabled: headerOption === 'auto',
        watermark_opacity: 0.10,
        // Configuration spécifique pour le papier en-tête
        background_letterhead: headerOption === 'letterhead' ? {
          enabled: true,
          margins: margins
        } : undefined
      };
      
      // 1. Créer le cabinet
      await cabinetApi.create(configData);
      
      // 2. Uploader le logo si mode auto
      if (headerOption === 'auto' && logoFile) {
        await cabinetApi.uploadLogo(logoFile);
      }
      
      // 3. Uploader le papier en-tête si mode letterhead
      if (headerOption === 'letterhead' && letterheadFile) {
        // Appel API spécifique pour le papier en-tête
        const formData = new FormData();
        formData.append('file', letterheadFile);
        formData.append('margins_top', margins.top.toString());
        formData.append('margins_bottom', margins.bottom.toString());
        await fetch('http://localhost:8000/api/clinics/me/letterhead', {
          method: 'POST',
          body: formData
        });
      }
      
      // 4. Rediriger vers le dashboard
      navigate('/dashboard');
    } catch (error: any) {
      console.error('Erreur création cabinet:', error);
      setErrors({ submit: error.response?.data?.detail || 'Erreur lors de la création du cabinet' });
    } finally {
      setLoading(false);
    }
  };

  // =============================================================================
  // RENDU ÉTAPE 1: IDENTITÉ
  // =============================================================================
  const renderStep1 = () => (
    <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-slate-900">Identité de votre cabinet</h2>
        <p className="text-slate-600 mt-2">Ces informations apparaîtront sur vos documents officiels</p>
      </div>

      <div className="space-y-5">
        {/* Nom du cabinet */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            <Building2 className="w-4 h-4 inline mr-1" />
            Nom du cabinet *
          </label>
          <input
            type="text"
            value={identity.nomCabinet}
            onChange={(e) => handleIdentityChange('nomCabinet', e.target.value)}
            placeholder="Cabinet Dentaire Benmoussa"
            className={cn(
              "w-full px-4 py-3 rounded-lg border focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all",
              errors.nomCabinet ? "border-red-300" : "border-slate-300"
            )}
          />
          {errors.nomCabinet && <p className="text-sm text-red-500 mt-1">{errors.nomCabinet}</p>}
        </div>

        {/* Nom du praticien */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            <User className="w-4 h-4 inline mr-1" />
            Nom complet du praticien *
          </label>
          <input
            type="text"
            value={identity.nomPraticien}
            onChange={(e) => handleIdentityChange('nomPraticien', e.target.value)}
            placeholder="Dr. Benmoussa Achraf"
            className={cn(
              "w-full px-4 py-3 rounded-lg border focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all",
              errors.nomPraticien ? "border-red-300" : "border-slate-300"
            )}
          />
          {errors.nomPraticien && <p className="text-sm text-red-500 mt-1">{errors.nomPraticien}</p>}
        </div>

        {/* Adresse */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            <MapPin className="w-4 h-4 inline mr-1" />
            Adresse complète *
          </label>
          <textarea
            value={identity.adresse}
            onChange={(e) => handleIdentityChange('adresse', e.target.value)}
            placeholder="156, 1er étage, Secteur 3, Lotissement Zerdal Gharbia, Sidi Bouknadel, Salé"
            rows={3}
            className={cn(
              "w-full px-4 py-3 rounded-lg border focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-all",
              errors.adresse ? "border-red-300" : "border-slate-300"
            )}
          />
          {errors.adresse && <p className="text-sm text-red-500 mt-1">{errors.adresse}</p>}
        </div>
      </div>
    </div>
  );

  // =============================================================================
  // RENDU ÉTAPE 2: SPÉCIALITÉS (Grille de checkboxes)
  // =============================================================================
  const renderStep2 = () => (
    <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-slate-900">Vos spécialités</h2>
        <p className="text-slate-600 mt-2">Sélectionnez les domaines d'expertise de votre cabinet</p>
      </div>

      {errors.specialties && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{errors.specialties}</p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {SPECIALTIES_DICT.map((spec) => {
          const isSelected = selectedSpecialties.includes(spec.id);
          return (
            <button
              key={spec.id}
              onClick={() => toggleSpecialty(spec.id)}
              className={cn(
                "relative p-4 rounded-xl border-2 text-left transition-all duration-200",
                isSelected
                  ? "border-blue-500 bg-blue-50 shadow-sm"
                  : "border-slate-200 bg-white hover:border-blue-300 hover:bg-slate-50"
              )}
            >
              <div className="flex items-start gap-3">
                <div className={cn(
                  "w-5 h-5 rounded border-2 flex items-center justify-center mt-0.5 transition-colors",
                  isSelected ? "bg-blue-500 border-blue-500" : "border-slate-300"
                )}>
                  {isSelected && <Check className="w-3.5 h-3.5 text-white" />}
                </div>
                <div className="flex-1">
                  <p className="font-medium text-slate-900">{spec.fr}</p>
                  <p className="text-sm text-slate-500" dir="rtl">{spec.ar}</p>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Récapitulatif des sélections */}
      {selectedSpecialties.length > 0 && (
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-xl">
          <p className="text-sm font-medium text-blue-900 mb-2">Sélection actuelle :</p>
          <div className="flex flex-wrap gap-2">
            {selectedSpecialties.map(id => {
              const spec = SPECIALTIES_DICT.find(s => s.id === id);
              return spec ? (
                <span key={id} className="px-3 py-1 bg-white text-blue-700 text-sm rounded-full border border-blue-200">
                  {spec.fr}
                </span>
              ) : null;
            })}
          </div>
        </div>
      )}
    </div>
  );

  // =============================================================================
  // RENDU ÉTAPE 3: CONTACTS (Checkboxes conditionnelles)
  // =============================================================================
  const renderStep3 = () => {
    const contactConfigs: { type: ContactType; icon: React.ElementType; label: string; placeholder: string }[] = [
      { type: 'fixe', icon: Phone, label: 'Fixe', placeholder: '05 37 82 23 33' },
      { type: 'mobile', icon: Smartphone, label: 'Mobile', placeholder: '06 12 34 56 78' },
      { type: 'whatsapp', icon: MessageCircle, label: 'WhatsApp', placeholder: '06 48 27 58 52' },
      { type: 'instagram', icon: Instagram, label: 'Instagram', placeholder: '@votre.cabinet' }
    ];

    return (
      <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-slate-900">Vos coordonnées</h2>
          <p className="text-slate-600 mt-2">Sélectionnez les moyens de contact à afficher sur vos documents</p>
        </div>

        {errors.contacts && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{errors.contacts}</p>
          </div>
        )}

        <div className="space-y-4">
          {contactConfigs.map(({ type, icon: Icon, label, placeholder }) => {
            const config = contacts[type];
            const hasError = errors[`contact_${type}`];
            
            return (
              <div key={type} className={cn(
                "border-2 rounded-xl overflow-hidden transition-all",
                config.enabled ? "border-blue-500 bg-blue-50/30" : "border-slate-200 bg-white"
              )}>
                {/* Checkbox */}
                <button
                  onClick={() => toggleContact(type)}
                  className="w-full p-4 flex items-center gap-4 text-left hover:bg-slate-50/50 transition-colors"
                >
                  <div className={cn(
                    "w-5 h-5 rounded border-2 flex items-center justify-center transition-colors",
                    config.enabled ? "bg-blue-500 border-blue-500" : "border-slate-300"
                  )}>
                    {config.enabled && <Check className="w-3.5 h-3.5 text-white" />}
                  </div>
                  <Icon className={cn("w-5 h-5", config.enabled ? "text-blue-600" : "text-slate-400")} />
                  <span className={cn("font-medium", config.enabled ? "text-slate-900" : "text-slate-600")}>
                    {label}
                  </span>
                  {type === 'fixe' && (
                    <span className="ml-auto text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                      Recommandé
                    </span>
                  )}
                </button>
                
                {/* Input conditionnel */}
                {config.enabled && (
                  <div className="px-4 pb-4 animate-in slide-in-from-top-2 duration-200">
                    <input
                      type="text"
                      value={config.value}
                      onChange={(e) => updateContactValue(type, e.target.value)}
                      placeholder={placeholder}
                      className={cn(
                        "w-full px-4 py-2.5 rounded-lg border bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all",
                        hasError ? "border-red-300" : "border-slate-300"
                      )}
                    />
                    {hasError && <p className="text-xs text-red-500 mt-1">{hasError}</p>}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Aperçu du format final */}
        {buildContactString() && (
          <div className="mt-6 p-4 bg-slate-50 border border-slate-200 rounded-xl">
            <p className="text-sm font-medium text-slate-700 mb-2">Format sur les documents :</p>
            <p className="text-sm text-slate-600 font-mono bg-white p-3 rounded-lg border">
              {buildContactString()}
            </p>
          </div>
        )}
      </div>
    );
  };

  // =============================================================================
  // RENDU ÉTAPE 4: DESIGN DE L'EN-TÊTE (Choix binaire)
  // =============================================================================
  const renderStep4 = () => (
    <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-slate-900">Design de l'en-tête</h2>
        <p className="text-slate-600 mt-2">Choisissez comment apparaîtra votre en-tête sur les documents</p>
      </div>

      {/* Toggle entre les deux options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Option A : Génération automatique */}
        <button
          onClick={() => setHeaderOption('auto')}
          className={cn(
            "relative p-6 rounded-xl border-2 text-left transition-all",
            headerOption === 'auto'
              ? "border-blue-500 bg-blue-50 shadow-md"
              : "border-slate-200 bg-white hover:border-blue-300"
          )}
        >
          {headerOption === 'auto' && (
            <div className="absolute top-4 right-4">
              <div className="bg-blue-600 text-white rounded-full p-1">
                <Check className="w-4 h-4" />
              </div>
            </div>
          )}
          <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-4">
            <ImageIcon className="w-6 h-6 text-blue-600" />
          </div>
          <h3 className="font-semibold text-slate-900 mb-2">Générer automatiquement</h3>
          <p className="text-sm text-slate-500">
            Nous créons votre en-tête avec votre logo, nom et coordonnées automatiquement formatés.
          </p>
        </button>

        {/* Option B : Papier en-tête personnalisé */}
        <button
          onClick={() => setHeaderOption('letterhead')}
          className={cn(
            "relative p-6 rounded-xl border-2 text-left transition-all",
            headerOption === 'letterhead'
              ? "border-green-500 bg-green-50 shadow-md"
              : "border-slate-200 bg-white hover:border-green-300"
          )}
        >
          {headerOption === 'letterhead' && (
            <div className="absolute top-4 right-4">
              <div className="bg-green-600 text-white rounded-full p-1">
                <Check className="w-4 h-4" />
              </div>
            </div>
          )}
          <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mb-4">
            <FileImage className="w-6 h-6 text-green-600" />
          </div>
          <h3 className="font-semibold text-slate-900 mb-2">J'ai mon papier en-tête A5</h3>
          <p className="text-sm text-slate-500">
            Uploadez votre propre papier à en-tête. Nous ajustons les marges pour un rendu parfait.
          </p>
        </button>
      </div>

      {/* Contenu conditionnel selon l'option */}
      <div className="mt-8">
        {headerOption === 'auto' ? (
          <div className="p-6 bg-slate-50 border border-slate-200 rounded-xl">
            <label className="block text-sm font-medium text-slate-700 mb-4">
              <Upload className="w-4 h-4 inline mr-1" />
              Logo du cabinet (optionnel)
            </label>
            
            <div 
              onClick={() => logoInputRef.current?.click()}
              className={cn(
                "w-full h-40 rounded-xl border-2 border-dashed cursor-pointer flex flex-col items-center justify-center transition-colors",
                logoPreview 
                  ? "border-blue-500 bg-blue-50" 
                  : "border-slate-300 hover:border-blue-400 hover:bg-slate-100"
              )}
            >
              {logoPreview ? (
                <img src={logoPreview} alt="Logo preview" className="h-full object-contain p-4" />
              ) : (
                <>
                  <ImageIcon className="w-10 h-10 text-slate-400 mb-2" />
                  <span className="text-sm text-slate-500">Cliquez pour uploader votre logo</span>
                  <span className="text-xs text-slate-400 mt-1">PNG ou SVG (max 2Mo)</span>
                </>
              )}
            </div>
            <input
              ref={logoInputRef}
              type="file"
              accept="image/png, image/svg+xml"
              onChange={handleLogoChange}
              className="hidden"
            />
            {errors.logo && <p className="text-sm text-red-500 mt-2">{errors.logo}</p>}
            
            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-700">
                <strong>Info :</strong> Sans logo, votre en-tête sera généré avec du texte uniquement, 
                avec le filigrane du cabinet en arrière-plan.
              </p>
            </div>
          </div>
        ) : (
          <div className="p-6 bg-green-50 border border-green-200 rounded-xl space-y-6">
            {/* Upload papier en-tête */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-4">
                <Upload className="w-4 h-4 inline mr-1" />
                Votre papier en-tête A5 *
              </label>
              
              <div 
                onClick={() => letterheadInputRef.current?.click()}
                className={cn(
                  "w-full h-48 rounded-xl border-2 border-dashed cursor-pointer flex flex-col items-center justify-center transition-colors",
                  letterheadPreview 
                    ? "border-green-500 bg-white" 
                    : "border-slate-300 hover:border-green-400 hover:bg-white/50"
                )}
              >
                {letterheadPreview ? (
                  <img src={letterheadPreview} alt="Letterhead preview" className="h-full object-contain p-4" />
                ) : (
                  <>
                    <FileImage className="w-10 h-10 text-slate-400 mb-2" />
                    <span className="text-sm text-slate-500">Cliquez pour uploader votre papier en-tête</span>
                    <span className="text-xs text-slate-400 mt-1">JPG ou PNG (max 5Mo)</span>
                  </>
                )}
              </div>
              <input
                ref={letterheadInputRef}
                type="file"
                accept="image/jpeg, image/png"
                onChange={handleLetterheadChange}
                className="hidden"
              />
              {errors.letterhead && <p className="text-sm text-red-500 mt-2">{errors.letterhead}</p>}
            </div>

            {/* Sliders pour les marges */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-slate-700 mb-3">
                  <Settings2 className="w-4 h-4" />
                  Marge Haute
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="1"
                    max="8"
                    step="0.5"
                    value={margins.top}
                    onChange={(e) => setMargins(prev => ({ ...prev, top: parseFloat(e.target.value) }))}
                    className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-green-600"
                  />
                  <span className="text-sm font-medium text-slate-700 w-16 text-right">
                    {margins.top.toFixed(1)} cm
                  </span>
                </div>
              </div>

              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-slate-700 mb-3">
                  <Settings2 className="w-4 h-4" />
                  Marge Basse
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="1"
                    max="6"
                    step="0.5"
                    value={margins.bottom}
                    onChange={(e) => setMargins(prev => ({ ...prev, bottom: parseFloat(e.target.value) }))}
                    className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-green-600"
                  />
                  <span className="text-sm font-medium text-slate-700 w-16 text-right">
                    {margins.bottom.toFixed(1)} cm
                  </span>
                </div>
              </div>
            </div>

            <div className="p-3 bg-white border border-green-200 rounded-lg">
              <p className="text-sm text-green-800">
                <strong>Configuration :</strong> Les marges définissent l'espace réservé pour votre 
                en-tête (haut) et pied de page (bas). Le contenu sera inséré entre ces marges.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  // =============================================================================
  // RENDU ÉTAPE 5: VALIDATION FINALE
  // =============================================================================
  const renderStep5 = () => {
    const specialties = buildSpecialtyStrings();
    
    return (
      <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-slate-900">Récapitulatif</h2>
          <p className="text-slate-600 mt-2">Vérifiez vos informations avant de finaliser</p>
        </div>

        <div className="bg-slate-50 rounded-xl p-6 space-y-6">
          {/* Identité */}
          <div className="border-b border-slate-200 pb-4">
            <h3 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <Building2 className="w-5 h-5 text-blue-600" />
              Identité du cabinet
            </h3>
            <div className="space-y-2 text-sm">
              <p><span className="text-slate-500">Cabinet:</span> <span className="font-medium">{identity.nomCabinet || 'Non renseigné'}</span></p>
              <p><span className="text-slate-500">Praticien:</span> <span className="font-medium">{identity.nomPraticien || 'Non renseigné'}</span></p>
              <p><span className="text-slate-500">Adresse:</span> {identity.adresse || 'Non renseignée'}</p>
            </div>
          </div>

          {/* Spécialités */}
          <div className="border-b border-slate-200 pb-4">
            <h3 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <Stethoscope className="w-5 h-5 text-blue-600" />
              Spécialités
            </h3>
            <div className="space-y-2">
              <p className="text-sm text-slate-600">{specialties.fr}</p>
              <p className="text-sm text-slate-600" dir="rtl">{specialties.ar}</p>
            </div>
          </div>

          {/* Contacts */}
          <div className="border-b border-slate-200 pb-4">
            <h3 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <Phone className="w-5 h-5 text-blue-600" />
              Coordonnées
            </h3>
            <p className="text-sm text-slate-600">{buildContactString()}</p>
          </div>

          {/* Design */}
          <div>
            <h3 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <Palette className="w-5 h-5 text-blue-600" />
              Design de l'en-tête
            </h3>
            <div className="flex items-center gap-3 p-3 bg-white rounded-lg border border-slate-200">
              {headerOption === 'auto' ? (
                <>
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <ImageIcon className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">Génération automatique</p>
                    <p className="text-sm text-slate-500">
                      {logoFile ? `Logo: ${logoFile.name}` : 'Sans logo (texte uniquement)'}
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <FileImage className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">Papier en-tête personnalisé</p>
                    <p className="text-sm text-slate-500">
                      {letterheadFile?.name} | Marges: {margins.top}cm / {margins.bottom}cm
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {errors.submit && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">{errors.submit}</p>
          </div>
        )}

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-700">
            <strong>Note:</strong> Vous pourrez modifier tous ces réglages à tout moment depuis 
            les paramètres du cabinet.
          </p>
        </div>
      </div>
    );
  };

  // =============================================================================
  // RENDU PRINCIPAL
  // =============================================================================
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
              <Building2 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-slate-900">Digital Crown</h1>
              <p className="text-xs text-slate-500">Configuration initiale</p>
            </div>
          </div>
          <div className="text-sm text-slate-500">
            Étape {currentStep} sur {STEPS.length}
          </div>
        </div>
      </header>

      {/* Progress Bar */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            {STEPS.map((step, index) => {
              const Icon = step.icon;
              const isActive = step.id === currentStep;
              const isCompleted = step.id < currentStep;
              
              return (
                <React.Fragment key={step.id}>
                  <div className="flex flex-col items-center">
                    <div
                      className={cn(
                        "w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center transition-colors",
                        isActive && "bg-blue-600 text-white",
                        isCompleted && "bg-green-500 text-white",
                        !isActive && !isCompleted && "bg-slate-100 text-slate-400"
                      )}
                    >
                      {isCompleted ? <Check className="w-5 h-5 sm:w-6 sm:h-6" /> : <Icon className="w-5 h-5 sm:w-6 sm:h-6" />}
                    </div>
                    <span className={cn(
                      "mt-2 text-xs sm:text-sm font-medium hidden sm:block",
                      isActive ? "text-blue-600" : "text-slate-500"
                    )}>
                      {step.title}
                    </span>
                  </div>
                  
                  {index < STEPS.length - 1 && (
                    <div className={cn(
                      "flex-1 h-1 mx-2 sm:mx-4 rounded",
                      isCompleted ? "bg-green-500" : "bg-slate-200"
                    )} />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-2xl mx-auto px-4 py-8">
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 p-6 sm:p-8">
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
          {currentStep === 4 && renderStep4()}
          {currentStep === 5 && renderStep5()}

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8 pt-6 border-t border-slate-200">
            <button
              onClick={handleBack}
              disabled={currentStep === 1 || loading}
              className={cn(
                "flex items-center gap-2 px-4 sm:px-6 py-3 rounded-lg font-medium transition-colors",
                currentStep === 1
                  ? "opacity-0 cursor-default"
                  : "text-slate-600 hover:bg-slate-100"
              )}
            >
              <ChevronLeft className="w-5 h-5" />
              Retour
            </button>

            {currentStep < 5 ? (
              <button
                onClick={handleNext}
                className="flex items-center gap-2 px-4 sm:px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                Continuer
                <ChevronRight className="w-5 h-5" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={loading}
                className={cn(
                  "flex items-center gap-2 px-6 sm:px-8 py-3 rounded-lg font-medium transition-colors",
                  loading
                    ? "bg-slate-400 cursor-not-allowed"
                    : "bg-green-600 hover:bg-green-700 text-white"
                )}
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
                    Création...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-5 h-5" />
                    Terminer
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default SetupWizard;
