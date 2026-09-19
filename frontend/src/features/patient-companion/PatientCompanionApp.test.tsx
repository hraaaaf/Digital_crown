import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { PatientCompanionApp } from './PatientCompanionApp';

afterEach(() => { vi.restoreAllMocks(); window.history.replaceState({}, '', '/companion'); });

describe('PatientCompanionApp PC-00', () => {
  it('does not persist the Firebase credential and exposes no staff shell', () => {
    render(<PatientCompanionApp />);
    expect(screen.getByText('Patient Companion')).toBeInTheDocument();
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
    expect(localStorage.length).toBe(0);
  });

  it('loads an authorized context after identity verification', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ contexts: [{ access_id: 'opaque-access', relationship_type: 'SELF', patient: { prenom: 'Aya', nom: 'Test' } }] }) }));
    render(<PatientCompanionApp />);
    fireEvent.change(screen.getByLabelText('Jeton Firebase'), { target: { value: 'firebase-id-token' } });
    fireEvent.click(screen.getByText('Continuer'));
    await waitFor(() => expect(screen.getByText('Aya Test')).toBeInTheDocument());
    expect(localStorage.getItem('firebase-id-token')).toBeNull();
  });

  it('falls back to activation when no active context exists', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ contexts: [] }) }));
    render(<PatientCompanionApp />);
    fireEvent.change(screen.getByLabelText('Jeton Firebase'), { target: { value: 'firebase-id-token' } });
    fireEvent.click(screen.getByText('Continuer'));
    await waitFor(() => expect(screen.getByText('Activer mon accès')).toBeInTheDocument());
  });
});
