import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Settings as SettingsIcon,
  UserCircle,
  Palette,
  Brain,
  Shield,
  Users,
  Save,
  Loader2,
  CheckCircle2,
  BookOpen,
  Calendar
} from 'lucide-react';
import { useSettingsStore } from './hooks/useSettingsStore';
import { SettingsReadError, TabButton } from './components/SharedUI';
import { TeamReadTruthGate } from './components/TeamReadTruthGate';
import { ProfileTab } from './tabs/ProfileTab';
import { BrandingTab } from './tabs/BrandingTab';
import { IATab } from './tabs/IATab';
import { SecurityTab } from './tabs/SecurityTab';
import { CatalogTab } from './tabs/CatalogTab';
import { AgendaTab } from './tabs/AgendaTab';
import { cn } from '../../../utils/cn';
import type { Tab } from './types';
import { DigitalCrownLoader } from '../../../components/DigitalCrownLoader';
import { useAuthStore } from '../../../stores/useAuthStore';
import { getSettingsAccess } from '../../../utils/settingsAccess';
import { commitRuntimePreferences } from './runtimePreferences';
import { api } from '../../../services/api';

const profileBackedTabs: Tab[] = ['profil', 'branding', 'ia'];

const SettingsContainer: React.FC = () => {
  const user = useAuthStore((state) => state.user);
  const access = getSettingsAccess(user);
  const [profileReadError, setProfileReadError] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>(() => {
    if (access.canSettings) return 'profil';
    if (access.canAgenda) return 'agenda';
    return 'securite';
  });
  const { fetchProfile, saveProfile, loading, saving, saveSuccess, isDirty } = useSettingsStore();

  const tabs = useMemo(() => [
    ...(access.canSettings ? [
      { id: 'profil' as Tab, label: 'Profil Cabinet', icon: <UserCircle size={20} /> },
      { id: 'branding' as Tab, label: 'Design & Ambiance', icon: <Palette size={20} /> },
      { id: 'catalogue' as Tab, label: 'Catalogue Actes', icon: <BookOpen size={20} /> },
    ] : []),
    ...(access.canAgenda ? [
      { id: 'agenda' as Tab, label: 'Horaires & Agenda', icon: <Calendar size={20} /> },
    ] : []),
    ...(access.canSettings ? [
      { id: 'ia' as Tab, label: 'IA & Système', icon: <Brain size={20} /> },
    ] : []),
    ...(access.canAdmin ? [
      { id: 'securite' as Tab, label: 'Sécurité & Backup', icon: <Shield size={20} /> },
      { id: 'equipe' as Tab, label: 'Mon Équipe', icon: <Users size={20} /> },
    ] : []),
  ], [access.canAdmin, access.canAgenda, access.canSettings]);

  useEffect(() => {
    const interceptor = api.interceptors.response.use(
      (response) => response,
      (error) => {
        const url = error?.config?.url;
        const method = (error?.config?.method || 'get').toLowerCase();
        if (method === 'get' && url === '/clinics/me') {
          setProfileReadError(true);
        }
        return Promise.reject(error);
      },
    );
    return () => api.interceptors.response.eject(interceptor);
  }, []);

  const retryProfile = useCallback(async () => {
    setProfileReadError(false);
    await fetchProfile();
  }, [fetchProfile]);

  useEffect(() => {
    void retryProfile();
  }, [retryProfile]);

  useEffect(() => {
    if (tabs.length > 0 && !tabs.some((tab) => tab.id === activeTab)) {
      setActiveTab(tabs[0].id);
    }
  }, [activeTab, tabs]);

  const handleGlobalSave = async () => {
    try {
      await saveProfile();
      commitRuntimePreferences(useSettingsStore.getState().profile);
    } catch {
      // The store owns the user-facing error toast. Runtime preferences remain
      // untouched until a backend write succeeds.
    }
  };

  if (loading) {
    return (
      <DigitalCrownLoader text="Initialisation du Centre de Contrôle..." minHeight="min-h-[600px]" />
    );
  }

  if (tabs.length === 0) {
    return null;
  }

  const activeProfileBackedTab = profileBackedTabs.includes(activeTab);

  return (
    <div className="max-w-[1600px] mx-auto px-4 sm:px-8 py-8 animate-in fade-in duration-700">
      <div className="flex flex-col lg:flex-row gap-12 items-start">
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

          <nav data-tour="settings-navigation" className="space-y-2 bg-white/50 backdrop-blur-md p-3 rounded-[2rem] border border-slate-100 shadow-sm">
            {tabs.map((tab) => (
              <TabButton
                key={tab.id}
                active={activeTab === tab.id}
                onClick={() => setActiveTab(tab.id)}
                icon={tab.icon}
                label={tab.label}
              />
            ))}
          </nav>

          {access.canSettings && !profileReadError && (
            <div className="pt-6">
              <button
                onClick={handleGlobalSave}
                disabled={saving || (!isDirty && !saveSuccess)}
                className={cn(
                  "w-full py-5 rounded-[1.5rem] font-black text-base transition-all duration-500 shadow-2xl flex items-center justify-center gap-4",
                  saveSuccess
                    ? "bg-emerald-500 text-white shadow-emerald-500/30"
                    : (!isDirty && !saveSuccess)
                      ? "bg-slate-200 text-slate-400 shadow-none cursor-not-allowed"
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
          )}
        </div>

        <div className="flex-1 w-full bg-white rounded-[3rem] border border-slate-100 shadow-2xl shadow-slate-200/50 min-h-[800px] relative">
          <div className="p-8 sm:p-12">
            {profileReadError && activeProfileBackedTab ? (
              <SettingsReadError
                title={activeTab === 'profil' ? 'Profil indisponible' : 'Configuration cabinet indisponible'}
                message="Impossible de vérifier la configuration réelle du cabinet. Aucune valeur de repli n’est modifiable tant que la lecture backend n’a pas réussi."
                onRetry={retryProfile}
              />
            ) : (
              <>
                {activeTab === 'profil' && access.canSettings && <ProfileTab />}
                {activeTab === 'branding' && access.canSettings && <BrandingTab />}
                {activeTab === 'catalogue' && access.canSettings && <CatalogTab />}
                {activeTab === 'agenda' && access.canAgenda && <AgendaTab />}
                {activeTab === 'ia' && access.canSettings && <IATab />}
                {activeTab === 'securite' && access.canAdmin && <SecurityTab />}
                {activeTab === 'equipe' && access.canAdmin && <TeamReadTruthGate />}
              </>
            )}
          </div>

          <div className="absolute bottom-8 right-12 opacity-[0.03] pointer-events-none select-none">
            <SettingsIcon size={200} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsContainer;
