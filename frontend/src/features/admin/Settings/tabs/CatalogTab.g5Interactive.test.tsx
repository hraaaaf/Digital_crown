import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CatalogTab } from './CatalogTab';

const state = vi.hoisted(() => ({
  loading: false,
  readError: null as string | null,
  specialties: [
    {
      id: 1,
      name: 'Soins',
      color: '#3B82F6',
      acts: [{ id: 10, name: 'Détartrage', code: 'DET', base_price: 500, color: '#60A5FA', is_active: true }],
      pathologies: [{ id: 20, name: 'Gingivite', description: 'Inflammation', is_active: true }],
    },
  ] as any[],
  fetchCatalog: vi.fn(),
  createSpecialty: vi.fn(),
  updateSpecialty: vi.fn(),
  createAct: vi.fn(),
  updateAct: vi.fn(),
  createPathology: vi.fn(),
  updatePathology: vi.fn(),
}));

vi.mock('../hooks/useCatalogStore', () => ({
  useCatalogStore: () => state,
  normalizeCatalogActApplicability: (value:any = {}) => ({
    dentitions: [],
    tooth_types: [],
    treatment_areas: [],
    selection_modes: [],
    requires_present_tooth: false,
    requires_missing_tooth: false,
    min_selected_teeth: 0,
    max_selected_teeth: null,
    suggestion_priority: 0,
    searchable_when_not_suggested: true,
    ...value,
    dentitions: [...(value.dentitions || [])],
    tooth_types: [...(value.tooth_types || [])],
    treatment_areas: [...(value.treatment_areas || [])],
    selection_modes: [...(value.selection_modes || [])],
  }),
}));

beforeEach(() => {
  vi.clearAllMocks();
  state.loading = false;
  state.readError = null;
  state.specialties = [{
    id: 1,
    name: 'Soins',
    color: '#3B82F6',
    acts: [{ id: 10, name: 'Détartrage', code: 'DET', base_price: 500, color: '#60A5FA', is_active: true }],
    pathologies: [{ id: 20, name: 'Gingivite', description: 'Inflammation', is_active: true }],
  }];
  state.fetchCatalog.mockResolvedValue(undefined);
  state.createSpecialty.mockResolvedValue(true);
  state.updateSpecialty.mockResolvedValue(true);
  state.createAct.mockResolvedValue(true);
  state.updateAct.mockResolvedValue(true);
  state.createPathology.mockResolvedValue(true);
  state.updatePathology.mockResolvedValue(true);
});

afterEach(() => cleanup());

