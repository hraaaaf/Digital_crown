import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { AppUser } from '../../types';

const { mockGet } = vi.hoisted(() => ({ mockGet: vi.fn() }));
vi.mock('../../services/api', () => ({ api: { get: mockGet } }));
vi.mock('../patients/components/PatientMediaTimeline', () => ({
  PatientMediaTimeline: ({ patientId, readOnly }: { patientId: number; readOnly?: boolean }) =>
    <div data-testid="actual-media-component">patient={patientId};readonly={String(readOnly)}</div>,
}));
vi.mock('../multiview/HistoricBilanReadonlyPanel', () => ({
  HistoricBilanReadonlyPanel: ({ patientId }: { patientId: number }) =>
    <div data-testid="actual-historic-bilan-panel">patient={patientId}</div>,
}));

import { CommandCabinetPatientSurfaces, parseCommandPatients } from './CommandCabinetPatientSurfaces';

const authorized = { id: '101', role: 'SECRETAIRE', employer_id: 10,
  permissions: { agenda: true, patients: true } } as unknown as AppUser;
const denied = { ...authorized, permissions: { agenda: true, patients: false } } as AppUser;
const patient = { id: 81, nom: 'TEST-LOCALE', prenom: 'PATIENT', numero_dossier: 'T2-081' };

beforeEach(() => {
  mockGet.mockReset();
  mockGet.mockImplementation((url: string) => {
    if (url === '/patients/') return Promise.resolve({ data: [patient] });
    if (url === '/patients/81') return Promise.resolve({ data: patient });
    return Promise.reject(new Error('UNEXPECTED_API'));
  });
});
afterEach(() => cleanup());

describe('LOT07 R4 — actual patient + media Cabinet contract', () => {
  it('rejects malformed and mixed patient lists instead of fabricating an empty state', () => {
    expect(parseCommandPatients(null)).toBeNull();
    expect(parseCommandPatients([{ ...patient, id: 0 }])).toBeNull();
    expect(parseCommandPatients([patient, { ...patient, nom: null }])).toBeNull();
    expect(parseCommandPatients([patient])).toEqual([patient]);
  });

  it('never issues a patient fetch or mounts imaging for an agenda-only actor', () => {
    render(<CommandCabinetPatientSurfaces user={denied} surface="imagerie" />);
    expect(screen.getByRole('alert')).toHaveTextContent('permission patients');
    expect(mockGet).not.toHaveBeenCalled();
    expect(screen.queryByTestId('actual-media-component')).toBeNull();
  });

  it('requires explicit patient selection and matching GET before any imaging mount', async () => {
    const { rerender } = render(<CommandCabinetPatientSurfaces user={authorized} surface="dossier" />);
    expect(screen.queryByTestId('r4-verified-dossier')).toBeNull();
    const selector = await screen.findByLabelText('Sélectionner un dossier autorisé');
    expect(screen.getByText(/Aucun dossier ouvert/)).toBeInTheDocument();
    fireEvent.change(selector, { target: { value: '81' } });
    expect(await screen.findByTestId('r4-verified-dossier')).toHaveTextContent('PATIENT TEST-LOCALE');
    expect(screen.getByTestId('actual-historic-bilan-panel')).toHaveTextContent('patient=81');
    rerender(<CommandCabinetPatientSurfaces user={authorized} surface="imagerie" />);
    expect(await screen.findByTestId('r4-verified-imagerie')).toBeInTheDocument();
    expect(screen.getByTestId('actual-media-component')).toHaveTextContent('patient=81;readonly=true');
    expect(mockGet).toHaveBeenCalledWith('/patients/81');
  });

  it('fails closed when the detail endpoint returns another patient id', async () => {
    mockGet.mockImplementation((url: string) => Promise.resolve({ data:
      url === '/patients/' ? [patient] : { ...patient, id: 82 },
    }));
    render(<CommandCabinetPatientSurfaces user={authorized} surface="imagerie" />);
    const selector = await screen.findByLabelText('Sélectionner un dossier autorisé');
    fireEvent.change(selector, { target: { value: '81' } });
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('non vérifiable'));
    expect(screen.queryByTestId('actual-media-component')).toBeNull();
  });

  it('does not turn 403 or API failure into an empty patient list', async () => {
    mockGet.mockRejectedValue({ response: { status: 403 } });
    render(<CommandCabinetPatientSurfaces user={authorized} surface="dossier" />);
    expect(await screen.findByRole('alert')).toHaveTextContent('non vérifiable');
    expect(screen.queryByLabelText('Sélectionner un dossier autorisé')).toBeNull();
  });
});
