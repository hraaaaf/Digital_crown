import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PendingRequestCard, type PendingRequest } from './PendingRequestCard';

vi.mock('../../services/api', () => ({ api: { post: vi.fn() } }));

const base: PendingRequest = {
  id: 77, patient_name: 'PATIENT AUTORISE', phone: '0600000000',
  motif: 'Rendez-vous', source: 'frontdesk',
  datetime_start: '2026-10-24T10:30:00', duration_minutes: 30,
  status: 'EN_ATTENTE_DEMANDE', created_at: '2026-10-21T09:00:00',
};

describe('LOT07/07-C Frontdesk agenda-only visual privacy contract', () => {
  it('renders a neutral request instead of blank patient identity and disables a personal letter', () => {
    render(<PendingRequestCard request={{
      ...base, patient_name: null, phone: null, motif: null, source: null,
    }} onAction={() => {}} />);
    expect(screen.getByText('Demande de rendez-vous — identité masquée')).toBeTruthy();
    expect(screen.queryByText('PATIENT AUTORISE')).toBeNull();
    expect(screen.queryByText(/0600000000/)).toBeNull();
    expect(screen.getByRole('button', { name: 'Demander confirmation' }).hasAttribute('disabled')).toBe(true);
    expect(screen.getByRole('button', { name: 'Confirmer' }).hasAttribute('disabled')).toBe(false);
  });

  it('keeps authorized names visible and the allowed confirmation action enabled', () => {
    render(<PendingRequestCard request={base} onAction={() => {}} />);
    expect(screen.getByText('PATIENT AUTORISE')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Demander confirmation' }).hasAttribute('disabled')).toBe(false);
  });
});
