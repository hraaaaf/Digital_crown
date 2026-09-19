import { act, cleanup, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useDocumentGenerator } from './useDocumentGenerator';
import { useAccountingStore } from '../store/useAccountingStore';
import { api } from '../../../services/api';

vi.mock('../../../services/api', () => ({
  API_BASE:'http://api.test',
  api:{post:vi.fn(),get:vi.fn()},
}));
vi.mock('react-hot-toast', () => {
  const toast:any=vi.fn();
  toast.error=vi.fn();
  toast.success=vi.fn();
  return {default:toast};
});

const base:any={
  patientId:'7',
  patientDetails:{id:7,nom:'BENALI',prenom:'Sara',date_naissance:'1990-01-01',genre:'F'},
  activeTab:'honoraires',
  drugs:[],
  certifType:'',
  certifDays:0,
  certifStartDate:'',
  certifCustomMotif:'',
  items:[{id:1,description:'Détartrage',dent:'11',price:500,category:'CONSERVATRICE',toothNumbers:[11]}],
  paymentMode:'Espèces',
  libreTitle:'',
  libreContent:'',
  libreCustomPatient:'',
  libreCustomDate:'',
  libreHideHeader:false,
  librePageSize:'A5',
  libreAlignment:'left',
  docDate:'2026-09-19',
  selectedTeethFromOdontogram:[],
  smartSuggestion:null,
  installments:[],
  isAccounted:true,
  paymentStatus:'PAYE',
  isGlobalNote:false,
  showLegalAnnotations:true,
};

beforeEach(()=>{
  vi.clearAllMocks();
  useAccountingStore.getState().reset();
  vi.stubGlobal('URL',{
    createObjectURL:vi.fn(()=> 'blob:test-pdf'),
    revokeObjectURL:vi.fn(),
  });
  vi.spyOn(window,'open').mockImplementation(()=>null);
});
afterEach(()=>{
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  useAccountingStore.getState().reset();
});

