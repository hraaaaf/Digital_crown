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
  it('affiche uniquement l alerte générique fournie par le backend caché', async () => {
    const { api } = await import('../../../../services/api');
    vi.mocked(api.get).mockResolvedValueOnce({
      data: {
        status: 'SPECIALIST_REVIEW_REQUIRED',
        alert_key: 'SPECIALIST_REVIEW_RECOMMENDED',
        read_only: true,
      },
    } as any);

    render(
      <PrescriptionAgenticStudio
        patientId="42"
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

    expect(await screen.findByText('Avis spécialisé recommandé.')).toBeInTheDocument();
    expect(screen.queryByText(/MRONJ|endocard|anticoag|CTX|drug holiday|bisphosph|denosumab/i)).not.toBeInTheDocument();
  });


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

    expect(screen.getByText('Ordonnance')).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: 'Ajouter un médicament ou un protocole' })).toBeInTheDocument();
    expect(screen.getByText('1 ligne renseignée')).toBeInTheDocument();
    expect(screen.getByLabelText('Indication de cette ordonnance')).toHaveValue('Contexte documenté');
    expect(screen.queryByText(/Suggestion clinique bloquée/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Contrôle clinique automatique bloqué/i)).not.toBeInTheDocument();
    expect(screen.queryByText('Contexte patient')).not.toBeInTheDocument();
    expect(screen.queryByText('Prévention endocardite')).not.toBeInTheDocument();

    const studio = container.querySelector('[data-prescription-intelligence-studio="v1"]');
    expect(studio).toHaveAttribute('data-clinical-rule-status', 'blocked');
    expect(studio).toHaveAttribute('data-safety-status', 'blocked');
    expect(studio).toHaveAttribute('data-safety-mechanics', 'background-only');
  });

  it('ouvre le choix contextuel de forme et conserve le chemin de modification manuelle', () => {
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
    const trigger = screen.getByRole('button', { name: 'Forme' });
    fireEvent.click(trigger);

    expect(screen.getByRole('menu')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('menuitem', { name: /COMPRIMÉS/i }));
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Forme' })).toHaveTextContent('COMPRIMÉS');

    fireEvent.click(screen.getByRole('button', { name: 'Forme' }));
    expect(screen.getByRole('menuitem', { name: /Modifier manuellement/i })).toBeInTheDocument();
  });

});
