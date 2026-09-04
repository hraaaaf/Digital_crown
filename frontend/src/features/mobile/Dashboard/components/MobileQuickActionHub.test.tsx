import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MobileQuickActionHub } from './MobileQuickActionHub';

afterEach(() => cleanup());

describe('MobileQuickActionHub', () => {
  it('opens from the promoted FAB and exposes the five authorized actions', () => {
    const onNewAppointment = vi.fn();
    const onNewPatient = vi.fn();
    const onPatientAction = vi.fn();

    render(
      <MobileQuickActionHub
        canPay
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
    expect(screen.getByText('Encaisser rapidement')).toBeTruthy();

    fireEvent.click(screen.getByText('Nouveau RDV'));
    expect(onNewAppointment).toHaveBeenCalledTimes(1);
    expect(screen.queryByText('Que voulez-vous faire ?')).toBeNull();
  });

  it('hides payment when financial access is not available', () => {
    render(
      <MobileQuickActionHub
        canPay={false}
        isOnline
        onNewAppointment={() => undefined}
        onNewPatient={() => undefined}
        onPatientAction={() => undefined}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir les actions rapides' }));
    expect(screen.queryByText('Encaisser rapidement')).toBeNull();
  });

  it('fails closed offline and does not dispatch quick actions', () => {
    const onNewAppointment = vi.fn();
    render(
      <MobileQuickActionHub
        canPay
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
});
