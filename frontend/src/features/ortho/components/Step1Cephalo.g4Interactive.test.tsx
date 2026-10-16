import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Step1Cephalo } from './Step1Cephalo';
import { CEPHALO_ANALYSIS_CHANGE_EVENT } from '../cephaloAnalysisBridge';

const state = vi.hoisted(() => ({
  imageSrc:'blob:cephalo' as string|undefined,
  magnifierEnabled:false,
  imgFilters:{brightness:100,contrast:110,invert:false},
  setImgFilters:vi.fn(),
  vtoSettings:{
    enabled:false,
    showGhostFace:true,
    showSoftTissue:true,
    u1_offset:{x:0,y:0},
    l1_offset:{x:0,y:0},
    mand_offset:{x:0,y:0},
  },
  activeMorphing:'none' as 'none'|'T1'|'T2',
  layerVisibility:{landmarks:true,plans:true,hard_tissue:false,teeth:true,soft_tissue:true,measurements:true,t1:false,t2:false},
  layerOpacity:{landmarks:1,plans:1,hard_tissue:0.85,teeth:1,soft_tissue:0.9,measurements:1,t1:0.5,t2:0.5},
  local:{landmarks:[{id:'S',x:10,y:20}],version:1},
  landmarkEditTimeline:{baseline:[{id:'S',x:10,y:20}],undoStack:[],redoStack:[],auditTrail:[],nextSequence:1} as any,
  setMagnifierEnabled:vi.fn(),
  setIsStep1Fullscreen:vi.fn(),
  activePointId:null as string|null,
  setActivePointId:vi.fn(),
  setVtoSettings:vi.fn(),
  setActiveMorphing:vi.fn(),
  setLayerVisible:vi.fn(),
  toggleLayer:vi.fn(),
  setLayerOpacity:vi.fn(),
  resetLayers:vi.fn(),
  undoLandmarkEdit:vi.fn(),
  redoLandmarkEdit:vi.fn(),
  resetLandmarkEdits:vi.fn(),
}));

vi.mock('../stores/useOrthoStore',()=>({
  useOrthoStore:(selector:any)=>selector(state),
}));
vi.mock('./Step1CephaloBase',()=>({
  Step1Cephalo:({ embedded, activeAnalysis, inspectedPointId }: { embedded?: boolean; activeAnalysis?: string; inspectedPointId?: string|null }) =>
    <div data-embedded={embedded ? 'true' : 'false'} data-active-analysis={activeAnalysis} data-inspected-point={inspectedPointId ?? ''}>Cephalo base stage</div>,
}));
vi.mock('./CephaloAnalysisWorkbenchPanel',()=>({
  CephaloAnalysisWorkbenchPanel:({analysis}:any)=><div>Workbench analysis: {analysis}</div>,
}));

const P:any={
  bg:'#fff',bgPanel:'#fff',bgCard:'#fff',bgInput:'#f8fafc',border:'#ddd',borderFocus:'#003380',
  text:'#111',textMuted:'#666',textDim:'#999',accent:'#003380',accentSuccess:'#0a0',
  accentWarning:'#a60',accentError:'#d00',shadow:'none',shadowLg:'none'
};

beforeEach(()=>{
  vi.clearAllMocks();
  state.imageSrc='blob:cephalo';
  state.activePointId=null;
  state.magnifierEnabled=false;
  state.imgFilters={brightness:100,contrast:110,invert:false};
  state.activeMorphing='none';
  state.layerVisibility={landmarks:true,plans:true,hard_tissue:false,teeth:true,soft_tissue:true,measurements:true,t1:false,t2:false};
  state.layerOpacity={landmarks:1,plans:1,hard_tissue:0.85,teeth:1,soft_tissue:0.9,measurements:1,t1:0.5,t2:0.5};
  state.local={landmarks:[{id:'S',x:10,y:20}],version:1};
  state.landmarkEditTimeline={baseline:[{id:'S',x:10,y:20}],undoStack:[],redoStack:[],auditTrail:[],nextSequence:1};
  state.vtoSettings={
    enabled:false,showGhostFace:true,showSoftTissue:true,
    u1_offset:{x:0,y:0},l1_offset:{x:0,y:0},mand_offset:{x:0,y:0},
  };
  state.setVtoSettings.mockImplementation((fn:any)=>{ if(typeof fn==='function') fn(state.vtoSettings); });
});
afterEach(()=>cleanup());

