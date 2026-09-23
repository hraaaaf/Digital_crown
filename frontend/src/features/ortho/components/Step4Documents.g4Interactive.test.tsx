import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Step4Documents } from './Step4Documents';
import { REQUIRED_LANDMARKS } from '../cephaloShared';
import { api } from '../../../services/api';

const state = vi.hoisted(() => ({
  photos:[
    {id:'radio',type:'radio',file:null,preview:null,label:'Radiographie Céphalométrique'},
    {id:'extra_face',type:'extra_face',file:null,preview:null,label:'Photo Extra-orale Face'},
  ],
  handlePhotoUpload:vi.fn(),
  handlePrint:vi.fn(),
  handlePreview:vi.fn(),
  silentSave:vi.fn(),
  isPrinting:false,
  isPreviewLoading:false,
  etape3Data:{preference_technique:'',cvm:''},
  diag:{synthese_diagnostique:'Synthèse praticien',strategie_therapeutique:''},
  setEtape3Data:vi.fn(),
  setDiag:vi.fn(),
  anglesData:{},
  patientId:7 as number|null,
  patientName:'Sara BENALI',
  analysisId:99 as number|undefined,
  imageSrc:'blob:cephalo' as string|undefined,
  isCalibrated:true,
  local:{landmarks:[] as any[]},
}));

vi.mock('../stores/useOrthoStore',()=>({
  useOrthoStore:()=>state,
}));
vi.mock('../../../services/api',()=>({
  api:{get:vi.fn(),post:vi.fn()},
}));
vi.mock('react-hot-toast',()=>{
  const toast:any=vi.fn();
  toast.success=vi.fn();
  toast.error=vi.fn();
  return {default:toast};
});

const P:any={
  bg:'#fff',bgPanel:'#fff',bgCard:'#fff',bgInput:'#fff',border:'#ddd',
  text:'#111',textMuted:'#666',textDim:'#999',accent:'#003380'
};

beforeEach(()=>{
  vi.clearAllMocks();
  state.analysisId=99;
  state.imageSrc='blob:cephalo';
  state.isCalibrated=true;
  state.local={landmarks:REQUIRED_LANDMARKS.map((id:string,i:number)=>({id,x:i,y:i}))};
  state.diag={synthese_diagnostique:'Synthèse praticien',strategie_therapeutique:''};
  state.etape3Data={preference_technique:'',cvm:''};
  state.setEtape3Data.mockImplementation((fn:any)=>{ if(typeof fn==='function') fn(state.etape3Data); });
  state.setDiag.mockImplementation((fn:any)=>{ if(typeof fn==='function') fn(state.diag); });
  state.silentSave.mockResolvedValue(undefined);
  state.handlePrint.mockResolvedValue(undefined);
  state.handlePreview.mockResolvedValue(undefined);

  vi.mocked(api.get).mockResolvedValue({data:{is_valid:true,fatals:[],warnings:[]}} as never);
  vi.mocked(api.post).mockResolvedValue({data:new Uint8Array([1,2,3])} as never);
  vi.stubGlobal('URL',{createObjectURL:vi.fn(()=> 'blob:draft'),revokeObjectURL:vi.fn()});
});

afterEach(()=>{
  cleanup();
  vi.unstubAllGlobals();
});

