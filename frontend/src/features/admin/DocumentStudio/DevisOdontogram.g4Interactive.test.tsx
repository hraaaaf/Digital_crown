import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AccountingStudio } from '../AccountingStudio';
import { useAccountingStore } from '../store/useAccountingStore';
import { api } from '../../../services/api';

const catalogState = vi.hoisted(() => ({
  specialties:[
    {
      id:1,
      name:'PROTHESE',
      pathologies:[],
      acts:[{
        id:1,
        specialty_id:1,
        name:'Bridge',
        base_price:1800,
        is_active:true,
        applicability:{
          dentitions:['PERMANENT'],
          treatment_areas:['TOOTH_RANGE'],
          selection_modes:['GROUP'],
          min_selected_teeth:3,
          suggestion_priority:95,
        },
      }],
    },
    {
      id:2,
      name:'CONSERVATRICE',
      pathologies:[],
      acts:[{
        id:2,
        specialty_id:2,
        name:'Détartrage',
        base_price:500,
        is_active:true,
        applicability:{ searchable_when_not_suggested:true },
      }],
    },
    {
      id:3,
      name:'PEDODONTIE',
      pathologies:[],
      acts:[{
        id:3,
        specialty_id:3,
        name:"Mainteneur d'espace",
        base_price:1200,
        is_active:true,
        applicability:{
          dentitions:['PRIMARY'],
          treatment_areas:['TOOTH_RANGE','ARCH'],
          selection_modes:['GROUP'],
          min_selected_teeth:2,
          suggestion_priority:85,
        },
      }],
    },
  ],
  fetchCatalog:vi.fn(),
  createAct:vi.fn(),
  updateAct:vi.fn(),
}));

