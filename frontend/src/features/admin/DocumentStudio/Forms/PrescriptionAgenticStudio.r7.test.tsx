import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

vi.mock('../../../../services/api', () => ({
  api: {
    get: vi.fn(async () => ({ data: [] })),
    put: vi.fn(async () => ({ data: [] })),
    post: vi.fn(async () => ({ data: [] })),
    interceptors: {
      request: { use: vi.fn(() => 1), eject: vi.fn() },
      response: { use: vi.fn(() => 2), eject: vi.fn() },
    },
  },
}));

import { PrescriptionAgenticStudio } from './PrescriptionAgenticStudio';

describe('PrescriptionAgenticStudio V1 context terminology', () => {
  it('présente le contexte structuré et l indication du document sans activer de suggestion clinique', () => {
    render(
      <PrescriptionAgenticStudio
        patientId=""
        drugs={[
          {
            id: 1,
            name: 'AMOXICILLINE TEST',
            dosage: '1 G',
            forme: 'COMPRIME',
            posologie: '',
            type: 'MEDICAMENT',
            catalogPresentationId: 'cnops:test',
            catalogDci: 'AMOXICILLINE',
            catalogSourceId: 'cnops-open-data-medications',
            catalogSourceLabel: 'CNOPS Open Data — Référentiel des médicaments',
            catalogSnapshotDate: '2021-12-13',
            catalogMarketingStatusVerified: false,
          },
          { id: 2, name: '', dosage: '', forme: '', posologie: '', type: 'MEDICAMENT' },
        ]}
        setDrugs={vi.fn()}
        prescriptionIndication="Infection odontogène documentée"
        onPrescriptionIndicationChange={vi.fn()}
        onUpdateDrug={vi.fn()}
        onRemoveDrug={vi.fn()}
        onAddDrug={vi.fn()}
        validationErrors={[]}
      />,
    );

    expect(screen.getByText(/Recherche documentaire → présentation explicite → validation praticien/)).toBeInTheDocument();
    expect(screen.getByText('1 ligne renseignée')).toBeInTheDocument();
    expect(screen.getByText(/Contexte clinique structuré/)).toBeInTheDocument();
    expect(screen.getByLabelText('Indication de cette ordonnance')).toHaveValue('Infection odontogène documentée');
    expect(screen.getByText(/enregistrée avec l’ordonnance, pas dans les faits durables du patient/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Suggestion clinique/).length).toBeGreaterThan(0);
    expect(screen.getByText(/aucune règle de dose V1 n’est certifiée ni activée/i)).toBeInTheDocument();
  });
});
