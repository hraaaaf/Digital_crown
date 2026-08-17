import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import TreatmentPlanStudio, { buildTreatmentPlanSafetyWarnings } from './TreatmentPlanStudio';

const mocks = vi.hoisted(() => ({
  get: vi.fn(),
}));

vi.mock('../../../services/api', () => ({
  api: { get: mocks.get },
}));

vi.mock('../Settings/hooks/useSettingsStore', () => ({
  useSettingsStore: () => ({ profile: { clinical_tips_enabled: false } }),
}));

describe('P7-A TreatmentPlanStudio safety boundary', () => {
  beforeEach(() => {
    mocks.get.mockReset();
    mocks.get.mockResolvedValue({ data: { antecedents_medicaux: '' } });
  });

  it('signals medication context without substituting the proposed therapy', () => {
    const acts = ['Antibiothérapie et antalgiques', 'Ouverture camérale'];
    const warnings = buildTreatmentPlanSafetyWarnings('Allergie pénicilline connue', acts);

    expect(warnings).toHaveLength(1);
    expect(warnings[0]).toMatch(/aucune substitution thérapeutique automatique/i);
    expect(acts).toEqual(['Antibiothérapie et antalgiques', 'Ouverture camérale']);
    expect(warnings.join(' ')).not.toMatch(/clindamycine|macrolide/i);
  });

  it('signals AINS context without proposing corticosteroid substitution', () => {
    const warnings = buildTreatmentPlanSafetyWarnings(
      'Allergie aux AINS',
      ['Antibiothérapie et anti-inflammatoires stéroïdiens'],
    );

    expect(warnings).toHaveLength(1);
    expect(warnings[0]).toMatch(/aucune substitution thérapeutique automatique/i);
    expect(warnings.join(' ')).not.toMatch(/corticostéro/i);
  });

  it('resets diagnosis and proposed plan when patientId changes', async () => {
    const { rerender } = render(<TreatmentPlanStudio patientId={1} />);

    await waitFor(() => expect(mocks.get).toHaveBeenCalledWith('/patients/1'));

    fireEvent.click(screen.getByRole('button', { name: 'Contrôle de routine / Tartre' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Visite de contrôle annuelle' })).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Visite de contrôle annuelle' }));
    await waitFor(() => expect(screen.getByText('Hypothèse à confirmer')).toBeInTheDocument());
    expect(screen.getByText('Bilan bucco-dentaire de routine')).toBeInTheDocument();

    rerender(<TreatmentPlanStudio patientId={2} />);

    await waitFor(() => expect(mocks.get).toHaveBeenCalledWith('/patients/2'));
    expect(screen.queryByText('Hypothèse à confirmer')).not.toBeInTheDocument();
    expect(screen.queryByText('Bilan bucco-dentaire de routine')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Urgence / Douleur aiguë' })).toBeInTheDocument();
  });
});