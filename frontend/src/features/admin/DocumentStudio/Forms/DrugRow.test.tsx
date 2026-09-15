import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

import { api } from '../../../../services/api';
import { DrugRow } from './DrugRow';
import type { DrugItem } from './prescriptionTypes';

vi.mock('../../../../services/api', () => ({
  api: { get: vi.fn() },
}));

const presentation = {
  presentation_id: 'cnops:test-500',
  nom: 'PARACETAMOL TEST 500 MG',
  dci: 'PARACETAMOL',
  dosage: '500',
  unite: 'MG',
  forme: 'COMPRIME',
  source: {
    id: 'cnops-open-data-medications',
    label: 'CNOPS Open Data — Référentiel des médicaments',
    license: 'ODbL',
    source_url: 'https://www.data.gov.ma/data/fr/dataset/referentiel-des-medicaments',
    snapshot_date: '2021-12-13',
    freshness: 'historical_snapshot',
    current_marketing_status_verified: false,
  },
};

const baseDrug: DrugItem = {
  id: 1,
  name: 'PARACE',
  dosage: '',
  forme: '',
  posologie: '',
  type: 'MEDICAMENT',
};

const noop = () => {};

function renderDrugRow(overrides: Partial<React.ComponentProps<typeof DrugRow>> = {}) {
  const onUpdateDrug = vi.fn();
  const props: React.ComponentProps<typeof DrugRow> = {
    drug: baseDrug,
    idx: 0,
    drugsCount: 1,
    assessment: null,
    validationErrors: [],
    forcedDrugs: [],
    activeSearchId: null,
    suggestions: { medications: [], dosages: [], posologies: [] },
    highlightedIdx: -1,
    medChecks: {},
    onUpdateDrug,
    onRemoveDrug: noop,
    onMove: noop,
    onSearch: noop,
    onKeyDown: noop,
    onApplySuggestion: noop,
    onFormeOpen: noop,
    onForceAllergy: noop,
    onToggleType: noop,
    ...overrides,
  };
  render(<DrugRow {...props} />);
  return { onUpdateDrug };
}

describe('DrugRow — Prescription Intelligence V1', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.get).mockResolvedValue({ data: [presentation] } as any);
  });

  it('recherche uniquement dans le référentiel médicament après 2 caractères', async () => {
    renderDrugRow();

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/medications/search', { params: { q: 'PARACE' } });
    });
    expect(await screen.findByText('PARACETAMOL TEST 500 MG')).toBeInTheDocument();
    expect(screen.getByText(/CNOPS Open Data · 2021-12-13 · statut commercial actuel non certifié/i)).toBeInTheDocument();
  });

  it('sélectionne explicitement une présentation et n injecte aucune posologie', async () => {
    const { onUpdateDrug } = renderDrugRow();
    const suggestion = await screen.findByText('PARACETAMOL TEST 500 MG');

    fireEvent.mouseDown(suggestion.closest('button')!);

    expect(onUpdateDrug).toHaveBeenCalledWith(1, 'name', 'PARACETAMOL TEST 500 MG');
    expect(onUpdateDrug).toHaveBeenCalledWith(1, 'dosage', '500 MG');
    expect(onUpdateDrug).toHaveBeenCalledWith(1, 'forme', 'COMPRIME');
    expect(onUpdateDrug).toHaveBeenCalledWith(1, 'posologie', '');
    expect(onUpdateDrug).toHaveBeenCalledWith(1, 'catalogPresentationId', 'cnops:test-500');
    expect(onUpdateDrug).toHaveBeenCalledWith(1, 'catalogMarketingStatusVerified', false);
  });

  it('échoue fermé si le référentiel est indisponible', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('offline'));
    renderDrugRow();

    expect(await screen.findByText(/Référentiel médicament indisponible/)).toBeInTheDocument();
    expect(screen.queryByText('PARACETAMOL TEST 500 MG')).not.toBeInTheDocument();
  });

  it('bloque la suggestion clinique même après sélection documentaire', () => {
    renderDrugRow({
      drug: {
        ...baseDrug,
        name: 'PARACETAMOL TEST 500 MG',
        dosage: '500 MG',
        forme: 'COMPRIME',
        catalogPresentationId: 'cnops:test-500',
        catalogDci: 'PARACETAMOL',
        catalogSourceId: 'cnops-open-data-medications',
        catalogSourceLabel: 'CNOPS Open Data — Référentiel des médicaments',
        catalogSnapshotDate: '2021-12-13',
        catalogMarketingStatusVerified: false,
      },
    });

    expect(screen.getByText(/Suggestion clinique indisponible/)).toBeInTheDocument();
    expect(screen.getByText(/Aucune règle de dose V1 certifiée/)).toBeInTheDocument();
  });

  it('efface identité documentaire et champs cliniques si le nom sélectionné est modifié', () => {
    const { onUpdateDrug } = renderDrugRow({
      drug: {
        ...baseDrug,
        name: 'PARACETAMOL TEST 500 MG',
        dosage: '500 MG',
        forme: 'COMPRIME',
        posologie: 'ancienne posologie',
        catalogPresentationId: 'cnops:test-500',
      },
    });

    fireEvent.change(screen.getByDisplayValue('PARACETAMOL TEST 500 MG'), {
      target: { value: 'PARACETAMOL TEST' },
    });

    expect(onUpdateDrug).toHaveBeenCalledWith(1, 'catalogPresentationId', undefined);
    expect(onUpdateDrug).toHaveBeenCalledWith(1, 'dosage', '');
    expect(onUpdateDrug).toHaveBeenCalledWith(1, 'forme', '');
    expect(onUpdateDrug).toHaveBeenCalledWith(1, 'posologie', '');
    expect(onUpdateDrug).toHaveBeenCalledWith(1, 'name', 'PARACETAMOL TEST');
  });
});
