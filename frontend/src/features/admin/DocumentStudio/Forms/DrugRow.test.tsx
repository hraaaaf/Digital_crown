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
    fireEvent.focus(screen.getByDisplayValue('PARACE'));

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/medications/neo/search', { params: { q: 'PARACE' } });
    });
    expect(await screen.findByText('PARACETAMOL TEST 500 MG')).toBeInTheDocument();
    expect(await screen.findByText(/CNOPS Open Data — Référentiel des médicaments · 2021-12-13/)).toBeInTheDocument();
  });

  it('sélectionne explicitement une présentation et n injecte aucune posologie', async () => {
    const { onUpdateDrug } = renderDrugRow();
    fireEvent.focus(screen.getByDisplayValue('PARACE'));
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
    fireEvent.focus(screen.getByDisplayValue('PARACE'));

    expect(await screen.findByText(/Recherche médicament indisponible pour le moment/)).toBeInTheDocument();
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

    expect(document.querySelector('[data-clinical-suggestion-status="blocked"]')).toBeInTheDocument();
    expect(screen.queryByText(/Suggestion clinique indisponible/)).not.toBeInTheDocument();
  });

  it('réévalue silencieusement la sécurité N5 quand une présentation exacte est liée', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/patients/42/neo-prescription-safety') {
        return { data: { status: 'READY' } } as any;
      }
      return { data: [presentation] } as any;
    });

    renderDrugRow({
      patientId: '42',
      drug: {
        ...baseDrug,
        name: 'PARACETAMOL TEST 500 MG',
        dosage: '500 MG',
        forme: 'COMPRIME',
        catalogPresentationId: 'cnops:test-500',
        catalogDci: 'PARACETAMOL',
      },
    });

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/patients/42/neo-prescription-safety', {
        params: { presentation_id: 'cnops:test-500' },
      });
    });
    expect(screen.queryByText(/Contexte patient à vérifier/i)).not.toBeInTheDocument();
  });

  it('réévalue N5 quand le contexte patient enregistré change', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/patients/42/neo-prescription-safety') {
        return { data: { status: 'READY' } } as any;
      }
      return { data: [presentation] } as any;
    });

    renderDrugRow({
      patientId: '42',
      drug: {
        ...baseDrug,
        name: 'PARACETAMOL TEST 500 MG',
        dosage: '500 MG',
        forme: 'COMPRIME',
        catalogPresentationId: 'cnops:test-500',
        catalogDci: 'PARACETAMOL',
      },
    });

    await waitFor(() => {
      expect(vi.mocked(api.get).mock.calls.filter(([url]) => url === '/patients/42/neo-prescription-safety')).toHaveLength(1);
    });

    window.dispatchEvent(new CustomEvent('digitalcrown:patient-clinical-context-updated', {
      detail: { patientId: 42 },
    }));

    await waitFor(() => {
      expect(vi.mocked(api.get).mock.calls.filter(([url]) => url === '/patients/42/neo-prescription-safety')).toHaveLength(2);
    });
  });

  it('demande confirmation locale après override manuel sans identité exacte', () => {
    renderDrugRow({
      patientId: '42',
      drug: {
        ...baseDrug,
        name: 'PARACETAMOL TEST',
        dosage: '750 MG',
        forme: 'COMPRIME',
        catalogPresentationId: undefined,
        catalogDci: 'PARACETAMOL',
      },
    });

    expect(screen.getByRole('alert')).toHaveTextContent('Présentation à confirmer avant validation.');
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
    expect(onUpdateDrug).not.toHaveBeenCalledWith(1, 'dosage', '');
    expect(onUpdateDrug).not.toHaveBeenCalledWith(1, 'forme', '');
    expect(onUpdateDrug).not.toHaveBeenCalledWith(1, 'posologie', '');
    expect(onUpdateDrug).toHaveBeenCalledWith(1, 'name', 'PARACETAMOL TEST');
  });

  it('verrouille le contrat accessible du choix manuel de forme utilisé par G4', () => {
    const { onUpdateDrug } = renderDrugRow({
      drug: {
        ...baseDrug,
        name: 'G4 MANUAL',
        catalogPresentationId: undefined,
        catalogDci: undefined,
      },
    });

    fireEvent.click(screen.getByRole('button', { name: 'Forme', exact: true }));
    const menu = screen.getByRole('menu', { name: 'Options Forme' });
    expect(menu.querySelectorAll('[role="menuitem"]')).toHaveLength(12);

    fireEvent.click(screen.getByRole('menuitem', { name: /Modifier manuellement/i }));
    const manual = screen.getByRole('textbox', { name: 'Valeur personnalisée' });
    fireEvent.change(manual, { target: { value: 'COMPRIMÉS' } });
    fireEvent.keyDown(manual, { key: 'Enter', code: 'Enter' });

    expect(onUpdateDrug).toHaveBeenCalledWith(1, 'forme', 'COMPRIMÉS');
  });
});
