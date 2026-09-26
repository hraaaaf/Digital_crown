import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AccountingStudio } from '../AccountingStudio';
import { useAccountingStore } from '../store/useAccountingStore';

const catalogState = vi.hoisted(() => ({
  specialties: [
    {
      id: 1,
      name: 'OMNIPRATIQUE',
      pathologies: [],
      acts: [],
    },
  ],
  fetchCatalog: vi.fn(),
  createAct: vi.fn(),
  updateAct: vi.fn(),
}));

vi.mock('../Settings/hooks/useCatalogStore', () => ({
  useCatalogStore: (selector?: any) => selector ? selector(catalogState) : catalogState,
}));
vi.mock('../../../components/odontogram/OdontogramSVG', () => ({
  OdontogramSVG: () => <div>Odontogram mock</div>,
}));
vi.mock('../../../components/odontogram/TreatmentSelector', () => ({
  TreatmentSelector: () => <div>Treatment selector mock</div>,
}));
vi.mock('./AccountingQuickActions', () => ({
  AccountingQuickActions: () => <div>Quick accounting actions</div>,
}));
vi.mock('../../../components/odontogram/PriceBrain', () => ({
  PriceBrain: { recordAct: vi.fn(), recordInstallmentPlan: vi.fn() },
}));
vi.mock('../../../services/api', () => ({
  api: { get:vi.fn().mockResolvedValue({data:[]}), post:vi.fn(), put:vi.fn() },
}));

beforeEach(() => {
  useAccountingStore.getState().reset();
  vi.clearAllMocks();
  catalogState.fetchCatalog.mockResolvedValue(undefined);
  catalogState.createAct.mockResolvedValue(true);
  catalogState.updateAct.mockResolvedValue(true);
});
afterEach(() => { cleanup(); useAccountingStore.getState().reset(); });

function renderHonoraires() {
  return render(
    <AccountingStudio
      isDevis={false}
      patientId="7"
      setSelectedTeethFromOdontogram={vi.fn()}
      coherenceWarnings={[]}
      validationErrors={[]}
    />,
  );
}

async function addCatalogBackedLine(name: string, price: number) {
  fireEvent.click(screen.getByRole('button',{name:/Ligne Manuelle/i}));
  const dialog=screen.getByRole('dialog',{name:'Ajouter un acte au catalogue'});
  fireEvent.change(within(dialog).getByRole('combobox',{name:'Spécialité'}),{target:{value:'1'}});
  fireEvent.change(within(dialog).getByPlaceholderText("Nom de l'acte"),{target:{value:name}});
  fireEvent.change(within(dialog).getByPlaceholderText('Tarif à définir'),{target:{value:String(price)}});
  fireEvent.click(within(dialog).getByRole('button',{name:'Créer et ajouter'}));
  await waitFor(() => expect(useAccountingStore.getState().items.some(item => item.description === name)).toBe(true));
}

describe('Honoraires G4 interactive controls', () => {
  it('adds, edits, reorders and removes catalog-backed honorarium lines while keeping total truth', async () => {
    renderHonoraires();

    await addCatalogBackedLine('Détartrage',500);
    expect(screen.getByText('500 MAD')).toBeTruthy();

    await addCatalogBackedLine('Contrôle',200);
    expect(screen.getByText('700 MAD')).toBeTruthy();

    fireEvent.click(screen.getByRole('button',{name:'Monter Contrôle'}));
    expect(useAccountingStore.getState().items[0].description).toBe('Contrôle');

    fireEvent.click(screen.getByRole('button',{name:'Supprimer Contrôle'}));
    expect(useAccountingStore.getState().items).toHaveLength(1);
    expect(screen.getByText('500 MAD')).toBeTruthy();
  });

  it('opens treasury and records explicit status/payment/accounting choices in canonical store', async () => {
    renderHonoraires();
    await addCatalogBackedLine('Consultation',300);

    fireEvent.click(screen.getByRole('button',{name:/Procéder à l'Encaissement/i}));
    expect(screen.getByText('Encaissement')).toBeTruthy();

    fireEvent.click(screen.getByRole('button',{name:'Réglé'}));
    expect(useAccountingStore.getState().paymentStatus).toBe('PAYE');

    fireEvent.click(screen.getByRole('button',{name:'TPE'}));
    expect(useAccountingStore.getState().paymentMode).toBe('TPE');

    const before=useAccountingStore.getState().isAccounted;
    const accountingLabel=screen.getByText('Comptabiliser CA', { exact:true });
    const accountingToggle=accountingLabel.parentElement?.querySelector('button');
    if(!accountingToggle) throw new Error('accounting toggle not found');
    fireEvent.click(accountingToggle);
    expect(useAccountingStore.getState().isAccounted).toBe(!before);
  });

  it('refuses partial-payment status and exposes the guard instead of silently changing state', async () => {
    renderHonoraires();
    await addCatalogBackedLine('Consultation',300);
    fireEvent.click(screen.getByRole('button',{name:/Procéder à l'Encaissement/i}));
    fireEvent.click(screen.getByRole('button',{name:'Partiel'}));

    expect(useAccountingStore.getState().paymentStatus).toBe('EN_ATTENTE');
    expect(screen.getByRole('alert')).toBeTruthy();
    expect(screen.getByRole('alert').textContent).toMatch(/Paiement partiel/i);

    fireEvent.click(screen.getByRole('button',{name:'Compris'}));
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('switches unique/global billing and adds/removes planned installments without persistence side effects', async () => {
    renderHonoraires();
    await addCatalogBackedLine('Consultation',300);
    fireEvent.click(screen.getByRole('button',{name:/Procéder à l'Encaissement/i}));

    fireEvent.click(screen.getByRole('button',{name:/Global \/ Planifié/i}));
    expect(useAccountingStore.getState().isGlobalNote).toBe(true);

    fireEvent.click(screen.getByRole('button',{name:/Nouvelle Échéance/i}));
    expect(useAccountingStore.getState().installments).toHaveLength(1);
    expect(screen.getByDisplayValue('Versement 1')).toBeTruthy();

    const row=screen.getByDisplayValue('Versement 1').closest('div')?.parentElement;
    const remove=row?.querySelector('button');
    if(!remove) throw new Error('installment remove control not found');
    fireEvent.click(remove);
    expect(useAccountingStore.getState().installments).toHaveLength(0);

    fireEvent.click(screen.getByRole('button',{name:'Unique'}));
    expect(useAccountingStore.getState().isGlobalNote).toBe(false);
  });

  it('closes the treasury modal without changing the configured payment state', async () => {
    renderHonoraires();
    await addCatalogBackedLine('Consultation',300);
    fireEvent.click(screen.getByRole('button',{name:/Procéder à l'Encaissement/i}));
    fireEvent.click(screen.getByRole('button',{name:'Cash'}));
    fireEvent.click(screen.getByRole('button',{name:'Appliquer à la note'}));

    await waitFor(() => expect(screen.queryByText('Encaissement')).toBeNull());
    expect(useAccountingStore.getState().paymentMode).toBe('Espèces');
  });
});
