import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AccountingStudio } from '../AccountingStudio';
import { useAccountingStore } from '../store/useAccountingStore';
import { api } from '../../../services/api';

const catalogState = vi.hoisted(() => ({
  specialties:[
    {name:'PROTHESE',acts:[{id:1,name:'Bridge',base_price:1800}]},
    {name:'CONSERVATRICE',acts:[{id:2,name:'Détartrage',base_price:500}]},
  ],
  fetchCatalog:vi.fn(),
}));

vi.mock('../Settings/hooks/useCatalogStore', () => ({
  useCatalogStore: (selector?: any) => selector ? selector(catalogState) : catalogState,
}));
vi.mock('../../../components/odontogram/OdontogramSVG', () => ({
  OdontogramSVG: ({onToothDirectClick,type}:any) => (
    <div>
      <span>Odontogram {type}</span>
      <button onClick={()=>onToothDirectClick(11)}>Tooth 11</button>
    </div>
  ),
}));
vi.mock('../../../components/odontogram/TreatmentSelector', () => ({
  TreatmentSelector: ({onConfirm,onCancel}:any) => (
    <div>
      <span>Treatment selector</span>
      <button onClick={()=>onConfirm(
        [{id:'det',name:'Détartrage',price:500,category:'CONSERVATRICE',scope:'UNITAIRE'}],
        ['O'],
        ''
      )}>Confirm treatment</button>
      <button onClick={onCancel}>Cancel treatment</button>
    </div>
  ),
}));
vi.mock('./AccountingQuickActions', () => ({
  AccountingQuickActions: ({onAddManual}:any) => <button onClick={onAddManual}>Quick manual</button>,
}));
vi.mock('../../../components/odontogram/PriceBrain', () => ({
  PriceBrain:{recordAct:vi.fn(),recordInstallmentPlan:vi.fn()},
}));
vi.mock('react-hot-toast', () => ({
  default:{success:vi.fn(),error:vi.fn()},
}));
vi.mock('../../../services/api', () => ({
  api:{
    get:vi.fn(),
    post:vi.fn(),
  },
}));

beforeEach(() => {
  useAccountingStore.getState().reset();
  vi.clearAllMocks();
  vi.mocked(api.get).mockImplementation(async (url:string) => {
    if(url.startsWith('/actes/search')) return {data:[{id:99,name:'Détartrage',base_price:999,category:'HABIT'}]} as never;
    if(url==='/accounting/frequent-acts') return {data:[]} as never;
    return {data:[]} as never;
  });
  vi.mocked(api.post).mockResolvedValue({data:[]} as never);
});
afterEach(() => {
  cleanup();
  useAccountingStore.getState().reset();
});

function renderDevis(){
  return render(<AccountingStudio isDevis patientId="7" setSelectedTeethFromOdontogram={vi.fn()} coherenceWarnings={[]} validationErrors={[]}/>);
}

