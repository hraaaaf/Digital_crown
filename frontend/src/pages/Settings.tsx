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
  CheckCircle2
} from 'lucide-react';
import { api } from '../services/api';
import { cn } from '../utils/cn';

type Tab = 'profil' | 'ia' | 'securite';

interface CabinetProfile {
  nom: string;
  adresse: string;
  telephone: string;
  inpe: string;
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
  const [profile, setProfile] = useState<CabinetProfile>({ nom: '', adresse: '', telephone: '', inpe: '' });
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // États Tab 2 : IA & Normes (LocalStorage)
  const defaultNorms: ClinicalNorms = { sna: 82, snb: 80, anb: 2, impa: 90, fma: 26 };
  const [norms, setNorms] = useState<ClinicalNorms>(() => {
    const saved = localStorage.getItem('clinical_norms');
    return saved ? JSON.parse(saved) : defaultNorms;
  });

  // --- EFFET : Chargement Profil ---
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await api.get('/cabinet/me');
        if (res.data) setProfile(res.data);
      } catch (err) {
        console.warn("Route /cabinet/me indisponible. Mock activé.");
        setProfile({
          nom: "Centre d'Orthodontie Moderne",
          adresse: "123 Avenue Hassan II, Casablanca",
          telephone: "05 22 33 44 55",
          inpe: "987654321"
        });
      } finally {
        setLoadingProfile(false);
      }
    };
    fetchProfile();
  }, []);

  // --- HANDLERS ---
  const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setProfile({ ...profile, [e.target.name]: e.target.value });
  };

  const saveProfile = async () => {
    setSavingProfile(true);
    setSaveSuccess(false);
    try {
      await api.put('/cabinet/me', profile);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.warn("Mock PUT /cabinet/me réussi");
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } finally {
      setSavingProfile(false);
    }
  };

  const handleNormChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newNorms = { ...norms, [e.target.name]: Number(e.target.value) };
    setNorms(newNorms);
    localStorage.setItem('clinical_norms', JSON.stringify(newNorms));
  };

  const handleExportDB = () => {
    // Déclenche le téléchargement via le navigateur de façon native
    window.open('http://127.0.0.1:8000/admin/export-db', '_blank');
  };

  // --- UI CLASSES ---
  const inputClass = "w-full px-5 py-4 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-4 focus:ring-[#003380]/10 focus:border-[#003380] transition-all duration-300 font-bold text-slate-800";
  const labelClass = "text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1";

  return (
    <div className="max-w-[1200px] mx-auto w-full px-6 py-8 md:p-10 animate-in fade-in duration-700">
      
      <div className="mb-10">
        <h2 className="text-4xl font-black text-[#003380] tracking-tight">Centre de Contrôle</h2>
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
                <div className="w-16 h-16 bg-blue-50 text-[#003380] rounded-2xl flex items-center justify-center shadow-inner border border-blue-100">
                  <UserCircle size={32} />
                </div>
                <div>
                  <h3 className="text-2xl font-black text-[#003380]">Identité Officielle</h3>
                  <p className="text-slate-500 text-sm font-medium mt-1">Ces informations apparaîtront sur vos bilans PDF.</p>
                </div>
              </div>

              {loadingProfile ? (
                <div className="flex justify-center py-20"><Loader2 className="animate-spin text-[#003380]" size={40} /></div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="md:col-span-2">
                    <label className={labelClass}>Nom du Cabinet / Praticien</label>
                    <input type="text" name="nom" value={profile.nom} onChange={handleProfileChange} className={inputClass} placeholder="Ex: Dr. Benmoussa" />
                  </div>
                  <div className="md:col-span-2">
                    <label className={labelClass}>Adresse complète</label>
                    <input type="text" name="adresse" value={profile.adresse} onChange={handleProfileChange} className={inputClass} />
                  </div>
                  <div>
                    <label className={labelClass}>Téléphone</label>
                    <input type="text" name="telephone" value={profile.telephone} onChange={handleProfileChange} className={inputClass} />
                  </div>
                  <div>
                    <label className={labelClass}>Numéro INPE</label>
                    <input type="text" name="inpe" value={profile.inpe} onChange={handleProfileChange} className={inputClass} />
                  </div>

                  <div className="md:col-span-2 mt-6 flex justify-end">
                    <button 
                      onClick={saveProfile} 
                      disabled={savingProfile}
                      className="px-8 py-4 bg-[#003380] hover:bg-blue-900 text-white rounded-xl font-black transition-all shadow-xl shadow-blue-900/20 flex items-center gap-3 disabled:opacity-70"
                    >
                      {savingProfile ? <Loader2 className="animate-spin" size={20}/> : (saveSuccess ? <CheckCircle2 size={20} className="text-emerald-400"/> : <Save size={20} />)}
                      {saveSuccess ? "Sauvegardé !" : "Sauvegarder les modifications"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 2 : IA & NORMES */}
          {activeTab === 'ia' && (
            <div className="space-y-8 animate-in slide-in-from-right-4 duration-500">
              <div className="mb-8 pb-6 border-b border-slate-100">
                <h3 className="text-2xl font-black text-[#003380] flex items-center gap-3"><Brain className="text-blue-500" /> Normes Céphalométriques</h3>
                <p className="text-slate-500 text-sm font-medium mt-2">Définissez vos standards cliniques pour l'analyse IA. Les alertes du tableau de bord se baseront sur ces valeurs.</p>
              </div>

              <div className="space-y-8 max-w-2xl">
                <NormSlider label="Angle SNA (°)" name="sna" value={norms.sna} min={70} max={95} onChange={handleNormChange} norm="82°" />
                <NormSlider label="Angle SNB (°)" name="snb" value={norms.snb} min={70} max={95} onChange={handleNormChange} norm="80°" />
                <NormSlider label="Angle ANB (°)" name="anb" value={norms.anb} min={-5} max={10} onChange={handleNormChange} norm="2°" />
                <NormSlider label="I / Mandibulaire - IMPA (°)" name="impa" value={norms.impa} min={70} max={110} onChange={handleNormChange} norm="90°" />
                <NormSlider label="Angle de Tweed - FMA (°)" name="fma" value={norms.fma} min={15} max={40} onChange={handleNormChange} norm="26°" />
              </div>
            </div>
          )}

          {/* TAB 3 : SÉCURITÉ */}
          {activeTab === 'securite' && (
            <div className="space-y-8 animate-in slide-in-from-right-4 duration-500">
               <div className="mb-8 pb-6 border-b border-slate-100">
                <h3 className="text-2xl font-black text-[#003380] flex items-center gap-3"><Database className="text-emerald-500" /> Gestion des Données</h3>
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
        ? "bg-[#003380] text-white shadow-lg shadow-blue-900/20 scale-[1.02]" 
        : "text-slate-500 hover:bg-slate-50 hover:text-[#003380]"
    )}
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
        <span className="text-xl font-black text-[#003380] bg-white px-3 py-1 rounded-lg shadow-sm border border-slate-200 w-16 text-center">{value}</span>
      </div>
    </div>
    <input 
      type="range" 
      name={name}
      min={min} 
      max={max} 
      value={value} 
      onChange={onChange}
      className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#003380]"
    />
  </div>
);