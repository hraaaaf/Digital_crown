import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CephaloWorkspace } from './CephaloWorkspace';
import { api } from '../../services/api';
import { cephaloRepository } from './cephaloRepository';

const state = vi.hoisted(() => ({
  analysisId: 99 as number | undefined,
  imageSrc: undefined as string | undefined,
  mmPerPixel: 0.1 as number | null,
  local: { landmarks: [], version: 0 },
  syncState: 'idle',
  isSaving: false,
  previewPdfUrl: null as string | null,
  isPreviewLoading: false,
  step: 1 as 1|2|3|4,
  completedSteps: new Set<number>(),
  uploadError: null as string | null,
  isStep1Fullscreen: false,
  etape2Data: { occlusal: {}, type_arcade: null },
  etape3Data: { selectedAnalysis: 'COM', osseuse: {}, esthetique: {}, age: '', cvm: '' },
  diag: { analyse_moulages: '', diagnostic_squelettique:'', synthese_diagnostique:'', strategie_therapeutique:'' },
  setPatientInfo: vi.fn(),
  setAnalysisId: vi.fn(),
  setImageSrc: vi.fn(),
  setLocal: vi.fn(),
  setAnglesData: vi.fn(),
  setVisionMetadata: vi.fn(),
  setIsCalibrated: vi.fn(),
  setMmPerPixel: vi.fn(),
  setCompletedSteps: vi.fn(),
  setStep: vi.fn(),
  setDiag: vi.fn(),
  setEtape3Data: vi.fn(),
  setShowCalibration: vi.fn(),
  setCalibrationClickPoints: vi.fn(),
  setCalibrationDistance: vi.fn(),
  setCalibrationStep: vi.fn(),
  setImgDim: vi.fn(),
  setPreviewPdfUrl: vi.fn(),
  setIsPreviewLoading: vi.fn(),
  handleSave: vi.fn(),
  goToStep: vi.fn(),
  setIsStep1Fullscreen: vi.fn(),
}));

vi.mock('./stores/useOrthoStore', () => ({
  useOrthoStore: () => state,
}));
vi.mock('../../services/api', () => ({
  API_BASE:'http://api.test',
  api:{get:vi.fn()},
}));
vi.mock('./cephaloRepository', () => ({
  cephaloRepository:{getAnalysis:vi.fn()},
}));
vi.mock('./cephaloUtils', () => ({
  computeStep3Data: () => ({age:30,cvm:'',osseuse:{},esthetique:{},analyse_moulages_auto:''}),
}));
vi.mock('./cephaloTheme', () => ({
  getCephaloPalette: () => ({
    bg:'#fff',bgPanel:'#fff',bgCard:'#fff',bgInput:'#fff',border:'#ddd',borderFocus:'#00f',
    text:'#111',textMuted:'#666',textDim:'#999',accent:'#003380',accentSuccess:'#0a0',
    accentWarning:'#a60',accentError:'#d00',shadow:'none',shadowLg:'none'
  }),
}));
vi.mock('./components/Step1Cephalo', () => ({Step1Cephalo:()=> <div>Step 1 content</div>}));
vi.mock('./components/Step2Occlusal', () => ({Step2Occlusal:()=> <div>Step 2 content</div>}));
vi.mock('./components/Step3Clinical', () => ({Step3Clinical:()=> <div>Step 3 content</div>}));
vi.mock('./components/Step4Documents', () => ({Step4Documents:()=> <div>Step 4 content</div>}));
vi.mock('./components/ClinicalScientificStudio', () => ({ClinicalScientificStudio:()=> <div>Scientific studio</div>}));
vi.mock('./components/SyncBadge', () => ({SyncBadge:()=> <div>Sync badge</div>}));
vi.mock('./components/Step2BlockerModal', () => ({Step2BlockerModal:()=> <div>Calibration blocker</div>}));
vi.mock('../admin/DocumentStudio/LivePreview', () => ({LivePreview:()=> <div>Cephalo preview</div>}));
vi.mock('./CephaloHistory', () => ({
  CephaloHistory:({onSelect}:any)=><div>
    <span>Cephalo history</span>
    <button onClick={()=>onSelect({id:42})}>Open archived analysis</button>
  </div>
}));

beforeEach(()=>{
  vi.clearAllMocks();
  state.analysisId=99;
  state.imageSrc=undefined;
  state.step=1;
  state.completedSteps=new Set();
  state.local={landmarks:[],version:0};
  state.mmPerPixel=0.1;
  state.uploadError=null;
  state.previewPdfUrl=null;
  state.isPreviewLoading=false;
  state.etape2Data={occlusal:{},type_arcade:null};
  state.etape3Data={selectedAnalysis:'COM',osseuse:{},esthetique:{},age:'',cvm:''};
  state.diag={analyse_moulages:'',diagnostic_squelettique:'',synthese_diagnostique:'',strategie_therapeutique:''};
  state.setEtape3Data.mockImplementation((fn:any)=>{ if(typeof fn==='function') fn(state.etape3Data); });
  state.setDiag.mockImplementation((fn:any)=>{ if(typeof fn==='function') fn(state.diag); });

  vi.mocked(api.get).mockResolvedValue({data:{date_naissance:'1990-01-01',sexe:'F'}} as never);
  vi.mocked(cephaloRepository.getAnalysis).mockResolvedValue({
    id:42,
    image_original_path:'ceph/42.png',
    landmarks_data:[{id:'S',x:1,y:2}],
    angles_data:{SNA:82,vision_metadata:{model:'onnx'}},
    calibration_data:{mm_per_pixel:0.1},
    is_calibrated:true,
    mm_per_pixel:0.1,
  } as never);
});

