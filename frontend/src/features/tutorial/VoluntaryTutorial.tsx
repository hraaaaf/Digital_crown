import { useEffect, useMemo, useState } from 'react';
import { CircleHelp, X } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { create } from 'zustand';
import { safeStorage } from '../../hooks/useLocalStorage';
import { useAuthStore } from '../../stores/useAuthStore';
import { hasAccess } from '../../utils/accessControl';
import { allowedDocumentStudioTabs } from '../admin/DocumentStudio/DocumentStudioPermissionPolicy';

type GuideId = 'dashboard' | 'create-patient' | 'agenda' | 'documents';
type GuideStatus = 'paused' | 'completed' | 'dismissed';

type PersistedProgress = Partial<Record<GuideId, { step: number; status: GuideStatus }>>;

interface GuideStep {
  title: string;
  body: string;
  target?: string;
  route?: string;
  routeMatch?: RegExp;
}

interface GuideDefinition {
  id: GuideId;
  title: string;
  description: string;
  steps: GuideStep[];
}

const STORAGE_KEY = 'digitalcrown_voluntary_tutorial_v1';

const readProgress = (): PersistedProgress => {
  const raw = safeStorage.get(STORAGE_KEY);
  if (!raw) return {};
  try {
    return JSON.parse(raw) as PersistedProgress;
  } catch {
    return {};
  }
};

const writeProgress = (progress: PersistedProgress) => {
  safeStorage.set(STORAGE_KEY, JSON.stringify(progress));
};

interface TutorialState {
  open: boolean;
  activeGuide: GuideId | null;
  step: number;
  progress: PersistedProgress;
  openPanel: () => void;
  closePanel: () => void;
  startGuide: (guide: GuideId) => void;
  nextStep: (totalSteps: number) => void;
  pause: () => void;
  dismiss: () => void;
}

export const useVoluntaryTutorial = create<TutorialState>((set, get) => ({
  // Non-negotiable: never derive panel visibility from storage. Refresh/new session stays quiet.
  open: false,
  activeGuide: null,
  step: 0,
  progress: readProgress(),
  openPanel: () => set({ open: true }),
  closePanel: () => set({ open: false }),
  startGuide: (guide) => {
    const saved = get().progress[guide];
    const resumeStep = saved?.status === 'paused' ? saved.step : 0;
    set({ open: true, activeGuide: guide, step: resumeStep });
  },
  nextStep: (totalSteps) => {
    const state = get();
    if (!state.activeGuide) return;
    if (state.step >= totalSteps - 1) {
      const progress = {
        ...state.progress,
        [state.activeGuide]: { step: totalSteps - 1, status: 'completed' as const },
      };
      writeProgress(progress);
      set({ activeGuide: null, step: 0, progress });
      return;
    }
    set({ step: state.step + 1 });
  },
  pause: () => {
    const state = get();
    if (!state.activeGuide) {
      set({ open: false });
      return;
    }
    const progress = {
      ...state.progress,
      [state.activeGuide]: { step: state.step, status: 'paused' as const },
    };
    writeProgress(progress);
    set({ open: false, activeGuide: null, step: 0, progress });
  },
  dismiss: () => {
    const state = get();
    if (!state.activeGuide) return;
    const progress = {
      ...state.progress,
      [state.activeGuide]: { step: state.step, status: 'dismissed' as const },
    };
    writeProgress(progress);
    set({ activeGuide: null, step: 0, progress });
  },
}));

