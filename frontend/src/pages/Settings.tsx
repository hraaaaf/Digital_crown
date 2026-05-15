import React, { useState, useEffect } from 'react';
import { API_BASE } from '../services/api';
import { 
  Shield, 
  Database, 
  UserCircle, 
  Building, 
  Brain, 
  Save, 
  Download,
  Loader2,
  CheckCircle2,
  Upload,
  FileText,
  Settings2,
  Phone,
  Smartphone,
  Instagram,
  MessageCircle,
  Users,
  QrCode,
  Link,
  MapPin,
  Stethoscope,
  Image as ImageIcon,
  Palette as PaletteIcon, 
  Trash2, 
  Moon, 
  Sun, 
  Leaf, 
  Heart, 
  Keyboard, 
  Activity, 
  Sparkles
} from 'lucide-react';
import { api } from '../services/api';
import { cn } from '../utils/cn';
import { TeamManager } from '../features/admin/TeamManager';
import { BRAND_IDENTITIES, SPECIALTIES_DICT, APP_THEMES, PREMIUM_FONTS, DESIGN_VARIANTS } from '../features/admin/constants';
import { safeStorage } from '../hooks/useLocalStorage';

// --- COMPOSANT : CLAVIER ARABE VIRTUEL ---
const ArabicKeyboard = ({ onInput }: { onInput: (char: string) => void }) => {
  const letters = [
    'ض', 'ص', 'ث', 'ق', 'ف', 'غ', 'ع', 'ه', 'خ', 'ح', 'ج', 'د',
    'ش', 'س', 'ي', 'ب', 'ل', 'ا', 'ت', 'ن', 'م', 'ك', 'ط',
    'ئ', 'ء', 'ؤ', 'ر', 'لا', 'ى', 'ة', 'و', 'ز', 'ظ'
  ];
  return (
    <div 
      className="grid grid-cols-11 gap-1 p-2 bg-slate-900 rounded-xl shadow-2xl border border-slate-700 animate-in fade-in zoom-in-95 duration-200 z-[60]"
      onMouseDown={(e) => e.preventDefault()}
      onClick={(e) => e.stopPropagation()}
    >
      {letters.map(l => (
        <button
          key={l}
          type="button"
          onClick={() => onInput(l)}
          className="w-8 h-8 flex items-center justify-center bg-slate-800 text-white rounded-md hover:bg-primary hover:scale-110 active:scale-95 transition-all text-sm font-arabic"
        >
          {l}
        </button>
      ))}
      <button 
        type="button"
        onClick={() => onInput(' ')} 
        className="col-span-3 h-8 bg-slate-700 text-white rounded-md hover:bg-primary hover:scale-[1.02] active:scale-95 transition-all text-[10px] font-black uppercase tracking-widest"
      >
        Espace
      </button>
    </div>
  );
};

type Tab = 'profil' | 'branding' | 'ia' | 'securite' | 'equipe';

interface ContactInfo {
  enabled: boolean;
  value: string;
}

interface ContactsJson {
  fixe: ContactInfo;
  mobile: ContactInfo;
  whatsapp: ContactInfo;
  instagram: ContactInfo;
  [key: string]: ContactInfo;
}

interface CabinetProfile {
  nom: string;
  adresse: string;
  telephone: string;
  inpe: string;
  nom_cabinet?: string;
  letterhead_path?: string;
  margin_top?: number;
  margin_bottom?: number;
  watermark_enabled?: boolean;
  ice?: string;
  if?: string;
  contacts_json?: ContactsJson;
  selected_theme?: string;
  app_accent_color?: string;
  font_fr?: string;
  selected_template?: string;
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  qr_code_enabled?: boolean;
  qr_code_type?: 'VCARD' | 'WEBSITE' | 'INSTAGRAM' | 'WHATSAPP' | 'LOCATION' | 'VALIDATION' | 'PAYMENT';
  qr_code_value?: string;
  qr_code_color?: string;
  qr_code_label?: string;
  show_patient_badges?: boolean;
  nom_praticien_ar?: string;
  specialty_ids?: string[];
  logo_path?: string;
  header_lines_fr?: string[];
  header_lines_ar?: string[];
}

const TabButton = ({ active, onClick, icon, label }: { active: boolean, onClick: () => void, icon: React.ReactNode, label: string }) => (
  <button 
    onClick={onClick} 
    className={cn(
      "flex items-center gap-4 px-6 py-4 rounded-2xl font-bold transition-all duration-300 w-full text-left",
      active 
        ? "text-white shadow-lg scale-[1.02]" 
        : "text-slate-500 hover:bg-slate-50 hover:text-primary"
    )}
    style={{ 
      backgroundColor: active ? 'var(--primary)' : 'transparent',
      boxShadow: active ? '0 10px 30px -10px var(--primary)' : 'none',
      color: active ? 'white' : undefined
    }}
  >
    {icon} <span>{label}</span>
  </button>
);

