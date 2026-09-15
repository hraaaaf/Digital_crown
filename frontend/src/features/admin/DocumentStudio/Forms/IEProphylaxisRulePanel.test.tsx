import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

import { api } from '../../../../services/api';
import { IEProphylaxisRulePanel } from './IEProphylaxisRulePanel';
import type { DrugItem } from './prescriptionTypes';

vi.mock('../../../../services/api', () => ({
  api: { post: vi.fn() },
}));

const amoxicillinDrug: DrugItem = {
  id: 1,
  name: 'AMOXICILLINE TEST',
  dosage: '500 MG',
  forme: 'GELULE',
  posologie: '',
  type: 'MEDICAMENT',
  catalogPresentationId: 'cnops:test-amoxicillin',
  catalogDci: 'AMOXICILLINE',
};

describe('IEProphylaxisRulePanel C2', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('reste absent sans présentation amoxicilline mono-composant', () => {
    render(<IEProphylaxisRulePanel patientId={42} drug={{ ...amoxicillinDrug, catalogDci: 'AMOXICILLINE / ACIDE CLAVULANIQUE' }} />);
    expect(screen.queryByText('Prévention endocardite')).not.toBeInTheDocument();
  });

  it('n appelle rien avant une action explicite du praticien', () => {
    render(<IEProphylaxisRulePanel patientId={42} drug={amoxicillinDrug} />);
    expect(screen.getByText('Prévention endocardite')).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  });

  it('envoie uniquement les faits explicites et affiche une suggestion read-only', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      data: {
        status: 'READY',
        rule_id: 'IE_PROPHYLAXIS_ADULT_ORAL_AMOXICILLIN',
        rule_version: '2026-09-15.v3',
        blockers: [],
        active_ingredient_code: 'AMOXICILLIN',
        total_dose_mg: 2000,
        timing_min_minutes_before: 30,
        timing_max_minutes_before: 60,
        single_dose: true,
        source_ids: ['AHA_VGS_IE_2021', 'ADA_IE_PROPHYLAXIS'],
      },
    } as any);

    render(<IEProphylaxisRulePanel patientId={42} drug={amoxicillinDrug} />);
    fireEvent.click(screen.getByRole('button', { name: /^Évaluer$/i }));
    fireEvent.change(screen.getByLabelText('Date prévue du geste'), { target: { value: '2026-10-01' } });
    fireEvent.change(screen.getByLabelText('Geste avec manipulation gingivale périapicale ou perforation muqueuse'), { target: { value: 'yes' } });
    fireEvent.change(screen.getByLabelText('Voie orale possible'), { target: { value: 'yes' } });
    fireEvent.change(screen.getByLabelText('Prise actuelle de pénicilline ou amoxicilline'), { target: { value: 'no' } });
    fireEvent.click(screen.getByRole('button', { name: /Vérifier la prophylaxie/i }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/prescriptions/clinical-rules/ie-prophylaxis/evaluate', {
      patient_id: 42,
      procedure_date: '2026-10-01',
      dental_procedure_qualifies: true,
      oral_route_possible: true,
      currently_taking_penicillin_or_amoxicillin: false,
      presentation_id: 'cnops:test-amoxicillin',
    }));
    expect(await screen.findByText('Amoxicilline 2 g, prise unique, 30–60 min avant le geste')).toBeInTheDocument();
    expect(screen.getByText(/American Heart Association \(2021\) et American Dental Association/i)).toBeInTheDocument();
    expect(screen.getByText(/ne modifie pas automatiquement l’ordonnance/i)).toBeInTheDocument();
  });

  it('traduit les blockers en langage praticien sans afficher leurs codes', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      data: {
        status: 'BLOCKED',
        rule_id: 'IE_PROPHYLAXIS_ADULT_ORAL_AMOXICILLIN',
        rule_version: '2026-09-15.v3',
        blockers: ['CARDIAC_RISK_UNKNOWN', 'PENICILLIN_ALLERGY_UNKNOWN'],
        active_ingredient_code: null,
        total_dose_mg: null,
        timing_min_minutes_before: null,
        timing_max_minutes_before: null,
        single_dose: null,
        source_ids: ['AHA_VGS_IE_2021', 'ADA_IE_PROPHYLAXIS'],
      },
    } as any);

    render(<IEProphylaxisRulePanel patientId={42} drug={amoxicillinDrug} />);
    fireEvent.click(screen.getByRole('button', { name: /^Évaluer$/i }));
    fireEvent.change(screen.getByLabelText('Date prévue du geste'), { target: { value: '2026-10-01' } });
    fireEvent.click(screen.getByRole('button', { name: /Vérifier la prophylaxie/i }));

    expect(await screen.findByText(/Situation cardiaque à vérifier dans le contexte patient/i)).toBeInTheDocument();
    expect(screen.getByText(/Allergie pénicilline\/amoxicilline à vérifier/i)).toBeInTheDocument();
    expect(screen.queryByText('CARDIAC_RISK_UNKNOWN')).not.toBeInTheDocument();
    expect(screen.queryByText('PENICILLIN_ALLERGY_UNKNOWN')).not.toBeInTheDocument();
  });

  it('échoue fermé si l évaluation réseau échoue', async () => {
    vi.mocked(api.post).mockRejectedValueOnce(new Error('offline'));
    render(<IEProphylaxisRulePanel patientId={42} drug={amoxicillinDrug} />);
    fireEvent.click(screen.getByRole('button', { name: /^Évaluer$/i }));
    fireEvent.change(screen.getByLabelText('Date prévue du geste'), { target: { value: '2026-10-01' } });
    fireEvent.click(screen.getByRole('button', { name: /Vérifier la prophylaxie/i }));

    expect(await screen.findByText(/Évaluation indisponible. Aucune suggestion n’est appliquée/i)).toBeInTheDocument();
  });
});