describe('Document generation G4 business pipeline',()=>{
  it('blocks an empty honorarium before any backend mutation',async()=>{
    const {result}=renderHook(()=>useDocumentGenerator({...base,items:[]}));
    await act(async()=>{await result.current.handleGenerate(true,false,false,false);});
    expect(api.post).not.toHaveBeenCalled();
    expect(result.current.validationErrors.some(e=>e.field==='items')).toBe(true);
  });

  it('blocks a paid honorarium with no payment method',async()=>{
    const {result}=renderHook(()=>useDocumentGenerator({...base,paymentMode:''}));
    await act(async()=>{await result.current.handleGenerate(true,false,false,false);});
    expect(api.post).not.toHaveBeenCalled();
    expect(result.current.validationErrors.some(e=>e.field==='paymentMode')).toBe(true);
  });

  it('archives a valid honorarium with exact accounting payload then opens the returned PDF',async()=>{
    useAccountingStore.setState({
      items:base.items,
      groupSelectedTeeth:[11],
      odontogramMode:'group',
    });
    vi.mocked(api.post).mockResolvedValueOnce({
      data:{pdf_url:'/files/note.pdf',status:'success'},
    } as never);
    vi.mocked(api.get).mockResolvedValueOnce({data:new Uint8Array([1,2,3])} as never);

    const {result}=renderHook(()=>useDocumentGenerator(base));
    await act(async()=>{await result.current.handleGenerate(true,false,false,false);});

    expect(api.post).toHaveBeenCalledWith(
      '/documents/generate?archive=true&preview=false&force=false',
      expect.objectContaining({
        type:'note',
        patient_id:7,
        is_accounted:true,
        payment_status:'PAYE',
        data:expect.objectContaining({
          doc_date:'2026-09-19',
          payments:[
            expect.objectContaining({
              acte:'Détartrage',
              dent:'11',
              dents:[11],
              prix_unitaire:500,
              montant:500,
              mode_reglement:'Espèces',
            }),
          ],
        }),
      }),
    );
    expect(api.get).toHaveBeenCalledWith('/files/note.pdf',{responseType:'blob'});
    expect(window.open).toHaveBeenCalledWith('blob:test-pdf','_blank');
    expect(useAccountingStore.getState().groupSelectedTeeth).toEqual([]);
    expect(useAccountingStore.getState().odontogramMode).toBe('individual');
    expect(useAccountingStore.getState().items).toHaveLength(1);
    expect(useAccountingStore.getState().items[0].description).toBe('');
  });

  it('preserves accounting state on backend refusal',async()=>{
    useAccountingStore.setState({items:base.items,groupSelectedTeeth:[11],odontogramMode:'group'});
    vi.mocked(api.post).mockRejectedValueOnce({response:{status:422,data:{detail:'Archivage refusé'}}});

    const {result}=renderHook(()=>useDocumentGenerator(base));
    await act(async()=>{await result.current.handleGenerate(true,false,false,false);});

    expect(useAccountingStore.getState().items[0].description).toBe('Détartrage');
    expect(useAccountingStore.getState().groupSelectedTeeth).toEqual([11]);
    expect(useAccountingStore.getState().odontogramMode).toBe('group');
    expect(window.open).not.toHaveBeenCalled();
  });

  it('requires explicit duplicate confirmation before retrying with force=true',async()=>{
    vi.mocked(api.post)
      .mockRejectedValueOnce({response:{status:409,data:{detail:{code:'DOUBLE_DETECTED'}}}})
      .mockResolvedValueOnce({data:{pdf_url:'/files/note.pdf'}} as never);
    vi.mocked(api.get).mockResolvedValueOnce({data:new Uint8Array([1])} as never);

    const {result}=renderHook(()=>useDocumentGenerator(base));
    await act(async()=>{await result.current.handleGenerate(true,false,false,false);});
    expect(result.current.showDuplicateModal).toBe(true);
    expect(api.post).toHaveBeenCalledTimes(1);

    await act(async()=>{result.current.confirmDuplicate();});
    await waitFor(()=>expect(api.post).toHaveBeenCalledTimes(2));
    expect(vi.mocked(api.post).mock.calls[1][0]).toBe('/documents/generate?archive=true&preview=false&force=true');
  });

  it('builds an ordonnance payload with legal-annotation choice and archives only a valid prescription',async()=>{
    vi.mocked(api.post).mockResolvedValueOnce({data:{pdf_url:'/files/rx.pdf'}} as never);
    vi.mocked(api.get).mockResolvedValueOnce({data:new Uint8Array([1])} as never);
    const params={
      ...base,
      activeTab:'ordonnance',
      paymentStatus:'EN_ATTENTE',
      drugs:[{id:1,name:'AMOXICILLINE',dosage:'1g',forme:'Gélules',posologie:'1 x 2/j',type:'MEDICAMENT'}],
      showLegalAnnotations:false,
    };
    const {result}=renderHook(()=>useDocumentGenerator(params as any));
    await act(async()=>{await result.current.handleGenerate(true,false,false,false);});

    expect(api.post).toHaveBeenCalledWith(
      '/documents/generate?archive=true&preview=false&force=false',
      expect.objectContaining({
        type:'ordonnance',
        data:expect.objectContaining({
          show_legal_annotations:false,
          medications:[expect.objectContaining({
            nom:'AMOXICILLINE',dosage:'1g',forme:'Gélules',posologie:'1 x 2/j',
          })],
        }),
      }),
    );
  });

  it('blocks an ordonnance drug without posology before backend mutation',async()=>{
    const params={
      ...base,
      activeTab:'ordonnance',
      drugs:[{id:1,name:'AMOXICILLINE',dosage:'1g',forme:'Gélules',posologie:'',type:'MEDICAMENT'}],
    };
    const {result}=renderHook(()=>useDocumentGenerator(params as any));
    await act(async()=>{await result.current.handleGenerate(true,false,false,false);});

    expect(api.post).not.toHaveBeenCalled();
    expect(result.current.validationErrors.some(e=>e.field==='drug_0')).toBe(true);
  });
});
