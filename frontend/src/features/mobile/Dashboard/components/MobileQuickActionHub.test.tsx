import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MobileQuickActionHub } from './MobileQuickActionHub';

const ALL_CAPABILITIES = {
  can_create_appointment: true,
  can_create_patient: true,
  can_open_clinical_context: true,
  can_pay: true,
};

afterEach(() => cleanup());

describe('MobileQuickActionHub', () => {
  it('opens from the promoted FAB and exposes the four Pocket actions', () => {
    const onNewAppointment = vi.fn();
    const onNewPatient = vi.fn();
    const onPatientAction = vi.fn();

    render(
      <MobileQuickActionHub
        capabilities={ALL_CAPABILITIES}
        isOnline
        onNewAppointment={onNewAppointment}
        onNewPatient={onNewPatient}
        onPatientAction={onPatientAction}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir les actions rapides' }));
    expect(screen.getByText('Action rapide')).toBeTruthy();
    expect(screen.getByText('Nouveau RDV')).toBeTruthy();
    expect(screen.getByText('Nouveau patient')).toBeTruthy();
    expect(screen.getByText('Photo clinique')).toBeTruthy();
    expect(screen.getByText('Scanner document')).toBeTruthy();
    expect(screen.queryByText('Encaisser rapidement')).toBeNull();
    expect(screen.getByRole('button', { name: 'Fermer les actions rapides' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Fermer' })).toBeNull();

    fireEvent.click(screen.getByText('Nouveau RDV'));
    expect(onNewAppointment).toHaveBeenCalledTimes(1);
    expect(screen.queryByText('Que voulez-vous faire ?')).toBeNull();
  });

  it('hides every action not granted by the server capability contract', () => {
    render(
      <MobileQuickActionHub
        capabilities={{
          can_create_appointment: true,
          can_create_patient: false,
          can_open_clinical_context: false,
          can_pay: false,
        }}
        isOnline
        onNewAppointment={() => undefined}
        onNewPatient={() => undefined}
        onPatientAction={() => undefined}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir les actions rapides' }));
    expect(screen.getByText('Nouveau RDV')).toBeTruthy();
    expect(screen.queryByText('Nouveau patient')).toBeNull();
    expect(screen.queryByText('Photo clinique')).toBeNull();
    expect(screen.queryByText('Scanner document')).toBeNull();
    expect(screen.queryByText('Encaisser rapidement')).toBeNull();
  });

  it('renders no FAB until capabilities are known or when none are granted', () => {
    const { rerender } = render(
      <MobileQuickActionHub
        capabilities={ALL_CAPABILITIES}
        capabilitiesLoaded={false}
        isOnline
        onNewAppointment={() => undefined}
        onNewPatient={() => undefined}
        onPatientAction={() => undefined}
      />,
    );
    expect(screen.queryByRole('button', { name: 'Ouvrir les actions rapides' })).toBeNull();

    rerender(
      <MobileQuickActionHub
        capabilities={{
          can_create_appointment: false,
          can_create_patient: false,
          can_open_clinical_context: false,
          can_pay: false,
        }}
        capabilitiesLoaded
        isOnline
        onNewAppointment={() => undefined}
        onNewPatient={() => undefined}
        onPatientAction={() => undefined}
      />,
    );
    expect(screen.queryByRole('button', { name: 'Ouvrir les actions rapides' })).toBeNull();
  });

  it('fails closed offline and does not dispatch quick actions', () => {
    const onNewAppointment = vi.fn();
    render(
      <MobileQuickActionHub
        capabilities={ALL_CAPABILITIES}
        isOnline={false}
        onNewAppointment={onNewAppointment}
        onNewPatient={() => undefined}
        onPatientAction={() => undefined}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir les actions rapides' }));
    expect(screen.getByText('Connexion cabinet requise pour créer ou enregistrer une action.')).toBeTruthy();
    const rdv = screen.getByText('Nouveau RDV').closest('button');
    expect(rdv?.hasAttribute('disabled')).toBe(true);
    if (rdv) fireEvent.click(rdv);
    expect(onNewAppointment).not.toHaveBeenCalled();
  });


  it('traps keyboard focus in the dialog and restores the launcher on Escape', () => {
    render(
      <MobileQuickActionHub
        capabilities={ALL_CAPABILITIES}
        isOnline
        onNewAppointment={() => undefined}
        onNewPatient={() => undefined}
        onPatientAction={() => undefined}
      />,
    );

    const launcher = screen.getByRole('button', { name: 'Ouvrir les actions rapides' });
    launcher.focus();
    fireEvent.click(launcher);

    const dialog = screen.getByRole('dialog');
    expect(dialog.contains(document.activeElement)).toBe(true);

    const dialogButtons = Array.from(dialog.querySelectorAll<HTMLButtonElement>('button:not([disabled])'));
    const first = dialogButtons[0];
    const last = dialogButtons[dialogButtons.length - 1];

    last.focus();
    fireEvent.keyDown(window, { key: 'Tab' });
    expect(document.activeElement).toBe(first);

    first.focus();
    fireEvent.keyDown(window, { key: 'Tab', shiftKey: true });
    expect(document.activeElement).toBe(last);

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(document.activeElement).toBe(launcher);
  });

  it('supports a controlled open state without rendering its legacy floating launcher', () => {
    const onOpenChange = vi.fn();
    const { rerender } = render(
      <MobileQuickActionHub
        capabilities={ALL_CAPABILITIES}
        isOnline
        open={false}
        onOpenChange={onOpenChange}
        hideLauncher
        onNewAppointment={() => undefined}
        onNewPatient={() => undefined}
        onPatientAction={() => undefined}
      />,
    );

    expect(screen.queryByRole('button', { name: 'Ouvrir les actions rapides' })).toBeNull();
    expect(screen.queryByText('Action rapide')).toBeNull();

    rerender(
      <MobileQuickActionHub
        capabilities={ALL_CAPABILITIES}
        isOnline
        open
        onOpenChange={onOpenChange}
        hideLauncher
        onNewAppointment={() => undefined}
        onNewPatient={() => undefined}
        onPatientAction={() => undefined}
      />,
    );

    expect(screen.getByText('Action rapide')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Fermer le fond des actions rapides' }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