describe('CatalogTab G5 interactive matrix', () => {
  it('loads catalogue truth before exposing specialty contents', async () => {
    render(<CatalogTab />);
    await waitFor(() => expect(state.fetchCatalog).toHaveBeenCalledTimes(1));
    expect(screen.getAllByText('Soins').length).toBeGreaterThan(0);
    expect(screen.getByText('Détartrage')).toBeTruthy();
    expect(screen.getByText('Gingivite')).toBeTruthy();
  });

  it('creates a specialty only through explicit submit and normalized name', async () => {
    render(<CatalogTab />);
    fireEvent.click(screen.getByRole('button', { name: /Nouvelle spécialité/i }));

    fireEvent.change(screen.getByPlaceholderText('Ex. Orthodontie'), { target: { value: '  Orthodontie   Clinique ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Créer' }));

    await waitFor(() => expect(state.createSpecialty).toHaveBeenCalledWith({
      name: 'Orthodontie Clinique',
      color: '#3B82F6',
    }));
  });

  it('blocks an invalid negative act tariff before store mutation', async () => {
    render(<CatalogTab />);
    fireEvent.click(screen.getByRole('button', { name: /Ajouter un acte/i }));

    fireEvent.change(screen.getByPlaceholderText('Ex. Détartrage'), { target: { value: 'Consultation' } });
    fireEvent.change(screen.getByPlaceholderText('0'), { target: { value: '-20' } });
    fireEvent.click(screen.getByRole('button', { name: 'Créer' }));

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByText(/tarif doit être un nombre positif ou nul/i)).toBeTruthy();
    expect(state.createAct).not.toHaveBeenCalled();
  });

  it('creates an act with code, price and active state', async () => {
    render(<CatalogTab />);
    fireEvent.click(screen.getByRole('button', { name: /Ajouter un acte/i }));

    fireEvent.change(screen.getByPlaceholderText('Ex. Détartrage'), { target: { value: 'Consultation' } });
    fireEvent.change(screen.getByPlaceholderText('Ex. DET'), { target: { value: 'CONS' } });
    fireEvent.change(screen.getByPlaceholderText('0'), { target: { value: '350' } });
    fireEvent.click(screen.getByRole('button', { name: 'Créer' }));

    await waitFor(() => expect(state.createAct).toHaveBeenCalledWith(
      1,
      expect.objectContaining({ name: 'Consultation', code: 'CONS', base_price: 350, is_active: true }),
    ));
  });

  it('creates a modular primary-tooth act with editable applicability', async () => {
    render(<CatalogTab />);
    fireEvent.click(screen.getByRole('button', { name: /Ajouter un acte/i }));

    fireEvent.change(screen.getByPlaceholderText('Ex. Détartrage'), { target: { value: 'Acte pédiatrique custom' } });
    fireEvent.change(screen.getByPlaceholderText('0'), { target: { value: '420' } });
    fireEvent.click(screen.getByRole('button', { name: 'Temporaire' }));
    fireEvent.click(screen.getByRole('button', { name: 'Ciblé' }));
    fireEvent.change(screen.getByLabelText('Priorité suggestion'), { target: { value: '70' } });
    fireEvent.click(screen.getByRole('button', { name: 'Créer' }));

    await waitFor(() => expect(state.createAct).toHaveBeenCalledWith(
      1,
      expect.objectContaining({
        name: 'Acte pédiatrique custom',
        base_price: 420,
        applicability: expect.objectContaining({
          dentitions: ['PRIMARY'],
          selection_modes: ['INDIVIDUAL'],
          suggestion_priority: 70,
        }),
      }),
    ));
  });

  it('edits and deactivates an existing act without deleting history', async () => {
    render(<CatalogTab />);
    fireEvent.click(screen.getByRole('button', { name: "Modifier l'acte Détartrage" }));

    fireEvent.click(screen.getByRole('checkbox', { name: 'Actif' }));
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));

    await waitFor(() => expect(state.updateAct).toHaveBeenCalledWith(
      10,
      expect.objectContaining({ name: 'Détartrage', code: 'DET', base_price: 500, is_active: false }),
    ));
  });

  it('creates and edits pathologies through their explicit forms', async () => {
    render(<CatalogTab />);
    fireEvent.click(screen.getByRole('button', { name: /Ajouter une pathologie/i }));
    fireEvent.change(screen.getByPlaceholderText('Ex. Gingivite'), { target: { value: 'Parodontite' } });
    fireEvent.change(screen.getByPlaceholderText('Description facultative'), { target: { value: 'Atteinte parodontale' } });
    fireEvent.click(screen.getByRole('button', { name: 'Créer' }));

    await waitFor(() => expect(state.createPathology).toHaveBeenCalledWith(1, {
      name: 'Parodontite',
      description: 'Atteinte parodontale',
      is_active: true,
    }));

    cleanup();
    render(<CatalogTab />);
    fireEvent.click(screen.getByRole('button', { name: 'Modifier la pathologie Gingivite' }));
    fireEvent.click(screen.getByRole('checkbox', { name: 'Actif' }));
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));

    await waitFor(() => expect(state.updatePathology).toHaveBeenCalledWith(
      20,
      expect.objectContaining({ name: 'Gingivite', description: 'Inflammation', is_active: false }),
    ));
  });

  it('fails closed on catalogue read error and retries', async () => {
    state.readError = 'Catalogue backend indisponible';
    render(<CatalogTab />);

    expect(screen.getByText('Catalogue indisponible')).toBeTruthy();
    expect(screen.queryByText('Détartrage')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));
    await waitFor(() => expect(state.fetchCatalog).toHaveBeenCalled());
  });

  it('keeps modal open when store mutation refuses save', async () => {
    state.createSpecialty.mockResolvedValueOnce(false);
    render(<CatalogTab />);
    fireEvent.click(screen.getByRole('button', { name: /Nouvelle spécialité/i }));
    fireEvent.change(screen.getByPlaceholderText('Ex. Orthodontie'), { target: { value: 'Implantologie' } });
    fireEvent.click(screen.getByRole('button', { name: 'Créer' }));

    await waitFor(() => expect(state.createSpecialty).toHaveBeenCalled());
    expect(screen.getByRole('dialog')).toBeTruthy();
  });
});