const guideDefinitions: GuideDefinition[] = [
  {
    id: 'dashboard',
    title: 'Découvrir le dashboard',
    description: 'Une seule étape pour retrouver rapidement un patient.',
    steps: [
      {
        title: 'Retrouver un patient',
        body: 'La recherche accepte le nom, le prénom ou le numéro de dossier. Ouvrez un résultat pour accéder directement au dossier.',
        target: 'patient-search',
        route: '/dashboard',
      },
    ],
  },
  {
    id: 'create-patient',
    title: 'Créer un patient',
    description: 'Du raccourci Dashboard à la vérification anti-doublon.',
    steps: [
      {
        title: 'Ouvrir un nouveau dossier',
        body: 'Le raccourci Nouveau Patient démarre la création sans passer par la liste complète.',
        target: 'quick-action-new-patient',
        route: '/dashboard',
      },
      {
        title: 'Vérifier le numéro de dossier',
        body: 'Digital Crown propose un numéro et vérifie sa disponibilité avant création.',
        target: 'patient-dossier-number',
        route: '/patients/new',
      },
      {
        title: 'Compléter l’identité',
        body: 'Renseignez les champs requis. Les erreurs restent visibles au niveau du champ concerné.',
        target: 'patient-identity',
        route: '/patients/new',
      },
      {
        title: 'Créer sans doublon',
        body: 'La validation finale contrôle les doublons. En cas de correspondance, vérifiez le patient existant avant de forcer une création.',
        target: 'patient-submit',
        route: '/patients/new',
      },
    ],
  },
  {
    id: 'agenda',
    title: 'Agenda / rendez-vous',
    description: 'Les gestes essentiels du planning clinique.',
    steps: [
      {
        title: 'Ouvrir l’Agenda',
        body: 'Le raccourci Agenda Clinique ouvre directement le studio de rendez-vous.',
        target: 'quick-action-agenda',
        route: '/dashboard',
      },
      {
        title: 'Naviguer dans le temps',
        body: 'Utilisez la date et les flèches pour changer la période affichée.',
        target: 'agenda-header',
        route: '/agenda',
      },
      {
        title: 'Choisir la bonne vue',
        body: 'Jour, semaine et mois répondent à des besoins différents. La vue multi-praticien reste une fonction avancée.',
        target: 'agenda-view-switcher',
        route: '/agenda',
      },
      {
        title: 'Travailler dans le planning',
        body: 'Sélectionnez un créneau pour créer ou modifier le rendez-vous sans quitter l’Agenda.',
        target: 'agenda-calendar',
        route: '/agenda',
      },
    ],
  },
  {
    id: 'documents',
    title: 'Documents patient',
    description: 'Choisir, préparer et générer un document depuis le dossier patient.',
    steps: [
      {
        title: 'Ouvrir Documents',
        body: 'Depuis un dossier patient, utilisez l’action Document ou l’onglet Documents.',
        target: 'patient-documents-entry',
        routeMatch: /^\/patients\/\d+/,
      },
      {
        title: 'Choisir le document autorisé',
        body: 'Les onglets proposés dépendent de vos permissions. Le guide ne présente jamais un type inaccessible.',
        target: 'document-tabs',
        routeMatch: /^\/patients\/\d+/,
      },
      {
        title: 'Préparer puis générer',
        body: 'Complétez les informations du document, contrôlez la prévisualisation si nécessaire, puis générez-le.',
        target: 'document-generate',
        routeMatch: /^\/patients\/\d+/,
      },
    ],
  },
];

const routeMatches = (pathname: string, step: GuideStep) => {
  if (step.route) return pathname === step.route;
  if (step.routeMatch) return step.routeMatch.test(pathname);
  return true;
};

export const TutorialHelpButton = () => {
  const openPanel = useVoluntaryTutorial(state => state.openPanel);
  return (
    <button
      type="button"
      onClick={openPanel}
      className="min-h-11 flex items-center gap-2 px-3 py-2 text-text-muted hover:text-primary hover:bg-primary/5 rounded-elite-sm transition-elite"
      aria-label="Ouvrir Aide et Guide"
      title="Aide / Guide"
      data-guide="help-entry"
    >
      <CircleHelp size={20} aria-hidden="true" />
      <span className="hidden xl:inline text-xs font-black">Aide</span>
    </button>
  );
};

