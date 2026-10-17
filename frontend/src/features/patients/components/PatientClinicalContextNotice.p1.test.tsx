import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { PatientClinicalContextNotice } from './PatientClinicalContextNotice';

afterEach(() => cleanup());

describe('LOT07 P1 — contexte clinique source-first, identité inchangée', () => {
  it('treats missing medical history as unknown and navigates only via its verified edit callback', () => {
    const onEdit = vi.fn();
    render(<PatientClinicalContextNotice medicalHistory="" onEdit={onEdit} />);
    const status = screen.getByRole('status', { name: 'Antécédents médicaux non renseignés' });
    expect(status.textContent).toContain('Cela ne confirme pas leur absence.');
    expect(status.textContent).not.toContain('Aucune allergie');
    const button = screen.getByRole('button', { name: 'Compléter les antécédents dans la fiche patient' });
    expect(button.className).toContain('focus-visible');
    expect(button.className).toContain('min-h-11');
    expect(button.className).toContain('basis-full');
    expect(button.className).toContain('sm:basis-auto');
    fireEvent.click(button);
    expect(onEdit).toHaveBeenCalledTimes(1);
  });

  it('displays missing null, undefined and whitespace histories without making up negatives', () => {
    for (const history of [null, undefined, '   ']) {
      const { unmount } = render(<PatientClinicalContextNotice medicalHistory={history} onEdit={vi.fn()} />);
      expect(screen.getByRole('status', { name: /Antécédents médicaux non renseignés/ })).toBeTruthy();
      unmount();
    }
  });

  it('never reports missing medical history when a real recorded history exists', () => {
    const { container } = render(
      <PatientClinicalContextNotice medicalHistory="Allergie déclarée au latex" onEdit={vi.fn()} />,
    );
    expect(container.querySelector('[data-testid="patient-clinical-context"]')).toBeNull();
    expect(screen.queryByRole('button')).toBeNull();
  });

  it('exposes the actual NBA title, message and suggested free text without fake execution', () => {
    const onEdit = vi.fn();
    render(
      <PatientClinicalContextNotice
        medicalHistory="Antécédents saisis"
        advice={{ title: 'Dossier à compléter', message: 'Évaluer la situation', action: 'Contacter le praticien' }}
        onEdit={onEdit}
      />,
    );
    const advice = screen.getByRole('note', { name: 'Conseil clinique du dossier' });
    expect(advice.textContent).toContain('Dossier à compléter');
    expect(advice.textContent).toContain('Évaluer la situation');
    expect(advice.textContent).toContain('Action conseillée (non exécutée) : Contacter le praticien');
    expect(screen.queryByRole('button')).toBeNull();
    expect(onEdit).not.toHaveBeenCalled();
  });

  it('deduplicates an identical NBA missing-history message without suppressing its real advice', () => {
    render(
      <PatientClinicalContextNotice
        medicalHistory=""
        advice={{ title: 'Dossier à compléter', message: 'Antécédents médicaux non renseignés', action: 'Compléter Dossier' }}
        onEdit={vi.fn()}
      />,
    );
    expect(screen.getAllByText('Antécédents médicaux non renseignés')).toHaveLength(1);
    expect(screen.getByText('Dossier à compléter')).toBeTruthy();
    expect(screen.getByText(/Action conseillée \(non exécutée\) :/)).toBeTruthy();
  });

  it('does not fabricate a severity/urgency score from the untyped NBA payload', () => {
    render(
      <PatientClinicalContextNotice
        medicalHistory=" "
        advice={{ title: 'Information à vérifier', message: 'Vérification requise' }}
        onEdit={vi.fn()}
      />,
    );
    expect(screen.queryByText(/Priorité élevée|Urgence clinique/)).toBeNull();
    expect(screen.getAllByText(/Conseil clinique/).length).toBeGreaterThan(0);
    expect(screen.getByText('Antécédents médicaux non renseignés')).toBeTruthy();
  });

  it('renders on existing semantic tokens without hardcoded theme colors or fonts', () => {
    const { container } = render(<PatientClinicalContextNotice medicalHistory={null} onEdit={vi.fn()} />);
    const panel = container.querySelector('[role="status"]')!;
    expect(panel.className).toContain('bg-warning-surface');
    expect(panel.className).toContain('text-text-main');
    expect(container.innerHTML).not.toContain('style=');
  });
});
