import { act, cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from '../../services/api';
import { R3TreatmentReadonlyPanel, validateR3MasterPlan } from './R3TreatmentReadonlyPanel';

vi.mock('../../services/api',()=>({api:{get:vi.fn(),post:vi.fn(),put:vi.fn(),delete:vi.fn()}}));
const plan=(patient_id:number,title:string)=>({
  id:41,patient_id,created_at:'2026-10-01T12:00:00Z',updated_at:'2026-10-02T12:00:00Z',
  steps:[{id:101,plan_id:41,title,assistant:'Clinique',status:'pending',date_str:'2026-11-12',
    order_index:0,catalog_snapshot:null}],
});
afterEach(()=>{cleanup();vi.clearAllMocks();});
describe('R3 Master Plan authenticated R-only adapter',()=>{
  it('renders only factual persisted steps from the canonical GET; no write method',async()=>{
    vi.mocked(api.get).mockResolvedValue({data:plan(17,'Séquence enregistrée')} as never);
    render(<R3TreatmentReadonlyPanel patientId={17}/>);
    expect(await screen.findByText('Séquence enregistrée',{exact:false})).toBeTruthy();
    expect(screen.getByTestId('r3-real-treatment').textContent).toContain('En attente');
    expect(screen.getByTestId('r3-real-treatment').textContent).toContain('Lecture seule');
    expect(api.get).toHaveBeenCalledExactlyOnceWith('/patients/17/master-plan');
    expect(api.post).not.toHaveBeenCalled();
    expect(api.put).not.toHaveBeenCalled();
    expect(api.delete).not.toHaveBeenCalled();
  });
  it('distinguishes genuinely absent plan from error and cross-patient response',async()=>{
    vi.mocked(api.get).mockResolvedValueOnce({data:null} as never);
    const {rerender}=render(<R3TreatmentReadonlyPanel patientId={17}/>);
    expect(await screen.findByText('Aucun plan de traitement enregistré.')).toBeTruthy();
    vi.mocked(api.get).mockResolvedValueOnce({data:plan(17,'Patient A only')} as never);
    rerender(<R3TreatmentReadonlyPanel patientId={18}/>);
    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.queryByText('Patient A only')).toBeNull();
    vi.mocked(api.get).mockRejectedValueOnce({response:{status:403}});
    rerender(<R3TreatmentReadonlyPanel patientId={19}/>);
    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.queryByText('Aucun plan de traitement enregistré.')).toBeNull();
  });
  it('drops stale patient A responses after switching to patient B',async()=>{
    let resolveA:(value:any)=>void=()=>{};
    vi.mocked(api.get).mockImplementation(url =>
      url==='/patients/17/master-plan'
        ? new Promise(resolve=>{resolveA=resolve;}) as never
        : Promise.resolve({data:plan(18,'Patient B step')}) as never);
    const {rerender}=render(<R3TreatmentReadonlyPanel patientId={17}/>);
    rerender(<R3TreatmentReadonlyPanel patientId={18}/>);
    expect(await screen.findByText('Patient B step',{exact:false})).toBeTruthy();
    await act(async()=>{resolveA({data:plan(17,'Patient A secret')});});
    expect(screen.queryByText('Patient A secret')).toBeNull();
  });
  it('fails closed on malformed or untrusted data',()=>{
    expect(validateR3MasterPlan({id:41,patient_id:18,steps:[]},17)).toBeUndefined();
    expect(validateR3MasterPlan({id:41,patient_id:17,steps:[{id:1,title:'Oops',assistant:'',status:'fake',date_str:null}]},17)).toBeUndefined();
    expect(validateR3MasterPlan(null,17)).toBeNull();
  });
});