export const VoluntaryTutorialPanel = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const user = useAuthStore(state => state.user);
  const open = useVoluntaryTutorial(state => state.open);
  const activeGuideId = useVoluntaryTutorial(state => state.activeGuide);
  const stepIndex = useVoluntaryTutorial(state => state.step);
  const progress = useVoluntaryTutorial(state => state.progress);
  const closePanel = useVoluntaryTutorial(state => state.closePanel);
  const startGuide = useVoluntaryTutorial(state => state.startGuide);
  const nextStep = useVoluntaryTutorial(state => state.nextStep);
  const pause = useVoluntaryTutorial(state => state.pause);
  const dismiss = useVoluntaryTutorial(state => state.dismiss);
  const [spotlight, setSpotlight] = useState<DOMRect | null>(null);

  const guides = useMemo(() => guideDefinitions.filter(guide => {
    if (guide.id === 'create-patient' || guide.id === 'dashboard') return hasAccess(user, 'patients');
    if (guide.id === 'agenda') return hasAccess(user, 'agenda');
    if (guide.id === 'documents') return allowedDocumentStudioTabs(user).length > 0;
    return false;
  }), [user]);

  const activeGuide = guides.find(guide => guide.id === activeGuideId) ?? null;
  const activeStep = activeGuide?.steps[stepIndex] ?? null;

  useEffect(() => {
    if (!open || !activeStep?.target || !routeMatches(location.pathname, activeStep)) {
      setSpotlight(null);
      return;
    }

    const update = () => {
      const element = document.querySelector<HTMLElement>(`[data-guide="${activeStep.target}"]`);
      setSpotlight(element?.getBoundingClientRect() ?? null);
    };

    update();
    window.addEventListener('resize', update);
    window.addEventListener('scroll', update, true);
    return () => {
      window.removeEventListener('resize', update);
      window.removeEventListener('scroll', update, true);
    };
  }, [activeStep, location.pathname, open]);

  if (!open) return null;

  const moveToStepRoute = () => {
    if (!activeStep) return;
    if (activeStep.route) {
      navigate(activeStep.route);
      return;
    }
    if (activeGuide?.id === 'documents' && !/^\/patients\/\d+/.test(location.pathname)) {
      navigate('/patients');
    }
  };

  const stepRouteReady = activeStep ? routeMatches(location.pathname, activeStep) : true;

  return (
    <>
      {spotlight && (
        <div
          className="fixed pointer-events-none z-[1100] rounded-3xl border-2 border-primary/60 shadow-[0_0_0_6px_rgba(59,130,246,0.10)] transition-all duration-200"
          style={{
            top: Math.max(4, spotlight.top - 6),
            left: Math.max(4, spotlight.left - 6),
            width: spotlight.width + 12,
            height: spotlight.height + 12,
          }}
          aria-hidden="true"
        />
      )}

      <aside
        className="fixed z-[1200] top-24 right-4 sm:right-6 w-[min(390px,calc(100vw-2rem))] max-h-[calc(100vh-7rem)] overflow-y-auto rounded-[2rem] border border-border-main bg-card-bg/95 backdrop-blur-2xl shadow-2xl p-5 sm:p-6"
        aria-label="Guide volontaire"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-primary">Guide volontaire</p>
            <h2 className="mt-1 text-xl font-black text-main">{activeGuide ? activeGuide.title : 'Découvrir Digital Crown'}</h2>
            <p className="mt-1 text-xs font-medium text-text-muted">Rien ne démarre sans votre action. Fermez ce panneau à tout moment.</p>
          </div>
          <button
            type="button"
            onClick={closePanel}
            className="min-w-11 min-h-11 rounded-full flex items-center justify-center text-text-muted hover:text-main hover:bg-primary/5"
            aria-label="Fermer le guide"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        {!activeGuide ? (
          <div className="mt-5 space-y-3">
            {guides.map(guide => {
              const saved = progress[guide.id];
              const documentsReady = guide.id !== 'documents' || /^\/patients\/\d+/.test(location.pathname);
              return (
                <div key={guide.id} className="rounded-2xl border border-border-main bg-white/40 dark:bg-slate-900/30 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-black text-main">{guide.title}</h3>
                      <p className="mt-1 text-xs text-text-muted">{guide.description}</p>
                    </div>
                    {saved?.status === 'completed' && <span className="text-[9px] font-black uppercase text-emerald-600">Terminé</span>}
                  </div>
                  {guide.id === 'documents' && !documentsReady && (
                    <p className="mt-2 text-[10px] font-bold text-amber-600">Ouvrez d’abord un dossier patient pour lancer ce guide contextuel.</p>
                  )}
                  <button
                    type="button"
                    onClick={() => startGuide(guide.id)}
                    disabled={!documentsReady}
                    className="mt-3 min-h-11 w-full rounded-xl bg-primary px-4 py-2 text-xs font-black text-white disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {saved?.status === 'paused' ? 'Reprendre' : saved?.status === 'completed' ? 'Revoir' : 'Commencer'}
                  </button>
                </div>
              );
            })}
          </div>
        ) : activeStep ? (
          <div className="mt-5">
            <div className="flex items-center justify-between text-[10px] font-black uppercase tracking-wider text-text-muted">
              <span>Étape {stepIndex + 1} sur {activeGuide.steps.length}</span>
              <span>{Math.round(((stepIndex + 1) / activeGuide.steps.length) * 100)}%</span>
            </div>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-primary/10">
              <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${((stepIndex + 1) / activeGuide.steps.length) * 100}%` }} />
            </div>

            <div className="mt-5 rounded-2xl border border-primary/15 bg-primary/5 p-4">
              <h3 className="text-base font-black text-main">{activeStep.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-text-muted">{activeStep.body}</p>
            </div>

            {!stepRouteReady && (
              <button
                type="button"
                onClick={moveToStepRoute}
                className="mt-4 min-h-11 w-full rounded-xl border border-primary/20 bg-primary/5 px-4 py-2 text-xs font-black text-primary hover:bg-primary/10"
              >
                {activeGuide.id === 'documents' ? 'Ouvrir les dossiers patients' : 'Aller à cette étape'}
              </button>
            )}

            <div className="mt-5 grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={dismiss}
                className="min-h-11 rounded-xl border border-border-main px-3 py-2 text-xs font-black text-text-muted hover:bg-primary/5"
              >
                Passer
              </button>
              <button
                type="button"
                onClick={() => nextStep(activeGuide.steps.length)}
                className="min-h-11 rounded-xl bg-primary px-3 py-2 text-xs font-black text-white"
              >
                {stepIndex === activeGuide.steps.length - 1 ? 'Terminer' : 'Étape suivante'}
              </button>
              <button
                type="button"
                onClick={pause}
                className="col-span-2 min-h-11 rounded-xl border border-primary/20 px-3 py-2 text-xs font-black text-primary hover:bg-primary/5"
              >
                Reprendre plus tard
              </button>
            </div>
          </div>
        ) : null}
      </aside>
    </>
  );
};
