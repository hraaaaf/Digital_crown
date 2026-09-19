import React from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProfileTab } from './ProfileTab';

const state = vi.hoisted(() => ({
  user: { id: 1, role: 'ADMIN', employer_id: null as number | null, is_superadmin: false } as any,
  profile: {
    nom: 'Achraf Benmoussa',
    nom_cabinet: 'Cabinet Test',
    nom_praticien_ar: '',
    adresse: 'Rabat',
    telephone: '',
    inpe: 'INPE1',
    inpe_etablissement: '',
    ice: '',
    if: '',
    cabinet_type: 'PRIVE',
    specialty_ids: [] as string[],
    custom_specialty_fr: '',
    custom_specialty_ar: '',
    header_customized: false,
    header_lines_fr: ['Dr. Achraf Benmoussa','Chirurgien Dentiste'],
    header_lines_ar: [],
    logo_path: '',
  } as any,
  contacts: {
    fixe: { enabled: true, value: '0537000000' },
    mobile: { enabled: false, value: '' },
    whatsapp: { enabled: false, value: '' },
    instagram: { enabled: false, value: '' },
  } as any,
  updateProfile: vi.fn(),
  saveProfile: vi.fn(),
  toggleContact: vi.fn(),
  updateContactValue: vi.fn(),
  uploadLogo: vi.fn(),
  deleteLogo: vi.fn(),
}));

vi.mock('../hooks/useSettingsStore', () => ({
  useSettingsStore: () => state,
}));

vi.mock('../../../../stores/useAuthStore', () => ({
  useAuthStore: (selector: any) => selector({ user: state.user }),
}));

vi.mock('../../../../hooks/useAuthenticatedImage', () => ({
  useAuthenticatedImage: () => '',
}));

vi.mock('../../constants', () => ({
  SPECIALTIES_DICT: [{
    id: 'ortho',
    fr: 'Orthodontie',
    ar: 'تقويم الأسنان',
    icon: (props: any) => React.createElement('span', props, 'O'),
  }],
}));

vi.mock('../components/ArabicKeyboard', () => ({
  ArabicKeyboard: () => <div>Arabic keyboard</div>,
}));

vi.mock('../../../../services/api', () => ({
  API_BASE: 'http://local.test',
}));

beforeEach(() => {
  vi.clearAllMocks();
  state.user = { id: 1, role: 'ADMIN', employer_id: null, is_superadmin: false };
  state.profile = {
    nom: 'Achraf Benmoussa',
    nom_cabinet: 'Cabinet Test',
    nom_praticien_ar: '',
    adresse: 'Rabat',
    telephone: '',
    inpe: 'INPE1',
    inpe_etablissement: '',
    ice: '',
    if: '',
    cabinet_type: 'PRIVE',
    specialty_ids: [],
    custom_specialty_fr: '',
    custom_specialty_ar: '',
    header_customized: false,
    header_lines_fr: ['Dr. Achraf Benmoussa','Chirurgien Dentiste'],
    header_lines_ar: [],
    logo_path: '',
  };
  state.contacts = {
    fixe: { enabled: true, value: '0537000000' },
    mobile: { enabled: false, value: '' },
    whatsapp: { enabled: false, value: '' },
    instagram: { enabled: false, value: '' },
  };
  state.saveProfile.mockResolvedValue(undefined);
  state.uploadLogo.mockResolvedValue(undefined);
  state.deleteLogo.mockResolvedValue(undefined);
});

afterEach(() => cleanup());

describe('ProfileTab G5 interactive matrix', () => {
  it('stages cabinet identity changes through updateProfile', () => {
    render(<ProfileTab />);

    const cabinet = screen.getByPlaceholderText('Ex: Cabinet Dentaire Benmoussa');
    fireEvent.change(cabinet, { target: { value: 'Clinique Crown' } });
    fireEvent.blur(cabinet);

    expect(state.updateProfile).toHaveBeenCalledWith({ nom_cabinet: 'Clinique Crown' });
  });

  it('stages specialty selection and regenerates non-customized header truth', () => {
    render(<ProfileTab />);
    fireEvent.click(screen.getByRole('button', { name: /Orthodontie/i }));

    expect(state.updateProfile).toHaveBeenCalledWith(expect.objectContaining({
      specialty_ids: ['ortho'],
      header_lines_fr: expect.arrayContaining(['Dr. Achraf Benmoussa', 'Chirurgien Dentiste', 'Orthodontie']),
    }));
  });

  it('toggles and edits footer contacts through staged store controls', () => {
    render(<ProfileTab />);

    fireEvent.click(screen.getByRole('button', { name: 'Activer WhatsApp' }));
    expect(state.toggleContact).toHaveBeenCalledWith('whatsapp');

    const fixe = screen.getByDisplayValue('0537000000');
    fireEvent.change(fixe, { target: { value: '0537111111' } });
    expect(state.updateContactValue).toHaveBeenCalledWith('fixe', '0537111111');
  });

  it('uploads a selected logo and deletes an existing logo only through explicit controls', async () => {
    state.profile.logo_path = 'logo.png';
    const { container } = render(<ProfileTab />);
    const file = new File(['logo'], 'logo.png', { type: 'image/png' });
    const input = container.querySelector('#logo-input') as HTMLInputElement;

    fireEvent.change(input, { target: { files: [file] } });
    await waitFor(() => expect(state.uploadLogo).toHaveBeenCalledWith(file));

    const deleteButton = screen.getByRole('button', { name: /Supprimer/i });
    fireEvent.click(deleteButton);
    expect(state.deleteLogo).toHaveBeenCalledTimes(1);
  });

  it('saves explicitly and does not signal saved state when save rejects', async () => {
    state.saveProfile.mockRejectedValueOnce(new Error('save refused'));
    render(<ProfileTab />);

    fireEvent.click(screen.getByRole('button', { name: 'Mettre à jour le profil' }));
    await waitFor(() => expect(state.saveProfile).toHaveBeenCalledTimes(1));
    expect(screen.queryByText('✓ Enregistré !')).toBeNull();
  });

  it('prevents an employee dentist from editing practitioner identity', () => {
    state.user = { id: 2, role: 'DENTISTE', employer_id: 1, is_superadmin: false };
    render(<ProfileTab />);

    const name = screen.getByPlaceholderText('Ex: Benmoussa Achraf') as HTMLInputElement;
    const inpe = screen.getByPlaceholderText('INPE du praticien') as HTMLInputElement;
    expect(name.disabled).toBe(true);
    expect(inpe.disabled).toBe(true);
  });
});
