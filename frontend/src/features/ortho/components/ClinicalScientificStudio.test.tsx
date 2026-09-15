import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { PALETTE } from '../cephaloTheme';
import { ClinicalScientificStudio } from './ClinicalScientificStudio';
import { api } from '../../../services/api';

vi.mock('../../../services/api', () => ({ api: { get: vi.fn() } }));

const stage = (overrides: Record<string, unknown>) => ({
  stage_id: 'R11', title: 'Diagnostic scientifique', presentation_state: 'BLOCKED', authoritative_status: null,
  summary: 'Résumé interne de test.', blocking_gates: ['r11_authoritative_snapshot_not_persisted'],
  missing_data_refs: ['measurement:missing'], contradictions: ['contradiction:test'], contraindications: ['contraindication:test'],
  provenance: [{ label: 'Source', value: 'typed-evidence-v1' }],
  clinician_action: { available: false, audit_required: true, label: 'Validation praticien', reason: 'Action indisponible sans preuve backend résolue.' },
  ...overrides,
});
const snapshot = {
  contract_version: 'R15_CLINICAL_STUDIO_VIEW_V1', patient_id: 915, analysis_id: 9915, evidence_graph_present: true,
  active_runtime_chain_verified: true, blocking_gate_count: 4, blocking_gates: ['r11_authoritative_snapshot_not_persisted'],
  clinical_validation_available: false, clinical_validation_reason: 'Aucune validation clinique sans preuve backend.',
  stages: [
    stage({ stage_id: 'R11', title: 'Diagnostic scientifique' }),
    stage({ stage_id: 'R12', title: 'Problem list & objectifs', blocking_gates: ['r11_not_authoritative'] }),
    stage({ stage_id: 'R13', title: 'Options thérapeutiques', presentation_state: 'EVALUABLE', blocking_gates: ['clinician_selection_required'], clinician_action: { available: false, audit_required: true, label: 'Sélection praticien', reason: 'La sélection reste indisponible tant que le backend ne persiste pas la preuve exacte.' } }),
    stage({ stage_id: 'R14', title: 'Validation clinique finale', blocking_gates: ['r14_authoritative_snapshot_not_persisted'] }),
  ],
};

describe('ClinicalScientificStudio client copy', () => {
  beforeEach(() => vi.clearAllMocks());

  it('keeps the clinical flow while hiding internal implementation vocabulary', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: snapshot } as never);
    render(<ClinicalScientificStudio patientId={915} analysisId={9915} P={PALETTE.dark} />);

    await screen.findByText('Parcours clinique');
    expect(api.get).toHaveBeenCalledWith('/patients/915/cephalo-clinical-studio?analysis_id=9915');
    expect(screen.getByText('Diagnostic → décision clinique')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Diagnostic —/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Objectifs —/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Options —/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Validation —/i })).toBeInTheDocument();
    expect(screen.getByTestId('r15-stage-rail')).toHaveClass('grid-cols-4');

    fireEvent.click(screen.getByRole('button', { name: /Options —/i }));
    expect(screen.getAllByText('À évaluer').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Sélection explicite du praticien requise')).toBeInTheDocument();
    expect(screen.getByText('Aucune validation disponible')).toBeInTheDocument();
    expect(screen.getByText('Données manquantes')).toBeInTheDocument();
    expect(screen.getByText('Contradictions')).toBeInTheDocument();
    expect(screen.getByText('Contre-indications')).toBeInTheDocument();
    expect(screen.queryByText(/R1[1-4]|snapshot|backend|runtime|gate|réf\. technique|contrat/i)).not.toBeInTheDocument();
    expect(screen.queryByText('clinician_selection_required')).not.toBeInTheDocument();
    expect(screen.queryByText('measurement:missing')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /valider|accepter|sélectionner/i })).not.toBeInTheDocument();
  });

  it('shows a client-safe unavailable state when clinical data cannot be loaded', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('offline'));
    render(<ClinicalScientificStudio patientId={915} analysisId={9915} P={PALETTE.dark} />);
    expect(await screen.findByText('Validation indisponible')).toBeInTheDocument();
    expect(screen.getByText(/aucune validation n'est autorisée/i)).toBeInTheDocument();
    expect(screen.queryByText(/fail-closed|backend|snapshot/i)).not.toBeInTheDocument();
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/patients/915/cephalo-clinical-studio?analysis_id=9915'));
  });

  it('falls back to the latest patient analysis only when no analysis is selected', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: snapshot } as never);
    render(<ClinicalScientificStudio patientId={915} P={PALETTE.dark} />);
    await screen.findByText('Parcours clinique');
    expect(api.get).toHaveBeenCalledWith('/patients/915/cephalo-clinical-studio');
  });
});
