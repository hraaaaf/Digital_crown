import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { PALETTE } from '../cephaloTheme';
import { ClinicalScientificStudio } from './ClinicalScientificStudio';
import { api } from '../../../services/api';

vi.mock('../../../services/api', () => ({
  api: {
    get: vi.fn(),
  },
}));

const stage = (overrides: Record<string, unknown>) => ({
  stage_id: 'R11',
  title: 'Diagnostic scientifique',
  presentation_state: 'BLOCKED',
  authoritative_status: null,
  summary: 'Résumé autoritaire de test.',
  blocking_gates: ['r11_authoritative_snapshot_not_persisted'],
  missing_data_refs: ['measurement:missing'],
  contradictions: ['contradiction:test'],
  contraindications: ['contraindication:test'],
  provenance: [{ label: 'Source', value: 'typed-evidence-v1' }],
  clinician_action: {
    available: false,
    audit_required: true,
    label: 'Validation praticien',
    reason: 'Action indisponible sans preuve backend résolue.',
  },
  ...overrides,
});

const snapshot = {
  contract_version: 'R15_CLINICAL_STUDIO_VIEW_V1',
  patient_id: 915,
  analysis_id: 9915,
  evidence_graph_present: true,
  active_runtime_chain_verified: true,
  blocking_gate_count: 4,
  blocking_gates: ['r11_authoritative_snapshot_not_persisted'],
  clinical_validation_available: false,
  clinical_validation_reason: 'Aucune validation clinique sans preuve backend.',
  stages: [
    stage({ stage_id: 'R11', title: 'Diagnostic scientifique' }),
    stage({ stage_id: 'R12', title: 'Problem list & objectifs', blocking_gates: ['r11_not_authoritative'] }),
    stage({
      stage_id: 'R13',
      title: 'Options thérapeutiques',
      presentation_state: 'EVALUABLE',
      blocking_gates: ['clinician_selection_required'],
      summary: "Évaluable n'est jamais une prescription.",
      clinician_action: {
        available: false,
        audit_required: true,
        label: 'Sélection praticien',
        reason: 'La sélection reste indisponible tant que le backend ne persiste pas la preuve exacte.',
      },
    }),
    stage({ stage_id: 'R14', title: 'Validation clinique finale', blocking_gates: ['r14_authoritative_snapshot_not_persisted'] }),
  ],
};

describe('ClinicalScientificStudio R15', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows the complete R11-R14 authority chain and keeps EVALUABLE non-prescriptive', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: snapshot } as never);

    render(<ClinicalScientificStudio patientId={915} analysisId={9915} P={PALETTE.dark} />);

    await screen.findByText('Chaîne clinique scientifique');
    expect(api.get).toHaveBeenCalledWith('/patients/915/cephalo-clinical-studio?analysis_id=9915');
    expect(screen.getByText('R11 → R14')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /R11/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /R12/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /R13/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /R14/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /R13/i }));

    expect(await screen.findByText('Évaluable · non sélectionné')).toBeInTheDocument();
    expect(screen.getByText("Évaluable n'est jamais une prescription.")).toBeInTheDocument();
    expect(screen.getByText('clinician_selection_required')).toBeInTheDocument();
    expect(screen.getByText('Aucune validation disponible')).toBeInTheDocument();
    expect(screen.getByText(/preuve backend résolue/i)).toBeInTheDocument();
    expect(screen.getByText('Données manquantes')).toBeInTheDocument();
    expect(screen.getByText('Contradictions')).toBeInTheDocument();
    expect(screen.getByText('Contre-indications')).toBeInTheDocument();
    expect(screen.getByText('measurement:missing')).toBeInTheDocument();
    expect(screen.getByText('contradiction:test')).toBeInTheDocument();
    expect(screen.getByText('contraindication:test')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /valider|accepter|sélectionner/i })).not.toBeInTheDocument();
  });

  it('fails closed when the clinical snapshot cannot be loaded', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('offline'));

    render(<ClinicalScientificStudio patientId={915} analysisId={9915} P={PALETTE.dark} />);

    expect(await screen.findByText('Fail-closed')).toBeInTheDocument();
    expect(screen.getByText(/aucune validation n'est autorisée/i)).toBeInTheDocument();
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/patients/915/cephalo-clinical-studio?analysis_id=9915'));
  });

  it('falls back to the patient latest-analysis projection only when no analysis is selected', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: snapshot } as never);

    render(<ClinicalScientificStudio patientId={915} P={PALETTE.dark} />);

    await screen.findByText('Chaîne clinique scientifique');
    expect(api.get).toHaveBeenCalledWith('/patients/915/cephalo-clinical-studio');
  });
});
