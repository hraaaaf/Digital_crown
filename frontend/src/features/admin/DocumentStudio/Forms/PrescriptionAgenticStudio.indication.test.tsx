import { render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

let requestHandler: ((config: any) => any) | undefined;

vi.mock('../../../../services/api', () => ({
  api: {
    get: vi.fn(async () => ({ data: [] })),
    put: vi.fn(async () => ({ data: [] })),
    interceptors: {
      request: {
        use: vi.fn((handler: (config: any) => any) => {
          requestHandler = handler;
          return 1;
        }),
        eject: vi.fn(),
      },
      response: { use: vi.fn(() => 2), eject: vi.fn() },
    },
  },
}));

import { PrescriptionAgenticStudio } from './PrescriptionAgenticStudio';

const drug = {
  id: 1,
  name: 'MEDICAMENT TEST',
  dosage: '500 MG',
  forme: 'COMPRIME',
  posologie: 'Saisie praticien',
  type: 'MEDICAMENT' as const,
};

function renderStudio(indication = 'Infection odontogène documentée') {
  render(
    <PrescriptionAgenticStudio
      patientId=""
      drugs={[drug]}
      setDrugs={vi.fn()}
      prescriptionIndication={indication}
      onPrescriptionIndicationChange={vi.fn()}
      onUpdateDrug={vi.fn()}
      onRemoveDrug={vi.fn()}
      onAddDrug={vi.fn()}
      validationErrors={[]}
    />,
  );
}

describe('PrescriptionAgenticStudio V1 — indication document-scoped', () => {
  it('injecte l indication uniquement dans le payload ordonnance', () => {
    requestHandler = undefined;
    renderStudio();
    expect(requestHandler).toBeTypeOf('function');

    const ordonnanceConfig = requestHandler!({
      url: '/documents/generate?archive=true',
      data: {
        type: 'ordonnance',
        data: { medications: [{ nom: 'MEDICAMENT TEST', forme: 'COMPRIME' }] },
      },
    });
    expect(ordonnanceConfig.data.data.indication).toBe('Infection odontogène documentée');

    const certificatConfig = requestHandler!({
      url: '/documents/generate?archive=true',
      data: { type: 'certificat', data: { reason: 'test' } },
    });
    expect(certificatConfig.data.data.indication).toBeUndefined();
  });

  it('normalise une indication vide à null sans fabriquer de contexte', () => {
    requestHandler = undefined;
    renderStudio('   ');

    const config = requestHandler!({
      url: '/documents/generate?preview=true',
      data: { type: 'ordonnance', data: { medications: [] } },
    });
    expect(config.data.data.indication).toBeNull();
  });
});