describe('Cephalo Step4 G4 document controls',()=>{
  it('disables archive when scientific prerequisites are incomplete',async()=>{
    state.imageSrc=undefined;
    state.local={landmarks:[]};
    render(<Step4Documents P={P}/>);
    await waitFor(()=>expect(api.get).toHaveBeenCalledWith('/patients/7/cephalo-validation'));

    expect((screen.getByRole('button',{name:/Archiver le bilan/i}) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByText(/Aucune image uploadée/i)).toBeTruthy();
    expect(screen.getByText(/0% des points requis placés/i)).toBeTruthy();
  });

  it('previews only through the canonical preview boundary',async()=>{
    render(<Step4Documents P={P}/>);
    await waitFor(()=>expect(api.get).toHaveBeenCalled());

    const preview=screen.getByRole('button',{name:/Prévisualiser/i}) as HTMLButtonElement;
    expect(preview.disabled).toBe(false);
    fireEvent.click(preview);
    expect(state.handlePreview).toHaveBeenCalledTimes(1);
    expect(state.handlePrint).not.toHaveBeenCalled();
  });

  it('builds a draft by silent-saving first, then downloading the non-archived PDF',async()=>{
    const click=vi.fn();
    const original=document.createElement.bind(document);
    vi.spyOn(document,'createElement').mockImplementation(((tag:string)=>{
      const el=original(tag);
      if(tag==='a') Object.defineProperty(el,'click',{value:click});
      return el;
    }) as typeof document.createElement);

    render(<Step4Documents P={P}/>);
    await waitFor(()=>expect(api.get).toHaveBeenCalled());

    fireEvent.click(screen.getByRole('button',{name:/Brouillon PDF/i}));

    await waitFor(()=>expect(state.silentSave).toHaveBeenCalledTimes(1));
    expect(api.post).toHaveBeenCalledWith('/patients/7/pdf',{}, {responseType:'arraybuffer'});
    expect(click).toHaveBeenCalledTimes(1);
    expect(state.handlePrint).not.toHaveBeenCalled();
  });

  it('revalidates immediately before archive and archives only when no fatal remains',async()=>{
    vi.mocked(api.get)
      .mockResolvedValueOnce({data:{is_valid:true,fatals:[],warnings:[]}} as never)
      .mockResolvedValueOnce({data:{is_valid:true,fatals:[],warnings:['Avertissement']}} as never);

    render(<Step4Documents P={P}/>);
    await waitFor(()=>expect(api.get).toHaveBeenCalledTimes(1));

    const archive=screen.getByRole('button',{name:/Archiver le bilan/i}) as HTMLButtonElement;
    expect(archive.disabled).toBe(false);
    fireEvent.click(archive);

    await waitFor(()=>expect(api.get).toHaveBeenCalledTimes(2));
    expect(state.handlePrint).toHaveBeenCalledTimes(1);
  });

  it('blocks archive when the just-in-time backend validation returns a fatal',async()=>{
    vi.mocked(api.get)
      .mockResolvedValueOnce({data:{is_valid:true,fatals:[],warnings:[]}} as never)
      .mockResolvedValueOnce({data:{is_valid:false,fatals:['Landmarks incohérents'],warnings:[]}} as never);

    render(<Step4Documents P={P}/>);
    await waitFor(()=>expect(api.get).toHaveBeenCalledTimes(1));

    fireEvent.click(screen.getByRole('button',{name:/Archiver le bilan/i}));
    await waitFor(()=>expect(api.get).toHaveBeenCalledTimes(2));
    expect(state.handlePrint).not.toHaveBeenCalled();
    expect(await screen.findByText('Landmarks incohérents')).toBeTruthy();
  });

  it('refreshes coherence validation only when explicitly requested',async()=>{
    render(<Step4Documents P={P}/>);
    await waitFor(()=>expect(api.get).toHaveBeenCalledTimes(1));

    const refresh=await screen.findByRole('button',{name:'Actualiser'});
    fireEvent.click(refresh);
    await waitFor(()=>expect(api.get).toHaveBeenCalledTimes(2));
  });

  it('wires photo upload and practitioner-entered therapeutic metadata explicitly',async()=>{
    render(<Step4Documents P={P}/>);
    await waitFor(()=>expect(api.get).toHaveBeenCalled());

    const file=new File(['photo'],'face.jpg',{type:'image/jpeg'});
    const photoInputs=[...document.querySelectorAll('input[type="file"]')] as HTMLInputElement[];
    fireEvent.change(photoInputs[0],{target:{files:[file]}});
    expect(state.handlePhotoUpload).toHaveBeenCalledWith('radio',file);

    const selects=screen.getAllByRole('combobox');
    fireEvent.change(selects[0],{target:{value:'ALIGNEURS'}});
    expect(state.setEtape3Data).toHaveBeenCalled();

    fireEvent.change(selects[1],{target:{value:'CS4'}});
    expect(state.setEtape3Data).toHaveBeenCalled();

    fireEvent.change(screen.getByPlaceholderText(/Saisie libre ou contenu historique/i),{target:{value:'Note praticien'}});
    expect(state.setDiag).toHaveBeenCalled();
  });
});
