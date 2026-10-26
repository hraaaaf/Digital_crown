import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { AppUser } from '../../types';
import { useAuthStore } from '../../stores/useAuthStore';
import { workstationModeService } from '../../services/workstationMode';
import { api } from '../../services/api';

vi.mock('../../services/workstationMode',()=>({
  workstationModeService:{getBootstrapState:vi.fn(),subscribe:vi.fn(()=>()=>{})},
}));
vi.mock('../../services/api',()=>({API_BASE:'http://localhost:8005',api:{get:vi.fn()}}));
vi.mock('../patients/components/PatientMediaTimeline',()=>({
  PatientMediaTimeline:({patientId,readOnly,fixedAssetType}:{patientId:number;readOnly?:boolean;fixedAssetType?:string})=><div data-testid="media-live" data-read-only={String(Boolean(readOnly))} data-fixed-type={fixedAssetType ?? 'ALL'}>Media API module patient {patientId}</div>,
}));
vi.mock('../ortho/OrthoLongitudinalComparePanel',()=>({
  OrthoLongitudinalComparePanel:({patientId}:{patientId:number})=><div data-testid="suivi-live">Longitudinal patient {patientId}</div>,
}));
import { CabinetMultiViewLab, isCabinetMultiViewLabEnabled, isR3SplitLabEnabled, isR3FocusLabEnabled } from './CabinetMultiViewLab';

const patient={id:17,prenom:'Prénom-A',nom:'NOM-A',numero_dossier:'DOS-A'};
const user=(permissions:Record<string,boolean>={patients:true,cephalo:true})=>({
  id:'actor-A',role:'SECRETAIRE',employer_id:11,permissions,
} as unknown as AppUser);
let desktop=true;

beforeEach(()=>{
  vi.clearAllMocks();
  desktop=true;
  Object.defineProperty(window,'innerWidth',{configurable:true,value:1920});
  Object.defineProperty(window,'matchMedia',{configurable:true,value:vi.fn(()=>({
    get matches(){return desktop;},media:'(min-width: 1280px)',
    addEventListener:vi.fn(),removeEventListener:vi.fn(),
  }))});
  vi.stubGlobal('ResizeObserver',class {
    observe=vi.fn();disconnect=vi.fn();unobserve=vi.fn();
    constructor(_cb:ResizeObserverCallback){}
  });
  vi.spyOn(HTMLElement.prototype,'getBoundingClientRect').mockImplementation(()=>({
    x:0,y:0,top:0,left:0,right:1600,bottom:800,width:1600,height:800,toJSON:()=>({}),
  }));
  vi.mocked(workstationModeService.getBootstrapState).mockResolvedValue({
    workstationId:'workstation-verified',authenticated:true,enrollmentRequired:false,
    defaultExperience:'cabinet',stationLocked:false,stationEscapeAuthorized:false,
  });
  vi.mocked(api.get).mockResolvedValue({data:patient} as never);
  useAuthStore.setState({user:user(),isAuthenticated:true,isLoading:false});
});
afterEach(()=>{
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  useAuthStore.setState({user:null,isAuthenticated:false,isLoading:false});
});