describe('Devis/Odontogram G4 interactive controls', () => {
  it('switches adult/pediatric and individual/group/general-care odontogram modes', () => {
    renderDevis();

    expect(screen.getByText('Odontogram ADULT')).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:'Enfant'}));
    expect(screen.getByText('Odontogram PEDIATRIC')).toBeTruthy();

    fireEvent.click(screen.getByRole('button',{name:/Bridge & Prothèses/i}));
    expect(useAccountingStore.getState().odontogramMode).toBe('group');

    fireEvent.click(screen.getByRole('button',{name:/Soins Généraux/i}));
    expect(useAccountingStore.getState().odontogramMode).toBe('ortho');

    fireEvent.click(screen.getByRole('button',{name:/Soins Ciblés/i}));
    expect(useAccountingStore.getState().odontogramMode).toBe('individual');
  });

  it('turns an individual tooth treatment confirmation into a structured priced devis line', () => {
    renderDevis();
    fireEvent.click(screen.getByRole('button',{name:'Tooth 11'}));
    expect(screen.getByText('Treatment selector')).toBeTruthy();

    fireEvent.click(screen.getByRole('button',{name:'Confirm treatment'}));

    const items=useAccountingStore.getState().items;
    expect(items).toHaveLength(1);
    expect(items[0]).toEqual(expect.objectContaining({
      description:'Détartrage',
      price:500,
      category:'CONSERVATRICE',
    }));
    expect(items[0].dent).toContain('11');
    expect(screen.queryByText('Treatment selector')).toBeNull();
  });

  it('uses quick tooth groups then applies a custom grouped treatment only with positive price', () => {
    renderDevis();
    fireEvent.click(screen.getByRole('button',{name:/Bridge & Prothèses/i}));
    fireEvent.click(screen.getByRole('button',{name:'Q1'}));
    expect(useAccountingStore.getState().groupSelectedTeeth).toEqual([11,12,13,14,15,16,17,18]);

    fireEvent.change(screen.getByPlaceholderText('Ou saisir un autre acte...'),{target:{value:'Acte groupé test'}});
    fireEvent.change(screen.getByPlaceholderText('Prix'),{target:{value:'1200'}});
    fireEvent.click(screen.getByRole('button',{name:'Appliquer'}));

    const items=useAccountingStore.getState().items;
    expect(items).toHaveLength(1);
    expect(items[0]).toEqual(expect.objectContaining({
      description:'Acte groupé test',
      price:1200,
      dent:'11, 12, 13, 14, 15, 16, 17, 18',
      toothNumbers:[11,12,13,14,15,16,17,18],
    }));
    expect(useAccountingStore.getState().groupSelectedTeeth).toEqual([]);
  });

  it('adds a catalog-priced predefined grouped act and resets selected group', () => {
    renderDevis();
    fireEvent.click(screen.getByRole('button',{name:/Bridge & Prothèses/i}));
    fireEvent.click(screen.getByRole('button',{name:'Q1'}));
    fireEvent.click(screen.getByRole('button',{name:'Bridge'}));

    expect(useAccountingStore.getState().items[0]).toEqual(expect.objectContaining({
      description:'Bridge',
      price:1800,
      category:'PROTHESE',
    }));
    expect(useAccountingStore.getState().groupSelectedTeeth).toEqual([]);
  });

  it('resets a quick tooth selection without creating a line', () => {
    renderDevis();
    fireEvent.click(screen.getByRole('button',{name:/Bridge & Prothèses/i}));
    fireEvent.click(screen.getByRole('button',{name:'Q1'}));
    fireEvent.click(screen.getByRole('button',{name:'Réinitialiser'}));

    expect(useAccountingStore.getState().groupSelectedTeeth).toEqual([]);
    expect(useAccountingStore.getState().items).toHaveLength(0);
  });

  it('applies catalog truth to an act search suggestion instead of trusting habit price', async () => {
    renderDevis();
    fireEvent.click(screen.getByRole('button',{name:/Ligne Manuelle/i}));
    const input=screen.getByPlaceholderText('Rechercher ou saisir un acte...');
    fireEvent.change(input,{target:{value:'Détartrage'}});

    const suggestionLabel=await screen.findByText('Détartrage');
    const suggestion=suggestionLabel.closest('button');
    expect(suggestion).toBeTruthy();
    fireEvent.click(suggestion!);

    expect(useAccountingStore.getState().items[0]).toEqual(expect.objectContaining({
      description:'Détartrage',
      price:500,
      category:'CONSERVATRICE',
    }));
  });

  it('organizes a populated devis by phases through the visible control', () => {
    useAccountingStore.setState({
      items:[
        {id:1,description:'Détartrage',dent:'11',price:500,category:'CONSERVATRICE'},
        {id:2,description:'Bridge',dent:'11-13',price:1800,category:'PROTHESE'},
      ],
    });
    renderDevis();

    fireEvent.click(screen.getByRole('button',{name:/Organiser par phases/i}));
    const descriptions=useAccountingStore.getState().items.map(i=>i.description);
    expect(descriptions.some(d=>d.startsWith('--- '))).toBe(true);
    expect(descriptions).toContain('Détartrage');
    expect(descriptions).toContain('Bridge');
  });

  it('does not expose treasury collection controls in devis mode', () => {
    renderDevis();
    expect(screen.queryByRole('button',{name:/Procéder à l'Encaissement/i})).toBeNull();
  });
});
