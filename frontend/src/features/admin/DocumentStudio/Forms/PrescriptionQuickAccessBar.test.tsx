import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

import { api } from '../../../../services/api';
import { PrescriptionQuickAccessBar } from './PrescriptionQuickAccessBar';

vi.mock('../../../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

const emptyLine = {
  id: 1,
  name: '',
  dosage: '',
  forme: '',
  posologie: '',
  type: 'MEDICAMENT' as const,
};

describe('Neo prescription quick access', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url.includes('/habits/presets')) return { data: [{
        id: 7,
        act_context: 'EXTRACTION SIMPLE',
        label: 'Extraction simple',
        kind: 'PROTOCOL',
        drugs: [
          {
            name: 'MED A',
            dosage: '1',
            forme: 'COMPRIME',
            posologie: '1 comprimé matin et soir pendant 7 jours',
            type: 'MEDICAMENT',
            quantite: 2,
            non_substituable: true,
            catalogPresentationId: 'ammps:med-a',
            catalogDci: 'MED A DCI',
            catalogSourceId: 'ammps-current',
            catalogMarketingStatusVerified: true,
          },
          { name: 'RADIO PANORAMIQUE', dosage: '', forme: '', posologie: '', type: 'EXAMEN', quantite: 1 },
        ],
        is_favorite: true,
        usage_count: 3,
        last_used: '2026-09-30T20:00:00',
      }] } as never;
      if (url.includes('/habits/suggest')) return { data: {
        recent_medications: ['DOLIPRANE'],
        frequent_medications: ['AMOXICILLINE'],
      } } as never;
      if (url.includes('/medications/neo/search')) return { data: [{
        presentation_id: 'p1',
        nom: 'DOLIPRANE',
        dci: 'PARACETAMOL',
        dosage: '1',
        unite: 'G',
        forme: 'COMPRIMES',
        source: { id: 'ammps-x', current_marketing_status_verified: true },
      }] } as never;
      return { data: [] } as never;
    });
    vi.mocked(api.post).mockResolvedValue({ data: { status: 'success' } } as never);
    vi.mocked(api.put).mockResolvedValue({ data: { status: 'success' } } as never);
  });

  it('inserts a protocol as editable prescription lines and records its use', async () => {
    const setDrugs = vi.fn();
    render(<PrescriptionQuickAccessBar drugs={[emptyLine]} setDrugs={setDrugs} prescriptionIndication="" />);

    fireEvent.click(await screen.findByRole('button', { name: 'Extraction simple' }));

    expect(setDrugs).toHaveBeenCalledTimes(1);
    expect(setDrugs.mock.calls[0][0]).toMatchObject([
      {
        name: 'MED A',
        dosage: '1',
        forme: 'COMPRIME',
        posologie: '1 comprimé matin et soir pendant 7 jours',
        type: 'MEDICAMENT',
        quantite: 2,
        non_substituable: true,
        catalogPresentationId: 'ammps:med-a',
        catalogDci: 'MED A DCI',
      },
      {
        name: 'RADIO PANORAMIQUE',
        type: 'EXAMEN',
        quantite: 1,
      },
    ]);
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/prescriptions/preferences/7/use'));
  });

  it('shows recent and frequent medication quick picks', async () => {
    render(<PrescriptionQuickAccessBar drugs={[emptyLine]} setDrugs={vi.fn()} prescriptionIndication="" />);
    await screen.findByRole('button', { name: 'Extraction simple' });

    fireEvent.click(screen.getByRole('tab', { name: 'Récentes' }));
    expect(screen.getByRole('button', { name: /DOLIPRANE/ })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('tab', { name: 'Fréquentes' }));
    expect(screen.getByRole('button', { name: /AMOXICILLINE/ })).toBeInTheDocument();
  });

  it('lets the practitioner update the explicitly applied protocol source', async () => {
    const Harness = () => {
      const [drugs, setDrugs] = React.useState<import('./prescriptionTypes').DrugItem[]>([emptyLine]);
      return <PrescriptionQuickAccessBar drugs={drugs} setDrugs={setDrugs} prescriptionIndication="" />;
    };
    render(<Harness />);
    fireEvent.click(await screen.findByRole('button', { name: 'Extraction simple' }));

    fireEvent.click(screen.getByRole('button', { name: 'Actions ordonnance' }));
    fireEvent.click(screen.getByRole('button', { name: /Mettre à jour « Extraction simple »/i }));
    expect(screen.getByRole('textbox', { name: 'Nom' })).toHaveValue('Extraction simple');
  });

  it('can favorite a reusable item without changing prescription lines', async () => {
    const setDrugs = vi.fn();
    render(<PrescriptionQuickAccessBar drugs={[emptyLine]} setDrugs={setDrugs} prescriptionIndication="" />);
    const star = await screen.findByRole('button', { name: /Retirer Extraction simple des favoris/i });
    fireEvent.click(star);
    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/prescriptions/preferences/7/favorite', { is_favorite: false }));
    expect(setDrugs).not.toHaveBeenCalled();
  });

  it('restores the indication when applying a saved prescription', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url.includes('/habits/presets')) return { data: [{
        id: 9,
        act_context: 'POST OP SAVED',
        label: 'Post-op sauvegardée',
        kind: 'SAVED_PRESCRIPTION',
        indication: 'Douleur postopératoire',
        drugs: [{ name: 'MED X', dosage: '1', forme: 'COMPRIME', posologie: 'x' }],
        is_favorite: false,
        usage_count: 1,
        last_used: '2026-09-30T21:00:00',
      }] } as never;
      if (url.includes('/habits/suggest')) return { data: {} } as never;
      return { data: [] } as never;
    });
    const setIndication = vi.fn();
    render(
      <PrescriptionQuickAccessBar
        drugs={[emptyLine]}
        setDrugs={vi.fn()}
        prescriptionIndication=""
        onPrescriptionIndicationChange={setIndication}
      />,
    );

    fireEvent.click(await screen.findByRole('tab', { name: 'Ordonnances' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Post-op sauvegardée' }));
    expect(setIndication).toHaveBeenCalledWith('Douleur postopératoire');
  });

  it('prioritizes a medication presentation over a homonymous reusable on Enter', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url.includes('/habits/presets')) return { data: [{
        id: 10,
        act_context: 'DOL PROTOCOLE',
        label: 'Dol protocole',
        kind: 'PROTOCOL',
        drugs: [{ name: 'PROTO', dosage: '', forme: '', posologie: '' }],
        is_favorite: false,
        usage_count: 0,
        last_used: null,
      }] } as never;
      if (url.includes('/habits/suggest')) return { data: {} } as never;
      if (url.includes('/medications/neo/search')) return { data: [{
        presentation_id: 'dol-1',
        nom: 'DOLIPRANE',
        dci: 'PARACETAMOL',
        dosage: '1',
        unite: 'G',
        forme: 'COMPRIMES',
        source: { id: 'ammps-x', current_marketing_status_verified: true },
      }] } as never;
      return { data: [] } as never;
    });
    const setDrugs = vi.fn();
    render(<PrescriptionQuickAccessBar drugs={[emptyLine]} setDrugs={setDrugs} prescriptionIndication="" />);

    const input = screen.getByRole('textbox', { name: 'Ajouter un médicament ou un protocole' });
    fireEvent.change(input, { target: { value: 'dol' } });
    await screen.findByText('DOLIPRANE');
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(setDrugs).toHaveBeenCalled();
    expect(setDrugs.mock.calls[0][0][0]).toMatchObject({
      name: 'DOLIPRANE',
      catalogPresentationId: 'dol-1',
    });
  });

  it('saves the current draft explicitly as a protocol', async () => {
    const current = [{
      ...emptyLine,
      name: 'MED TEST',
      dosage: '1G',
      posologie: 'x',
      catalogPresentationId: 'ammps:save-1',
      catalogDci: 'MED TEST DCI',
      catalogSourceId: 'ammps-current',
      catalogMarketingStatusVerified: true,
    }];
    render(<PrescriptionQuickAccessBar drugs={current} setDrugs={vi.fn()} prescriptionIndication="Test" />);
    await screen.findByRole('button', { name: 'Extraction simple' });

    fireEvent.click(screen.getByRole('button', { name: 'Actions ordonnance' }));
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer comme protocole/i }));
    fireEvent.change(screen.getByRole('textbox', { name: 'Nom' }), { target: { value: 'Mon protocole' } });
    fireEvent.click(screen.getByRole('button', { name: /^Enregistrer$/ }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/prescriptions/preferences', expect.objectContaining({
      act_code: 'Mon protocole',
      label: 'Mon protocole',
      kind: 'PROTOCOL',
      indication: null,
      drugs: [expect.objectContaining({
        catalogPresentationId: 'ammps:save-1',
        catalogDci: 'MED TEST DCI',
        catalogSourceId: 'ammps-current',
        catalogMarketingStatusVerified: true,
      })],
    })));
  });
});
