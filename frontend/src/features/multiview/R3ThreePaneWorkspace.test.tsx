import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { R3ThreePaneWorkspace } from './R3ThreePaneWorkspace';
import type { Layout, WorkspaceContext } from './studioLayouts';

const layout: Layout = {
  id:'verified-three-real',label:'Dossier + Médias + Suivi',
  geometry:'three-columns',
  slots:[{id:'dossier',module:'dossier'},{id:'imagerie',module:'imagerie'},{id:'suivi',module:'suivi'}],
};
const context: WorkspaceContext = {
  authenticated:true,userId:'synthetic-u',tenantId:'synthetic-t',
  workstationId:'synthetic-w',patientId:17,cssViewportWidth:1920,
  allowedModules:['dossier','imagerie','suivi'],
};
afterEach(()=>{cleanup();vi.restoreAllMocks();});

describe('LOT07 R3-2 — genuine R-only three panes and temporary focus',()=>{
  it('mounts three real modules, focuses exactly one, restores without persistence',()=>{
    const renderSlot=vi.fn((slot:{module:string})=>
      <div data-testid={'real-'+slot.module}>{slot.module} patient synthetic A</div>);
    render(<R3ThreePaneWorkspace layout={layout} context={context} renderSlot={renderSlot}/>);
    expect(screen.getByTestId('r3-2-three-real-panes')).toBeTruthy();
    expect(screen.getAllByRole('region',{name:/Panneau /})).toHaveLength(3);
    expect(renderSlot).toHaveBeenCalledTimes(3);
    fireEvent.click(screen.getByRole('button',{name:'Agrandir le panneau 2 : imagerie'}));
    expect(screen.getByTestId('r3-2-single-focus')).toBeTruthy();
    expect(screen.getAllByRole('region',{name:/Panneau /})).toHaveLength(1);
    expect(screen.getByTestId('real-imagerie')).toBeTruthy();
    expect(screen.queryByTestId('real-dossier')).toBeNull();
    expect(screen.queryByTestId('real-suivi')).toBeNull();
    fireEvent.click(screen.getByRole('button',{name:'Restaurer les trois panneaux'}));
    expect(screen.getAllByRole('region',{name:/Panneau /})).toHaveLength(3);
    expect(screen.getByTestId('real-dossier')).toBeTruthy();
    expect(screen.getByTestId('real-suivi')).toBeTruthy();
  });

  it('denies without mounting any clinical slot on missing tenant, patient, role or desktop width',()=>{
    for(const denied of [
      {...context,tenantId:null},
      {...context,patientId:18,authenticated:false},
      {...context,allowedModules:['dossier','imagerie'] as const},
      {...context,cssViewportWidth:1279},
      {...context,cssViewportWidth:1300},
    ]) {
      const renderer=vi.fn(()=> <p>Never mounted</p>);
      const {unmount}=render(<R3ThreePaneWorkspace layout={layout} context={denied}
        renderSlot={renderer}/>);
      expect(screen.getByTestId('r3-2-denied')).toBeTruthy();
      expect(renderer).not.toHaveBeenCalled();
      unmount();
    }
  });

  it('removes focused clinical data immediately when workstation identity is revoked',()=>{
    const {rerender}=render(<R3ThreePaneWorkspace layout={layout} context={context}
      renderSlot={slot=><p>synthetic A {slot.module}</p>}/>);
    fireEvent.click(screen.getByRole('button',{name:'Agrandir le panneau 1 : dossier'}));
    expect(screen.getByTestId('r3-2-single-focus')).toBeTruthy();
    rerender(<R3ThreePaneWorkspace layout={layout} context={{...context,workstationId:null}}
      renderSlot={slot=><p>synthetic A {slot.module}</p>}/>);
    expect(screen.getByRole('alert')).toBeTruthy();
    expect(screen.queryByTestId('r3-2-single-focus')).toBeNull();
    expect(screen.queryByText('synthetic A dossier')).toBeNull();
  });

  it('rejects write/exclusive slots and unsupported layouts, including hidden clinical mounts',()=>{
    const view=vi.fn(()=> <p>Sensitive synthetic preview</p>);
    for(const denied of [
      {...layout,slots:[{...layout.slots[0],access:'W' as const},...layout.slots.slice(1)]},
      {...layout,slots:[layout.slots[0],{...layout.slots[1],access:'X' as const},layout.slots[2]]},
      {...layout,geometry:'two-columns' as const},
    ]) {
      const {unmount}=render(<R3ThreePaneWorkspace layout={denied} context={context} renderSlot={view}/>);
      expect(screen.getByTestId('r3-2-denied')).toBeTruthy();
      expect(view).not.toHaveBeenCalled();
      unmount();
    }
  });

  it('supports hero-two three real modules with focused R-only restoration',()=>{
    const hero={...layout,geometry:'hero-two' as const};
    render(<R3ThreePaneWorkspace layout={hero} context={context} renderSlot={s=><p>{s.module}</p>}/>);
    expect(screen.getAllByRole('region',{name:/Panneau /})).toHaveLength(3);
    fireEvent.click(screen.getByRole('button',{name:'Agrandir le panneau 3 : suivi'}));
    expect(screen.getByTestId('r3-2-single-focus')).toBeTruthy();
    expect(screen.getByText('suivi')).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:'Restaurer les trois panneaux'}));
    expect(screen.getAllByRole('region',{name:/Panneau /})).toHaveLength(3);
  });
});
