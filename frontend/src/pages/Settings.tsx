import React, { useState, useEffect } from 'react';
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
  MessageCircle
} from 'lucide-react';
import { api } from '../services/api';
import { cn } from '../utils/cn';

type Tab = 'profil' | 'ia' | 'securite';

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
  contacts_json?: any;
}

interface ClinicalNorms {
  sna: number;
  snb: number;
  anb: number;
  impa: number;
  fma: number;
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
    watermark_enabled: true
  });
  const [contacts, setContacts] = useState<any>({
    fixe: { enabled: true, value: '' },
    mobile: { enabled: false, value: '' },
    whatsapp: { enabled: false, value: '' },
    instagram: { enabled: false, value: '' }
  });
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // États Tab 2 : IA & Normes (LocalStorage)
  const defaultNorms: ClinicalNorms = { sna: 82, snb: 80, anb: 2, impa: 90, fma: 26 };
  const [norms, setNorms] = useState<ClinicalNorms>(() => {
    const saved = localStorage.getItem('clinical_norms');
    return saved ? JSON.parse(saved) : defaultNorms;
  });

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
            letterhead_path: res.data.letterhead_path || undefined
          });

          if (res.data.contacts_json && Object.keys(res.data.contacts_json).length > 0) {
            setContacts(res.data.contacts_json);
          } else if (res.data.footer_phones) {
            setContacts((prev: any) => ({
                ...prev,
                fixe: { enabled: true, value: res.data.footer_phones }
            }));
          }
        }
      } catch (err) {
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
      const payload = {
        ...profile,
        footer_phones: contactString,
        contacts_json: contacts
      };
      await api.put('/clinics/me', payload);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error("Erreur sauvegarde profil:", err);
    } finally {
      setSavingProfile(false);
    }
  };

  const toggleContact = (type: string) => {
    setContacts((prev: any) => ({
      ...prev,
      [type]: { ...prev[type], enabled: !prev[type].enabled }
    }));
  };

  const updateContactValue = (type: string, val: string) => {
    setContacts((prev: any) => ({
      ...prev,
      [type]: { ...prev[type], value: val }
    }));
  };

  const handleNormChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newNorms = { ...norms, [e.target.name]: Number(e.target.value) };
    setNorms(newNorms);
    localStorage.setItem('clinical_norms', JSON.stringify(newNorms));
  };

  const togglePerformanceMode = () => {
    const newVal = !performanceMode;
    setPerformanceMode(newVal);
    localStorage.setItem('performance_mode', String(newVal));
  };

  const handleExportDB = () => {
    window.open('http://127.0.0.1:8000/api/admin/export-db', '_blank');
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
        <div className="w-full md:w-64 shrink-0 flex flex-col gap-2 bg-white/80 backdrop-blur-xl border border-slate-200/60 p-3 rounded-[2rem] shadow-sm sticky top-28">
          <TabButton active={activeTab === 'profil'} onClick={() => setActiveTab('profil')} icon={<Building size={20}/>} label="Profil Cabinet" />
          <TabButton active={activeTab === 'ia'} onClick={() => setActiveTab('ia')} icon={<Brain size={20}/>} label="IA & Normes" />
          <TabButton active={activeTab === 'securite'} onClick={() => setActiveTab('securite')} icon={<Shield size={20}/>} label="Sécurité & Data" />
        </div>

        {/* CONTENU DES ONGLETS */}
        <div className="flex-1 bg-white/80 backdrop-blur-xl border border-slate-200/60 shadow-[0_8px_40px_rgba(0,0,0,0.04)] rounded-[2.5rem] p-10 min-h-[500px]">
          
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
                      style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)', borderColor: 'rgba(var(--primary-rgb), 0.2)' } as any}
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className={labelClass}>Adresse complète</label>
                    <input type="text" name="adresse" value={profile.adresse} onChange={handleProfileChange} className={inputClass} style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)' } as any} />
                  </div>
                  <div>
                    <label className={labelClass}>Téléphone</label>
                    <input type="text" name="telephone" value={profile.telephone} onChange={handleProfileChange} className={inputClass} style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)' } as any} />
                  </div>
                  <div>
                    <label className={labelClass}>Numéro INPE</label>
                    <input type="text" name="inpe" value={profile.inpe} onChange={handleProfileChange} className={inputClass} style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)' } as any} />
                  </div>
                  <div>
                    <label className={labelClass}>Identifiant Commun Entreprise (ICE)</label>
                    <input type="text" name="ice" value={profile.ice} onChange={handleProfileChange} className={inputClass} placeholder="Ex: 001234..." style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)' } as any} />
                  </div>
                  <div>
                    <label className={labelClass}>Identifiant Fiscal (IF)</label>
                    <input type="text" name="if" value={profile.if} onChange={handleProfileChange} className={inputClass} placeholder="Ex: 56789..." style={{ '--tw-ring-color': 'rgba(var(--primary-rgb), 0.1)' } as any} />
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
                              style={{ borderColor: c.enabled ? 'var(--primary)' : undefined } as any}
                            />
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="md:col-span-2 mt-6 flex justify-end">
                    <button 
                      onClick={saveProfile} 
                      disabled={savingProfile}
                      className="px-8 py-4 text-white rounded-xl font-black transition-all shadow-xl flex items-center gap-3 disabled:opacity-70"
                      style={{ backgroundColor: 'var(--primary)', boxShadow: '0 10px 30px -10px var(--primary)' }}
                    >
                      {savingProfile ? <Loader2 className="animate-spin" size={20}/> : (saveSuccess ? <CheckCircle2 size={20} className="text-emerald-400"/> : <Save size={20} />)}
                      {saveSuccess ? "Sauvegardé !" : "Sauvegarder les modifications"}
                    </button>
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
                                 src={profile.letterhead_path.startsWith('http') ? profile.letterhead_path : `http://localhost:8000/static/uploads/${profile.letterhead_path}`} 
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

          {/* TAB 2 : IA & NORMES */}
          {activeTab === 'ia' && (
            <div className="space-y-8 animate-in slide-in-from-right-4 duration-500">
              <div className="mb-8 pb-6 border-b border-slate-100">
                <h3 className="text-2xl font-black flex items-center gap-3"><Brain style={{ color: 'var(--primary)' }} /> Normes Céphalométriques</h3>
                <p className="text-slate-500 text-sm font-medium mt-2">Définissez vos standards cliniques pour l'analyse IA. Les alertes du tableau de bord se baseront sur ces valeurs.</p>
              </div>

              <div className="space-y-8 max-w-2xl">
                <NormSlider label="Angle SNA (°)" name="sna" value={norms.sna} min={70} max={95} onChange={handleNormChange} norm="82°" />
                <NormSlider label="Angle SNB (°)" name="snb" value={norms.snb} min={70} max={95} onChange={handleNormChange} norm="80°" />
                <NormSlider label="Angle ANB (°)" name="anb" value={norms.anb} min={-5} max={10} onChange={handleNormChange} norm="2°" />
                <NormSlider label="I / Mandibulaire - IMPA (°)" name="impa" value={norms.impa} min={70} max={110} onChange={handleNormChange} norm="90°" />
                <NormSlider label="Angle de Tweed - FMA (°)" name="fma" value={norms.fma} min={15} max={40} onChange={handleNormChange} norm="26°" />
              </div>

              <div className="mt-12 pt-8 border-t border-slate-100">
                <h3 className="text-xl font-black flex items-center gap-3 mb-6" style={{ color: 'var(--primary)' }}>Optimisation du Système</h3>
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

const NormSlider = ({ label, name, value, min, max, onChange, norm }: any) => (
  <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100">
    <div className="flex justify-between items-center mb-4">
      <label className="font-black text-slate-700">{label}</label>
      <div className="flex items-center gap-3">
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Standard : {norm}</span>
        <span className="text-xl font-black bg-white px-3 py-1 rounded-lg shadow-sm border border-slate-200 w-16 text-center" style={{ color: 'var(--primary)' }}>{value}</span>
      </div>
    </div>
    <input 
      type="range" 
      name={name}
      min={min} 
      max={max} 
      value={value} 
      onChange={onChange}
      className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
      style={{ accentColor: 'var(--primary)' }}
    />
  </div>
);