import React, { useEffect } from 'react';
import { Sidebar } from '../Sidebar';
import { Header } from '../Header';
import { LicenseBanner } from '../LicenseBanner';
import { useEliteStore } from '../../stores/useEliteStore';
import { useSettingsStore } from '../../features/admin/Settings/hooks/useSettingsStore';
import { useAuthStore } from '../../stores/useAuthStore';
import { hasAccess } from '../../utils/accessControl';
import { useLocation } from 'react-router-dom';
import { safeStorage } from '../../hooks/useLocalStorage';
import { AnimatedBackground } from '../AnimatedBackground';
import { PREMIUM_FONTS } from '../../features/admin/constants';
import { VoluntaryTutorialPanel } from '../../features/tutorial/VoluntaryTutorial';
import { ClinicPractitionerBar } from '../../features/clinic/ClinicPractitionerBar';
import './patientDossierResponsive.css';
import { SignatureIconicCabinetControls, type CabinetSignaturePreview } from '../../features/desktop-experience/SignatureIconicCabinetControls';
import '../../features/desktop-experience/SignatureIconicCabinetPreview.css';
import {R5SignaturePreferencesPanel} from '../../features/desktop-experience/R5SignaturePreferencesPanel';

import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import { Bot, Menu } from 'lucide-react';
import { CrownBotChat } from '../CrownBot/CrownBotChat';

interface LayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<LayoutProps> = ({ children }) => {
  const { fetchPatientIntelligence } = useEliteStore();
  const location = useLocation();

  useEffect(() => {
    const match = location.pathname.match(/\/patients\/(\d+)/);
    if (match && match[1]) {
      fetchPatientIntelligence(parseInt(match[1], 10));
    }
  }, [location.pathname, fetchPatientIntelligence]);

  const { profile, fetchProfile } = useSettingsStore();
  const { user } = useAuthStore();
  // A principal, cabinet, role or permission switch must discard the whole
  // CrownBotChat tree (sessions, insights, patient previews). Revoking a right
  // without logging out must not leave cached patient data on-screen.
  // The key remains stable across viewport resize, preserving in-progress drafts.
  const crownBotEffectiveRights = (['patients', 'agenda', 'accounting'] as const)
    .map(permission => hasAccess(user, permission) ? '1' : '0').join('');
  const crownBotPrincipalKey = user
    ? `${user.id}:${user.employer_id ?? user.id}:${user.role}:${crownBotEffectiveRights}`
    : 'anonymous';
  const canReadSettings = hasAccess(user, 'settings');
  const [animatedBg, setAnimatedBg] = React.useState(() => safeStorage.get('app_background_animated') === 'true');

  useEffect(() => {
    if (!profile.nom && canReadSettings) {
      fetchProfile();
    }
  }, [profile.nom, fetchProfile, canReadSettings]);

  useEffect(() => {
    const handleSettingsUpdate = () => {
      setAnimatedBg(safeStorage.get('app_background_animated') === 'true');
    };
    window.addEventListener('settings_updated', handleSettingsUpdate);
    return () => window.removeEventListener('settings_updated', handleSettingsUpdate);
  }, []);

