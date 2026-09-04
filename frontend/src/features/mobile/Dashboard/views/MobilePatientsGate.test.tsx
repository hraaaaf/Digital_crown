import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MobilePatientsGate } from './MobilePatientsGate';

vi.mock('./MobilePatientsView', () => ({
  MobilePatientsView: () => <div data-testid="online-patient-cockpit">Patient cockpit online</div>,
}));

describe('MobilePatientsGate', () => {
  it('fails closed with an explicit offline state and never mounts patient search', () => {
    const onClose = vi.fn();
    render(<MobilePatientsGate isOnline={false} onClose={onClose} />);

    expect(screen.getByText('Recherche patient indisponible hors ligne')).toBeTruthy();
    expect(screen.queryByTestId('online-patient-cockpit')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Retour à l’Agenda' }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('mounts the patient cockpit only while online', () => {
    render(<MobilePatientsGate isOnline onClose={() => undefined} />);
    expect(screen.getByTestId('online-patient-cockpit')).toBeTruthy();
  });
});
