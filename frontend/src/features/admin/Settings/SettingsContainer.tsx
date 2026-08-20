import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  BookOpen,
  Calendar,
  CheckCircle2,
  Gauge,
  Loader2,
  Palette,
  Save,
  Settings as SettingsIcon,
  Shield,
  UserCircle,
  Users,
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
import { api } from '../../../services/api';
import {
  isProfileBackedTab,
  shouldShowPendingConfigNotice,
  shouldShowSharedSaveBar,
  shouldWarnBeforeUnload,
} from './saveDoctrine';

const SettingsSaveBar: React.FC<{
  saving: boolean;
  saveSuccess: boolean;
  onSave: () => Promise<void>;
}> = ({ saving, saveSuccess, onSave }) => (
  <div className="sticky top-4 z-30 mb-6" data-testid="settings-save-bar">
    <div
      role="status"
      aria-live="polite"
      className={cn(
        'flex flex-col gap-4 rounded-2xl border px-4 py-4 shadow-lg backdrop-blur-xl sm:flex-row sm:items-center sm:justify-between sm:px-5',
        saveSuccess
          ? 'border-emerald-200 bg-emerald-50/95 shadow-emerald-100/70'
          : 'border-amber-200 bg-amber-50/95 shadow-amber-100/70',
      )}
    >
      <div className="flex min-w-0 items-start gap-3">
        <div
          className={cn(
            'mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl',
            saveSuccess ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700',
          )}
        >
          {saveSuccess ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
        </div>
        <div className="min-w-0">
          <p className={cn('font-black', saveSuccess ? 'text-emerald-900' : 'text-amber-950')}>
            {saveSuccess
              ? 'Configuration enregistrée'
              : saving
                ? 'Enregistrement de la configuration…'
                : 'Modifications de la configuration non enregistrées'}
          </p>
          <p className={cn('mt-1 text-xs font-medium leading-relaxed', saveSuccess ? 'text-emerald-700' : 'text-amber-800')}>
            {saveSuccess
              ? 'Les réglages Profil, Design et Performance ont été confirmés par le backend.'
              : 'Profil, Design & Ambiance et Performance & Assistance partagent cette sauvegarde.'}
          </p>
        </div>
      </div>

      {!saveSuccess && (
        <button
          type="button"
          onClick={() => void onSave()}
          disabled={saving}
          className="inline-flex w-full shrink-0 items-center justify-center gap-2 rounded-xl bg-slate-950 px-5 py-3 text-sm font-black text-white shadow-lg shadow-slate-950/15 transition hover:bg-black disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
        >
          {saving ? <Loader2 size={17} className="animate-spin" /> : <Save size={17} />}
          {saving ? 'Enregistrement…' : 'Enregistrer la configuration'}
        </button>
      )}
    </div>
  </div>
);

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
      { id: 'ia' as Tab, label: 'Performance & Assistance', icon: <Gauge size={20} /> },
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

  useEffect(() => {
    if (!shouldWarnBeforeUnload(isDirty)) return undefined;

    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = '';
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isDirty]);

  const handleGlobalSave = async () => {
    try {
      await saveProfile();
    } catch {
      // The store owns the user-facing error toast and keeps isDirty=true.
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

  const activeProfileBackedTab = isProfileBackedTab(activeTab);
  const showSharedSaveBar = access.canSettings && !profileReadError && shouldShowSharedSaveBar(activeTab, {
    isDirty,
    saving,
    saveSuccess,
  });
  const showPendingNotice = access.canSettings && !profileReadError && shouldShowPendingConfigNotice(activeTab, isDirty);

  return (
    <div className="max-w-[1600px] mx-auto px-4 sm:px-8 py-8 animate-in fade-in duration-700">
      {activeTab === 'profil' && (
        <style>{`
          /* R1: the Settings shell is now the only visible owner of staged saves. */
          .settings-profile-surface .sticky.bottom-6 {
            display: none !important;
          }
        `}</style>
      )}
      {activeTab === 'equipe' && (
        <style>{`
          @media (max-width: 639px) {
            .settings-team-surface select {
              min-width: 0 !important;
              max-width: 100% !important;
            }

            .settings-team-surface .space-y-3 > .group {
              flex-direction: column !important;
              align-items: stretch !important;
              gap: 1rem;
            }

            .settings-team-surface .space-y-3 > .group > div:first-child {
              min-width: 0;
              width: 100%;
            }

            .settings-team-surface .space-y-3 > .group > div:first-child > div:last-child {
              min-width: 0;
            }

            .settings-team-surface .space-y-3 > .group > div:first-child > div:last-child > h4,
            .settings-team-surface .space-y-3 > .group > div:first-child > div:last-child > div {
              flex-wrap: wrap;
              min-width: 0;
            }

            .settings-team-surface .space-y-3 > .group > div:first-child span {
              min-width: 0;
              overflow-wrap: anywhere;
            }

            .settings-team-surface .space-y-3 > .group > div:last-child {
              opacity: 1 !important;
              align-self: flex-end;
              flex-wrap: wrap;
              max-width: 100%;
            }
          }
        `}</style>
      )}
      <div className="flex flex-col lg:flex-row gap-12 items-start min-w-0">
        <div className="w-full lg:w-80 space-y-8 sticky top-24 min-w-0">
          <div className="flex items-center gap-4 mb-10 min-w-0">
            <div className="w-14 h-14 shrink-0 bg-primary text-white rounded-[1.25rem] flex items-center justify-center shadow-2xl shadow-primary/30">
              <SettingsIcon size={28} />
            </div>
            <div className="min-w-0">
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

          {showPendingNotice && (
            <div
              data-testid="settings-pending-config-notice"
              className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-900 shadow-sm"
            >
              <AlertTriangle size={17} className="mt-0.5 shrink-0 text-amber-600" />
              <div className="min-w-0">
                <p className="text-xs font-black">Configuration non enregistrée</p>
                <p className="mt-1 text-[11px] font-medium leading-relaxed text-amber-700">
                  Revenez à Profil, Design ou Performance pour enregistrer les modifications en attente.
                </p>
              </div>
            </div>
          )}
        </div>

        <div className={cn(
          "flex-1 min-w-0 w-full bg-white rounded-[3rem] border border-slate-100 shadow-2xl shadow-slate-200/50 min-h-[800px] relative",
          activeTab === 'profil' && 'settings-profile-surface',
          activeTab === 'equipe' && 'settings-team-surface'
        )}>
          <div className="min-w-0 p-5 sm:p-12">
            {showSharedSaveBar && (
              <SettingsSaveBar
                saving={saving}
                saveSuccess={saveSuccess}
                onSave={handleGlobalSave}
              />
            )}

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