describe('07.1.A/B actual Cabinet DEV opt-in G1 adapter',()=>{
  it('is hard-disabled in production even if the opt-in flag is set',()=>{
    expect(isCabinetMultiViewLabEnabled(false,'1')).toBe(false);
    expect(isCabinetMultiViewLabEnabled(true,undefined)).toBe(false);
    expect(isCabinetMultiViewLabEnabled(true,'true')).toBe(false);
    expect(isCabinetMultiViewLabEnabled(true,'1')).toBe(true);
    expect(isR3SplitLabEnabled(false,'1')).toBe(false);
    expect(isR3SplitLabEnabled(true,undefined)).toBe(false);
    expect(isR3SplitLabEnabled(true,'true')).toBe(false);
    expect(isR3SplitLabEnabled(true,'1')).toBe(true);
    expect(isR3FocusLabEnabled(false,'1')).toBe(false);
    expect(isR3FocusLabEnabled(true,undefined)).toBe(false);
    expect(isR3FocusLabEnabled(true,'true')).toBe(false);
    expect(isR3FocusLabEnabled(true,'1')).toBe(true);
  });

  it('mounts the real MultiView imagerie adapter in read-only R mode',async()=>{
    render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={user()}/>);
    await screen.findByTestId('multiview-real-dossier');
    expect(screen.getByTestId('media-live').getAttribute('data-read-only')).toBe('true');
  });

  it('requires real signed-in workstation bootstrap AND fresh exact-patient GET before mounting media',async()=>{
    const {container}=render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={user()}/>);
    expect(screen.queryByTestId('media-live')).toBeNull();
    await screen.findByTestId('multiview-real-dossier');
    expect(screen.getAllByTestId('media-live')).toHaveLength(1);
    expect(screen.getByText('DOS-A')).toBeTruthy();
    expect(vi.mocked(api.get)).toHaveBeenCalledWith('/patients/17');
    expect(vi.mocked(workstationModeService.getBootstrapState)).toHaveBeenCalled();
    expect(container.querySelectorAll('[data-v15-071-viewslot]')).toHaveLength(2);
  });

  it('accepts an authenticated enrolled Cabinet workstation with no selected default mode',async()=>{
    vi.mocked(workstationModeService.getBootstrapState).mockResolvedValue({
      workstationId:'ws-cabinet-initial',authenticated:true,enrollmentRequired:false,
      defaultExperience:null,stationLocked:false,stationEscapeAuthorized:false,
    });
    render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={user()}/>);
    await screen.findByTestId('multiview-real-dossier');
    expect(screen.getAllByTestId('media-live')).toHaveLength(1);
  });

  it('refuses mounting all clinical slots when workstation enrollment or mode is not verified',async()=>{
    vi.mocked(workstationModeService.getBootstrapState).mockResolvedValue({
      workstationId:null,authenticated:true,enrollmentRequired:true,
      defaultExperience:'station',stationLocked:true,stationEscapeAuthorized:false,
    });
    render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={user()}/>);
    await waitFor(()=>expect(vi.mocked(api.get)).toHaveBeenCalled());
    expect(screen.queryByTestId('media-live')).toBeNull();
    expect(screen.queryByTestId('multiview-real-dossier')).toBeNull();
    expect(screen.getByRole('alert').textContent).toContain('indisponibles');
  });

  it('does not query any patient or mount views when route patient differs, or when patients access is revoked',async()=>{
    const actor=user({patients:false,cephalo:true});
    useAuthStore.setState({user:actor,isAuthenticated:true});
    const {rerender}=render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={actor}/>);
    expect(screen.getByRole('alert').textContent).toContain('refusées');
    expect(vi.mocked(api.get)).not.toHaveBeenCalled();
    expect(vi.mocked(workstationModeService.getBootstrapState)).not.toHaveBeenCalled();
    const permitted=user();
    useAuthStore.setState({user:permitted,isAuthenticated:true});
    rerender(<CabinetMultiViewLab patient={patient} routePatientId="18" user={permitted}/>);
    expect(screen.getByRole('alert').textContent).toContain('refusées');
    expect(vi.mocked(api.get)).not.toHaveBeenCalled();
  });

  it('shows all 9 roadmap directions disabled and previews without mounting extra API modules',async()=>{
    render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={user()}/>);
    await screen.findByTestId('multiview-real-dossier');
    const select=screen.getByRole('combobox',{name:'Disposition MultiView'});
    expect(select.querySelectorAll('option:disabled')).toHaveLength(9);
    expect(screen.queryByTestId('suivi-live')).toBeNull();
    fireEvent.change(select,{target:{value:'dossier-media-suivi-3cols'}});
    fireEvent.click(screen.getByRole('button',{name:'Aperçu'}));
    expect(screen.getByTestId('multiview-schematic-preview')).toBeTruthy();
    expect(screen.queryByTestId('suivi-live')).toBeNull();
    fireEvent.click(screen.getByRole('button',{name:'Appliquer'}));
    expect(await screen.findByTestId('suivi-live')).toBeTruthy();
    expect(screen.getAllByTestId('media-live')).toHaveLength(1);
    expect(screen.queryByTestId('multiview-schematic-preview')).toBeNull();
    fireEvent.click(screen.getByRole('button',{name:'Échanger les vues'}));
    expect(screen.getAllByTestId('media-live')).toHaveLength(1);
    fireEvent.click(screen.getByRole('button',{name:'Réinitialiser'}));
    expect(screen.queryByTestId('suivi-live')).toBeNull();
  });

  it('R3-1 opt-in mounts an interactive split over the SAME verified real read-only modules',async()=>{
    render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={user()} enableR3Split/>);
    await screen.findByTestId('multiview-real-dossier');
    expect(screen.getByTestId('media-live').getAttribute('data-read-only')).toBe('true');
    const sep=screen.getByRole('separator',{name:'Séparateur vertical des panneaux'});
    expect(sep.getAttribute('aria-valuenow')).toBe('50');
    fireEvent.keyDown(sep,{key:'ArrowRight'});
    expect(sep.getAttribute('aria-valuenow')).toBe('55');
    fireEvent.click(screen.getByRole('button',{name:'Réinitialiser'}));
    expect(screen.getByRole('separator').getAttribute('aria-valuenow')).toBe('50');
    expect(screen.getAllByTestId('media-live')).toHaveLength(1);
    const select=screen.getByRole('combobox',{name:'Disposition MultiView'});
    fireEvent.change(select,{target:{value:'dossier-media-2rows'}});
    fireEvent.click(screen.getByRole('button',{name:'Aperçu'}));
    fireEvent.click(screen.getByRole('button',{name:'Appliquer'}));
    expect(screen.getByRole('separator',{name:'Séparateur horizontal des panneaux'})).toBeTruthy();
    expect(screen.getByTestId('media-live').getAttribute('data-read-only')).toBe('true');
  });

  it('R3 premium toolbar groups actions while retaining the R-only, nine-disabled-preset contract',async()=>{
    render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={user()} enableR3Split/>);
    await screen.findByTestId('multiview-real-dossier');
    expect(screen.getByTestId('r3-1-premium-actions')).toBeTruthy();
    expect(screen.getByRole('group',{name:'Disposition des panneaux'})).toBeTruthy();
    expect(screen.getByRole('group',{name:'Outils de disposition'})).toBeTruthy();
    expect(screen.getByRole('group',{name:'Confirmation de disposition'})).toBeTruthy();
    expect(screen.getByTestId('r3-1-dossier-readonly-help').textContent).toContain('consultation seule');
    expect(screen.getByRole('combobox',{name:'Disposition MultiView'}).querySelectorAll('option:disabled')).toHaveLength(9);
    expect(screen.getByTestId('media-live').getAttribute('data-read-only')).toBe('true');
    expect(screen.getByRole('button',{name:'Appliquer'}).hasAttribute('disabled')).toBe(true);
    fireEvent.change(screen.getByRole('combobox',{name:'Disposition MultiView'}),{target:{value:'dossier-media-2rows'}});
    fireEvent.click(screen.getByRole('button',{name:'Aperçu'}));
    expect(screen.getByTestId('multiview-schematic-preview')).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:'Appliquer'}));
    expect(screen.getByRole('separator',{name:'Séparateur horizontal des panneaux'})).toBeTruthy();
    expect(screen.queryByTestId('multiview-schematic-preview')).toBeNull();
    fireEvent.click(screen.getByRole('button',{name:'Réinitialiser'}));
    expect(screen.getByRole('separator',{name:'Séparateur vertical des panneaux'})).toBeTruthy();
    expect(screen.getAllByTestId('media-live')).toHaveLength(1);
  });

  it('R3 module selector previews swaps without mounting duplicates, then applies or cancels',async()=>{
    render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={user()}
      enableR3Split enableR3Focus/>);
    await screen.findByTestId('multiview-real-dossier');
    expect(screen.getByTestId('r3-module-chooser')).toBeTruthy();
    const modules=screen.getByRole('combobox',{name:'Module panneau 1'});
    expect((modules as HTMLSelectElement).value).toBe('dossier');
    fireEvent.change(modules,{target:{value:'suivi'}});
    expect((modules as HTMLSelectElement).value).toBe('suivi');
    // Draft does not mutate the mounted real modules before Apply.
    expect(screen.getByTestId('multiview-real-dossier')).toBeTruthy();
    expect(screen.queryByTestId('suivi-live')).toBeNull();
    fireEvent.click(screen.getByRole('button',{name:'Annuler'}));
    expect((screen.getByRole('combobox',{name:'Module panneau 1'}) as HTMLSelectElement).value)
      .toBe('dossier');

    fireEvent.change(screen.getByRole('combobox',{name:'Module panneau 1'}),{target:{value:'suivi'}});
    fireEvent.click(screen.getByRole('button',{name:'Aperçu'}));
    expect(screen.getByTestId('multiview-schematic-preview')).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:'Appliquer'}));
    expect(screen.getByTestId('suivi-live')).toBeTruthy();
    expect(screen.queryByTestId('multiview-real-dossier')).toBeNull();
    expect(screen.getAllByTestId('media-live')).toHaveLength(1);
    expect(screen.getByTestId('media-live').getAttribute('data-read-only')).toBe('true');
    expect(screen.getByTestId('r3-module-chooser')).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:'Réinitialiser'}));
    expect(screen.getByTestId('multiview-real-dossier')).toBeTruthy();
    expect(screen.queryByTestId('suivi-live')).toBeNull();
    expect(screen.getAllByTestId('media-live')).toHaveLength(1);
    expect(screen.getByRole('combobox',{name:'Disposition MultiView'})
      .querySelectorAll('option:disabled')).toHaveLength(7);
  });

  it('R3 selector swaps all three authorized slots without duplicated clinical viewers',async()=>{
    render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={user()}
      enableR3Split enableR3Focus/>);
    await screen.findByTestId('multiview-real-dossier');
    fireEvent.change(screen.getByRole('combobox',{name:'Disposition MultiView'}),{
      target:{value:'dossier-media-suivi-3cols'},
    });
    fireEvent.click(screen.getByRole('button',{name:'Aperçu'}));
    fireEvent.click(screen.getByRole('button',{name:'Appliquer'}));
    const chooser=screen.getByRole('combobox',{name:'Module panneau 1'});
    expect((chooser as HTMLSelectElement).value).toBe('dossier');
    fireEvent.change(chooser,{target:{value:'suivi'}});
    expect((screen.getByRole('combobox',{name:'Module panneau 3'}) as HTMLSelectElement).value)
      .toBe('dossier');
    fireEvent.click(screen.getByRole('button',{name:'Aperçu'}));
    fireEvent.click(screen.getByRole('button',{name:'Appliquer'}));
    const panes=screen.getByTestId('r3-2-three-real-panes').querySelectorAll('[data-v15-071-viewslot]');
    expect(Array.from(panes,el=>el.getAttribute('data-v15-071-viewslot')))
      .toEqual(['suivi','imagerie','dossier']);
    expect(screen.getAllByTestId('media-live')).toHaveLength(1);
    expect(screen.getByTestId('media-live').getAttribute('data-read-only')).toBe('true');
  });

  it('offers 3/9 genuine roadmap layouts only when Agenda and patient permissions are verified',async()=>{
    const actor=user({patients:true,cephalo:true,agenda:true});
    useAuthStore.setState({user:actor,isAuthenticated:true});
    vi.mocked(api.get).mockImplementation(async url =>
      url.startsWith('/appointments/?') ? {data:[]} as never : {data:patient} as never);
    render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={actor}
      enableR3Split enableR3Focus/>);
    await screen.findByTestId('multiview-real-dossier');
    const select=screen.getByRole('combobox',{name:'Disposition MultiView'});
    expect(select.querySelectorAll('option:disabled')).toHaveLength(3);
    for(const id of ['vue-ensemble','consultation','agenda-cabinet','suivi-clinique','imagerie','gestion-administrative'])
      expect(select.querySelector('option[value="'+id+'"]')).toBeTruthy();
    expect(select.querySelector('option[value="future-comparaison-orthodontique"]')?.hasAttribute('disabled')).toBe(true);
    fireEvent.change(select,{target:{value:'vue-ensemble'}});
    fireEvent.click(screen.getByRole('button',{name:'Aperçu'}));
    fireEvent.click(screen.getByRole('button',{name:'Appliquer'}));
    expect(await screen.findByTestId('r3-real-agenda')).toBeTruthy();
    expect(screen.getByTestId('multiview-real-dossier')).toBeTruthy();
    expect(screen.getAllByTestId('media-live')).toHaveLength(1);
    expect(screen.getByTestId('media-live').getAttribute('data-read-only')).toBe('true');
    expect(screen.getByTestId('r3-2-three-real-panes')).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:'Agrandir le panneau 2 : agenda'}));
    expect(screen.getByTestId('r3-2-single-focus')).toBeTruthy();
    expect(screen.queryByTestId('multiview-real-dossier')).toBeNull();
    expect(screen.queryByTestId('media-live')).toBeNull();
    fireEvent.click(screen.getByRole('button',{name:'Restaurer les trois panneaux'}));
    expect(screen.getByTestId('multiview-real-dossier')).toBeTruthy();

    fireEvent.change(select,{target:{value:'consultation'}});
    fireEvent.click(screen.getByRole('button',{name:'Aperçu'}));
    fireEvent.click(screen.getByRole('button',{name:'Appliquer'}));
    expect(screen.getByTestId('r3-real-agenda')).toBeTruthy();
    expect(screen.queryByTestId('media-live')).toBeNull();
    fireEvent.change(select,{target:{value:'agenda-cabinet'}});
    fireEvent.click(screen.getByRole('button',{name:'Aperçu'}));
    fireEvent.click(screen.getByRole('button',{name:'Appliquer'}));
    expect(screen.getByTestId('r3-real-agenda')).toBeTruthy();
    expect(screen.getByTestId('multiview-real-dossier')).toBeTruthy();

    fireEvent.change(select,{target:{value:'suivi-clinique'}});
    fireEvent.click(screen.getByRole('button',{name:'Aperçu'}));
    fireEvent.click(screen.getByRole('button',{name:'Appliquer'}));
    expect(screen.getByTestId('suivi-live')).toBeTruthy();
    expect(screen.getByTestId('media-live').getAttribute('data-read-only')).toBe('true');
    expect(screen.getByTestId('r3-module-chooser')).toBeTruthy();
    expect(select.querySelectorAll('option:disabled')).toHaveLength(3);

    fireEvent.change(select,{target:{value:'gestion-administrative'}});
    fireEvent.click(screen.getByRole('button',{name:'Aperçu'}));
    fireEvent.click(screen.getByRole('button',{name:'Appliquer'}));
    expect(screen.getByTestId('r3-real-agenda')).toBeTruthy();
    expect(screen.getByTestId('media-live').getAttribute('data-fixed-type')).toBe('DOCUMENT');
    expect(screen.getByTestId('media-live').getAttribute('data-read-only')).toBe('true');
    expect(screen.queryByTestId('multiview-real-dossier')).toBeNull();
  });

  it('Imagerie preset uses independent real RADIOGRAPH and PHOTO media adapters, both R-only',async()=>{
    render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={user()}
      enableR3Split enableR3Focus/>);
    await screen.findByTestId('multiview-real-dossier');
    const select=screen.getByRole('combobox',{name:'Disposition MultiView'});
    expect(select.querySelector('option[value="imagerie"]')).toBeTruthy();
    fireEvent.change(select,{target:{value:'imagerie'}});
    fireEvent.click(screen.getByRole('button',{name:'Aperçu'}));
    fireEvent.click(screen.getByRole('button',{name:'Appliquer'}));
    const viewers=screen.getAllByTestId('media-live');
    expect(viewers).toHaveLength(2);
    expect(viewers.map(x=>x.getAttribute('data-fixed-type'))).toEqual(['RADIOGRAPH','PHOTO']);
    expect(viewers.every(x=>x.getAttribute('data-read-only')==='true')).toBe(true);
    expect(screen.queryByTestId('suivi-live')).toBeNull();
    expect(screen.queryByTestId('multiview-real-dossier')).toBeNull();
    expect(select.querySelectorAll('option:disabled')).toHaveLength(7);
  });

  it('R3-2 triple-opt-in mounts exactly three TRUE R-only slots and focus unmounts the rest',async()=>{
    render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={user()}
      enableR3Split enableR3Focus/>);
    await screen.findByTestId('multiview-real-dossier');
    const select=screen.getByRole('combobox',{name:'Disposition MultiView'});
    fireEvent.change(select,{target:{value:'dossier-media-suivi-3cols'}});
    fireEvent.click(screen.getByRole('button',{name:'Aperçu'}));
    fireEvent.click(screen.getByRole('button',{name:'Appliquer'}));
    expect(screen.getByTestId('r3-2-three-real-panes')).toBeTruthy();
    expect(screen.getByTestId('multiview-ronly-contract').textContent).toContain('R · lecture seule');
    expect(screen.getByRole('heading',{name:'MultiView'})).toBeTruthy();
    expect(screen.getByRole('button',{name:'Échanger les vues'})).toBeTruthy();
    expect(screen.getByRole('button',{name:'Réinitialiser'})).toBeTruthy();
    expect(screen.getByRole('button',{name:'Agrandir le panneau 2 : imagerie'}).textContent).toContain('Médias');
    expect(screen.getAllByRole('region',{name:/Panneau /})).toHaveLength(3);
    expect(screen.getByTestId('media-live').getAttribute('data-read-only')).toBe('true');
    expect(screen.getAllByTestId('media-live')).toHaveLength(1);
    expect(screen.getByTestId('suivi-live')).toBeTruthy();
    expect(screen.getByTestId('multiview-real-dossier')).toBeTruthy();
    expect(select.querySelectorAll('option:disabled')).toHaveLength(7);

    fireEvent.click(screen.getByRole('button',{name:'Agrandir le panneau 2 : imagerie'}));
    expect(screen.getByTestId('r3-2-single-focus')).toBeTruthy();
    expect(screen.getByTestId('media-live').getAttribute('data-read-only')).toBe('true');
    expect(screen.queryByTestId('suivi-live')).toBeNull();
    expect(screen.queryByTestId('multiview-real-dossier')).toBeNull();
    fireEvent.click(screen.getByRole('button',{name:'Restaurer les trois panneaux'}));
    expect(screen.getByTestId('r3-2-three-real-panes')).toBeTruthy();
    expect(screen.getByTestId('suivi-live')).toBeTruthy();
    expect(screen.getAllByTestId('media-live')).toHaveLength(1);
  });

  it('R3-2 cannot activate with only the R3-1 flag; no new R3-2 viewer mounts',async()=>{
    render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={user()}
      enableR3Split enableR3Focus={false}/>);
    await screen.findByTestId('multiview-real-dossier');
    const select=screen.getByRole('combobox',{name:'Disposition MultiView'});
    fireEvent.change(select,{target:{value:'dossier-media-suivi-3cols'}});
    fireEvent.click(screen.getByRole('button',{name:'Aperçu'}));
    fireEvent.click(screen.getByRole('button',{name:'Appliquer'}));
    expect(screen.queryByTestId('r3-2-three-real-panes')).toBeNull();
    expect(screen.queryByRole('group',{name:'Agrandir un panneau'})).toBeNull();
    expect(screen.getByTestId('suivi-live')).toBeTruthy();
  });

  it('R3-2 hides three-pane selectors and mounted sources without a cephalo permission',async()=>{
    const restricted=user({patients:true,cephalo:false});
    useAuthStore.setState({user:restricted,isAuthenticated:true});
    render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={restricted}
      enableR3Split enableR3Focus/>);
    await screen.findByTestId('multiview-real-dossier');
    const select=screen.getByRole('combobox',{name:'Disposition MultiView'});
    expect(select.querySelector('option[value="dossier-media-suivi-3cols"]')).toBeNull();
    expect(select.querySelector('option[value="dossier-media-suivi-hero"]')).toBeNull();
    expect(screen.queryByTestId('r3-2-three-real-panes')).toBeNull();
    expect(screen.queryByTestId('suivi-live')).toBeNull();
  });

  it('does not offer longitudinal comparison without the canonical cephalo permission',async()=>{
    const actor=user({patients:true,cephalo:false});
    useAuthStore.setState({user:actor,isAuthenticated:true});
    render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={actor}/>);
    await screen.findByTestId('media-live');
    const s=screen.getByRole('combobox',{name:'Disposition MultiView'});
    expect(s.querySelector('option[value="dossier-media-suivi-3cols"]')).toBeNull();
    expect(s.querySelector('option[value="dossier-media-suivi-hero"]')).toBeNull();
  });

  it('uses read-only mode for the verified desktop fallback when panels are too narrow',async()=>{
    vi.spyOn(HTMLElement.prototype,'getBoundingClientRect').mockImplementation(()=>({
      x:0,y:0,top:0,left:0,right:1200,bottom:800,width:1200,height:800,toJSON:()=>({}),
    }));
    render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={user()}/>);
    await screen.findByTestId('multiview-responsive-single-media-fallback');
    expect(screen.getByTestId('media-live').getAttribute('data-read-only')).toBe('true');
  });

  it('preserves the existing single media module on narrow screens with no workspace bootstrap',async()=>{
    desktop=false;
    render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={user()}/>);
    expect(screen.getAllByTestId('media-live')).toHaveLength(1);
    expect(screen.getByTestId('media-live').getAttribute('data-read-only')).toBe('true');
    expect(screen.queryByTestId('multiview-real-dossier')).toBeNull();
    expect(vi.mocked(workstationModeService.getBootstrapState)).not.toHaveBeenCalled();
    expect(vi.mocked(api.get)).not.toHaveBeenCalled();
  });

  it('unmounts all clinical slots immediately after a mid-session patients permission revocation',async()=>{
    const allowed=user({patients:true,cephalo:true});
    useAuthStore.setState({user:allowed,isAuthenticated:true});
    const {rerender}=render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={allowed}/>);
    await screen.findByTestId('multiview-real-dossier');
    expect(screen.getByTestId('media-live')).toBeTruthy();
    const revoked=user({patients:false,cephalo:true});
    useAuthStore.setState({user:revoked,isAuthenticated:true});
    rerender(<CabinetMultiViewLab patient={patient} routePatientId="17" user={revoked}/>);
    expect(screen.getByRole('alert').textContent).toContain('refusées');
    expect(screen.queryByTestId('media-live')).toBeNull();
    expect(screen.queryByText('DOS-A')).toBeNull();
  });

  it('ignores a late API response for A after route patient switches to B',async()=>{
    const actor=user();
    const next={id:18,nom:'NOM-B',prenom:'Prénom-B',numero_dossier:'DOS-B'};
    let resolveA: ((result: unknown) => void) | undefined;
    vi.mocked(api.get).mockImplementation((url) =>
      url==='/patients/17'
        ? new Promise(resolve=>{resolveA=resolve;}) as never
        : Promise.resolve({data:next}) as never
    );
    const {rerender}=render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={actor}/>);
    await waitFor(()=>expect(vi.mocked(api.get)).toHaveBeenCalledWith('/patients/17'));
    rerender(<CabinetMultiViewLab patient={next} routePatientId="18" user={actor}/>);
    await screen.findByText('DOS-B');
    expect(screen.getByTestId('media-live').textContent).toContain('18');
    await act(async()=>{
      if (!resolveA) throw new Error('old synthetic request not created');
      resolveA({data:patient});
      await Promise.resolve();
    });
    expect(screen.queryByText('DOS-A')).toBeNull();
    expect(screen.queryByText('NOM-A')).toBeNull();
    expect(screen.getByTestId('media-live').textContent).toContain('18');
  });

  it('synchronously denies and removes old clinical viewer on account logout and patient A→B',async()=>{
    const actor=user();
    const {rerender}=render(<CabinetMultiViewLab patient={patient} routePatientId="17" user={actor}/>);
    await screen.findByTestId('multiview-real-dossier');
    const next={id:18,nom:'NOM-B',prenom:'Prénom-B',numero_dossier:'DOS-B'};
    vi.mocked(api.get).mockResolvedValue({data:next} as never);
    rerender(<CabinetMultiViewLab patient={next} routePatientId="18" user={actor}/>);
    expect(screen.queryByText('NOM-A')).toBeNull();
    expect(screen.queryByTestId('media-live')).toBeNull();
    await screen.findByText('DOS-B');
    expect(screen.getByTestId('media-live').textContent).toContain('18');
    act(()=>{useAuthStore.setState({user:null,isAuthenticated:false});});
    rerender(<CabinetMultiViewLab patient={next} routePatientId="18" user={null}/>);
    expect(screen.queryByTestId('media-live')).toBeNull();
    expect(screen.queryByText('DOS-B')).toBeNull();
  });
});