afterEach(()=>cleanup());

describe('CephaloWorkspace G4 shell matrix',()=>{
  it('fails closed when patient age/sex truth is incomplete instead of inventing clinical data',async()=>{
    vi.mocked(api.get).mockResolvedValueOnce({data:{date_naissance:'1990-01-01',sexe:null}} as never);
    render(<CephaloWorkspace patientId={7} patientName="Sara BENALI"/>);

    expect(await screen.findByText('Données Patient requises')).toBeTruthy();
    expect(screen.getByText(/ne peut pas calculer avec un âge ou un sexe inventé/i)).toBeTruthy();
    expect(screen.queryByText('Step 1 content')).toBeNull();
  });

  it('wires all four step controls and previous/next navigation to the canonical goToStep boundary',async()=>{
    render(<CephaloWorkspace patientId={7} patientName="Sara BENALI"/>);
    expect(await screen.findByText('Step 1 content')).toBeTruthy();

    fireEvent.click(screen.getByRole('button',{name:'1. Céphalométrie'}));
    fireEvent.click(screen.getByRole('button',{name:'2. Moulages'}));
    fireEvent.click(screen.getByRole('button',{name:'3. Synthèse clinique'}));
    fireEvent.click(screen.getByRole('button',{name:'4. Documents & stratégie'}));
    expect(state.goToStep).toHaveBeenNthCalledWith(1,1);
    expect(state.goToStep).toHaveBeenNthCalledWith(2,2);
    expect(state.goToStep).toHaveBeenNthCalledWith(3,3);
    expect(state.goToStep).toHaveBeenNthCalledWith(4,4);

    fireEvent.click(screen.getByRole('button',{name:/Passer aux moulages/i}));
    expect(state.goToStep).toHaveBeenLastCalledWith(2);
  });

  it('saves only through the store save boundary and disables save when no analysis exists',async()=>{
    const view=render(<CephaloWorkspace patientId={7} patientName="Sara BENALI"/>);
    await screen.findByText('Step 1 content');
    const save=screen.getByRole('button',{name:'Sauvegarder'}) as HTMLButtonElement;
    expect(save.disabled).toBe(false);
    fireEvent.click(save);
    expect(state.handleSave).toHaveBeenCalledTimes(1);

    view.unmount();
    state.analysisId=undefined;
    render(<CephaloWorkspace patientId={7} patientName="Sara BENALI"/>);
    await screen.findByText('Step 1 content');
    expect((screen.getByRole('button',{name:'Sauvegarder'}) as HTMLButtonElement).disabled).toBe(true);
  });

  it('switches to history and hydrates the full archived scientific state before returning to studio',async()=>{
    render(<CephaloWorkspace patientId={7} patientName="Sara BENALI"/>);
    await screen.findByText('Step 1 content');

    fireEvent.click(screen.getByRole('button',{name:'Historique'}));
    expect(screen.getByText('Cephalo history')).toBeTruthy();

    fireEvent.click(screen.getByRole('button',{name:'Open archived analysis'}));
    await waitFor(()=>expect(cephaloRepository.getAnalysis).toHaveBeenCalledWith(42));

    expect(state.setAnalysisId).toHaveBeenCalledWith(42);
    expect(state.setImageSrc).toHaveBeenCalledWith('http://api.test/ceph/42.png');
    expect(state.setLocal).toHaveBeenCalledWith(expect.objectContaining({landmarks:[{id:'S',x:1,y:2}]}));
    expect(state.setAnglesData).toHaveBeenCalledWith(expect.objectContaining({SNA:82,__calibrationData:{mm_per_pixel:0.1}}));
    expect(state.setVisionMetadata).toHaveBeenCalledWith({model:'onnx'});
    expect(state.setIsCalibrated).toHaveBeenCalledWith(true);
    expect(state.setMmPerPixel).toHaveBeenCalledWith(0.1);
    expect(state.setCompletedSteps).toHaveBeenCalledWith(new Set([1]));
    expect(state.setStep).toHaveBeenCalledWith(1);
    expect(await screen.findByText('Step 1 content')).toBeTruthy();
  });

  it('keeps history visible and does not mutate scientific state when archived analysis loading fails',async()=>{
    vi.mocked(cephaloRepository.getAnalysis).mockRejectedValueOnce(new Error('history failed'));
    render(<CephaloWorkspace patientId={7} patientName="Sara BENALI"/>);
    await screen.findByText('Step 1 content');

    fireEvent.click(screen.getByRole('button',{name:'Historique'}));
    fireEvent.click(screen.getByRole('button',{name:'Open archived analysis'}));

    await waitFor(()=>expect(cephaloRepository.getAnalysis).toHaveBeenCalledWith(42));
    expect(screen.getByText('Cephalo history')).toBeTruthy();
    expect(state.setAnalysisId).not.toHaveBeenCalledWith(42);
  });
});