describe('Cephalo Step1 G4 workbench controls',()=>{
  it('falls back to the base upload/calibration surface when no image exists',()=>{
    state.imageSrc=undefined;
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    expect(screen.getByText('Cephalo base stage')).toBeTruthy();
    expect(screen.queryByRole('button',{name:'Loupe'})).toBeNull();
  });

  it('lets a first-time desktop clinician reach the existing fullscreen radiograph in one click',()=>{
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    const cta=document.querySelector('[data-cephalo-focus-entry="desktop"]') as HTMLButtonElement;
    expect(cta).toBeTruthy();
    expect(cta.getAttribute('aria-label')).toBe('Activer le mode Focus radiographie');
    expect(cta.className).toContain('xl:inline-flex');
    fireEvent.click(cta);
    expect(state.setIsStep1Fullscreen).toHaveBeenCalledWith(true);
    expect(document.querySelector('[data-r20-radiograph-stage]')).toBeTruthy();
    expect(document.querySelector('[data-r20-measures-panel]')).toBeTruthy();
  });

  it('reserves a readable desktop analysis selector without shrinking the clinical measurement panel',()=>{
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    const grid=document.querySelector('[data-r20-workbench-layout]') as HTMLElement;
    expect(grid.className).toContain('xl:grid-cols-[minmax(0,1fr)_350px]');
    const selector=screen.getByRole('combobox',{name:'Analyse clé en main'}) as HTMLSelectElement;
    expect(selector.className).toContain('text-[13px]');
    expect(Array.from(selector.options).find(o=>o.value==='all')?.textContent).toBe('Toutes analyses');
    expect(document.querySelector('[data-r20-radiograph-stage]')).toBeTruthy();
  });

  it('starts image-first on desktop with reversible utility and measurement panels',()=>{
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    const root=document.querySelector('[data-r20-workbench-layout]') as HTMLElement;
    const utility=document.querySelector('[data-r20-workbench-sidebar]') as HTMLElement;
    const metrics=document.querySelector('[data-r20-measures-panel]') as HTMLElement;
    expect(root.dataset.r23ImageFirst).toBe('tools-collapsed');
    expect(utility.className).toContain('hidden');
    const tools=screen.getByRole('button',{name:'Afficher les outils'});
    fireEvent.click(tools);
    expect(root.className).toContain('xl:grid-cols-[200px_minmax(0,1fr)_350px]');
    expect(utility.className).not.toContain('hidden');
    expect(screen.getByRole('button',{name:'Masquer les outils'}).getAttribute('aria-expanded')).toBe('true');
    fireEvent.click(screen.getByRole('button',{name:'Masquer les outils'}));
    expect(root.className).toContain('xl:grid-cols-[minmax(0,1fr)_350px]');
    fireEvent.click(screen.getByRole('button',{name:'Masquer les mesures'}));
    expect(metrics.className).toContain('hidden');
    expect(root.className).toContain('xl:grid-cols-[minmax(0,1fr)]');
    fireEvent.click(screen.getByRole('button',{name:'Afficher les mesures'}));
    expect(metrics.className).not.toContain('hidden');
    expect(document.querySelectorAll('#cephalo-ready-analysis')).toHaveLength(1);
  });

  it('keeps the mobile utility rail one click away while prioritizing the radiograph',()=>{
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    const rail=document.querySelector('[data-r20-workbench-sidebar]') as HTMLElement;
    const tools=screen.getByRole('button',{name:'Afficher les outils'});
    expect(tools.className).toContain('inline-flex');
    expect(rail.className).toContain('hidden');
    fireEvent.click(tools);
    expect(rail.className).not.toContain('hidden');
    fireEvent.click(screen.getByRole('button',{name:'Masquer les outils'}));
    expect(rail.className).toContain('hidden');
    expect(screen.getByRole('combobox',{name:'Analyse clé en main'})).toBeTruthy();
  });

  it('keeps the selected analysis name readable at mobile width',()=>{
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    const selector=screen.getByRole('combobox',{name:'Analyse clé en main'}) as HTMLSelectElement;
    expect(selector.className).toContain('min-w-[142px]');
    expect(selector.value).toBe('all');
  });

  it('makes every anatomical name accessible on narrow displays without backgrounds',()=>{
    state.local={landmarks:Array.from({length:38},(_,i)=>({
      id:'P'+String(i).padStart(2,'0'),x:i*10,y:i*9,
    })),version:1};
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    const menu=document.querySelector('[data-r23-mobile-point-directory]') as HTMLDetailsElement;
    expect(menu).toBeTruthy();
    fireEvent.click(screen.getByLabelText('Parcourir les repères anatomiques'));
    expect(menu.open).toBe(true);
    expect(menu.querySelectorAll('[data-r23-point-select]')).toHaveLength(38);
    fireEvent.click(screen.getByRole('button',{name:'Inspecter le repère P07'}));
    expect(state.setActivePointId).not.toHaveBeenCalled();
    expect(screen.getByText('Cephalo base stage').getAttribute('data-inspected-point')).toBe('P07');
    expect(menu.open).toBe(false);
    expect(screen.getByRole('combobox',{name:'Analyse clé en main'})).toBeTruthy();
  });

  it('keeps the selected analysis in the actual stage when the workbench selector changes',()=>{
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    fireEvent.change(screen.getByRole('combobox',{name:'Analyse clé en main'}),{target:{value:'steiner'}});
    expect(screen.getByText('Cephalo base stage').getAttribute('data-active-analysis')).toBe('steiner');
  });

  it('renders the registry-driven layer manager and keeps planned anatomy fail-closed',()=>{
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);

    fireEvent.click(screen.getByText('Gestionnaire de couches'));
    expect(screen.getByRole('region',{name:'Gestionnaire de couches'})).toBeTruthy();
    const hardTissue=screen.getByRole('button',{name:/Tissus durs/}) as HTMLButtonElement;
    expect(hardTissue.disabled).toBe(true);

    fireEvent.click(screen.getByRole('button',{name:'Landmarks'}));
    expect(state.setLayerVisible).toHaveBeenCalledWith('landmarks',false);

    fireEvent.change(screen.getByRole('slider',{name:/Landmarks/}),{target:{value:'35'}});
    expect(state.setLayerOpacity).toHaveBeenCalledWith('landmarks',0.35);
  });

  it('displays desktop layer opacity numerically, with slider accessible percentage',()=>{
    const view=render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    const slider=screen.getByRole('slider',{name:'Opacité Landmarks'}) as HTMLInputElement;
    expect(slider.getAttribute('aria-valuetext')).toBe('100 pour cent');
    expect(document.querySelector('[data-ortho-layer-opacity-value="landmarks"]')?.textContent?.trim()).toBe('100 %');
    fireEvent.change(slider,{target:{value:'35'}});
    expect(state.setLayerOpacity).toHaveBeenCalledWith('landmarks',0.35);
    state.layerOpacity={...state.layerOpacity,landmarks:0.35};
    view.rerender(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    expect(screen.getByRole('slider',{name:'Opacité Landmarks'}).getAttribute('aria-valuetext')).toBe('35 pour cent');
    expect(document.querySelector('[data-ortho-layer-opacity-value="landmarks"]')?.textContent?.trim()).toBe('35 %');
    expect(screen.queryByText('Opacité Tissus durs')).toBeNull();
  });

  it('exposes correction history controls with fail-closed disabled states',()=>{
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);

    fireEvent.click(screen.getByText('Historique des corrections'));
    expect(screen.getByRole('region',{name:'Historique des corrections'})).toBeTruthy();
    expect((screen.getByRole('button',{name:/Annuler/}) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole('button',{name:/Rétablir/}) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole('button',{name:/Revenir aux repères initialement chargés/}) as HTMLButtonElement).disabled).toBe(true);

    state.local={landmarks:[{id:'S',x:14,y:20}],version:2};
    state.landmarkEditTimeline={
      baseline:[{id:'S',x:10,y:20}],
      undoStack:[{id:'landmark-edit-1',sequence:1,source:'POINTER_DRAG',before:[{id:'S',x:10,y:20}],after:[{id:'S',x:14,y:20}],changedLandmarkIds:['S']}],
      redoStack:[],auditTrail:[],nextSequence:2,
    };
    cleanup();
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    fireEvent.click(screen.getByText('Historique des corrections'));
    fireEvent.click(screen.getByRole('button',{name:/Annuler/}));
    expect(state.undoLandmarkEdit).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole('button',{name:/Revenir aux repères initialement chargés/}));
    expect(state.resetLandmarkEdits).toHaveBeenCalledTimes(1);
  });

  it('toggles magnifier, soft tissue and 3D face through explicit store boundaries',()=>{
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);

    fireEvent.click(screen.getByRole('button',{name:'Loupe'}));
    expect(state.setMagnifierEnabled).toHaveBeenCalledWith(true);

    fireEvent.click(screen.getByText('Gestionnaire de couches'));
    fireEvent.click(screen.getByRole('button',{name:'Tissus mous'}));
    const softUpdater=state.setVtoSettings.mock.calls.at(-1)?.[0];
    expect(softUpdater(state.vtoSettings).showSoftTissue).toBe(false);

    fireEvent.click(screen.getByText('Projections et VTO'));
    fireEvent.click(screen.getByRole('button',{name:'Face 3D'}));
    const faceUpdater=state.setVtoSettings.mock.calls.at(-1)?.[0];
    expect(faceUpdater(state.vtoSettings).showGhostFace).toBe(false);
  });

  it('toggles T1/T2 as independent registry-driven layers',()=>{
    const first=render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);

    fireEvent.click(screen.getByText('Projections et VTO'));
    fireEvent.click(screen.getByRole('button',{name:'Projection T1'}));
    expect(state.setLayerVisible).toHaveBeenCalledWith('t1',true);

    fireEvent.click(screen.getByRole('button',{name:'Projection T2'}));
    expect(state.setLayerVisible).toHaveBeenCalledWith('t2',true);

    first.unmount();
    state.layerVisibility={...state.layerVisibility,t1:true};
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    fireEvent.click(screen.getByText('Projections et VTO'));
    fireEvent.click(screen.getByRole('button',{name:'Projection T1'}));
    expect(state.setLayerVisible).toHaveBeenLastCalledWith('t1',false);
  });

  it('keeps image filter actions available inside the dedicated disclosure',()=>{
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    expect(screen.getByText('Cephalo base stage').getAttribute('data-embedded')).toBe('true');
    fireEvent.click(screen.getByText('Réglages image'));
    fireEvent.change(screen.getByRole('slider',{name:'Luminosité'}),{target:{value:'125'}});
    const brightnessUpdate=state.setImgFilters.mock.calls.at(-1)?.[0];
    expect(brightnessUpdate(state.imgFilters)).toEqual({brightness:125,contrast:110,invert:false});
    fireEvent.click(screen.getByRole('button',{name:'Inverser le contraste'}));
    const invertUpdate=state.setImgFilters.mock.calls.at(-1)?.[0];
    expect(invertUpdate(state.imgFilters)).toEqual({brightness:100,contrast:110,invert:true});
  });

  it('keeps VTO accessible after removing the duplicate floating toolbar',()=>{
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    fireEvent.click(screen.getByText('Projections et VTO'));
    fireEvent.click(screen.getByRole('button',{name:'VTO'}));
    const updater=state.setVtoSettings.mock.calls.at(-1)?.[0];
    expect(updater(state.vtoSettings).enabled).toBe(true);
  });

  it('updates the active scientific analysis label from the canonical analysis event',()=>{
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    expect(screen.getByText('Workbench analysis: all')).toBeTruthy();

    act(() => window.dispatchEvent(new CustomEvent(CEPHALO_ANALYSIS_CHANGE_EVENT,{detail:'steiner'})));
    expect(screen.getByText('Workbench analysis: steiner')).toBeTruthy();
  });
});