vi.mock('../Settings/hooks/useCatalogStore', () => ({
  useCatalogStore: (selector?: any) => selector ? selector(catalogState) : catalogState,
}));
vi.mock('../../../components/odontogram/PremiumOdontogramSVG', () => ({
  PremiumOdontogramSVG: ({onToothClick,type}:any) => (
    <div>
      <span>Odontogram {type}</span>
      {type==='PEDIATRIC'
        ? <button onClick={()=>onToothClick(51)}>Tooth 51</button>
        : <button onClick={()=>onToothClick(11)}>Tooth 11</button>}
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
  catalogState.fetchCatalog.mockResolvedValue(undefined);
  catalogState.createAct.mockResolvedValue(true);
  catalogState.updateAct.mockResolvedValue(true);
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
function renderHonoraires(){
  return render(<AccountingStudio isDevis={false} patientId="7" setSelectedTeethFromOdontogram={vi.fn()} coherenceWarnings={[]} validationErrors={[]}/>);
}

describe('Devis/Odontogram G4 interactive controls', () => {
  it('switches adult/pediatric and uses the same 1→N tooth selection gesture without modes', () => {
    renderDevis();

    expect(screen.getByText('Odontogram ADULT')).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:'Tooth 11'}));
    expect(useAccountingStore.getState().groupSelectedTeeth).toEqual([11]);
    fireEvent.click(screen.getByRole('button',{name:'Tooth 11'}));
    expect(useAccountingStore.getState().groupSelectedTeeth).toEqual([]);

    fireEvent.click(screen.getByRole('button',{name:'Enfant'}));
    expect(screen.getByText('Odontogram PEDIATRIC')).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:'Tooth 51'}));
    expect(useAccountingStore.getState().groupSelectedTeeth).toEqual([51]);

    expect(screen.queryByRole('button',{name:/Bridge & Prothèses/i})).toBeNull();
    expect(screen.queryByRole('button',{name:/Soins groupés/i})).toBeNull();
    expect(screen.queryByRole('button',{name:/Soins Ciblés/i})).toBeNull();
    expect(screen.queryByRole('button',{name:/Soins Généraux/i})).toBeNull();
  });

  it('adds a single-tooth catalog act directly from the contextual search', () => {
    renderDevis();
    fireEvent.click(screen.getByRole('button',{name:'Tooth 11'}));

    const search=screen.getByPlaceholderText('Rechercher un acte pour cette sélection…');
    fireEvent.change(search,{target:{value:'Détartrage'}});
    fireEvent.click(screen.getByRole('button',{name:/Détartrage/}));

    expect(useAccountingStore.getState().items[0]).toEqual(expect.objectContaining({
      description:'Détartrage',
      price:500,
      category:'CONSERVATRICE',
      toothNumbers:[11],
    }));
    expect(useAccountingStore.getState().groupSelectedTeeth).toEqual([]);
  });

  it('uses neutral whole-arch quick selection and adds a compatible multi-tooth act', () => {
    renderDevis();
    fireEvent.click(screen.getByText('Sélection rapide',{exact:true}));
    fireEvent.click(screen.getByRole('button',{name:'Maxillaire'}));

    expect(useAccountingStore.getState().groupSelectedTeeth).toEqual([11,12,13,14,15,16,17,18,21,22,23,24,25,26,27,28]);
    fireEvent.click(screen.getByRole('button',{name:'Bridge'}));

    expect(useAccountingStore.getState().items[0]).toEqual(expect.objectContaining({
      description:'Bridge',
      price:1800,
      category:'PROTHESE',
      toothNumbers:[11,12,13,14,15,16,17,18,21,22,23,24,25,26,27,28],
    }));
    expect(useAccountingStore.getState().groupSelectedTeeth).toEqual([]);
  });

  it('keeps pediatric applicability contextual without a pediatric group mode', () => {
    renderDevis();
    fireEvent.click(screen.getByRole('button',{name:'Enfant'}));
    fireEvent.click(screen.getByText('Sélection rapide',{exact:true}));
    fireEvent.click(screen.getByRole('button',{name:'Maxillaire'}));

    expect(screen.queryByRole('button',{name:'Bridge'})).toBeNull();
    expect(screen.getByRole('button',{name:"Mainteneur d'espace"})).toBeTruthy();
  });

  it('offers only secondary neutral shortcuts and resets without creating a line', () => {
    renderDevis();
    fireEvent.click(screen.getByText('Sélection rapide',{exact:true}));

    for (const label of ['Maxillaire','Mandibule','Toutes']) {
      expect(screen.getByRole('button',{name:label})).toBeTruthy();
    }

    fireEvent.click(screen.getByRole('button',{name:'Maxillaire'}));
    fireEvent.click(screen.getByRole('button',{name:'Réinitialiser'}));

    expect(useAccountingStore.getState().groupSelectedTeeth).toEqual([]);
    expect(useAccountingStore.getState().items).toHaveLength(0);
  });

  it('creates a new catalog act from the devis manual action, then inserts the same act into the document', async () => {
    renderDevis();
    fireEvent.click(screen.getByRole('button',{name:/Ligne Manuelle/i}));
    expect(screen.getByRole('dialog',{name:'Ajouter un acte au catalogue'})).toBeTruthy();

    fireEvent.change(screen.getByRole('combobox',{name:'Spécialité'}),{target:{value:'2'}});
    fireEvent.change(screen.getByPlaceholderText("Nom de l'acte"),{target:{value:'Acte devis custom'}});
    fireEvent.change(screen.getByPlaceholderText('Tarif à définir'),{target:{value:'650'}});
    fireEvent.click(screen.getByRole('button',{name:'Créer et ajouter'}));

    await waitFor(() => expect(catalogState.createAct).toHaveBeenCalledWith(
      2,
      expect.objectContaining({name:'Acte devis custom',base_price:650}),
    ));
    expect(useAccountingStore.getState().items[0]).toEqual(expect.objectContaining({
      description:'Acte devis custom',
      price:650,
      category:'CONSERVATRICE',
    }));
  });

  it('reuses an existing catalog act without creating a duplicate and uses its catalog tariff', async () => {
    renderDevis();
    fireEvent.click(screen.getByRole('button',{name:/Ligne Manuelle/i}));
    fireEvent.change(screen.getByRole('combobox',{name:'Spécialité'}),{target:{value:'2'}});
    fireEvent.change(screen.getByPlaceholderText("Nom de l'acte"),{target:{value:'Détartrage'}});
    fireEvent.click(screen.getByRole('button',{name:'Créer et ajouter'}));

    await waitFor(() => expect(useAccountingStore.getState().items).toHaveLength(1));
    expect(catalogState.createAct).not.toHaveBeenCalled();
    expect(useAccountingStore.getState().items[0]).toEqual(expect.objectContaining({
      description:'Détartrage',
      price:500,
      category:'CONSERVATRICE',
    }));
  });

  it('uses the same central-catalog creation path from Note d’honoraires', async () => {
    renderHonoraires();
    fireEvent.click(screen.getByRole('button',{name:/Ligne Manuelle/i}));
    fireEvent.change(screen.getByRole('combobox',{name:'Spécialité'}),{target:{value:'3'}});
    fireEvent.change(screen.getByPlaceholderText("Nom de l'acte"),{target:{value:'Acte honoraires custom'}});
    fireEvent.click(screen.getByRole('button',{name:'Créer et ajouter'}));

    await waitFor(() => expect(catalogState.createAct).toHaveBeenCalledWith(
      3,
      expect.objectContaining({name:'Acte honoraires custom',base_price:0}),
    ));
    expect(useAccountingStore.getState().items[0]).toEqual(expect.objectContaining({
      description:'Acte honoraires custom',
      price:0,
      category:'PEDODONTIE',
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
