import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { useState } from 'react';
import type { DrugItem } from './prescriptionTypes';
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

describe('PrescriptionAgenticStudio practitioner copy', () => {
  it('conserve les statuts internes sans afficher les bandeaux techniques', () => {
    const { container } = render(
      <PrescriptionAgenticStudio
        patientId=""
        drugs={[
          { id: 1, name: 'MEDICAMENT TEST', dosage: '1 G', forme: 'COMPRIME', posologie: '', type: 'MEDICAMENT' },
          { id: 2, name: '', dosage: '', forme: '', posologie: '', type: 'MEDICAMENT' },
        ]}
        setDrugs={vi.fn()}
        prescriptionIndication="Contexte documenté"
        onPrescriptionIndicationChange={vi.fn()}
        onUpdateDrug={vi.fn()}
        onRemoveDrug={vi.fn()}
        onAddDrug={vi.fn()}
        validationErrors={[]}
      />,
    );

    expect(screen.getByText(/Recherche médicament → présentation → validation/)).toBeInTheDocument();
    expect(screen.getByText('1 ligne renseignée')).toBeInTheDocument();
    expect(screen.getByLabelText('Indication de cette ordonnance')).toHaveValue('Contexte documenté');
    expect(screen.queryByText(/Suggestion clinique bloquée/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Contrôle clinique automatique bloqué/i)).not.toBeInTheDocument();

    const studio = container.querySelector('[data-prescription-intelligence-studio="v1"]');
    expect(studio).toHaveAttribute('data-clinical-rule-status', 'blocked');
    expect(studio).toHaveAttribute('data-safety-status', 'blocked');
  });

  it('ouvre réellement le sélecteur manuel de forme et applique le choix explicite', () => {
    const Harness = () => {
      const [drugs, setDrugs] = useState<DrugItem[]>([
        { id: 1, name: 'MEDICAMENT TEST', dosage: '', forme: '', posologie: '', type: 'MEDICAMENT' as const },
      ]);
      return (
        <PrescriptionAgenticStudio
          patientId=""
          drugs={drugs}
          setDrugs={setDrugs}
          prescriptionIndication=""
          onPrescriptionIndicationChange={vi.fn()}
          onUpdateDrug={(id, field, value) => setDrugs(current => current.map(drug => (
            drug.id === id ? { ...drug, [field]: value } : drug
          )))}
          onRemoveDrug={vi.fn()}
          onAddDrug={vi.fn()}
          validationErrors={[]}
        />
      );
    };

    render(<Harness />);
    const trigger = screen.getByTitle('Choisir la forme manuellement');
    fireEvent.click(trigger);

    expect(screen.getByRole('menu', { name: 'Choisir la forme' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('menuitemradio', { name: 'COMPRIMÉS' }));
    expect(screen.queryByRole('menu', { name: 'Choisir la forme' })).not.toBeInTheDocument();
    expect(screen.getByTitle('Choisir la forme manuellement')).toHaveTextContent('COMPRIMÉS');
  });

});
