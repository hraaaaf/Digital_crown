import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { InstallmentStudio } from './Forms/InstallmentStudioInner';
import { api } from '../../../services/api';

vi.mock('../../../services/api', () => ({
  api: { get: vi.fn(), post: vi.fn(), put: vi.fn() },
}));
vi.mock('../../../components/odontogram/PriceBrain', () => ({
  PriceBrain: { recordInstallmentPlan: vi.fn() },
}));
vi.mock('react-hot-toast', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

function fieldAfter(label: string) {
  const labelNode=screen.getByText(label);
  const scope=labelNode.parentElement!;
  return scope.querySelector('input,select') as HTMLInputElement | HTMLSelectElement;
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.get).mockImplementation(async (url:string) => {
    if(url==='/patients/7') return {data:{telephone:'0612345678'}} as never;
    if(url==='/installments/patient/7/latest') throw {response:{status:404}};
    throw new Error('unexpected GET '+url);
  });
  vi.spyOn(window,'open').mockImplementation(()=>null);
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('InstallmentStudio G4 payment-plan controls', () => {
  it('generates an exactly balanced schedule then persists it only after explicit save', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      data:{
        id:55,
        installments:[
          {id:101,label:'Avance Initiale',amount:200,due_date:'2026-09-19T00:00:00',status:'EN_ATTENTE'},
          {id:102,label:'Mensualité 1',amount:400,due_date:'2026-10-19T00:00:00',status:'EN_ATTENTE'},
          {id:103,label:'Mensualité 2',amount:400,due_date:'2026-11-19T00:00:00',status:'EN_ATTENTE'},
        ],
      },
    } as never);

    render(<InstallmentStudio patientId="7"/>);

    fireEvent.change(fieldAfter('Montant Total Prévu (MAD)'),{target:{value:'1000'}});
    fireEvent.change(fieldAfter('Avance (MAD)'),{target:{value:'200'}});
    fireEvent.change(fieldAfter('Nbre Mensualités'),{target:{value:'2'}});

    fireEvent.click(screen.getByRole('button',{name:/Générer le tableau des échéances/i}));
    expect(await screen.findByDisplayValue('Avance Initiale')).toBeTruthy();
    expect(screen.getByDisplayValue('Mensualité 1')).toBeTruthy();
    expect(screen.getByDisplayValue('Mensualité 2')).toBeTruthy();
    expect(screen.getByText('Total équilibré')).toBeTruthy();
    expect(api.post).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button',{name:'Enregistrer le plan'}));
    await waitFor(()=>expect(api.post).toHaveBeenCalledWith('/installments/',{
      patient_id:7,
      title:'Plan de paiement',
      total_amount:1000,
      installments:[
        expect.objectContaining({label:'Avance Initiale',amount:200,status:'EN_ATTENTE'}),
        expect.objectContaining({label:'Mensualité 1',amount:400,status:'EN_ATTENTE'}),
        expect.objectContaining({label:'Mensualité 2',amount:400,status:'EN_ATTENTE'}),
      ],
    }));
    expect(await screen.findByText(/Plan enregistré #55/)).toBeTruthy();
  });

  it('adds/removes a manual draft row without backend mutation', async () => {
    render(<InstallmentStudio patientId="7"/>);
    fireEvent.click(screen.getByRole('button',{name:/Ajouter manuellement/i}));
    expect(await screen.findByDisplayValue('Nouveau versement')).toBeTruthy();
    expect(api.post).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button',{name:/Supprimer Nouveau versement/i}));
    expect(screen.queryByDisplayValue('Nouveau versement')).toBeNull();
    expect(api.post).not.toHaveBeenCalled();
  });

  it('collects a persisted installment only after payment method selection and backend ACK', async () => {
    let latestReads = 0;
    vi.mocked(api.get).mockImplementation(async (url:string) => {
      if(url==='/patients/7') return {data:{telephone:'0612345678'}} as never;
      if(url==='/installments/patient/7/latest') {
        latestReads += 1;
        return {
          data:{id:55,title:'Plan existant',total_amount:500,installments:[
            {id:101,label:'Mensualité 1',amount:500,due_date:'2026-10-19T00:00:00',status:latestReads > 1 ? 'PAYE' : 'EN_ATTENTE'}
          ]}
        } as never;
      }
      throw new Error('unexpected GET '+url);
    });
    vi.mocked(api.put).mockResolvedValueOnce({data:{status:'PAYE'}} as never);

    render(<InstallmentStudio patientId="7"/>);
    const method=await screen.findByLabelText('Mode de règlement Mensualité 1');
    const collect=screen.getByRole('button',{name:/Encaisser/i}) as HTMLButtonElement;
    expect(collect.disabled).toBe(true);

    fireEvent.change(method,{target:{value:'CARTE'}});
    expect(collect.disabled).toBe(false);
    fireEvent.click(collect);

    await waitFor(()=>expect(api.put).toHaveBeenCalledWith('/installments/101',{
      status:'PAYE',payment_method:'CARTE'
    }));
    expect(await screen.findByText('PAYÉ')).toBeTruthy();
  });

  it('preserves an unpaid installment when collection is refused', async () => {
    vi.mocked(api.get).mockImplementation(async (url:string) => {
      if(url==='/patients/7') return {data:{telephone:'0612345678'}} as never;
      if(url==='/installments/patient/7/latest') return {
        data:{id:55,title:'Plan existant',total_amount:500,installments:[
          {id:101,label:'Mensualité 1',amount:500,due_date:'2026-10-19T00:00:00',status:'EN_ATTENTE'}
        ]}
      } as never;
      throw new Error('unexpected GET '+url);
    });
    vi.mocked(api.put).mockRejectedValueOnce({response:{data:{detail:'Encaissement interdit'}}});

    render(<InstallmentStudio patientId="7"/>);
    fireEvent.change(await screen.findByLabelText('Mode de règlement Mensualité 1'),{target:{value:'ESPECES'}});
    fireEvent.click(screen.getByRole('button',{name:/Encaisser/i}));

    await waitFor(()=>expect(api.put).toHaveBeenCalledWith('/installments/101',{
      status:'PAYE',payment_method:'ESPECES'
    }));
    expect(screen.queryByText('PAYÉ')).toBeNull();
    expect(screen.getByDisplayValue('Plan existant')).toBeTruthy();
  });

  it('opens a WhatsApp reminder only after the reminder control is enabled', async () => {
    vi.mocked(api.get).mockImplementation(async (url:string) => {
      if(url==='/patients/7') return {data:{telephone:'0612345678'}} as never;
      if(url==='/installments/patient/7/latest') return {
        data:{id:55,title:'Plan existant',total_amount:500,installments:[
          {id:101,label:'Mensualité 1',amount:500,due_date:'2026-10-19T00:00:00',status:'EN_ATTENTE'}
        ]}
      } as never;
      throw new Error('unexpected GET '+url);
    });

    render(<InstallmentStudio patientId="7"/>);
    fireEvent.click(await screen.findByLabelText('Activer rappel WhatsApp Mensualité 1'));
    fireEvent.click(screen.getByTitle('Ouvrir WhatsApp avec le rappel prérempli'));
    expect(window.open).toHaveBeenCalledWith(expect.stringContaining('https://wa.me/212612345678?text='),'_blank');
  });
});