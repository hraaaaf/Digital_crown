import { act,cleanup,fireEvent,render,screen } from '@testing-library/react';
import { afterEach,describe,expect,it,vi } from 'vitest';
import { api } from '../../services/api';
import { R3CephaloTimepointReadonlyPanel } from './R3CephaloTimepointReadonlyPanel';
import { R3PatientPresentationPanel } from './R3PatientPresentationPanel';
vi.mock('../../services/api',()=>({api:{get:vi.fn(),post:vi.fn(),put:vi.fn(),delete:vi.fn()}}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
const patient={id:17,prenom:'Patient',nom:'SYNTHETIQUE',numero_dossier:'T2-SAFE'};
const timepoints=[
  {id:31,patient_id:17,ortho_case_id:9,ordinal:0,occurred_at:'2026-01-02',note:null,evidences:[]},
  {id:32,patient_id:17,ortho_case_id:9,ordinal:1,occurred_at:'2026-06-02',note:null,evidences:[]},
];
const compare=(withCephalo=true)=>({
  patient_id:17,ortho_case_id:9,
  from_timepoint:{id:31,ordinal:0,occurred_at:'2026-01-02',note:null,
    evidences:withCephalo?[{kind:'CEPHALO',ref_id:300,recorded_at:null,label:'Analyse T0'}]:[]},
  to_timepoint:{id:32,ordinal:1,occurred_at:'2026-06-02',note:null,
    evidences:withCephalo?[{kind:'CEPHALO',ref_id:301,recorded_at:null,label:'Analyse T1'}]:[]},
  measurements:[{key:'sna',label:'SNA',unit:'°',from_value:80,to_value:81,delta:1}],
  measurement_status:'AVAILABLE',interpretation_policy:'NUMERIC_ONLY_CLINICIAN_INTERPRETATION',
});
function mockEvidence(withCephalo=true){
  vi.mocked(api.get).mockImplementation(async path=>{
    if(path==='/patients/17/ortho-case')return {data:{id:9,patient_id:17,lifecycle_status:'ACTIVE',current_phase_key:null}} as never;
    if(path==='/patients/17/ortho-case/9/timepoints')return {data:timepoints} as never;
    if(path==='/patients/17/ortho-case/9/compare')return {data:compare(withCephalo)} as never;
    throw Error('Unexpected endpoint '+path);
  });
}
describe('LOT07 R3 canonical independent T0/T1 read-only panels',()=>{
  it('renders two separate, source-bound analyses without cephalo editor or writes',async()=>{
    mockEvidence();
    render(<><R3CephaloTimepointReadonlyPanel patientId={17} ordinal={0}/>
      <R3CephaloTimepointReadonlyPanel patientId={17} ordinal={1}/></>);
    expect(await screen.findByText('Analyse source #300')).toBeTruthy();
    expect(await screen.findByText('Analyse source #301')).toBeTruthy();
    expect(screen.getAllByText('SNA')).toHaveLength(2);
    expect(screen.getByTestId('r3-cephalo-t0').textContent).toContain('80');
    expect(screen.getByTestId('r3-cephalo-t1').textContent).toContain('81');
    expect(api.post).not.toHaveBeenCalled();expect(api.put).not.toHaveBeenCalled();expect(api.delete).not.toHaveBeenCalled();
  });
  it('does not misrepresent photo-only synthetic evidence as two cephalometries',async()=>{
    mockEvidence(false);
    render(<><R3CephaloTimepointReadonlyPanel patientId={17} ordinal={0}/>
      <R3CephaloTimepointReadonlyPanel patientId={17} ordinal={1}/></>);
    expect(await screen.findByTestId('r3-cephalo-missing-t0')).toBeTruthy();
    expect(await screen.findByTestId('r3-cephalo-missing-t1')).toBeTruthy();
    expect(screen.queryByText('Analyse source #300')).toBeNull();
  });
  it('denies a cross-patient comparison even with matching ordinals',async()=>{
    mockEvidence();
    vi.mocked(api.get).mockImplementation(async path=>{
      if(path==='/patients/17/ortho-case')return {data:{id:9,patient_id:17}} as never;
      if(path==='/patients/17/ortho-case/9/timepoints')return {data:timepoints} as never;
      return {data:{...compare(),patient_id:18}} as never;
    });
    render(<R3CephaloTimepointReadonlyPanel patientId={17} ordinal={0}/>);
    expect(await screen.findByRole('alert')).toBeTruthy();
  });
});
describe('LOT07 R3 patient presentation on this screen ONLY',()=>{
  it('never renders identifiable data before explicit clinician action; masks at once',async()=>{
    vi.mocked(api.get).mockResolvedValue({data:{id:55,patient_id:17,steps:[{
      id:1,title:'Étape réelle',assistant:'Dentiste',date_str:null,status:'pending'}]}} as never);
    render(<R3PatientPresentationPanel patient={patient}/>);
    expect(screen.queryByText('Patient SYNTHETIQUE')).toBeNull();
    expect(api.get).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button',{name:'Présenter sur cet écran'}));
    expect(await screen.findByText('Patient SYNTHETIQUE')).toBeTruthy();
    expect(screen.getByText(/Étape réelle/)).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:'Masquer immédiatement'}));
    expect(screen.queryByText('Patient SYNTHETIQUE')).toBeNull();
    expect(api.post).not.toHaveBeenCalled();expect(api.put).not.toHaveBeenCalled();
  });
  it('denies cross-patient plan and rejects late server reply after manual mask',async()=>{
    let resolve:(value:any)=>void=()=>{};
    vi.mocked(api.get).mockImplementation(()=>new Promise(r=>{resolve=r;}) as never);
    render(<R3PatientPresentationPanel patient={patient}/>);
    fireEvent.click(screen.getByRole('button',{name:'Présenter sur cet écran'}));
    fireEvent.click(screen.getByRole('button',{name:'Masquer immédiatement'}));
    await act(async()=>resolve({data:{id:51,patient_id:17,steps:[]}}));
    expect(screen.queryByText('Patient SYNTHETIQUE')).toBeNull();
    cleanup();
    vi.mocked(api.get).mockResolvedValue({data:{id:51,patient_id:18,steps:[]}} as never);
    render(<R3PatientPresentationPanel patient={patient}/>);
    fireEvent.click(screen.getByRole('button',{name:'Présenter sur cet écran'}));
    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.queryByText('Patient SYNTHETIQUE')).toBeNull();
  });
});
