import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

vi.mock('../../../../services/api', () => ({
  api: {
    get: vi.fn(async () => ({ data: [] })),
    post: vi.fn(async () => ({ data: [] })),
    interceptors: {
      request: { use: vi.fn(() => 1), eject: vi.fn() },
      response: { use: vi.fn(() => 2), eject: vi.fn() },
    },
  },
}));

import { PrescriptionAgenticStudio } from './PrescriptionAgenticStudio';

describe('PrescriptionAgenticStudio V1 — isolation legacy', () => {
  it('retire les automatismes prescriptifs legacy du chemin actif sans exposer le jargon interne', () => {
    render(
      <PrescriptionAgenticStudio
        patientId=""
        drugs={[]}
        setDrugs={vi.fn()}
        prescriptionIndication=""
        onPrescriptionIndicationChange={vi.fn()}
        onUpdateDrug={vi.fn()}
        onRemoveDrug={vi.fn()}
        onAddDrug={vi.fn()}
        validationErrors={[]}
      />,
    );

    expect(screen.getByText('Prescription')).toBeInTheDocument();
    expect(screen.getByText('Recherche médicament → présentation → validation')).toBeInTheDocument();
    expect(screen.queryByText(/Suggestion clinique bloquée/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Contrôle clinique automatique bloqué/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Prescription Intelligence V1/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Protocoles Cliniques/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Saisie rapide/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Établir l'Ordonnance/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Mes protocoles/i })).not.toBeInTheDocument();
  });
});
