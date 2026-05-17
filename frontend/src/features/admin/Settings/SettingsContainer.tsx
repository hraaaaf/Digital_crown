import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon,
  UserCircle,
  Palette,
  Brain,
  Shield,
  Users,
  Save,
  Loader2,
  CheckCircle2
} from 'lucide-react';
import { useSettingsStore } from './hooks/useSettingsStore';
import { TabButton } from './components/SharedUI';
import { ProfileTab } from './tabs/ProfileTab';
import { BrandingTab } from './tabs/BrandingTab';
import { IATab } from './tabs/IATab';
import { SecurityTab } from './tabs/SecurityTab';
import { TeamManager } from '../TeamManager';
import { cn } from '../../../utils/cn';
import type { Tab } from './types';

const SettingsContainer: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('profil');
  const { fetchProfile, saveProfile, loading, saving, saveSuccess } = useSettingsStore();

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[600px] gap-4">
        <Loader2 className="animate-spin text-primary" size={48} />
        <p className="text-sm font-black text-slate-400 uppercase tracking-widest animate-pulse">Initialisation du Centre de Contrôle...</p>
      </div>
    );
  }

  const tabs = [
    { id: 'profil', label: 'Profil Cabinet', icon: <UserCircle size={20} /> },
    { id: 'branding', label: 'Design & Ambiance', icon: <Palette size={20} /> },
    { id: 'ia', label: 'IA & Système', icon: <Brain size={20} /> },
    { id: 'securite', label: 'Sécurité & Backup', icon: <Shield size={20} /> },
    { id: 'equipe', label: 'Mon Équipe', icon: <Users size={20} /> },
  ];

  return (
    <div className="max-w-[1600px] mx-auto px-4 sm:px-8 py-8 animate-in fade-in duration-700">
      <div className="flex flex-col lg:flex-row gap-12 items-start">
        
        {/* SIDEBAR DE NAVIGATION */}
        <div className="w-full lg:w-80 space-y-8 sticky top-24">
          <div className="flex items-center gap-4 mb-10">
            <div className="w-14 h-14 bg-primary text-white rounded-[1.25rem] flex items-center justify-center shadow-2xl shadow-primary/30">
              <SettingsIcon size={28} />
            </div>
            <div>
              <h1 className="text-2xl font-black text-slate-900 tracking-tight">Paramètres</h1>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mt-1">Ghost Elite Studio</p>
            </div>
          </div>

          <nav className="space-y-2 bg-white/50 backdrop-blur-md p-3 rounded-[2rem] border border-slate-100 shadow-sm">
            {tabs.map(t => (
              <TabButton 
                key={t.id}
                active={activeTab === t.id}
                onClick={() => setActiveTab(t.id as Tab)}
                icon={t.icon}
                label={t.label}
              />
            ))}
          </nav>

          {/* BOUTON SAUVEGARDE GLOBAL */}
          <div className="pt-6">
            <button
              onClick={saveProfile}
              disabled={saving}
              className={cn(
                "w-full py-5 rounded-[1.5rem] font-black text-base transition-all duration-500 shadow-2xl flex items-center justify-center gap-4",
                saveSuccess 
                  ? "bg-emerald-500 text-white shadow-emerald-500/30" 
                  : "bg-slate-900 text-white hover:bg-black shadow-slate-900/20"
              )}
            >
              {saving ? (
                <>
                  <Loader2 className="animate-spin" size={24} />
                  <span>Synchronisation...</span>
                </>
              ) : saveSuccess ? (
                <>
                  <CheckCircle2 size={24} />
                  <span>Config. Sauvegardée !</span>
                </>
              ) : (
                <>
                  <Save size={24} />
                  <span>Mettre à jour le Profil</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* CONTENU DES ONGLETS */}
        <div className="flex-1 w-full bg-white rounded-[3rem] border border-slate-100 shadow-2xl shadow-slate-200/50 min-h-[800px] relative">
          <div className="p-8 sm:p-12">
             {activeTab === 'profil' && <ProfileTab />}
             {activeTab === 'branding' && <BrandingTab />}
             {activeTab === 'ia' && <IATab />}
             {activeTab === 'securite' && <SecurityTab />}
             {activeTab === 'equipe' && <TeamManager />}
          </div>
          
          {/* Filigrane discret */}
          <div className="absolute bottom-8 right-12 opacity-[0.03] pointer-events-none select-none">
            <SettingsIcon size={200} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsContainer;
