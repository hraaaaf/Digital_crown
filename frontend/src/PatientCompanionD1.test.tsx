import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { PatientCompanionPage } from './pages/PatientCompanionPage';
import { PatientCompanionApiError, type PatientContext } from './patient-companion/patientCompanionApi';

const verifiedUser = { uid: 'patient-firebase-a', email: 'patient@example.test', emailVerified: true };
const contextA: PatientContext = {
  access_id: 'access-a',
  relationship_type: 'SELF',
  patient: { display_name: 'Nadia Test', prenom: 'Nadia', nom: 'Test' },
};
const contextB: PatientContext = {
  access_id: 'access-b',
  relationship_type: 'PARENT',
  patient: { display_name: 'Yanis Test', prenom: 'Yanis', nom: 'Test' },
};

function makeServices(overrides: Record<string, unknown> = {}) {
  const api = {
    getContexts: vi.fn().mockResolvedValue([contextA]),
    activate: vi.fn().mockResolvedValue(contextA),
    getAppointments: vi.fn().mockResolvedValue([]),
    getShares: vi.fn().mockResolvedValue([]),
    ...(overrides.api as object | undefined),
  };
  const auth = {
    configured: () => true,
    observe: vi.fn(async (listener: (value: typeof verifiedUser) => void) => {
      listener(verifiedUser);
      return () => undefined;
    }),
    signIn: vi.fn().mockResolvedValue(verifiedUser),
    create: vi.fn().mockResolvedValue(verifiedUser),
    resendVerification: vi.fn().mockResolvedValue(undefined),
    refresh: vi.fn().mockResolvedValue(verifiedUser),
    signOut: vi.fn().mockResolvedValue(undefined),
    ...(overrides.auth as object | undefined),
  };
  return { auth, api, initialToken: overrides.initialToken as string | undefined };
}

describe('Patient Companion D1 UI', () => {
  it('fails closed into activation when Firebase identity has no active access', async () => {
    const activate = vi.fn().mockResolvedValue(contextA);
    const getContexts = vi.fn()
      .mockRejectedValueOnce(new PatientCompanionApiError(403, 'Aucun accès patient actif.'))
      .mockResolvedValue([contextA]);
    const services = makeServices({ api: { getContexts, activate } });

    render(<PatientCompanionPage services={services as any} />);

    expect(await screen.findByText('Activer mon espace patient')).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText('Code d’activation'), 'ABCD-EFGH-JKLM');
    await userEvent.click(screen.getByRole('button', { name: 'Activer mon espace' }));

    await waitFor(() => expect(activate).toHaveBeenCalledWith({ manual_code: 'ABCD-EFGH-JKLM' }));
    expect(await screen.findByText('Nadia Test')).toBeInTheDocument();
  });

  it('requires explicit context choice when one Firebase identity has multiple patient accesses', async () => {
    const getAppointments = vi.fn().mockResolvedValue([]);
    const services = makeServices({
      api: {
        getContexts: vi.fn().mockResolvedValue([contextA, contextB]),
        getAppointments,
      },
    });

    render(<PatientCompanionPage services={services as any} />);

    expect(await screen.findByText('Choisissez le dossier à consulter')).toBeInTheDocument();
    expect(getAppointments).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole('button', { name: /Yanis Test/i }));
    await waitFor(() => expect(getAppointments).toHaveBeenCalledWith('access-b'));
  });

  it('renders appointments and explicitly shared metadata without a byte-download affordance', async () => {
    const services = makeServices({
      api: {
        getContexts: vi.fn().mockResolvedValue([contextA]),
        getAppointments: vi.fn().mockResolvedValue([{
          id: 12,
          datetime_start: '2026-09-20T10:30:00',
          duration_minutes: 30,
          motif: 'Contrôle',
          status: 'PLANIFIE',
          scheduling_type: 'CONSULTATION',
        }]),
        getShares: vi.fn().mockResolvedValue([
          { share_id: 'doc-a', resource_type: 'document', resource_id: 5, title: 'Compte rendu', document_type: 'COURRIER' },
          { share_id: 'media-a', resource_type: 'media', resource_id: 8, asset_type: 'PHOTO', mime_type: 'image/jpeg' },
        ]),
      },
    });

    render(<PatientCompanionPage services={services as any} />);

    expect(await screen.findByText('Contrôle')).toBeInTheDocument();
    expect(screen.getByText('Compte rendu')).toBeInTheDocument();
    expect(screen.getByText(/aperçu non exposé en D1/i)).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /modifier|annuler|prendre/i })).not.toBeInTheDocument();
  });
});
