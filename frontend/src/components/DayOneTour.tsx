import React, { useState, useEffect } from 'react';
import { Joyride as OriginalJoyride, STATUS } from 'react-joyride';
import { TOUR_STORAGE_KEY, TOUR_VERSION } from './GuidedTour/tourConfig';

const Joyride: any = OriginalJoyride;
const LEGACY_TOUR_STORAGE_KEY = 'digital_crown_tour_completed';

export const DayOneTour: React.FC = () => {
  const [run, setRun] = useState(false);

  useEffect(() => {
    const hasCompletedTour = localStorage.getItem(TOUR_STORAGE_KEY);
    const legacyCompletedTour = localStorage.getItem(LEGACY_TOUR_STORAGE_KEY);

    if (!hasCompletedTour && legacyCompletedTour) {
      localStorage.setItem(TOUR_STORAGE_KEY, TOUR_VERSION);
      localStorage.removeItem(LEGACY_TOUR_STORAGE_KEY);
      return;
    }

    if (!hasCompletedTour) {
      // Small delay to allow dashboard to render completely
      const timer = setTimeout(() => {
        setRun(true);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleJoyrideCallback = (data: any) => {
    const { status } = data;
    const finishedStatuses: string[] = [STATUS.FINISHED, STATUS.SKIPPED];

    if (finishedStatuses.includes(status)) {
      setRun(false);
      localStorage.setItem(TOUR_STORAGE_KEY, TOUR_VERSION);
      localStorage.removeItem(LEGACY_TOUR_STORAGE_KEY);
    }
  };

  const steps: any[] = [
    {
      target: 'body',
      placement: 'center',
      content: (
        <div className="text-center space-y-3">
          <h2 className="text-xl font-black text-primary font-outfit">Bienvenue sur Digital Crown</h2>
          <p className="text-sm text-slate-500 font-medium">
            Découvrons ensemble comment gérer votre cabinet dentaire plus efficacement avec notre IA.
          </p>
        </div>
      ),
      disableBeacon: true,
    },
    {
      target: '[data-tour="quick-action-new-patient"]',
      content: (
        <div className="space-y-2">
          <h3 className="font-bold text-primary">Créer votre premier dossier</h3>
          <p className="text-sm">Tout commence ici. Cliquez pour enregistrer votre premier patient.</p>
        </div>
      ),
    },
    {
      target: '[data-tour="dashboard-agenda"]',
      content: (
        <div className="space-y-2">
          <h3 className="font-bold text-primary">Activité Récente & Agenda</h3>
          <p className="text-sm">Retrouvez en un coup d'œil vos derniers patients consultés et la file d'attente du jour.</p>
        </div>
      ),
    },
    {
      target: '[data-tour="dashboard-stats"]',
      content: (
        <div className="space-y-2">
          <h3 className="font-bold text-primary">Intelligence Analytique</h3>
          <p className="text-sm">Vos performances financières et cliniques sont analysées en temps réel par notre algorithme.</p>
        </div>
      ),
    }
  ];

  return (
    <Joyride
      steps={steps}
      run={run}
      continuous
      scrollToFirstStep
      callback={handleJoyrideCallback}
      styles={{
        options: {
          primaryColor: 'var(--primary, #0f172a)',
          textColor: '#334155',
          backgroundColor: '#ffffff',
          overlayColor: 'rgba(0, 0, 0, 0.5)',
        },
        buttonNext: {
          backgroundColor: 'var(--primary, #0f172a)',
          borderRadius: '8px',
          padding: '8px 16px',
          fontWeight: 'bold',
          fontSize: '12px',
          textTransform: 'uppercase',
          letterSpacing: '0.05em'
        },
        buttonBack: {
          color: '#64748b',
          marginRight: '8px',
        },
        buttonSkip: {
          color: '#94a3b8',
        },
        tooltip: {
          borderRadius: '16px',
          padding: '24px',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        }
      } as any}
      locale={{
        back: 'Retour',
        close: 'Fermer',
        last: 'Terminer',
        next: 'Suivant',
        skip: 'Passer la visite'
      }}
    />
  );
};
