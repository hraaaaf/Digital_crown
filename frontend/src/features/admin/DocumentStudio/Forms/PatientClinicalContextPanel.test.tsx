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
  penicillin_allergy_status: 'UNKNOWN',
  ie_cardiac_risk_category: 'UNKNOWN',
  renal_context_status: 'UNKNOWN',
  renal_context_note: null,
  hepatic_context_status: 'UNKNOWN',
  hepatic_context_note: null,
  updated_at: null,
  updated_by_user_id: null,
};

describe('PatientClinicalContextPanel C2', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.get).mockResolvedValue({ data: emptyContext } as any);
    vi.mocked(api.put).mockImplementation(async (_url, payload) => ({
      data: { ...emptyContext, ...(payload as object), updated_by_user_id: 7 },
    } as any));
  });

  it('charge un état inconnu replié sans inventer de valeur clinique', async () => {
    render(<PatientClinicalContextPanel patientId={42} />);

    const expand = await screen.findByRole('button', { name: /Renseigner/i });
    expect(api.get).toHaveBeenCalledWith('/patients/42/clinical-context');
    expect(screen.getByText('Contexte patient')).toBeInTheDocument();
    expect(screen.getByText(/Poids, allergies et informations médicales utiles à la prescription/i)).toBeInTheDocument();
    expect(screen.getByText(/Poids :/i)).toBeInTheDocument();
    expect(screen.getByText(/Pénicilline :/i)).toBeInTheDocument();
    expect(screen.getByText(/Risque endocardite :/i)).toBeInTheDocument();
    expect(screen.queryByLabelText('Poids explicite en kilogrammes')).not.toBeInTheDocument();

    fireEvent.click(expand);

    expect(screen.getByLabelText('Poids explicite en kilogrammes')).toHaveValue(null);
    expect(screen.getByLabelText('Statut des allergies médicamenteuses')).toHaveValue('UNKNOWN');
    expect(screen.getByLabelText('Statut allergie pénicilline ou amoxicilline')).toHaveValue('UNKNOWN');
    expect(screen.getByLabelText('Catégorie cardiaque endocardite infectieuse')).toHaveValue('UNKNOWN');
    expect(screen.getByLabelText('Statut du contexte rénal')).toHaveValue('UNKNOWN');
    expect(screen.getByLabelText('Statut du contexte hépatique')).toHaveValue('UNKNOWN');
    expect(screen.queryByLabelText(/Indication/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Aucun calcul de dose n’est activé/i)).not.toBeInTheDocument();
  });

  it('enregistre les faits C1 et C2 explicitement saisis puis replie le panneau', async () => {
    render(<PatientClinicalContextPanel patientId={42} />);
    fireEvent.click(await screen.findByRole('button', { name: /Renseigner/i }));

    fireEvent.change(screen.getByLabelText('Poids explicite en kilogrammes'), { target: { value: '72.5' } });
    fireEvent.change(screen.getByLabelText('Statut des allergies médicamenteuses'), { target: { value: 'NONE_KNOWN' } });
    fireEvent.change(screen.getByLabelText('Statut allergie pénicilline ou amoxicilline'), { target: { value: 'NONE_KNOWN' } });
    fireEvent.change(screen.getByLabelText('Catégorie cardiaque endocardite infectieuse'), { target: { value: 'PREVIOUS_INFECTIVE_ENDOCARDITIS' } });
    fireEvent.change(screen.getByLabelText('Statut du contexte rénal'), { target: { value: 'NO_KNOWN_IMPAIRMENT' } });
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer le contexte/i }));

    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/patients/42/clinical-context', {
      weight_kg: 72.5,
      medication_allergy_status: 'NONE_KNOWN',
      medication_allergies: [],
      penicillin_allergy_status: 'NONE_KNOWN',
      ie_cardiac_risk_category: 'PREVIOUS_INFECTIVE_ENDOCARDITIS',
      renal_context_status: 'NO_KNOWN_IMPAIRMENT',
      renal_context_note: null,
      hepatic_context_status: 'UNKNOWN',
      hepatic_context_note: null,
    }));
    expect(await screen.findByText('Contexte enregistré')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Renseigner/i })).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getByText('72.5 kg')).toBeInTheDocument();
    expect(screen.getByText('aucune connue')).toBeInTheDocument();
    expect(screen.getByText('haut risque déclaré')).toBeInTheDocument();
  });

  it('préserve les faits C2 existants lors d une sauvegarde C1', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: {
        ...emptyContext,
        penicillin_allergy_status: 'NONE_KNOWN',
        ie_cardiac_risk_category: 'PROSTHETIC_CARDIAC_VALVE',
      },
    } as any);
    render(<PatientClinicalContextPanel patientId={42} />);

    fireEvent.click(await screen.findByRole('button', { name: /Renseigner/i }));
    fireEvent.change(screen.getByLabelText('Poids explicite en kilogrammes'), { target: { value: '68' } });
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer le contexte/i }));

    await waitFor(() => expect(api.put).toHaveBeenCalled());
    const [, payload] = vi.mocked(api.put).mock.calls[0];
    expect((payload as any).penicillin_allergy_status).toBe('NONE_KNOWN');
    expect((payload as any).ie_cardiac_risk_category).toBe('PROSTHETIC_CARDIAC_VALVE');
  });

  it('échoue fermé si le contexte ne peut pas être chargé', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('offline'));
    render(<PatientClinicalContextPanel patientId={42} />);

    expect(await screen.findByText(/Contexte non chargé. Aucune valeur n’est supposée/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Renseigner/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Enregistrer le contexte/i })).not.toBeInTheDocument();
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

    fireEvent.click(await screen.findByRole('button', { name: /Renseigner/i }));
    const renalStatus = screen.getByLabelText('Statut du contexte rénal');
    expect(screen.getByLabelText('Note rénale factuelle')).toHaveValue('Note existante');
    fireEvent.change(renalStatus, { target: { value: 'NO_KNOWN_IMPAIRMENT' } });
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer le contexte/i }));

    await waitFor(() => expect(api.put).toHaveBeenCalled());
    const [, payload] = vi.mocked(api.put).mock.calls[0];
    expect((payload as any).renal_context_status).toBe('NO_KNOWN_IMPAIRMENT');
    expect((payload as any).renal_context_note).toBeNull();
  });
});