  const fontClass = PREMIUM_FONTS.find(f => f.id === profile.font_fr)?.class || 'font-sans';
  const [isBotOpen, setIsBotOpen] = useState(false);
  // Only one CrownBotChat can mount at a time: the hidden duplicate would
  // otherwise open a second websocket and duplicate effectful API reads.
  const [isWideDesktop, setIsWideDesktop] = useState(
    () => typeof window !== 'undefined'
      && typeof window.matchMedia === 'function'
      && window.matchMedia('(min-width: 1600px)').matches,
  );
  const [isDockableDesktop, setIsDockableDesktop] = useState(
    () => typeof window !== 'undefined'
      && typeof window.matchMedia === 'function'
      && window.matchMedia('(min-width: 768px)').matches,
  );
  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return;
    const wideQuery = window.matchMedia('(min-width: 1600px)');
    const dockQuery = window.matchMedia('(min-width: 768px)');
    const onWideChange = () => setIsWideDesktop(wideQuery.matches);
    const onDockChange = () => setIsDockableDesktop(dockQuery.matches);
    onWideChange();
    onDockChange();
    wideQuery.addEventListener('change', onWideChange);
    dockQuery.addEventListener('change', onDockChange);
    return () => {
      wideQuery.removeEventListener('change', onWideChange);
      dockQuery.removeEventListener('change', onDockChange);
    };
  }, []);
  // CB-01: >=1600 CSS px keeps the sidecar. At 768-1599 CSS px a
  // non-overlapping bottom dock reserves space in the scrollable clinical
  // workspace, instead of covering patient or agenda actions.
  // Below 768 CSS px retain the original web floating fallback (not Pocket).
  // Both opt-in flags stay OFF in the actual cabinet.
  const associateSidecarEnabled =
    import.meta.env.VITE_CROWN_BOT_ASSOCIATE_SIDECAR_ENABLED === 'true'
    && import.meta.env.VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED === 'true';
  const showAssociateSidecar = associateSidecarEnabled && isWideDesktop;
  const showWorkspaceDock = associateSidecarEnabled && isDockableDesktop && !isWideDesktop;
  const showStructuredPanel = showAssociateSidecar || showWorkspaceDock;
  const sidecarCloseButtonRef = React.useRef<HTMLButtonElement>(null);
  const associatePanelRef = React.useRef<HTMLDivElement>(null);
  const wasSidecarOpenRef = React.useRef(false);
  const crownBotLauncherRef = React.useRef<HTMLButtonElement>(null);
  const restoreSidecarFocusRef = React.useRef(false);
  const closeAssociateSidecar = () => {
    restoreSidecarFocusRef.current = true;
    setIsBotOpen(false);
  };
  useEffect(() => {
    const sidecarOpen = showStructuredPanel && isBotOpen;
    if (sidecarOpen && !wasSidecarOpenRef.current) {
      sidecarCloseButtonRef.current?.focus();
    } else if (isBotOpen && wasSidecarOpenRef.current && !sidecarOpen) {
      // A 200% zoom / viewport reflow must not strand keyboard focus when
      // the desktop-only reducer disappears; the same Chat stays mounted.
      associatePanelRef.current?.focus();
    } else if (!isBotOpen && restoreSidecarFocusRef.current) {
      restoreSidecarFocusRef.current = false;
      crownBotLauncherRef.current?.focus();
    }
    wasSidecarOpenRef.current = sidecarOpen;
  }, [showStructuredPanel, isBotOpen]);
  // Parent badge survives a closed chat: scope its state to the exact
  // principal/rights key, not just the keyed CrownBotChat subtree. When
  // changing tenants the old count is hidden on the FIRST render.
  const [ghostUnreadState, setGhostUnreadState] = useState({
    principalKey: crownBotPrincipalKey,
    count: 0,
  });
  const ghostUnreadCount = ghostUnreadState.principalKey === crownBotPrincipalKey
    ? ghostUnreadState.count : 0;
  useEffect(() => {
    setGhostUnreadState({ principalKey: crownBotPrincipalKey, count: 0 });
  }, [crownBotPrincipalKey]);
  const onCrownBotUnreadChange = React.useCallback((count: number) => {
    // An old unmounted chat can only update its own scope, never B's badge.
    setGhostUnreadState({ principalKey: crownBotPrincipalKey, count: Math.max(0, count) });
  }, [crownBotPrincipalKey]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const isPatientRoute = /^\/patients(?:\/|$)/.test(location.pathname);
  // Preserve LOT07 07-C dev-only lab isolation from current master.
  const isCommandCabinetLab = location.pathname === '/command-cabinet-lab';
  // Four genuine routes + Command lab; no real mode switch in production and no preference persisted.
  const r4SignaturePreviewEnabled = import.meta.env.DEV
    && import.meta.env.VITE_V15_07_R4_SIGNATURE_LAB === 'true'
    && (/^\/(?:dashboard|agenda)$/.test(location.pathname)
      || /^\/patients\/\d+$/.test(location.pathname)
      || isCommandCabinetLab);
  const [r4SignatureMode, setR4SignatureMode] = useState<CabinetSignaturePreview>('core');
  const r5SignaturePrefsEnabled = r4SignaturePreviewEnabled && import.meta.env.DEV && import.meta.env.VITE_V15_07_R5_PREFS_LAB === 'true';
  // POLISH-02 is isolated to the authenticated DEV patient lab; production layout is unchanged.
  const r5PatientPolishEnabled = r5SignaturePrefsEnabled && isPatientRoute;
  const isDocumentStudio = /^\/patients\/\d+$/.test(location.pathname)
    && new URLSearchParams(location.search).get('tab') === 'admin';
  const showPractitionerContext = ['/dashboard', '/agenda', '/settings'].includes(location.pathname);

  React.useEffect(() => {
    setIsSidebarOpen(false);
  }, [location.pathname]);

  return (
    <div data-r4-signature={r4SignaturePreviewEnabled ? r4SignatureMode : undefined} className={`flex flex-row h-screen overflow-hidden ${fontClass} selection:bg-primary selection:text-white relative bg-medical-pearl`} style={{ color: 'var(--text-main)' }}>
      {animatedBg && <AnimatedBackground />}

      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] rounded-full bg-primary/10 blur-[100px]" />
        <div className="absolute -bottom-[10%] -right-[10%] w-[30%] h-[50%] rounded-full opacity-20 blur-[120px]" style={{ backgroundColor: 'var(--accent)' }} />
      </div>

      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />

      <div
        data-cb01-workspace-shell
        className={`relative z-10 flex flex-1 min-h-0 min-w-0 ${showWorkspaceDock && isBotOpen && !isCommandCabinetLab ? 'flex-col' : 'flex-row'}`}
      >
      <div className="flex-1 flex flex-col relative z-10 overflow-hidden min-w-0 min-h-0">
        <LicenseBanner />
        <button
          onClick={() => setIsSidebarOpen(true)}
          className="lg:hidden fixed top-5 left-4 z-[9998] p-2 rounded-xl bg-card-bg border border-border-main shadow-elite text-text-main hover:text-primary hover:bg-primary/5 transition-all"
          aria-label="Menu"
        >
          <Menu size={22} />
        </button>
        <Header
          isCrownBotOpen={isBotOpen}
          crownBotUnreadCount={ghostUnreadCount}
          onToggleCrownBot={isPatientRoute ? () => setIsBotOpen(value => !value) : undefined}
        />
        <VoluntaryTutorialPanel />

        <main className={`flex-1 min-h-0 overflow-y-auto overflow-x-hidden pt-0 flex flex-col custom-scrollbar ${isDocumentStudio ? 'p-2 sm:p-4 lg:p-8' : r5PatientPolishEnabled ? 'p-3 sm:p-4 lg:px-5 lg:pt-3 lg:pb-5' : 'p-3 sm:p-4 lg:p-8'}`}>
          {r5SignaturePrefsEnabled ? (
            <R5SignaturePreferencesPanel user={user} mode={r4SignatureMode} onChange={setR4SignatureMode}
              compactOnPatientRoute={isPatientRoute} />
          ) : r4SignaturePreviewEnabled && (
            <SignatureIconicCabinetControls mode={r4SignatureMode} onChange={setR4SignatureMode} />
          )}
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              className={`min-w-0 flex flex-1 flex-col rounded-elite border backdrop-blur-xl shadow-elite transition-elite ${isDocumentStudio ? 'p-2 sm:p-4 lg:p-6' : r5PatientPolishEnabled ? 'p-3 sm:p-4 lg:px-5 lg:py-3' : 'p-3 sm:p-4 lg:p-6'}`}
              style={{
                backgroundColor: 'var(--glass-bg)',
                borderColor: 'var(--glass-border)'
              }}
            >
              {showPractitionerContext && (
                <div className="mb-4 min-w-0">
                  <ClinicPractitionerBar />
                </div>
              )}
              <div className="min-w-0 flex-1">
                {children}
              </div>
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {associateSidecarEnabled && isBotOpen && !isCommandCabinetLab && (
        <div
          ref={associatePanelRef}
          tabIndex={-1}
          data-cb01-associate-sidecar={showStructuredPanel ? true : undefined}
          data-cb01-workspace-dock={showWorkspaceDock ? true : undefined}
          data-ux1-c-crownbot-overlay={!showStructuredPanel ? true : undefined}
          role={showStructuredPanel ? 'complementary' : undefined}
          aria-label={showAssociateSidecar
            ? 'Crown Bot — assistant latéral expérimental'
            : showWorkspaceDock ? 'Crown Bot — assistant ancré sous le dossier' : undefined}
          onKeyDown={event => {
            if (showStructuredPanel && event.key === 'Escape') {
              event.preventDefault();
              event.stopPropagation();
              closeAssociateSidecar();
            }
          }}
          className={showAssociateSidecar
            ? 'relative z-20 flex h-full min-h-0 w-[clamp(360px,30vw,480px)] shrink-0 flex-col border-l border-slate-200 bg-white shadow-2xl'
            : showWorkspaceDock
              ? 'relative z-20 flex h-[clamp(250px,36dvh,340px)] min-h-0 w-full shrink-0 flex-col border-t border-slate-200 bg-white shadow-2xl'
              : `fixed z-[1000] rounded-[24px] overflow-hidden shadow-2xl border border-white/20 bg-white/5 backdrop-blur-3xl ${
                isPatientRoute
                  ? 'inset-3 lg:inset-auto lg:bottom-28 lg:right-8 lg:w-[400px] lg:h-[600px]'
                  : 'inset-3 sm:inset-auto sm:bottom-28 sm:right-8 sm:w-[400px] sm:h-[600px] sm:max-h-[calc(100dvh-8rem)]'
              }`}
        >
          {showStructuredPanel && (
            <div className="flex shrink-0 items-center justify-between border-b border-slate-200 bg-slate-50 px-4 py-2">
              <div className="min-w-0">
                <p className="text-xs font-bold text-slate-800">Crown Bot · Associate</p>
                <p className="text-[11px] text-slate-500">Aperçu expérimental — aucune écriture</p>
              </div>
              <button
                type="button"
                aria-label="Réduire le panneau Crown Bot"
                ref={sidecarCloseButtonRef}
                onClick={closeAssociateSidecar}
                className="min-h-11 rounded-lg border border-slate-300 bg-white px-3 text-xs font-semibold text-slate-700 hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
              >
                Réduire
              </button>
            </div>
          )}
          <div className={showStructuredPanel ? 'min-h-0 flex-1' : 'h-full'}>
            <CrownBotChat
              key={crownBotPrincipalKey}
              onClose={showStructuredPanel ? closeAssociateSidecar : () => setIsBotOpen(false)}
              onUnreadChange={onCrownBotUnreadChange}
            />
          </div>
        </div>
      )}
      </div>

      {!isCommandCabinetLab && <div
        data-ux1-c-crownbot-floating
        className={`${showStructuredPanel && isBotOpen ? 'hidden lg:hidden' : (isPatientRoute ? 'hidden lg:block' : '')} fixed right-4 z-50 bottom-[max(1rem,env(safe-area-inset-bottom))] sm:bottom-8 sm:right-8`}
      >
        <button
          ref={crownBotLauncherRef}
          onClick={() => setIsBotOpen(!isBotOpen)}
          aria-label={isBotOpen ? 'Fermer CrownBot' : 'Ouvrir CrownBot'}
          aria-expanded={isBotOpen}
          className="w-12 h-12 sm:w-14 sm:h-14 bg-gradient-to-tr from-primary to-secondary text-white rounded-full shadow-2xl flex items-center justify-center hover:scale-110 active:scale-95 transition-all border border-white/20 relative"
        >
          <Bot size={24} />
          {ghostUnreadCount > 0 && !isBotOpen && (
            <span data-cb01-parent-unread className="absolute -top-1 -right-1 w-5 h-5 bg-amber-400 text-slate-900 text-[9px] font-black rounded-full flex items-center justify-center border-2 border-white animate-pulse shadow-lg">
              {ghostUnreadCount}
            </span>
          )}
        </button>
      </div>}

      <AnimatePresence>
        {isBotOpen && !associateSidecarEnabled && !isCommandCabinetLab && (
          <motion.div
            data-ux1-c-crownbot-overlay
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className={`fixed z-[1000] rounded-[24px] overflow-hidden shadow-2xl border border-white/20 bg-white/5 backdrop-blur-3xl ${
              isPatientRoute
                ? 'inset-3 lg:inset-auto lg:bottom-28 lg:right-8 lg:w-[400px] lg:h-[600px]'
                : 'inset-3 sm:inset-auto sm:bottom-28 sm:right-8 sm:w-[400px] sm:h-[600px]'
            }`}
          >
            <CrownBotChat key={crownBotPrincipalKey} onClose={() => setIsBotOpen(false)} onUnreadChange={onCrownBotUnreadChange} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
