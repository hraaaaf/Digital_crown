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
  it('retire les automatismes prescriptifs legacy du chemin actif', () => {
    render(
      <PrescriptionAgenticStudio
        patientId=""
        drugs={[]}
        setDrugs={vi.fn()}
        onUpdateDrug={vi.fn()}
        onRemoveDrug={vi.fn()}
        onAddDrug={vi.fn()}
        validationErrors={[]}
      />,
    );

    expect(screen.getByText('Prescription Intelligence V1')).toBeInTheDocument();
    expect(screen.getByText(/Suggestion clinique bloquée/)).toBeInTheDocument();
    expect(screen.queryByText(/Protocoles Cliniques/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Saisie rapide/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Établir l'Ordonnance/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Mes protocoles/i })).not.toBeInTheDocument();
  });
});
