import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { IntelligenceAlerts } from './IntelligenceAlerts';
import type { ProactiveAlert } from '../types';

const patientAlert: ProactiveAlert = {
  id: 11,
  patient_id: 7,
  nom: 'BENALI',
  prenom: 'Sara',
  type: 'clinical_followup',
  title: 'Dossier à vérifier',
  message: 'Information clinique à vérifier',
  action: 'Consulter le dossier',
  priority: 1,
};

const cabinetAlert: ProactiveAlert = {
  id: 22,
  patient_id: null,
  nom: null,
  prenom: null,
  type: 'cabinet',
  title: 'Stock à vérifier',
  message: 'Vérification du stock',
  action: 'Vérifier les fournitures',
  priority: 2,
};

afterEach(cleanup);

describe('LOT07 UX commun — alertes proactives Dashboard', () => {
  it('expose une priorité textuelle, un vrai bouton dossier et des actions indépendantes', () => {
    const navigate = vi.fn();
    const snooze = vi.fn();
    const markRead = vi.fn();
    render(
      <IntelligenceAlerts
        forecast={null}
        alerts={[patientAlert]}
        showForecast={false}
        showAlerts={true}
        onNavigatePatient={navigate}
        onSnooze={snooze}
        onMarkRead={markRead}
      />,
    );
    expect(screen.getByText('Priorité élevée')).toBeTruthy();
    expect(screen.getByText('Consulter le dossier')).toBeTruthy();

    const dossierButton = screen.getByRole('button', { name: /Ouvrir le dossier pour l’alerte : Dossier à vérifier/ });
    expect(dossierButton.tagName).toBe('BUTTON');
    expect(dossierButton.getAttribute('type')).toBe('button');
    expect(dossierButton.className).toContain('focus-visible');
    fireEvent.click(dossierButton);
    expect(navigate).toHaveBeenCalledExactlyOnceWith(7);

    fireEvent.click(screen.getByRole('button', { name: /Reporter l’alerte Dossier à vérifier de 24h/ }));
    expect(snooze).toHaveBeenCalledExactlyOnceWith(11);
    fireEvent.click(screen.getByRole('button', { name: /Marquer l’alerte Dossier à vérifier comme lue/ }));
    expect(markRead).toHaveBeenCalledExactlyOnceWith(11);
    expect(navigate).toHaveBeenCalledTimes(1);
  });

  it('ne transforme jamais une alerte cabinet sans patient en faux lien patient', () => {
    const navigate = vi.fn();
    render(
      <IntelligenceAlerts
        forecast={null}
        alerts={[cabinetAlert]}
        showForecast={false}
        showAlerts={true}
        onNavigatePatient={navigate}
        onSnooze={vi.fn()}
        onMarkRead={vi.fn()}
      />,
    );
    expect(screen.getByText('À traiter')).toBeTruthy();
    expect(screen.getByText('Stock à vérifier')).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Ouvrir le dossier/ })).toBeNull();
    expect(navigate).not.toHaveBeenCalled();
  });

  it('respecte le masquage du panneau selon le droit de lecture transmis', () => {
    const { container } = render(
      <IntelligenceAlerts
        forecast={null}
        alerts={[patientAlert]}
        showForecast={false}
        showAlerts={false}
        onNavigatePatient={vi.fn()}
        onSnooze={vi.fn()}
        onMarkRead={vi.fn()}
      />,
    );
    expect(container.querySelector('[data-testid="dashboard-proactive-alert"]')).toBeNull();
    expect(screen.queryByText('Dossier à vérifier')).toBeNull();
  });
});
