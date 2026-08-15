import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

vi.mock('./PrescriptionAgenticStudioLegacy', () => ({
  PrescriptionAgenticStudio: () => <div>legacy studio</div>,
}));

vi.mock('../../../../services/api', () => ({
  api: {
    post: vi.fn(async () => ({ data: [] })),
    interceptors: {
      request: { use: vi.fn(() => 1), eject: vi.fn() },
      response: { use: vi.fn(() => 2), eject: vi.fn() },
    },
  },
}));

import { PrescriptionAgenticStudio } from './PrescriptionAgenticStudio';

describe('PrescriptionAgenticStudio R7 context terminology', () => {
  it('présente un contexte patient déterministe et compte les lignes renseignées', () => {
    render(
      <PrescriptionAgenticStudio
        patientId=""
        drugs={[
          { id: 1, name: 'AMOXICILLINE', dosage: '1G', forme: 'COMPRIMÉS', posologie: '2x/j', type: 'MEDICAMENT' },
          { id: 2, name: '', dosage: '', forme: '', posologie: '', type: 'MEDICAMENT' },
        ]}
        setDrugs={vi.fn()}
        onUpdateDrug={vi.fn()}
        onRemoveDrug={vi.fn()}
        onAddDrug={vi.fn()}
        validationErrors={[]}
      />,
    );

    expect(screen.getByText('Contexte patient')).toBeInTheDocument();
    expect(screen.getByText(/Données du dossier et vérifications déterministes/)).toBeInTheDocument();
    expect(screen.getByText('1 ligne renseignée')).toBeInTheDocument();
  });
});
