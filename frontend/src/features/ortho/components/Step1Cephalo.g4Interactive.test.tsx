import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Step1Cephalo } from './Step1Cephalo';
import { CEPHALO_ANALYSIS_CHANGE_EVENT } from '../cephaloAnalysisBridge';

const state = vi.hoisted(() => ({
  imageSrc:'blob:cephalo' as string|undefined,
  magnifierEnabled:false,
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
  Step1Cephalo:()=> <div>Cephalo base stage</div>,
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
  state.magnifierEnabled=false;
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

  it('renders the registry-driven layer manager and keeps planned anatomy fail-closed',()=>{
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);

    expect(screen.getByRole('region',{name:'Gestionnaire de couches'})).toBeTruthy();
    const hardTissue=screen.getByRole('button',{name:/Tissus durs/}) as HTMLButtonElement;
    expect(hardTissue.disabled).toBe(true);

    fireEvent.click(screen.getByRole('button',{name:'Landmarks'}));
    expect(state.setLayerVisible).toHaveBeenCalledWith('landmarks',false);

    fireEvent.change(screen.getByRole('slider',{name:/Landmarks/}),{target:{value:'35'}});
    expect(state.setLayerOpacity).toHaveBeenCalledWith('landmarks',0.35);
  });

  it('exposes correction history controls with fail-closed disabled states',()=>{
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);

    expect(screen.getByRole('region',{name:'Historique des corrections'})).toBeTruthy();
    expect((screen.getByRole('button',{name:/Annuler/}) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole('button',{name:/Rétablir/}) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole('button',{name:/Réinitialiser le tracé/}) as HTMLButtonElement).disabled).toBe(true);

    state.local={landmarks:[{id:'S',x:14,y:20}],version:2};
    state.landmarkEditTimeline={
      baseline:[{id:'S',x:10,y:20}],
      undoStack:[{id:'landmark-edit-1',sequence:1,source:'POINTER_DRAG',before:[{id:'S',x:10,y:20}],after:[{id:'S',x:14,y:20}],changedLandmarkIds:['S']}],
      redoStack:[],auditTrail:[],nextSequence:2,
    };
    cleanup();
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    fireEvent.click(screen.getByRole('button',{name:/Annuler/}));
    expect(state.undoLandmarkEdit).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole('button',{name:/Réinitialiser le tracé/}));
    expect(state.resetLandmarkEdits).toHaveBeenCalledTimes(1);
  });

  it('toggles magnifier, soft tissue and 3D face through explicit store boundaries',()=>{
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);

    fireEvent.click(screen.getByRole('button',{name:'Loupe'}));
    expect(state.setMagnifierEnabled).toHaveBeenCalledWith(true);

    fireEvent.click(screen.getByRole('button',{name:'Tissus mous'}));
    const softUpdater=state.setVtoSettings.mock.calls.at(-1)?.[0];
    expect(softUpdater(state.vtoSettings).showSoftTissue).toBe(false);

    fireEvent.click(screen.getByRole('button',{name:'Face 3D'}));
    const faceUpdater=state.setVtoSettings.mock.calls.at(-1)?.[0];
    expect(faceUpdater(state.vtoSettings).showGhostFace).toBe(false);
  });

  it('toggles T1/T2 as independent registry-driven layers',()=>{
    const first=render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);

    fireEvent.click(screen.getByRole('button',{name:'Projection T1'}));
    expect(state.setLayerVisible).toHaveBeenCalledWith('t1',true);

    fireEvent.click(screen.getByRole('button',{name:'Projection T2'}));
    expect(state.setLayerVisible).toHaveBeenCalledWith('t2',true);

    first.unmount();
    state.layerVisibility={...state.layerVisibility,t1:true};
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    fireEvent.click(screen.getByRole('button',{name:'Projection T1'}));
    expect(state.setLayerVisible).toHaveBeenLastCalledWith('t1',false);
  });

  it('updates the active scientific analysis label from the canonical analysis event',()=>{
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    expect(screen.getByText('Workbench analysis: all')).toBeTruthy();

    act(() => window.dispatchEvent(new CustomEvent(CEPHALO_ANALYSIS_CHANGE_EVENT,{detail:'steiner'})));
    expect(screen.getByText('Workbench analysis: steiner')).toBeTruthy();
  });
});
