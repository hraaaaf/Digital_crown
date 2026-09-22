import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { api } from '../../../../services/api';
import { PrescriptionPresetBar } from './PrescriptionPresetBar';

vi.mock('../../../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

const currentDrug = {
  id: 1,
  name: 'PARACETAMOL',
  dosage: '1g',
  forme: 'Comprimés',
  posologie: '1 cp si douleur',
  type: 'MEDICAMENT',
  quantite: 1,
  non_substituable: false,
};

describe('CUST-04 practitioner prescription presets', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads doctor presets and applies them only after an explicit click', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: [{
        id: 7,
        act_context: 'Post-op personnel',
        drugs: [{
          name: 'IBUPROFENE',
          dosage: '400mg',
          forme: 'Comprimés',
          posologie: '1 cp après repas',
          type: 'MEDICAMENT',
          quantite: 2,
          non_substituable: true,
        }],
      }],
    } as never);

    const setDrugs = vi.fn();
    render(<PrescriptionPresetBar drugs={[]} setDrugs={setDrugs} />);

    expect(setDrugs).not.toHaveBeenCalled();
    fireEvent.click(await screen.findByRole('button', { name: /Post-op personnel/i }));

    expect(setDrugs).toHaveBeenCalledTimes(1);
    expect(setDrugs.mock.calls[0][0][0]).toMatchObject({
      name: 'IBUPROFENE',
      dosage: '400mg',
      forme: 'Comprimés',
      posologie: '1 cp après repas',
      type: 'MEDICAMENT',
      quantite: 2,
      non_substituable: true,
    });
  });

  it('does not overwrite an existing prescription unless replacement is confirmed', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: [{
        id: 8,
        act_context: 'Autre preset',
        drugs: [{
          name: 'AMOXICILLINE',
          dosage: '1g',
          forme: 'Gélules',
          posologie: '1 matin et soir',
          type: 'MEDICAMENT',
        }],
      }],
    } as never);

    const setDrugs = vi.fn();
    render(<PrescriptionPresetBar drugs={[currentDrug] as never} setDrugs={setDrugs} />);

    fireEvent.click(await screen.findByRole('button', { name: /Autre preset/i }));
    expect(await screen.findByRole('dialog', { name: /Remplacer les lignes actuelles/i })).toBeTruthy();
    expect(setDrugs).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: /Conserver mon brouillon/i }));
    expect(setDrugs).not.toHaveBeenCalled();
  });

  it('saves only reusable prescription-line fields under the explicit practitioner name', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] } as never);
    vi.mocked(api.post).mockResolvedValue({ data: { status: 'success' } } as never);

    render(<PrescriptionPresetBar drugs={[currentDrug] as never} setDrugs={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: /Enregistrer ce brouillon/i }));
    fireEvent.change(screen.getByRole('textbox', { name: /Nom du preset/i }), {
      target: { value: 'Mon post-op' },
    });
    fireEvent.click(screen.getByRole('button', { name: /^Enregistrer$/i }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/prescriptions/preferences', {
      act_code: 'Mon post-op',
      drugs: [{
        name: 'PARACETAMOL',
        dosage: '1g',
        forme: 'Comprimés',
        posologie: '1 cp si douleur',
        type: 'MEDICAMENT',
        quantite: 1,
        non_substituable: false,
      }],
    }));
  });

  it('deletes only the selected doctor preset through the scoped endpoint', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: [{ id: 9, act_context: 'Preset test', drugs: [currentDrug] }],
    } as never);
    vi.mocked(api.delete).mockResolvedValue({ data: { status: 'success' } } as never);

    render(<PrescriptionPresetBar drugs={[]} setDrugs={vi.fn()} />);

    fireEvent.click(await screen.findByRole('button', { name: /Supprimer le preset Preset test/i }));

    await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/prescriptions/preferences/Preset%20test'));
  });
});