export const Settings = () => {
  const [activeTab, setActiveTab] = useState<Tab>('profil');
  
  const [profile, setProfile] = useState<CabinetProfile>({ 
    nom: '', 
    adresse: '', 
    telephone: '', 
    inpe: '',
    ice: '',
    if: '',
    margin_top: 3.6,
    margin_bottom: 3.2,
    watermark_enabled: true,
    qr_code_enabled: false,
    qr_code_type: 'VCARD',
    qr_code_value: '',
    qr_code_color: '',
    qr_code_label: '',
    show_patient_badges: true,
    nom_praticien_ar: '',
    specialty_ids: [],
    logo_path: '',
    app_accent_color: undefined,
    font_fr: 'inter',
    selected_template: 'classic',
    header_lines_fr: [],
    header_lines_ar: []
  });

  const [contacts, setContacts] = useState<ContactsJson>({
    fixe: { enabled: true, value: '' },
    mobile: { enabled: false, value: '' },
    whatsapp: { enabled: false, value: '' },
    instagram: { enabled: false, value: '' }
  });

  const [loadingProfile, setLoadingProfile] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const [performanceMode, setPerformanceMode] = useState<boolean>(() => {
    return localStorage.getItem('performance_mode') === 'true';
  });

  const [clinicalTipsEnabled, setClinicalTipsEnabled] = useState<boolean>(() => {
    const saved = localStorage.getItem('clinical_tips_enabled');
    return saved === null ? true : saved === 'true';
  });

  const [showArKeyboard, setShowArKeyboard] = useState<{type: 'header' | 'name', idx?: number} | null>(null);

  const loadBenmoussaTemplate = () => {
    setProfile(p => ({
      ...p,
      header_lines_fr: [
        "Dr. Benmoussa Achraf",
        "Chirurgien Dentiste",
        "Soins - Prothèse",
        "Chirurgie - Parodontologie",
        "Blanchiment - Orthodontie"
      ],
      header_lines_ar: [
        "د. أشرف بنموسى",
        "طبيب جراح للأسنان",
        "علاج - تعويض الأسنان",
        "جراحة - أمراض اللثة",
        "تبييض - تقويم الأسنان"
      ]
    }));
  };

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await api.get('/clinics/me');
        if (res.data) {
          setProfile({
            nom: res.data.header_lines_fr?.[0] || res.data.nom_praticien || '',
            adresse: res.data.footer_address || res.data.adresse || '',
            telephone: res.data.footer_phones || res.data.telephone || '',
            inpe: res.data.inpe || '',
            ice: res.data.ice || '',
            if: res.data.if_ || res.data.if || '',
            margin_top: res.data.margin_top ?? 3.6,
            margin_bottom: res.data.margin_bottom ?? 3.2,
            watermark_enabled: res.data.watermark_enabled ?? true,
            letterhead_path: res.data.letterhead_path || undefined,
            selected_theme: res.data.selected_theme || 'elite',
            app_accent_color: res.data.app_accent_color || undefined,
            font_fr: res.data.font_fr || 'inter',
            selected_template: res.data.selected_template || 'classic',
            primary_color: res.data.primary_color || '#003380',
            secondary_color: res.data.secondary_color || '#1e40af',
            accent_color: res.data.accent_color || '#60a5fa',
            qr_code_enabled: res.data.qr_code_enabled ?? false,
            qr_code_type: res.data.qr_code_type || 'VCARD',
            qr_code_value: res.data.qr_code_value || '',
            qr_code_color: res.data.qr_code_color || '',
            qr_code_label: res.data.qr_code_label || '',
            show_patient_badges: res.data.show_patient_badges ?? true,
            nom_praticien_ar: res.data.nom_praticien_ar || '',
            specialty_ids: res.data.specialty_ids || [],
            logo_path: res.data.logo_path || '',
            header_lines_fr: res.data.header_lines_fr || [],
            header_lines_ar: res.data.header_lines_ar || []
          });
          
          localStorage.setItem('show_patient_badges', String(res.data.show_patient_badges ?? true));

          const themeValue = res.data.selected_theme === 'elite' ? '' : (res.data.selected_theme || '');
          document.body.dataset.theme = themeValue;
          if (res.data.app_accent_color) document.documentElement.style.setProperty('--primary', res.data.app_accent_color);

          if (res.data.contacts_json && Object.keys(res.data.contacts_json).length > 0) {
            setContacts(res.data.contacts_json as ContactsJson);
          } else if (res.data.footer_phones) {
            setContacts((prev) => ({
                ...prev,
                fixe: { enabled: true, value: res.data.footer_phones }
            }));
          }
        }
      } catch {
        console.warn("Route /api/clinics/me indisponible. Mock activé.");
        setProfile({
          nom: "Centre d'Orthodontie Moderne",
          adresse: "123 Avenue Hassan II, Casablanca",
          telephone: "05 22 33 44 55",
          inpe: "987654321",
          ice: "",
          if: "",
          margin_top: 3.6,
          margin_bottom: 3.2,
          watermark_enabled: true
        });
      } finally {
        setLoadingProfile(false);
      }
    };
    fetchProfile();
  }, []);

  useEffect(() => {
    if (loadingProfile) return;
    const themeValue = profile.selected_theme === 'elite' ? '' : (profile.selected_theme || '');
    document.body.dataset.theme = themeValue;
    if (profile.app_accent_color) {
      document.documentElement.style.setProperty('--primary', profile.app_accent_color);
    } else {
      document.documentElement.style.removeProperty('--primary');
    }
  }, [profile.selected_theme, profile.app_accent_color, loadingProfile]);

  const handleLetterheadUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('margins_top', (profile.margin_top || 3.6).toString());
    formData.append('margins_bottom', (profile.margin_bottom || 3.2).toString());

    try {
      setSavingProfile(true);
      const res = await api.post('/clinics/me/letterhead', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setProfile(prev => ({ 
        ...prev, 
        letterhead_path: res.data.letterhead_url,
        watermark_enabled: false 
      }));
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error("Erreur upload letterhead:", err);
    } finally {
      setSavingProfile(false);
    }
  };

  const generateHeaders = (nom: string, nomAr: string, specialtyIds: string[]) => {
    const linesFr = [];
    const linesAr = [];

    const cleanNom = nom.startsWith('Dr.') ? nom : `Dr. ${nom}`;
    const cleanNomAr = nomAr.endsWith(' .د') ? nomAr : `${nomAr} .د`;
    linesFr.push(cleanNom);
    linesAr.push(cleanNomAr);

    linesFr.push("Chirurgien Dentiste");
    linesAr.push("طبيب جراح للأسنان");

    const selected = SPECIALTIES_DICT.filter(s => specialtyIds.includes(s.id));
    for (let i = 0; i < selected.length; i += 2) {
      const pair = selected.slice(i, i + 2);
      linesFr.push(pair.map(p => p.fr).join(' - '));
      linesAr.push(pair.map(p => p.ar).reverse().join(' - '));
    }

    return { header_lines_fr: linesFr, header_lines_ar: linesAr };
  };

  const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    const updatedProfile = { ...profile, [name]: value };
    
    if (name === 'nom' || name === 'nom_praticien_ar') {
      const { header_lines_fr, header_lines_ar } = generateHeaders(updatedProfile.nom, updatedProfile.nom_praticien_ar || '', updatedProfile.specialty_ids || []);
      updatedProfile.header_lines_fr = header_lines_fr;
      updatedProfile.header_lines_ar = header_lines_ar;
    }
    
    setProfile(updatedProfile);
  };

  const toggleSpecialty = (id: string) => {
    const current = profile.specialty_ids || [];
    const updated = current.includes(id) 
      ? current.filter(sid => sid !== id) 
      : [...current, id];
    
    const { header_lines_fr, header_lines_ar } = generateHeaders(profile.nom, profile.nom_praticien_ar || '', updated);
    setProfile(prev => ({ 
      ...prev, 
      specialty_ids: updated,
      header_lines_fr,
      header_lines_ar
    }));
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setSavingProfile(true);
      const res = await api.post('/clinics/me/logo', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setProfile(prev => ({ ...prev, logo_path: res.data.logo_url }));
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error("Erreur upload logo:", err);
    } finally {
      setSavingProfile(false);
    }
  };

  const saveProfile = async () => {
    setSavingProfile(true);
    setSaveSuccess(false);

    const parts: string[] = [];
    Object.keys(contacts).forEach(type => {
      const c = contacts[type];
      if (c.enabled && c.value.trim()) {
        const icon = type === 'fixe' ? '📞' : type === 'mobile' ? '📱' : type === 'whatsapp' ? '💬' : '📸';
        parts.push(`${icon} ${c.value.trim()}`);
      }
    });
    const contactString = parts.join(' | ');

    try {
      const payload: any = {
        ...profile,
        nom_praticien_ar: profile.nom_praticien_ar,
        specialty_ids: profile.specialty_ids,
        footer_phones: contactString,
        contacts_json: contacts
      };

      if (!payload.qr_code_color) payload.qr_code_color = null;
      if (!payload.qr_code_value) payload.qr_code_value = null;
      if (!payload.qr_code_label) payload.qr_code_label = null;

      await api.put('/clinics/me', payload);
      
      if (safeStorage.get('appMode') === 'demo') {
        sessionStorage.setItem('demoConfig', JSON.stringify({
          selected_theme: profile.selected_theme,
          primary_color: profile.primary_color,
          secondary_color: profile.secondary_color,
          accent_color: profile.accent_color
        }));
      }

      const themeValue = profile.selected_theme === 'elite' ? '' : profile.selected_theme;
      document.body.dataset.theme = themeValue;
      if (profile.app_accent_color) {
        document.documentElement.style.setProperty('--primary', profile.app_accent_color);
      } else {
        document.documentElement.style.removeProperty('--primary');
      }
      
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error("Erreur sauvegarde profil:", err);
    } finally {
      setSavingProfile(false);
    }
  };

  const toggleContact = (type: string) => {
    setContacts((prev) => ({
      ...prev,
      [type]: { ...prev[type], enabled: !prev[type].enabled }
    }));
  };

  const updateContactValue = (type: string, val: string) => {
    setContacts((prev) => ({
      ...prev,
      [type]: { ...prev[type], value: val }
    }));
  };

  const togglePerformanceMode = () => {
    const newVal = !performanceMode;
    setPerformanceMode(newVal);
    localStorage.setItem('performance_mode', String(newVal));
  };

  const toggleClinicalTips = () => {
    const newVal = !clinicalTipsEnabled;
    setClinicalTipsEnabled(newVal);
    localStorage.setItem('clinical_tips_enabled', String(newVal));
    window.dispatchEvent(new Event('clinical-tips-changed'));
  };

  const handleExportDB = () => {
    window.open(`${API_BASE}/api/admin/export-db`, '_blank');
  };

  const inputClass = "w-full px-5 py-4 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-4 transition-all duration-300 font-bold text-slate-800";
  const labelClass = "text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1";

  return (
    <div className="max-w-[1200px] mx-auto w-full px-6 py-8 md:p-10 animate-in fade-in duration-700">
      
      <div className="mb-10">
        <h2 className="text-4xl font-black tracking-tight" style={{ color: 'var(--primary)' }}>Centre de Contrôle</h2>
        <p className="text-slate-500 font-medium mt-2 text-lg">Configuration globale de l'environnement Digital Crown.</p>
      </div>

      <div className="flex flex-col md:flex-row gap-10 items-start">
        
        {/* NAVIGATION DES ONGLETS */}
        <div data-tour="settings-navigation" className="w-full md:w-64 shrink-0 flex flex-col gap-2 bg-white/80 backdrop-blur-xl border border-slate-200/60 p-3 rounded-[2rem] shadow-sm sticky top-28">
          <TabButton active={activeTab === 'profil'} onClick={() => setActiveTab('profil')} icon={<Building size={20}/>} label="Profil Cabinet" />
          <TabButton active={activeTab === 'branding'} onClick={() => setActiveTab('branding')} icon={<PaletteIcon size={20}/>} label="Design & Ambiance" />
          <TabButton active={activeTab === 'equipe'} onClick={() => setActiveTab('equipe')} icon={<Users size={20}/>} label="Mon Équipe" />
          <TabButton active={activeTab === 'ia'} onClick={() => setActiveTab('ia')} icon={<Brain size={20}/>} label="Optimisation" />
          <TabButton active={activeTab === 'securite'} onClick={() => setActiveTab('securite')} icon={<Shield size={20}/>} label="Sécurité & Data" />
        </div>

        {/* CONTENU DES ONGLETS */}
        <div className="flex-1 bg-white/80 backdrop-blur-xl border border-slate-200/60 shadow-[0_8px_40px_rgba(0,0,0,0.04)] rounded-[2.5rem] overflow-hidden flex flex-col min-h-[600px]">
          
          {/* HEADER D'ACTION COLLANT */}
          <div className="sticky top-0 z-20 bg-white/40 backdrop-blur-md border-b border-slate-100 px-10 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Configuration Active</span>
            </div>
            
            <button 
              onClick={saveProfile} 
              disabled={savingProfile}
              className={cn(
                "px-6 py-3 text-white rounded-xl font-black transition-all shadow-lg flex items-center gap-3 disabled:opacity-70 text-xs",
                saveSuccess ? "scale-105" : "hover:scale-[1.02] active:scale-[0.98]"
              )}
              style={saveSuccess ? { backgroundColor: '#10b981', boxShadow: '0 8px 20px -6px rgba(16, 185, 129, 0.5)' } : { backgroundColor: 'var(--primary)', boxShadow: '0 8px 20px -6px var(--primary)' }}
            >
              {savingProfile ? <Loader2 className="animate-spin" size={16}/> : (saveSuccess ? <CheckCircle2 size={16} className="text-white"/> : <Save size={16} />)}
              {saveSuccess ? "Modifications Enregistrées" : "Enregistrer les réglages"}
            </button>
          </div>

          <div className="p-10 flex-1 overflow-y-auto">
            {/* TAB 1 : PROFIL CABINET */}
            {activeTab === 'profil' && (
              <div className="space-y-8 animate-in slide-in-from-right-4 duration-500">
                <div className="flex items-center gap-4 mb-8 pb-6 border-b border-slate-100">
                  <div className="w-16 h-16 bg-primary/5 rounded-2xl flex items-center justify-center shadow-inner border border-primary/10" style={{ color: 'var(--primary)' }}>
                    <UserCircle size={32} />
                  </div>
                  <div>
                    <h3 className="text-2xl font-black" style={{ color: 'var(--primary)' }}>Identité Officielle</h3>
                    <p className="text-slate-500 text-sm font-medium mt-1">Ces informations apparaîtront sur vos bilans PDF.</p>
                  </div>
                </div>

                {loadingProfile ? (
                  <div className="flex justify-center py-20"><Loader2 className="animate-spin" style={{ color: 'var(--primary)' }} size={40} /></div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div>
                      <label className={labelClass}>Nom du Praticien (Français)</label>
                      <input 
                        type="text" 
                        name="nom" 
                        value={profile.nom} 
                        onChange={handleProfileChange} 
                        className={inputClass} 
                        placeholder="Ex: Benmoussa Achraf" 
                        style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)', borderColor: 'rgba(var(--primary-rgb), 0.2)' } as React.CSSProperties}
                      />
                      <p className="text-[9px] text-slate-400 mt-2 font-medium italic">Le titre "Dr." sera ajouté automatiquement sur les documents.</p>
                    </div>
                    <div dir="rtl">
                      <label className={labelClass + " text-right"}>اسم الطبيب (بالعربية)</label>
                      <input 
                        type="text" 
                        name="nom_praticien_ar" 
                        value={profile.nom_praticien_ar} 
                        onChange={handleProfileChange} 
                        className={inputClass + " text-right font-amiri text-lg"} 
                        placeholder="مثال: بنموسى أشرف" 
                        style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)', borderColor: 'rgba(var(--primary-rgb), 0.2)' } as React.CSSProperties}
                      />
                      <p className="text-[9px] text-slate-400 mt-2 font-medium italic text-right">سيتم إضافة لقب ".د" تلقائياً.</p>
                    </div>

                    <div className="md:col-span-2 bg-primary/5 p-4 rounded-2xl border border-primary/10 flex items-center gap-4">
                      <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center text-primary shadow-sm">
                        <Stethoscope size={20} />
                      </div>
                      <div>
                        <p className="text-xs font-black text-primary uppercase tracking-wider">Titre Professionnel</p>
                        <p className="text-sm font-bold text-slate-700">Chirurgien Dentiste / طبيب جراح للأسنان</p>
                      </div>
                    </div>

                    {/* EXPERTISE CLINIQUE */}
                    <div className="md:col-span-2 mt-4">
                      <label className={labelClass}>Expertises & Spécialités Cliniques</label>
                      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 mt-4">
                        {SPECIALTIES_DICT.map(spec => {
                          const isSelected = profile.specialty_ids?.includes(spec.id);
                          return (
                            <button
                              key={spec.id}
                              onClick={() => toggleSpecialty(spec.id)}
                              className={cn(
                                "flex flex-col items-center gap-3 p-4 rounded-2xl border-2 transition-all group relative overflow-hidden",
                                isSelected 
                                  ? "border-primary bg-primary/5 shadow-md scale-[1.02]" 
                                  : "border-slate-100 bg-white hover:border-slate-200"
                              )}
                            >
                              <div className={cn(
                                "w-10 h-10 rounded-xl flex items-center justify-center transition-all",
                                isSelected ? "bg-primary text-white shadow-lg" : "bg-slate-50 text-slate-400 group-hover:scale-110"
                              )}>
                                <spec.icon size={20} />
                              </div>
                              <div className="text-center">
                                <span className={cn("block text-xs font-black", isSelected ? "text-primary" : "text-slate-600")}>{spec.fr}</span>
                                <span className={cn("block text-[10px] font-bold font-amiri", isSelected ? "text-primary/70" : "text-slate-400")}>{spec.ar}</span>
                              </div>
                              {isSelected && (
                                <div className="absolute top-2 right-2">
                                  <CheckCircle2 size={12} className="text-primary" />
                                </div>
                              )}
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    <div className="md:col-span-2">
                      <label className={labelClass}>Adresse complète du Cabinet</label>
                      <input type="text" name="adresse" value={profile.adresse} onChange={handleProfileChange} className={inputClass} style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)' } as React.CSSProperties} />
                    </div>
                    
                    <div className="md:col-span-2 mt-4 bg-amber-50 p-6 rounded-3xl border border-amber-100">
                      <div className="flex items-center gap-4 mb-4">
                        <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center text-amber-600 shadow-sm">
                          <PaletteIcon size={20} />
                        </div>
                        <h4 className="font-black text-amber-900">Logo du Cabinet</h4>
                      </div>
                      <div className="flex flex-col sm:flex-row items-center gap-8">
                        <div 
                          className="w-32 h-32 rounded-3xl bg-white border-2 border-dashed border-amber-200 flex items-center justify-center cursor-pointer hover:bg-amber-100/50 transition-all relative group overflow-hidden"
                          onClick={() => document.getElementById('logo-input')?.click()}
                        >
                          {profile.logo_path ? (
                            <>
                              <img 
                                src={profile.logo_path.startsWith('http') ? profile.logo_path : `${API_BASE}/static/uploads/${profile.logo_path}`} 
                                alt="Logo" 
                                className="w-full h-full object-contain p-4" 
                              />
                              <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                                <Upload className="text-white" size={24} />
                              </div>
                            </>
                          ) : (
                            <div className="flex flex-col items-center gap-2">
                              <ImageIcon className="text-amber-200" size={32} />
                              <span className="text-[9px] font-black text-amber-400 uppercase tracking-widest">Choisir Logo</span>
                            </div>
                          )}
                        </div>
                        <div className="flex-1 space-y-2">
                          <p className="text-xs font-bold text-amber-800">Conseil Elite :</p>
                          <p className="text-xs text-amber-700/80 leading-relaxed">Utilisez un logo sur fond transparent (PNG) pour une intégration parfaite dans vos entêtes Classic et Modern. Évitez les fichiers trop lourds (&gt; 2Mo).</p>
                          <input id="logo-input" type="file" className="hidden" accept="image/*" onChange={handleLogoUpload} />
                          {profile.logo_path && (
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                setProfile(p => ({ ...p, logo_path: '' }));
                                api.put('/clinics/me', { logo_path: null });
                              }}
                              className="mt-4 text-[10px] font-black text-rose-500 uppercase tracking-widest flex items-center gap-2 hover:text-rose-600 transition-colors"
                            >
                              <Trash2 size={12} /> Supprimer le logo
                            </button>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="md:col-span-2">
                      <label className={labelClass}>Téléphone & Visibilité</label>
                      <div className="w-full px-5 py-4 bg-blue-50/60 border border-blue-100 rounded-xl text-sm font-medium text-slate-500 flex items-center gap-3">
                        <Phone size={16} className="text-blue-400 shrink-0" />
                        <span>
                          Gérez vos numéros de contact dans la section{' '}
                          <strong className="text-slate-700">Contacts &amp; Visibilité</strong>{' '}ci-dessous — fixe, mobile et WhatsApp séparément.
                        </span>
                      </div>
                    </div>

                    <div>
                      <label className={labelClass}>Numéro INPE</label>
                      <input type="text" name="inpe" value={profile.inpe} onChange={handleProfileChange} className={inputClass} style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)' } as React.CSSProperties} />
                    </div>
                    <div>
                      <label className={labelClass}>ICE / IF</label>
                      <div className="grid grid-cols-2 gap-4">
                         <input type="text" name="ice" value={profile.ice} onChange={handleProfileChange} className={inputClass} placeholder="ICE" />
                         <input type="text" name="if" value={profile.if} onChange={handleProfileChange} className={inputClass} placeholder="IF" />
                      </div>
                    </div>

                    {/* SECTION SPÉCIALITÉS & EN-TÊTE BILINGUE */}
                    <div className="md:col-span-2 mt-8 py-8 border-t border-slate-100 space-y-8">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-primary/5 rounded-lg flex items-center justify-center shadow-inner" style={{ color: 'var(--primary)' }}>
                            <Users size={20} />
                          </div>
                          <h4 className="text-lg font-black text-slate-800">Spécialités & En-tête Bilingue</h4>
                        </div>
                        <button 
                          onClick={loadBenmoussaTemplate}
                          className="px-4 py-2 bg-primary/5 border border-primary/20 text-primary rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-primary/10 transition-all flex items-center gap-2"
                        >
                          <Settings2 size={14} />
                          Modèle Dr Benmoussa
                        </button>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Français */}
                        <div className="space-y-4">
                          <label className={labelClass}>En-tête Français (Document Header)</label>
                          <div className="space-y-2">
                            {(profile.header_lines_fr || []).map((line, idx) => (
                              <div key={`fr-${idx}`} className="flex gap-2">
                                <input 
                                  className={cn(inputClass, "py-2 px-3", idx === 0 && "text-primary text-base")} 
                                  value={line} 
                                  placeholder={idx === 0 ? "Nom du Praticien" : "Titre ou Spécialité..."}
                                  onChange={(e) => {
                                    const newLines = [...(profile.header_lines_fr || [])];
                                    newLines[idx] = e.target.value;
                                    setProfile({...profile, header_lines_fr: newLines});
                                  }}
                                />
                                <button 
                                  onClick={() => {
                                    const newLines = (profile.header_lines_fr || []).filter((_, i) => i !== idx);
                                    setProfile({...profile, header_lines_fr: newLines});
                                  }}
                                  className="p-2 text-red-400 hover:bg-red-50 rounded-lg transition-colors"
                                >
                                  ×
                                </button>
                              </div>
                            ))}
                            {(profile.header_lines_fr || []).length < 6 && (
                              <button 
                                onClick={() => setProfile({...profile, header_lines_fr: [...(profile.header_lines_fr || []), ""]})}
                                className="w-full py-2 border-2 border-dashed border-slate-200 text-slate-400 font-bold text-xs rounded-xl hover:bg-slate-50 transition-all"
                              >
                                + Ajouter une ligne (FR)
                              </button>
                            )}
                          </div>
                        </div>

                        {/* Arabe */}
                        <div className="space-y-4">
                          <label className={cn(labelClass, "text-right")}>En-tête Arabe (En-tête de l'ordonnance)</label>
                          <div className="space-y-2 relative">
                            {(profile.header_lines_ar || []).map((line, idx) => (
                              <div key={`ar-${idx}`} className="flex gap-2 group">
                                <button 
                                  onClick={() => {
                                    const newLines = (profile.header_lines_ar || []).filter((_, i) => i !== idx);
                                    setProfile({...profile, header_lines_ar: newLines});
                                  }}
                                  className="p-2 text-red-400 hover:bg-red-50 rounded-lg transition-colors"
                                >
                                  ×
                                </button>
                                <div className="flex-1 relative">
                                  <input 
                                    className={cn(inputClass, "py-2 px-3 text-right font-arabic", idx === 0 && "text-primary text-base")} 
                                    dir="rtl"
                                    value={line} 
                                    placeholder={idx === 0 ? "د. اسم الطبيب" : "التخصص..."}
                                    onChange={(e) => {
                                      const newLines = [...(profile.header_lines_ar || [])];
                                      newLines[idx] = e.target.value;
                                      setProfile({...profile, header_lines_ar: newLines});
                                    }}
                                    onFocus={() => setShowArKeyboard({type: 'header', idx})}
                                  />
                                  {showArKeyboard?.type === 'header' && showArKeyboard.idx === idx && (
                                    <div className="absolute top-full right-0 mt-2 z-50">
                                      <div className="fixed inset-0" onClick={() => setShowArKeyboard(null)} />
                                      <ArabicKeyboard onInput={(char) => {
                                        const newLines = [...(profile.header_lines_ar || [])];
                                        newLines[idx] = (newLines[idx] || '') + char;
                                        setProfile({...profile, header_lines_ar: newLines});
                                      }} />
                                    </div>
                                  )}
                                  <button className="absolute left-2 top-1/2 -translate-y-1/2 text-slate-300 hover:text-primary transition-colors opacity-0 group-hover:opacity-100" onClick={() => setShowArKeyboard({type: 'header', idx})}>
                                    <Keyboard size={14} />
                                  </button>
                                </div>
                              </div>
                            ))}
                            {(profile.header_lines_ar || []).length < 6 && (
                              <button 
                                onClick={() => setProfile({...profile, header_lines_ar: [...(profile.header_lines_ar || []), ""]})}
                                className="w-full py-2 border-2 border-dashed border-slate-200 text-slate-400 font-bold text-xs rounded-xl hover:bg-slate-50 transition-all"
                              >
                                + Ajouter une ligne (AR)
                              </button>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Gestion des spécialités (Chips) */}
                      <div className="space-y-6 pt-6 border-t border-slate-50">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                          <label className={labelClass}>Spécialités affichées (Chips de mise en avant)</label>
                          <div className="flex flex-wrap gap-1.5">
                            {['Endodontie', 'Esthétique', 'Implantologie', 'Stomatologie', 'Parodontologie', 'Blanchiment'].map(s => (
                              <button
                                key={s}
                                onClick={() => {
                                  if (!(profile.specialty_ids || []).includes(s)) {
                                    setProfile(p => ({ ...p, specialty_ids: [...(p.specialty_ids || []), s] }));
                                  }
                                }}
                                className="px-2.5 py-1 bg-slate-100 text-slate-500 rounded-full text-[9px] font-black uppercase hover:bg-primary/10 hover:text-primary transition-all border border-transparent hover:border-primary/20"
                              >
                                + {s}
                              </button>
                            ))}
                          </div>
                        </div>

                        <div className="flex flex-wrap gap-2 p-4 bg-white rounded-[1.5rem] border border-slate-200 shadow-inner min-h-[70px] relative">
                          {(profile.specialty_ids || []).map((spec, idx) => (
                            <div key={idx} className="flex items-center gap-2 bg-primary/5 px-3 py-1.5 rounded-full border border-primary/20 shadow-sm animate-in zoom-in-95 duration-200">
                              <span className="text-xs font-black text-primary">{spec}</span>
                              <button 
                                onClick={() => setProfile(p => ({ ...p, specialty_ids: p.specialty_ids?.filter((_, i) => i !== idx) }))}
                                className="w-4 h-4 rounded-full bg-white text-primary hover:bg-red-500 hover:text-white flex items-center justify-center text-[10px] transition-all shadow-sm"
                              >
                                ×
                              </button>
                            </div>
                          ))}
                          <input 
                            type="text" 
                            placeholder="Saisir manuellement..."
                            className="bg-transparent border-none outline-none text-xs font-bold text-slate-400 px-2 min-w-[150px]"
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                const val = (e.target as HTMLInputElement).value.trim();
                                if (val && !(profile.specialty_ids || []).includes(val)) {
                                  setProfile(p => ({ ...p, specialty_ids: [...(p.specialty_ids || []), val] }));
                                  (e.target as HTMLInputElement).value = '';
                                }
                              }
                            }}
                          />
                        </div>
                        <p className="text-[10px] text-slate-400 font-medium italic ml-2">Les spécialités ci-dessus apparaîtront sur vos en-têtes et documents de bilan.</p>
                      </div>
                    </div>

                    {/* SECTION CONTACTS DYNAMIQUE */}
                    <div className="md:col-span-2 mt-8 py-8 border-t border-slate-100">
                      <div className="flex items-center gap-3 mb-6">
                        <div className="w-10 h-10 bg-primary/5 rounded-lg flex items-center justify-center" style={{ color: 'var(--primary)' }}>
                          <Smartphone size={20} />
                        </div>
                        <h4 className="text-lg font-black text-slate-800">Contacts & Visibilité (Pied de page)</h4>
                      </div>
                      
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {Object.keys(contacts).map((type) => {
                          const c = contacts[type];
                          const Icon = type === 'fixe' ? Phone : type === 'mobile' ? Smartphone : type === 'whatsapp' ? MessageCircle : Instagram;
                          const label = type === 'fixe' ? 'Tél. Fixe' : type === 'mobile' ? 'Tél. Mobile' : type === 'whatsapp' ? 'WhatsApp' : 'Instagram';
                          const colorClass = type === 'whatsapp' ? 'text-emerald-500' : type === 'instagram' ? 'text-pink-500' : 'text-primary';

                          return (
                            <div key={type} className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-all">
                              <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-2">
                                  <Icon size={16} className={type !== 'whatsapp' && type !== 'instagram' ? colorClass : undefined} style={type === 'whatsapp' || type === 'instagram' ? {} : { color: 'var(--primary)' }} />
                                  <span className="text-xs font-black uppercase text-slate-400 tracking-wider font-mono">{label}</span>
                                </div>
                                <button 
                                  onClick={() => toggleContact(type)}
                                  className={cn(
                                    "w-10 h-5 rounded-full transition-all relative flex items-center px-1",
                                    c.enabled ? "bg-emerald-500" : "bg-slate-200"
                                  )}
                                >
                                  <div className={cn(
                                    "w-3 h-3 bg-white rounded-full transition-all",
                                    c.enabled ? "translate-x-5" : "translate-x-0"
                                  )} />
                                </button>
                              </div>
                              <input 
                                type="text" 
                                value={c.value} 
                                onChange={(e) => updateContactValue(type, e.target.value)}
                                disabled={!c.enabled}
                                placeholder={type === 'instagram' ? '@votrecompte' : 'Numéro...'}
                                className={cn(
                                  "w-full bg-slate-50 px-3 py-2 rounded-lg text-xs font-bold outline-none border border-transparent focus:border-primary/50 transition-all",
                                  !c.enabled && "opacity-50 grayscale cursor-not-allowed"
                                )}
                                style={{ borderColor: c.enabled ? 'var(--primary)' : undefined } as React.CSSProperties}
                              />
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* SECTION STRATÉGIE QR CODE */}
                    <div className="md:col-span-2 mt-12 py-8 border-t border-slate-100">
                      <div className="flex items-center gap-4 mb-8">
                        <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center shadow-inner border border-indigo-100">
                          <QrCode size={24} />
                        </div>
                        <div className="flex-1">
                          <h3 className="text-xl font-black text-slate-800">Stratégie QR Code</h3>
                          <p className="text-slate-500 text-sm font-medium">Ajoutez un code QR intelligent à vos documents pour faciliter le contact ou la validation.</p>
                        </div>
                        <button 
                          onClick={() => setProfile(p => ({ ...p, qr_code_enabled: !p.qr_code_enabled }))}
                          className={cn(
                            "w-14 h-7 rounded-full transition-all relative flex items-center px-1",
                            profile.qr_code_enabled ? "bg-indigo-600" : "bg-slate-200"
                          )}
                        >
                          <div className={cn(
                            "w-5 h-5 bg-white rounded-full transition-all shadow-md",
                            profile.qr_code_enabled ? "translate-x-7" : "translate-x-0"
                          )} />
                        </button>
                      </div>

                      {profile.qr_code_enabled && (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 animate-in slide-in-from-top-4 duration-300">
                          <div className="space-y-6">
                            <div>
                              <label className={labelClass}>Type de Contenu</label>
                              <div className="grid grid-cols-2 gap-2">
                                {[
                                  { id: 'VCARD', label: 'Carte Visite', icon: <UserCircle size={14}/> },
                                  { id: 'WEBSITE', label: 'Site Web', icon: <Link size={14}/> },
                                  { id: 'INSTAGRAM', label: 'Instagram', icon: <Instagram size={14}/> },
                                  { id: 'WHATSAPP', label: 'WhatsApp', icon: <MessageCircle size={14}/> },
                                  { id: 'LOCATION', label: 'Localisation', icon: <MapPin size={14}/> },
                                  { id: 'VALIDATION', label: 'Vérification', icon: <Shield size={14}/> },
                                  { id: 'PAYMENT', label: 'Paiement', icon: <Smartphone size={14}/> },
                                ].map(t => (
                                  <button
                                    key={t.id}
                                    onClick={() => setProfile(p => ({ ...p, qr_code_type: t.id as 'VCARD' | 'WEBSITE' | 'INSTAGRAM' | 'WHATSAPP' | 'LOCATION' | 'VALIDATION' | 'PAYMENT' }))}
                                    className={cn(
                                      "flex items-center gap-2 px-4 py-3 rounded-xl border font-bold text-xs transition-all",
                                      profile.qr_code_type === t.id 
                                        ? "bg-indigo-50 border-indigo-200 text-indigo-700 shadow-sm" 
                                        : "bg-white border-slate-100 text-slate-500 hover:border-slate-200"
                                    )}
                                  >
                                    {t.icon} {t.label}
                                  </button>
                                ))}
                              </div>
                            </div>

                            {(profile.qr_code_type !== 'VCARD' && profile.qr_code_type !== 'VALIDATION' && profile.qr_code_type !== 'PAYMENT') && (
                              <div>
                                <label className={labelClass}>Valeur (URL ou Handle)</label>
                                <input 
                                  type="text" 
                                  value={profile.qr_code_value} 
                                  onChange={(e) => setProfile(p => ({ ...p, qr_code_value: e.target.value }))}
                                  className={inputClass}
                                  placeholder={
                                    profile.qr_code_type === 'INSTAGRAM' ? '@votre_compte' :
                                    profile.qr_code_type === 'WHATSAPP' ? 'Numéro avec indicatif...' :
                                    'https://...'
                                  }
                                />
                              </div>
                            )}

                            <div>
                              <label className={labelClass}>Étiquette sous le QR (Optionnel)</label>
                              <input
                                type="text"
                                value={profile.qr_code_label}
                                onChange={(e) => setProfile(p => ({ ...p, qr_code_label: e.target.value }))}
                                className={inputClass}
                                placeholder="Ex: Scannez pour nous suivre"
                              />
                            </div>

                            <div className="flex items-center gap-4 p-4 bg-slate-50 rounded-2xl border border-slate-200">
                              <label className="text-xs font-black text-slate-500 uppercase tracking-widest flex-1">Couleur du QR</label>
                              <input
                                type="color"
                                value={profile.qr_code_color || profile.primary_color || '#003380'}
                                onChange={(e) => setProfile(p => ({ ...p, qr_code_color: e.target.value }))}
                                className="w-10 h-10 rounded-xl cursor-pointer border-2 border-white shadow-md bg-transparent"
                              />
                            </div>
                          </div>

                          <div className="bg-indigo-50/50 rounded-3xl p-8 border border-indigo-100 flex flex-col items-center justify-center text-center">
                            <div className="w-32 h-32 bg-white rounded-2xl shadow-xl flex items-center justify-center mb-6 border border-indigo-50">
                              <QrCode size={80} className="text-indigo-600" />
                            </div>
                            <h4 className="font-black text-indigo-900">Aperçu Stratégique</h4>
                            <p className="text-[10px] text-indigo-600/70 font-bold uppercase tracking-wider mt-2">
                              Mode : {profile.qr_code_type}
                            </p>
                            <div className="mt-6 p-4 bg-white/60 rounded-xl border border-indigo-100 text-[10px] font-medium text-indigo-800 leading-relaxed max-w-[240px]">
                              {profile.qr_code_type === 'VCARD' && "Le QR contiendra vos coordonnées complètes (Nom, Tél, Email, Adresse) pour ajout direct aux contacts."}
                              {profile.qr_code_type === 'WEBSITE' && "Le QR dirigera vos patients vers votre site web officiel ou portail de prise de rendez-vous."}
                              {profile.qr_code_type === 'INSTAGRAM' && "Le QR ouvrira directement votre profil Instagram pour booster votre visibilité sociale."}
                              {profile.qr_code_type === 'WHATSAPP' && "Permet au patient de vous envoyer un message WhatsApp instantané."}
                              {profile.qr_code_type === 'LOCATION' && "Ouvre Google Maps sur l'adresse exacte de votre cabinet."}
                              {profile.qr_code_type === 'VALIDATION' && "Insère une signature numérique sécurisée permettant de vérifier l'authenticité de l'ordonnance."}
                              {profile.qr_code_type === 'PAYMENT' && "Permet de suivre l'état des paiements et des échéances."}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* SECTION DESIGN & IMPRESSION (LETTERHEAD) */}
                    <div className="md:col-span-2 mt-12 pt-10 border-t border-slate-100">
                      <div className="flex items-center gap-4 mb-8">
                         <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center shadow-inner border border-emerald-100">
                          <FileText size={24} />
                        </div>
                        <div>
                          <h3 className="text-xl font-black text-slate-800">Design & Impression</h3>
                          <p className="text-slate-500 text-sm font-medium">Configurez votre papier à en-tête physique ou le design automatique.</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        {/* Upload Letterhead */}
                        <div className="space-y-6">
                          <div className="bg-slate-50 p-6 rounded-3xl border border-slate-200">
                            <label className={labelClass}>Papier à En-tête (A5/A4)</label>
                            <div 
                              onClick={() => document.getElementById('letterhead-input')?.click()}
                              className="mt-2 w-full h-40 rounded-2xl border-2 border-dashed border-slate-300 bg-white flex flex-col items-center justify-center cursor-pointer hover:bg-primary/5 transition-all overflow-hidden"
                              style={{ borderColor: 'var(--primary)' }}
                            >
                               {profile.letterhead_path ? (
                                 <img 
                                   src={profile.letterhead_path.startsWith('http') ? profile.letterhead_path : `${API_BASE}/static/uploads/${profile.letterhead_path}`}
                                   className="h-full object-contain p-4" 
                                   alt="Letterhead" 
                                  />
                               ) : (
                                 <>
                                   <Upload className="text-slate-300 mb-2" size={32} />
                                   <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest text-center px-4">Glissez votre PDF ou Image ici</span>
                                 </>
                               )}
                            </div>
                            <input 
                              id="letterhead-input" 
                              type="file" 
                              className="hidden" 
                              accept="image/*,application/pdf"
                              onChange={handleLetterheadUpload}
                            />
                            <p className="text-[9px] text-slate-400 mt-3 italic font-medium">L'upload d'un papier désactive automatiquement le design "Wizard" pour respecter votre identité visuelle physique.</p>
                          </div>

                          <div className="flex items-center justify-between p-4 bg-white border border-slate-200 rounded-2xl shadow-sm">
                             <div className="flex items-center gap-3">
                                <Settings2 size={16} className="text-slate-400" />
                                <span className="font-bold text-xs text-slate-700">Mode Design Automatique</span>
                             </div>
                             <button 
                               onClick={() => {
                                 const newVal = !profile.watermark_enabled;
                                 setProfile(p => ({ ...p, watermark_enabled: newVal }));
                                 api.put('/clinics/me', { watermark_enabled: newVal });
                               }}
                               className={cn(
                                 "w-12 h-6 rounded-full transition-all relative",
                                 profile.watermark_enabled ? "bg-emerald-500" : "bg-slate-300"
                               )}
                             >
                               <div className={cn("absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-all", profile.watermark_enabled ? "left-7" : "left-1")} />
                             </button>
                          </div>
                        </div>

                        {/* Marges */}
                        <div className="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm space-y-8">
                           <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
                             Réglage des Marges (CM)
                           </h4>
                           
                           <div className="space-y-6">
                              <div className="space-y-3">
                                 <div className="flex justify-between items-center">
                                    <span className="text-xs font-bold text-slate-700">Marge Supérieure</span>
                                    <span className="text-lg font-black" style={{ color: 'var(--primary)' }}>{profile.margin_top || 3.6} <span className="text-[10px]">cm</span></span>
                                 </div>
                                 <input 
                                   type="range" 
                                   min="0" max="10" step="0.2"
                                   value={profile.margin_top || 3.6} 
                                   onChange={(e) => {
                                     const val = parseFloat(e.target.value);
                                     setProfile(p => ({ ...p, margin_top: val }));
                                     api.put('/clinics/me', { margin_top: val });
                                   }}
                                   className="w-full h-1.5 bg-slate-100 rounded-lg cursor-pointer" 
                                   style={{ accentColor: 'var(--primary)' }}
                                 />
                              </div>

                              <div className="space-y-3">
                                 <div className="flex justify-between items-center">
                                    <span className="text-xs font-bold text-slate-700">Marge Inférieure</span>
                                    <span className="text-lg font-black text-emerald-600">{profile.margin_bottom || 3.2} <span className="text-[10px]">cm</span></span>
                                 </div>
                                 <input 
                                   type="range" 
                                   min="0" max="6" step="0.2"
                                   value={profile.margin_bottom || 3.2} 
                                   onChange={(e) => {
                                     const val = parseFloat(e.target.value);
                                     setProfile(p => ({ ...p, margin_bottom: val }));
                                     api.put('/clinics/me', { margin_bottom: val });
                                   }}
                                   className="w-full h-1.5 bg-slate-100 rounded-lg accent-emerald-600 cursor-pointer" 
                                 />
                              </div>
                           </div>
                        </div>
                        
                        <div className="p-4 bg-primary/5 rounded-2xl border border-primary/10 flex flex-col justify-center">
                           <p className="text-[10px] font-medium leading-relaxed" style={{ color: 'var(--primary)' }}>
                              <b>Note :</b> La marge haute correspond généralement à la hauteur de votre en-tête physique. La marge basse protège votre pied de page pré-imprimé.
                           </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 2 : DESIGN & AMBIANCE */}
            {activeTab === 'branding' && (
              <div data-tour="settings-branding" className="space-y-10 animate-in slide-in-from-right-4 duration-500">
                <div className="grid grid-cols-1 xl:grid-cols-5 gap-12">
                  {/* COLONNE RÉGLAGES */}
                  <div className="xl:col-span-3 space-y-12">

                    {/* 1. SÉLECTION DU THÈME */}
                    <div className="space-y-6">
                      <label className={labelClass}>Thème du Logiciel (Ambiance)</label>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {[
                          { id: 'elite', name: 'Ghost Elite', icon: <Sun size={20} />, desc: 'Clair & Pur', color: 'bg-slate-100 text-slate-600', preview: 'bg-medical-pearl' },
                          { id: 'emerald', name: 'Émeraude Zen', icon: <Leaf size={20} />, desc: 'Serein & Médical', color: 'bg-emerald-50 text-emerald-600', preview: 'bg-emerald-50/30' },
                          { id: 'rose', name: 'Rose Prestige', icon: <Heart size={20} />, desc: 'Luxe & Douceur', color: 'bg-rose-50 text-rose-600', preview: 'bg-rose-50/30' },
                          { id: 'prestige', name: 'Nuit Intense', icon: <Moon size={20} />, desc: 'Sombre Médical', color: 'bg-slate-800 text-slate-200', preview: 'bg-slate-900' },
                          { id: 'dark', name: 'Onyx Elite', icon: <Sparkles size={20} />, desc: 'Dark Mode Absolu', color: 'bg-slate-950 text-indigo-400', preview: 'bg-black' }
                        ].map(t => (
                          <button
                            key={t.id}
                            onClick={() => {
                              const newTheme = t.id;
                              setProfile({ ...profile, selected_theme: newTheme });
                              
                              document.body.dataset.theme = newTheme === 'elite' ? '' : newTheme;

                              if (safeStorage.get('appMode') === 'demo') {
                                const stored = sessionStorage.getItem('demoConfig');
                                if (stored) {
                                  try {
                                    const config = JSON.parse(stored);
                                    config.selected_theme = newTheme;
                                    sessionStorage.setItem('demoConfig', JSON.stringify(config));
                                  } catch (e) {}
                                }
                              }
                            }}
                            className={cn(
                              "p-5 rounded-elite-lg border-2 transition-elite flex items-center gap-4 text-left group relative overflow-hidden",
                              profile.selected_theme === t.id 
                                ? "border-primary bg-primary/5 shadow-elite scale-[1.02]" 
                                : "border-border-main bg-card-bg hover:bg-primary/5"
                            )}
                          >
                            <div className={cn("w-12 h-12 rounded-elite-sm flex items-center justify-center shadow-sm group-hover:scale-110 transition-elite", t.color)}>
                              {t.icon}
                            </div>
                            <div className="flex-1">
                              <span className="block font-black text-sm text-main" style={{ color: 'var(--text-main)' }}>{t.name}</span>
                              <span className="text-[10px] text-text-muted font-bold uppercase tracking-tight">{t.desc}</span>
                            </div>
                            {profile.selected_theme === t.id && (
                              <div className="absolute top-2 right-2">
                                <CheckCircle2 size={16} className="text-primary" />
                              </div>
                            )}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* 2. IDENTITÉ VISUELLE */}
                    <div className="space-y-6 pt-10 border-t border-slate-100">
                      <label className={labelClass}>Identité Visuelle (Couleurs Signature)</label>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {BRAND_IDENTITIES.map(id => (
                          <button
                            key={id.id}
                            onClick={() => {
                              setProfile({ 
                                ...profile, 
                                primary_color: id.primary, 
                                secondary_color: id.secondary, 
                                accent_color: id.accent 
                              });
                              document.documentElement.style.setProperty('--primary', id.primary);

                              if (safeStorage.get('appMode') === 'demo') {
                                const stored = sessionStorage.getItem('demoConfig');
                                if (stored) {
                                  try {
                                    const config = JSON.parse(stored);
                                    config.primary_color = id.primary;
                                    config.secondary_color = id.secondary;
                                    config.accent_color = id.accent;
                                    sessionStorage.setItem('demoConfig', JSON.stringify(config));
                                  } catch (e) {}
                                }
                              }
                            }}
                            className={cn(
                              "p-5 rounded-elite-lg border-2 transition-elite text-left flex flex-col gap-4 group relative overflow-hidden",
                              profile.primary_color === id.primary ? "border-primary bg-white shadow-elite scale-[1.02]" : "border-slate-100 bg-slate-50/50 hover:bg-white"
                            )}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex flex-col">
                                <h5 className="text-[11px] font-black uppercase tracking-tighter text-slate-900">{id.name}</h5>
                                <span className="text-[9px] text-slate-400 font-bold uppercase">{id.vibe}</span>
                              </div>
                              <div className="flex -space-x-2">
                                <div className="w-6 h-6 rounded-full border-2 border-white shadow-sm" style={{ backgroundColor: id.primary }} />
                                <div className="w-6 h-6 rounded-full border-2 border-white shadow-sm" style={{ backgroundColor: id.secondary }} />
                                <div className="w-6 h-6 rounded-full border-2 border-white shadow-sm" style={{ backgroundColor: id.accent }} />
                              </div>
                            </div>
                            <p className="text-[10px] text-slate-500 leading-relaxed font-medium">{id.desc}</p>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* AJUSTEMENT COULEURS MANUEL */}
                    <div className="p-6 bg-slate-50 rounded-2xl border border-slate-200 flex flex-col sm:flex-row items-start sm:items-center gap-6">
                      <div className="flex-1">
                        <h4 className="text-sm font-black text-slate-800">Ajustement Manuel</h4>
                        <p className="text-[10px] text-slate-500 mt-1 font-medium">Personnalisation HEX des teintes du document.</p>
                      </div>
                      <div className="flex items-center gap-6">
                        {[
                          { label: 'Primaire', key: 'primary_color' as const },
                          { label: 'Secondaire', key: 'secondary_color' as const },
                          { label: 'Accent', key: 'accent_color' as const }
                        ].map(({ label, key }) => (
                          <div key={key} className="flex flex-col items-center gap-2">
                            <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{label}</span>
                            <input
                              type="color"
                              value={profile[key] || '#003380'}
                              onChange={(e) => setProfile({ ...profile, [key]: e.target.value })}
                              className="w-10 h-10 rounded-xl cursor-pointer border-2 border-white shadow-md bg-transparent"
                            />
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* TYPOGRAPHIE + MISE EN PAGE */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                      <div className="space-y-3">
                        <label className={labelClass}>Typographie des documents</label>
                        <div className="space-y-2">
                          {PREMIUM_FONTS.map(f => (
                            <button
                              key={f.id}
                              onClick={() => setProfile({ ...profile, font_fr: f.id })}
                              className={cn(
                                "w-full p-3 rounded-xl border-2 text-left flex items-center justify-between transition-all",
                                (profile.font_fr === f.id || (!profile.font_fr && f.id === 'inter')) ? "border-amber-400 bg-amber-50/50" : "border-slate-100 bg-white hover:bg-slate-50"
                              )}
                            >
                              <div>
                                <span className={cn("block text-sm font-bold", f.class)}>{f.name}</span>
                                <span className="text-[9px] text-slate-400">{f.desc}</span>
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-3">
                        <label className={labelClass}>Modèle de mise en page</label>
                        <div className="space-y-2">
                          {DESIGN_VARIANTS.map((v: any) => (
                            <button
                              key={v.id}
                              onClick={() => setProfile({ ...profile, selected_template: v.id })}
                              className={cn(
                                "w-full p-3 rounded-xl border-2 text-left flex items-center gap-3 transition-all",
                                profile.selected_template === v.id ? "border-amber-400 bg-amber-50/50" : "border-slate-100 bg-white hover:bg-slate-50"
                              )}
                            >
                              <v.icon size={16} className={profile.selected_template === v.id ? "text-amber-600" : "text-slate-400"} />
                              <span className="text-xs font-bold text-slate-900">{v.name}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* COLONNE PRÉVISUALISATION LIVE */}
                  <div className="xl:col-span-2 space-y-6">
                    <label className={labelClass}>Aperçu Elite en Direct</label>
                    <div className="bg-slate-900 rounded-[2.5rem] p-4 shadow-2xl relative overflow-hidden h-[600px] border-[8px] border-slate-800">
                      
                      {/* MINI INTERFACE SIMULÉE */}
                      <div className={cn(
                        "w-full h-full rounded-[1.5rem] overflow-hidden flex flex-col relative transition-elite",
                        profile.selected_theme === 'dark' ? "bg-black" : 
                        profile.selected_theme === 'prestige' ? "bg-slate-900" :
                        profile.selected_theme === 'emerald' ? "bg-emerald-50" :
                        profile.selected_theme === 'rose' ? "bg-rose-50" : "bg-medical-pearl"
                      )}>
                        {/* Sidebar simulée */}
                        <div className={cn(
                          "absolute left-0 top-0 bottom-0 w-12 border-r flex flex-col items-center py-4 gap-4 transition-elite",
                          profile.selected_theme === 'dark' || profile.selected_theme === 'prestige' 
                            ? "bg-slate-900/50 border-slate-800" 
                            : "bg-white/80 border-slate-100"
                        )}>
                          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${profile.primary_color}22`, color: profile.primary_color }}>
                            <Building size={14}/>
                          </div>
                          <div className={cn("w-6 h-6 rounded-md", profile.selected_theme === 'dark' || profile.selected_theme === 'prestige' ? "bg-slate-800" : "bg-slate-50")} />
                          <div className={cn("w-6 h-6 rounded-md", profile.selected_theme === 'dark' || profile.selected_theme === 'prestige' ? "bg-slate-800" : "bg-slate-50")} />
                          <div className="w-6 h-6 rounded-md" style={{ backgroundColor: `${profile.primary_color}44` }} />
                        </div>
                        
                        {/* Header simulé */}
                        <div className={cn(
                          "ml-12 h-10 border-b flex items-center px-4 justify-between transition-elite",
                          profile.selected_theme === 'dark' || profile.selected_theme === 'prestige'
                            ? "bg-slate-900/40 border-slate-800"
                            : "bg-white/40 border-slate-100"
                        )}>
                          <div className={cn("w-20 h-2 rounded-full", profile.selected_theme === 'dark' || profile.selected_theme === 'prestige' ? "bg-slate-800" : "bg-slate-100")} />
                          <div className="w-4 h-4 rounded-full" style={{ backgroundColor: `${profile.primary_color}33` }} />
                        </div>

                        {/* Contenu simulé */}
                        <div className="ml-12 p-4 space-y-4">
                          <div className="space-y-2">
                            <div className="w-24 h-4 rounded-full mb-4" style={{ backgroundColor: `${profile.primary_color}22` }} />
                            <div className="grid grid-cols-2 gap-2">
                              <div className="h-16 rounded-xl shadow-sm p-2 flex flex-col justify-end" style={{ backgroundColor: profile.primary_color }}>
                                <div className="w-8 h-1 bg-white/40 rounded-full" />
                              </div>
                              <div className={cn(
                                "h-16 rounded-xl border shadow-sm",
                                profile.selected_theme === 'dark' || profile.selected_theme === 'prestige'
                                  ? "bg-slate-800 border-slate-700"
                                  : "bg-white border-slate-200"
                              )} />
                            </div>
                          </div>

                          <div className={cn(
                            "p-4 rounded-elite bg-white/60 backdrop-blur-sm border border-white/20 transition-elite",
                            profile.selected_theme === 'dark' || profile.selected_theme === 'prestige' 
                              ? "bg-slate-900/60 border-slate-800/40" 
                              : "bg-white/60 border-white/20"
                          )}>
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full flex items-center justify-center text-white" style={{ backgroundColor: profile.primary_color }}>
                                <Activity size={14} />
                              </div>
                              <div className="flex-1 space-y-2">
                                <div className={cn("h-2 w-full rounded-full", profile.selected_theme === 'dark' || profile.selected_theme === 'prestige' ? "bg-slate-700" : "bg-slate-200")} />
                                <div className={cn("h-2 w-2/3 rounded-full", profile.selected_theme === 'dark' || profile.selected_theme === 'prestige' ? "bg-slate-700" : "bg-slate-200")} />
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Overlay Thème */}
                        <div 
                          className="absolute inset-0 pointer-events-none transition-all duration-500 mix-blend-multiply opacity-10"
                          style={{ 
                            backgroundColor: profile.selected_theme === 'emerald' ? '#10b981' : 
                                             profile.selected_theme === 'rose' ? '#f43f5e' : 
                                             profile.selected_theme === 'prestige' ? '#0f172a' : 'transparent'
                          }}
                        />
                      </div>

                      <div className="absolute bottom-10 left-1/2 -translate-x-1/2 bg-white/90 backdrop-blur-md px-6 py-2 rounded-full border border-slate-200 shadow-xl">
                        <span className="text-[10px] font-black uppercase tracking-widest text-slate-800">Rendu Elite Temps Réel</span>
                      </div>
                    </div>
                    <p className="text-[10px] text-slate-400 italic text-center px-6">L'aperçu simule la disposition globale de votre tableau de bord avec les couleurs choisies.</p>
                  </div>
                </div>

                {/* ══════════════════════════════════════════════ */}
                {/* LIGNE 2 — AMBIANCE APPLICATION                 */}
                {/* ══════════════════════════════════════════════ */}
                <div className="rounded-[2.5rem] border-2 overflow-hidden" style={{ borderColor: 'color-mix(in srgb, var(--primary) 13%, transparent)' }}>
                  <div className="px-8 py-5 border-b flex items-center gap-4" style={{ backgroundColor: 'color-mix(in srgb, var(--primary) 5%, transparent)', borderColor: 'color-mix(in srgb, var(--primary) 10%, transparent)' }}>
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: 'color-mix(in srgb, var(--primary) 10%, transparent)', color: 'var(--primary)' }}>
                      <PaletteIcon size={20} />
                    </div>
                    <div>
                      <h3 className="text-base font-black" style={{ color: 'var(--text-main)' }}>Ambiance Application</h3>
                      <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">Thème · Mode sombre · Accent de l'interface</p>
                    </div>
                    <div className="ml-auto px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest" style={{ backgroundColor: 'color-mix(in srgb, var(--primary) 10%, transparent)', color: 'var(--primary)' }}>Interface uniquement</div>
                  </div>

                  <div className="p-8 space-y-8" style={{ backgroundColor: 'var(--card-bg)' }}>
                    {/* GRILLE DES THÈMES */}
                    <div className="space-y-4">
                      <label className={labelClass}>Preset de thème</label>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {APP_THEMES.map(t => (
                          <button
                            key={t.id}
                            onClick={() => setProfile({ ...profile, selected_theme: t.id, app_accent_color: profile.app_accent_color || t.defaultAccent })}
                            className={cn(
                              "relative rounded-2xl border-2 overflow-hidden transition-all group text-left",
                              profile.selected_theme === t.id ? "shadow-lg scale-[1.02]" : "border-slate-200 hover:border-slate-300"
                            )}
                            style={profile.selected_theme === t.id ? { borderColor: 'var(--primary)' } : {}}
                          >
                            {/* PREVIEW MINI */}
                            <div className="h-16 relative" style={{ backgroundColor: t.preview.bg }}>
                              <div className="absolute bottom-2 left-2 right-2 h-5 rounded-md" style={{ backgroundColor: t.preview.card, border: `1px solid ${t.preview.border}` }} />
                              <div className="absolute top-2 right-2 w-6 h-6 rounded-full" style={{ backgroundColor: t.preview.accent }} />
                            </div>
                            {/* LABEL */}
                            <div className="px-3 py-2.5" style={{ backgroundColor: t.preview.card, borderTop: `1px solid ${t.preview.border}` }}>
                              <span className="block text-[10px] font-black uppercase tracking-tight" style={{ color: t.preview.text }}>{t.name}</span>
                              <span className="text-[9px] font-medium opacity-60" style={{ color: t.preview.text }}>{t.desc}</span>
                            </div>
                            {profile.selected_theme === t.id && (
                              <div className="absolute top-2 left-2 w-5 h-5 rounded-full flex items-center justify-center shadow-lg" style={{ backgroundColor: 'var(--primary)' }}>
                                <CheckCircle2 size={12} className="text-white" />
                              </div>
                            )}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* ACCENT OVERRIDE */}
                    <div className="p-6 rounded-2xl border flex flex-col sm:flex-row items-start sm:items-center gap-6" style={{ backgroundColor: 'var(--input-bg)', borderColor: 'var(--border-color)' }}>
                      <div className="flex-1">
                        <h4 className="text-sm font-black" style={{ color: 'var(--text-main)' }}>Couleur d'accent de l'interface</h4>
                        <p className="text-[10px] mt-1 font-medium" style={{ color: 'var(--text-muted)' }}>Personnalisez la couleur principale de l'interface pour ce thème.</p>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="flex flex-col items-center gap-2">
                          <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Accent UI</span>
                          <input
                            type="color"
                            value={profile.app_accent_color || APP_THEMES.find(t => t.id === profile.selected_theme)?.defaultAccent || '#003380'}
                            onChange={(e) => setProfile({ ...profile, app_accent_color: e.target.value })}
                            className="w-12 h-12 rounded-xl cursor-pointer border-2 border-white shadow-md bg-transparent"
                          />
                        </div>
                        <button
                          onClick={() => setProfile({ ...profile, app_accent_color: APP_THEMES.find(t => t.id === profile.selected_theme)?.defaultAccent || '#003380' })}
                          className="px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest border border-slate-200 bg-white hover:bg-slate-50 transition-all text-slate-500"
                        >
                          Réinitialiser
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3 : OPTIMISATION & SYSTÈME */}
            {activeTab === 'ia' && (
              <div className="space-y-8 animate-in slide-in-from-right-4 duration-500">
                <div className="mb-8 pb-6 border-b border-slate-100">
                  <h3 className="text-2xl font-black flex items-center gap-3"><Brain style={{ color: 'var(--primary)' }} /> Intelligence & Système</h3>
                  <p className="text-slate-500 text-sm font-medium mt-2">Configurez les paramètres de performance et l'intelligence globale du système.</p>
                </div>

                <div className="space-y-8">
                  <div className="bg-slate-50 p-8 rounded-3xl border border-slate-200 flex items-center justify-between gap-8">
                    <div className="flex-1">
                      <h4 className="font-black text-slate-800">Mode Performance (PC Modestes)</h4>
                      <p className="text-sm text-slate-500 mt-1 font-medium">Désactive les effets visuels complexes et les animations lourdes pour garantir une fluidité maximale sur les processeurs plus anciens.</p>
                    </div>
                    <button 
                      onClick={togglePerformanceMode}
                      className={cn(
                        "w-14 h-7 rounded-full transition-all relative flex items-center px-1",
                        performanceMode ? "bg-primary" : "bg-slate-300"
                      )}
                      style={{ backgroundColor: performanceMode ? 'var(--primary)' : undefined }}
                    >
                      <div className={cn(
                        "w-5 h-5 bg-white rounded-full shadow-lg transition-all",
                        performanceMode ? "translate-x-7" : "translate-x-0"
                      )} />
                    </button>
                  </div>
                  {performanceMode && (
                    <div className="mt-4 p-4 bg-primary/5 rounded-2xl border border-primary/10 flex items-center gap-3">
                      <CheckCircle2 size={16} style={{ color: 'var(--primary)' }} />
                      <span className="text-xs font-bold" style={{ color: 'var(--primary)' }}>Mode Performance activé : L'interface est optimisée pour votre matériel.</span>
                    </div>
                  )}

                  <div className="bg-slate-50 p-8 rounded-3xl border border-slate-200 flex items-center justify-between gap-8">
                    <div className="flex-1">
                      <h4 className="font-black text-slate-800">Conseils Cliniques (Tips)</h4>
                      <p className="text-sm text-slate-500 mt-1 font-medium">Affiche des conseils et des faits scientifiques durant les temps d'attente ou l'analyse.</p>
                    </div>
                    <button 
                      onClick={toggleClinicalTips}
                      className={cn(
                        "w-14 h-7 rounded-full transition-all relative flex items-center px-1",
                        clinicalTipsEnabled ? "bg-emerald-500" : "bg-slate-300"
                      )}
                    >
                      <div className={cn(
                        "w-5 h-5 bg-white rounded-full shadow-lg transition-all",
                        clinicalTipsEnabled ? "translate-x-7" : "translate-x-0"
                      )} />
                    </button>
                  </div>

                  <div className="bg-slate-50 p-8 rounded-3xl border border-slate-200 flex items-center justify-between gap-8">
                    <div className="flex-1">
                      <h4 className="font-black text-slate-800">Badges de Fiabilité Patient</h4>
                      <p className="text-sm text-slate-500 mt-1 font-medium">Affiche les badges Platinum/Gold/Silver/Bronze sur les dossiers patients pour une évaluation rapide de la fiabilité.</p>
                    </div>
                    <button 
                      onClick={() => {
                        const newVal = !profile.show_patient_badges;
                        setProfile(p => ({ ...p, show_patient_badges: newVal }));
                        localStorage.setItem('show_patient_badges', String(newVal));
                        window.dispatchEvent(new Event('patient-badges-changed'));
                      }}
                      className={cn(
                        "w-14 h-7 rounded-full transition-all relative flex items-center px-1",
                        profile.show_patient_badges ? "bg-indigo-600" : "bg-slate-300"
                      )}
                    >
                      <div className={cn(
                        "w-5 h-5 bg-white rounded-full shadow-lg transition-all",
                        profile.show_patient_badges ? "translate-x-7" : "translate-x-0"
                      )} />
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 4 : SÉCURITÉ */}
            {activeTab === 'securite' && (
              <div className="space-y-8 animate-in slide-in-from-right-4 duration-500">
                <div className="mb-8 pb-6 border-b border-slate-100">
                  <h3 className="text-2xl font-black flex items-center gap-3"><Shield style={{ color: 'var(--primary)' }} /> Sécurité & Base de Données</h3>
                  <p className="text-slate-500 text-sm font-medium mt-2">Digital Crown garantit la souveraineté de vos données cliniques (SQLite Locale).</p>
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded-2xl p-8 flex flex-col items-center justify-center text-center gap-4">
                  <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center shadow-sm text-slate-700">
                    <Database size={32} />
                  </div>
                  <div>
                    <h4 className="font-black text-lg text-slate-800">Sauvegarde Complète (Backup)</h4>
                    <p className="text-sm text-slate-500 max-w-md mx-auto mt-2">Exportez l'intégralité de la base de données patients, radios et analyses dans un format sécurisé.</p>
                  </div>
                  <button 
                    onClick={handleExportDB}
                    className="mt-4 px-8 py-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-black transition-all shadow-xl shadow-emerald-600/20 flex items-center gap-3"
                  >
                    <Download size={20} /> Exporter la Base de Données
                  </button>
                </div>
              </div>
            )}

            {/* TAB 5 : MON ÉQUIPE */}
            {activeTab === 'equipe' && (
              <div className="animate-in slide-in-from-right-4 duration-500">
                <TeamManager />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;