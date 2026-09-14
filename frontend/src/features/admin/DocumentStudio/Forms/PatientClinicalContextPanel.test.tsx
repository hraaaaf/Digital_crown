import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

import { api } from '../../../../services/api';
import { PatientClinicalContextPanel } from './PatientClinicalContextPanel';

vi.mock('../../../../services/api', () => ({
  api: {
    get: vi.fn(),
    put: vi.fn(),
  },
}));

const emptyContext = {
  patient_id: 42,
  employer_id: 7,
  weight_kg: null,
  medication_allergy_status: 'UNKNOWN',
  medication_allergies: null,
  renal_context_status: 'UNKNOWN',
  renal_context_note: null,
  hepatic_context_status: 'UNKNOWN',
  hepatic_context_note: null,
  updated_at: null,
  updated_by_user_id: null,
};

describe('PatientClinicalContextPanel C1', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.get).mockResolvedValue({ data: emptyContext } as any);
    vi.mocked(api.put).mockImplementation(async (_url, payload) => ({
      data: { ...emptyContext, ...(payload as object), updated_by_user_id: 7 },
    } as any));
  });

  it('charge un état inconnu sans inventer de valeur clinique', async () => {
    render(<PatientClinicalContextPanel patientId={42} />);

    const weight = await screen.findByLabelText('Poids explicite en kilogrammes');
    expect(api.get).toHaveBeenCalledWith('/patients/42/clinical-context');
    expect(weight).toHaveValue(null);
    expect(screen.getByLabelText('Statut des allergies médicamenteuses')).toHaveValue('UNKNOWN');
    expect(screen.getByLabelText('Statut du contexte rénal')).toHaveValue('UNKNOWN');
    expect(screen.getByLabelText('Statut du contexte hépatique')).toHaveValue('UNKNOWN');
    expect(screen.queryByLabelText(/Indication/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Aucun calcul de dose n’est activé/i)).toBeInTheDocument();
  });

  it('enregistre uniquement les faits patient explicitement saisis', async () => {
    render(<PatientClinicalContextPanel patientId={42} />);
    const weight = await screen.findByLabelText('Poids explicite en kilogrammes');
    const saveButton = screen.getByRole('button', { name: /Enregistrer le contexte/i });
    expect(saveButton).toBeEnabled();

    fireEvent.change(weight, { target: { value: '72.5' } });
    fireEvent.change(screen.getByLabelText('Statut des allergies médicamenteuses'), { target: { value: 'PRESENT' } });
    fireEvent.change(screen.getByLabelText('Allergies médicamenteuses rapportées'), { target: { value: 'Pénicilline, Ibuprofène' } });
    fireEvent.change(screen.getByLabelText('Statut du contexte rénal'), { target: { value: 'IMPAIRMENT_REPORTED' } });
    fireEvent.change(screen.getByLabelText('Note rénale factuelle'), { target: { value: 'Atteinte rapportée' } });
    fireEvent.click(saveButton);

    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/patients/42/clinical-context', {
      weight_kg: 72.5,
      medication_allergy_status: 'PRESENT',
      medication_allergies: ['Pénicilline', 'Ibuprofène'],
      renal_context_status: 'IMPAIRMENT_REPORTED',
      renal_context_note: 'Atteinte rapportée',
      hepatic_context_status: 'UNKNOWN',
      hepatic_context_note: null,
    }));
    expect(await screen.findByText('Contexte enregistré')).toBeInTheDocument();
  });

  it('échoue fermé si le contexte ne peut pas être chargé', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('offline'));
    render(<PatientClinicalContextPanel patientId={42} />);

    expect(await screen.findByText(/Contexte non chargé. Aucune valeur n’est supposée/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Enregistrer le contexte/i })).toBeDisabled();
  });

  it('ne persiste pas une note d organe après retour à un statut non atteint', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: {
        ...emptyContext,
        renal_context_status: 'IMPAIRMENT_REPORTED',
        renal_context_note: 'Note existante',
      },
    } as any);
    render(<PatientClinicalContextPanel patientId={42} />);

    const renalStatus = await screen.findByLabelText('Statut du contexte rénal');
    expect(screen.getByLabelText('Note rénale factuelle')).toHaveValue('Note existante');
    fireEvent.change(renalStatus, { target: { value: 'NO_KNOWN_IMPAIRMENT' } });
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer le contexte/i }));

    await waitFor(() => expect(api.put).toHaveBeenCalled());
    const [, payload] = vi.mocked(api.put).mock.calls[0];
    expect((payload as any).renal_context_status).toBe('NO_KNOWN_IMPAIRMENT');
    expect((payload as any).renal_context_note).toBeNull();
  });
});
