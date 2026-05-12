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
  MapPin
} from 'lucide-react';
import { api } from '../services/api';
import { cn } from '../utils/cn';
import { TeamManager } from '../features/admin/TeamManager';
import { BRAND_IDENTITIES } from '../features/admin/constants';
import { Palette as PaletteIcon, Moon, Sun, Leaf, Heart } from 'lucide-react';

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
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  qr_code_enabled?: boolean;
  qr_code_type?: 'VCARD' | 'WEBSITE' | 'INSTAGRAM' | 'WHATSAPP' | 'LOCATION' | 'VALIDATION' | 'PAYMENT';
  qr_code_value?: string;
  qr_code_color?: string;
  qr_code_label?: string;
}



export const Settings = () => {
  const [activeTab, setActiveTab] = useState<Tab>('profil');
  
  // États Tab 1 : Profil
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
    qr_code_label: ''
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

  // États Tab 2 : IA & Système (LocalStorage)
  const [performanceMode, setPerformanceMode] = useState<boolean>(() => {
    return localStorage.getItem('performance_mode') === 'true';
  });

  // --- EFFET : Chargement Profil ---
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await api.get('/clinics/me');
        if (res.data) {
          // Mapping des noms de champs backend -> frontend avec repli sur chaîne vide
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
            primary_color: res.data.primary_color || '#003380',
            secondary_color: res.data.secondary_color || '#1e40af',
            accent_color: res.data.accent_color || '#60a5fa',
            qr_code_enabled: res.data.qr_code_enabled ?? false,
            qr_code_type: res.data.qr_code_type || 'VCARD',
            qr_code_value: res.data.qr_code_value || '',
            qr_code_color: res.data.qr_code_color || '',
            qr_code_label: res.data.qr_code_label || ''
          });

          // Appliquer le thème immédiatement (Standardisation sur body)
          const themeValue = res.data.selected_theme === 'elite' ? '' : res.data.selected_theme;
          document.body.dataset.theme = themeValue;
          if (res.data.primary_color) document.documentElement.style.setProperty('--primary', res.data.primary_color);
          if (res.data.secondary_color) document.documentElement.style.setProperty('--secondary', res.data.secondary_color);
          if (res.data.accent_color) document.documentElement.style.setProperty('--accent', res.data.accent_color);

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

  // --- EFFET : Live Preview Design ---
  useEffect(() => {
    if (loadingProfile) return;
    
    const themeValue = profile.selected_theme === 'elite' ? '' : profile.selected_theme;
    document.body.dataset.theme = themeValue;
    
    if (profile.primary_color) document.documentElement.style.setProperty('--primary', profile.primary_color);
    if (profile.secondary_color) document.documentElement.style.setProperty('--secondary', profile.secondary_color);
    if (profile.accent_color) document.documentElement.style.setProperty('--accent', profile.accent_color);
  }, [profile.selected_theme, profile.primary_color, profile.secondary_color, profile.accent_color, loadingProfile]);

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

  // --- HANDLERS ---
  const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setProfile({ ...profile, [e.target.name]: e.target.value });
  };

  const saveProfile = async () => {
    setSavingProfile(true);
    setSaveSuccess(false);

    // Construction de la string des contacts
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
        footer_phones: contactString,
        contacts_json: contacts
      };

      // Prevent Pydantic validation errors (422) on empty strings for optional fields
      if (!payload.qr_code_color) payload.qr_code_color = null;
      if (!payload.qr_code_value) payload.qr_code_value = null;
      if (!payload.qr_code_label) payload.qr_code_label = null;

      await api.put('/clinics/me', payload);
      
      // Appliquer le thème immédiatement après sauvegarde (Standardisation sur body)
      const themeValue = profile.selected_theme === 'elite' ? '' : profile.selected_theme;
      document.body.dataset.theme = themeValue;
      if (profile.primary_color) document.documentElement.style.setProperty('--primary', profile.primary_color);
      if (profile.secondary_color) document.documentElement.style.setProperty('--secondary', profile.secondary_color);
      if (profile.accent_color) document.documentElement.style.setProperty('--accent', profile.accent_color);
      
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

  const handleExportDB = () => {
    window.open(`${API_BASE}/api/admin/export-db`, '_blank');
  };

  // --- UI CLASSES ---
  const inputClass = "w-full px-5 py-4 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-4 transition-all duration-300 font-bold text-slate-800";
  const labelClass = "text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1";

  return (
    <div className="max-w-[1200px] mx-auto w-full px-6 py-8 md:p-10 animate-in fade-in duration-700">
      
      <div className="mb-10">
        <h2 className="text-4xl font-black tracking-tight" style={{ color: 'var(--primary)' }}>Centre de Contrôle</h2>
        <p className="text-slate-500 font-medium mt-2 text-lg">Configuration globale de l'environnement Digital Crown.</p>
      </div>

      <div className="flex flex-col md:flex-row gap-10 items-start">
        
        {/* NAVIGATION DES ONGLETS (Verticale) */}
        <div data-tour="settings-navigation" className="w-full md:w-64 shrink-0 flex flex-col gap-2 bg-white/80 backdrop-blur-xl border border-slate-200/60 p-3 rounded-[2rem] shadow-sm sticky top-28">
          <TabButton active={activeTab === 'profil'} onClick={() => setActiveTab('profil')} icon={<Building size={20}/>} label="Profil Cabinet" />
          <TabButton active={activeTab === 'branding'} onClick={() => setActiveTab('branding')} icon={<PaletteIcon size={20}/>} label="Design & Ambiance" />
          <TabButton active={activeTab === 'equipe'} onClick={() => setActiveTab('equipe')} icon={<Users size={20}/>} label="Mon Équipe" />
          <TabButton active={activeTab === 'ia'} onClick={() => setActiveTab('ia')} icon={<Brain size={20}/>} label="Optimisation" />
          <TabButton active={activeTab === 'securite'} onClick={() => setActiveTab('securite')} icon={<Shield size={20}/>} label="Sécurité & Data" />
        </div>

        {/* CONTENU DES ONGLETS */}
        <div className="flex-1 bg-white/80 backdrop-blur-xl border border-slate-200/60 shadow-[0_8px_40px_rgba(0,0,0,0.04)] rounded-[2.5rem] overflow-hidden flex flex-col min-h-[600px]">
          
          {/* HEADER D'ACTION COLLANT (Elite v4.9) */}
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
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="md:col-span-2">
                    <label className={labelClass}>Nom du Cabinet / Praticien</label>
                    <input 
                      type="text" 
                      name="nom" 
                      value={profile.nom} 
                      onChange={handleProfileChange} 
                      className={inputClass} 
                      placeholder="Ex: Dr. Benmoussa" 
                      style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)', borderColor: 'rgba(var(--primary-rgb), 0.2)' } as React.CSSProperties}
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className={labelClass}>Adresse complète</label>
                    <input type="text" name="adresse" value={profile.adresse} onChange={handleProfileChange} className={inputClass} style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)' } as React.CSSProperties} />
                  </div>
                  <div>
                    <label className={labelClass}>Téléphone</label>
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
                    <label className={labelClass}>Identifiant Commun Entreprise (ICE)</label>
                    <input type="text" name="ice" value={profile.ice} onChange={handleProfileChange} className={inputClass} placeholder="Ex: 001234..." style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)' } as React.CSSProperties} />
                  </div>
                  <div>
                    <label className={labelClass}>Identifiant Fiscal (IF)</label>
                    <input type="text" name="if" value={profile.if} onChange={handleProfileChange} className={inputClass} placeholder="Ex: 56789..." style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)' } as React.CSSProperties} />
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

                         <div className="p-4 bg-primary/5 rounded-2xl border border-primary/10">
                            <p className="text-[10px] font-medium leading-relaxed" style={{ color: 'var(--primary)' }}>
                               <b>Note :</b> La marge haute correspond généralement à la hauteur de votre en-tête physique. La marge basse protège votre pied de page pré-imprimé.
                            </p>
                         </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 2 : DESIGN & AMBIANCE */}
          {activeTab === 'branding' && (
            <div data-tour="settings-branding" className="space-y-12 animate-in slide-in-from-right-4 duration-500">
              <div className="flex items-center gap-4 mb-8 pb-6 border-b border-slate-100">
                <div className="w-16 h-16 bg-primary/5 rounded-2xl flex items-center justify-center shadow-inner border border-primary/10" style={{ color: 'var(--primary)' }}>
                  <PaletteIcon size={32} />
                </div>
                <div>
                  <h3 className="text-2xl font-black" style={{ color: 'var(--primary)' }}>Design & Ambiance</h3>
                  <p className="text-slate-500 text-sm font-medium mt-1">Personnalisez l'atmosphère de votre logiciel et de vos documents.</p>
                </div>
              </div>

              {/* 1. SÉLECTION DU THÈME (AMBIANCE) */}
              <div className="space-y-6">
                <label className={labelClass}>Thème du Logiciel (Ambiance)</label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { id: 'elite', name: 'Ghost Elite', icon: <Sun size={20} />, desc: 'Clair & Pur', color: 'bg-slate-100 text-slate-600' },
                    { id: 'emerald', name: 'Émeraude Zen', icon: <Leaf size={20} />, desc: 'Serein & Médical', color: 'bg-emerald-50 text-emerald-600' },
                    { id: 'rose', name: 'Rose Prestige', icon: <Heart size={20} />, desc: 'Luxe & Douceur', color: 'bg-rose-50 text-rose-600' },
                    { id: 'prestige', name: 'Nuit Intense', icon: <Moon size={20} />, desc: 'Sombre & Premium', color: 'bg-slate-900 text-slate-200' }
                  ].map(t => (
                    <button
                      key={t.id}
                      onClick={() => setProfile({ ...profile, selected_theme: t.id })}
                      className={cn(
                        "p-6 rounded-[2rem] border-2 transition-all flex flex-col items-center gap-3 text-center group",
                        profile.selected_theme === t.id 
                          ? "border-primary bg-primary/5 shadow-xl scale-[1.02]" 
                          : "border-slate-100 bg-white hover:border-slate-200"
                      )}
                    >
                      <div className={cn("w-12 h-12 rounded-2xl flex items-center justify-center shadow-sm group-hover:scale-110 transition-transform", t.color)}>
                        {t.icon}
                      </div>
                      <div>
                        <span className="block font-black text-sm text-slate-800">{t.name}</span>
                        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-tight">{t.desc}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* 2. IDENTITÉ VISUELLE (COULEURS) */}
              <div className="space-y-6 pt-10 border-t border-slate-100">
                <label className={labelClass}>Identité Visuelle (Couleurs Signature)</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {BRAND_IDENTITIES.map(id => (
                    <button
                      key={id.id}
                      onClick={() => setProfile({ 
                        ...profile, 
                        primary_color: id.primary, 
                        secondary_color: id.secondary, 
                        accent_color: id.accent 
                      })}
                      className={cn(
                        "p-5 rounded-3xl border-2 transition-all text-left flex flex-col gap-4 group relative overflow-hidden",
                        profile.primary_color === id.primary ? "border-primary bg-white shadow-lg scale-[1.02]" : "border-slate-100 bg-slate-50/50 hover:bg-white"
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

              {/* 3. COULEUR PERSONNALISÉE (DYNAMIQUE) */}
              <div className="p-8 bg-slate-50 rounded-[2.5rem] border border-slate-200/60 flex flex-col md:flex-row items-center gap-10">
                <div className="flex-1">
                  <h4 className="text-lg font-black text-slate-800">Ajustement Manuel</h4>
                  <p className="text-sm text-slate-500 mt-1 font-medium">Vous pouvez également choisir précisément vos teintes HEX pour une personnalisation totale.</p>
                </div>
                <div className="flex items-center gap-6">
                  <div className="flex flex-col items-center gap-2">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Primaire</span>
                    <input 
                      type="color" 
                      value={profile.primary_color} 
                      onChange={(e) => setProfile({ ...profile, primary_color: e.target.value })}
                      className="w-12 h-12 rounded-xl cursor-pointer border-2 border-white shadow-md bg-transparent"
                    />
                  </div>
                  <div className="flex flex-col items-center gap-2">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Accent</span>
                    <input 
                      type="color" 
                      value={profile.accent_color} 
                      onChange={(e) => setProfile({ ...profile, accent_color: e.target.value })}
                      className="w-12 h-12 rounded-xl cursor-pointer border-2 border-white shadow-md bg-transparent"
                    />
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
              </div>
            </div>
          )}

          {/* TAB 3 : SÉCURITÉ */}
          {activeTab === 'securite' && (
            <div className="space-y-8 animate-in slide-in-from-right-4 duration-500">
               <div className="mb-8 pb-6 border-b border-slate-100">
                <h3 className="text-2xl font-black flex items-center gap-3" style={{ color: 'var(--primary)' }}><Database className="text-emerald-500" /> Gestion des Données</h3>
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

          {/* TAB 4 : MON ÉQUIPE */}
          {activeTab === 'equipe' && (
            <TeamManager />
          )}

          </div>
        </div>
      </div>
    </div>
  );
};

// --- COMPOSANTS INTERNES ---

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