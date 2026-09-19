import { cleanup, fireEvent, render, screen } from '@testing-library/react';
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
  setMagnifierEnabled:vi.fn(),
  setVtoSettings:vi.fn(),
  setActiveMorphing:vi.fn(),
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

  it('activates T1/T2 projections and toggles an already active projection back to none',()=>{
    const first=render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);

    fireEvent.click(screen.getByRole('button',{name:'Projection T1'}));
    expect(state.setActiveMorphing).toHaveBeenCalledWith('T1');

    fireEvent.click(screen.getByRole('button',{name:'Projection T2'}));
    expect(state.setActiveMorphing).toHaveBeenCalledWith('T2');

    first.unmount();
    state.activeMorphing='T1';
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    fireEvent.click(screen.getByRole('button',{name:'Projection T1'}));
    expect(state.setActiveMorphing).toHaveBeenLastCalledWith('none');
  });

  it('updates the active scientific analysis label from the canonical analysis event',()=>{
    render(<Step1Cephalo P={P} fileRef={{current:null}} step1ContainerRef={{current:null}}/>);
    expect(screen.getByText('Workbench analysis: all')).toBeTruthy();

    window.dispatchEvent(new CustomEvent(CEPHALO_ANALYSIS_CHANGE_EVENT,{detail:'steiner'}));
    expect(screen.getByText('Workbench analysis: steiner')).toBeTruthy();
  });
});
