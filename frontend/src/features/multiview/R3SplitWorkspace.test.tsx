import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { getPreset, type Layout, type WorkspaceContext } from './studioLayouts';
import { clampSplitRatio, R3SplitWorkspace, splitTracks } from './R3SplitWorkspace';

const context: WorkspaceContext = {
  authenticated: true, userId: 'T2-actor-A', workstationId: 'T2-poste-A',
  tenantId: 'T2-tenant-A', patientId: 17, cssViewportWidth: 1920,
  allowedModules: ['dossier','agenda','suivi','photos'],
};
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });
const renderSlot = vi.fn((slot: { module: string }) => <p>{slot.module} — T2 uniquement</p>);

describe('LOT07 R3-1: real two-pane splitter, isolated and R-only', () => {
  it('starts at strict 50/50 in two columns, with accessible keyboard resizing and reset', () => {
    render(<R3SplitWorkspace layout={getPreset('consultation')!} context={context} renderSlot={renderSlot}/>);
    const separator = screen.getByRole('separator',{name:'Séparateur vertical des panneaux'});
    expect(separator.getAttribute('aria-orientation')).toBe('vertical');
    expect(separator.getAttribute('aria-valuenow')).toBe('50');
    expect((screen.getByTestId('r3-1-grid') as HTMLElement).style.gridTemplateColumns).toContain('50fr');
    fireEvent.keyDown(separator,{key:'ArrowRight'});
    expect(separator.getAttribute('aria-valuenow')).toBe('55');
    fireEvent.keyDown(separator,{key:'End'});
    expect(separator.getAttribute('aria-valuenow')).toBe('63');
    fireEvent.keyDown(separator,{key:'Home'});
    expect(separator.getAttribute('aria-valuenow')).toBe('37');
    fireEvent.click(screen.getByRole('button',{name:'Égaliser 50/50'}));
    expect(separator.getAttribute('aria-valuenow')).toBe('50');
    expect(screen.getByRole('region',{name:'Panneau 1'}).textContent).toContain('dossier');
    expect(screen.getByRole('region',{name:'Panneau 2'}).textContent).toContain('agenda');
  });

  it('supports vertical stacking, Up/Down and explicit strict vs content-fit', () => {
    render(<R3SplitWorkspace layout={getPreset('suivi-clinique')!} context={context} renderSlot={renderSlot}/>);
    const separator = screen.getByRole('separator',{name:'Séparateur horizontal des panneaux'});
    expect(separator.getAttribute('aria-orientation')).toBe('horizontal');
    fireEvent.keyDown(separator,{key:'ArrowDown'});
    expect(separator.getAttribute('aria-valuenow')).toBe('55');
    expect(screen.getByTestId('r3-1-grid').getAttribute('style')).toContain('55fr');
    fireEvent.click(screen.getByRole('button',{name:'Ajuster au contenu'}));
    expect(screen.queryByRole('separator')).toBeNull();
    expect(screen.getByTestId('r3-1-grid').getAttribute('style')).toContain('max-content');
    expect(screen.getByRole('button',{name:'Revenir au partage strict'}).getAttribute('aria-pressed')).toBe('true');
    fireEvent.click(screen.getByRole('button',{name:'Égaliser 50/50'}));
    expect(screen.getByRole('separator').getAttribute('aria-valuenow')).toBe('50');
    expect(screen.getByTestId('r3-1-grid').getAttribute('style')).toContain('50fr');
  });

  it('supports pointer drag on the divider with clamped percentage', () => {
    // JSDOM does not expose PointerEvent by default: use a MouseEvent-based
    // PointerEvent fixture preserving real pointerId/button/client coordinates.
    class SyntheticPointerEvent extends MouseEvent {
      readonly pointerId: number;
      constructor(type: string, options: MouseEventInit & { pointerId?: number }) {
        super(type, options);
        this.pointerId = options.pointerId ?? 1;
      }
    }
    vi.stubGlobal('PointerEvent', SyntheticPointerEvent);
    render(<R3SplitWorkspace layout={getPreset('consultation')!} context={context} renderSlot={renderSlot}/>);
    const grid = screen.getByTestId('r3-1-grid');
    vi.spyOn(grid, 'getBoundingClientRect').mockReturnValue({
      x: 0, y: 0, left: 0, top: 0, width: 1000, height: 600, right: 1000, bottom: 600, toJSON: () => ({}),
    });
    const separator = screen.getByRole('separator');
    fireEvent.pointerDown(separator,{pointerId:7,button:0});
    fireEvent.pointerMove(separator,{pointerId:7,clientX:600,clientY:0});
    expect(separator.getAttribute('aria-valuenow')).toBe('60');
    fireEvent.pointerUp(separator,{pointerId:7});
    fireEvent.pointerMove(separator,{pointerId:7,clientX:250,clientY:0});
    expect(separator.getAttribute('aria-valuenow')).toBe('60');
  });

  it('has deterministic min/max and rejects unsupported geometries', () => {
    expect(clampSplitRatio(0)).toBe(37);
    expect(clampSplitRatio(200)).toBe(63);
    expect(clampSplitRatio(Number.NaN)).toBe(50);
    expect(splitTracks('two-columns',50,'strict')).toBe('minmax(0,50fr) 12px minmax(0,50fr)');
    expect(splitTracks('two-rows',50,'content-fit')).toContain('max-content');
    expect(() => splitTracks('single',50,'strict')).toThrow();
    const renderForbidden=vi.fn(()=><p>Forbidden</p>);
    render(<R3SplitWorkspace layout={getPreset('presentation-patient')!} context={context} renderSlot={renderForbidden}/>);
    expect(screen.getByTestId('r3-1-split-denied')).toBeTruthy();
    expect(renderForbidden).not.toHaveBeenCalled();
  });

  it('never calls module renderers for W/X, revoked permissions or lost workstation', () => {
    const p = getPreset('consultation')!;
    for (const variant of [
      {...p, slots:[{...p.slots[0],access:'W'},p.slots[1]]} as Layout,
      {...p, slots:[{...p.slots[0],access:'X'},p.slots[1]]} as Layout,
    ]) {
      const forbidden=vi.fn(()=> <p>Protected data</p>);
      const result=render(<R3SplitWorkspace layout={variant} context={context} renderSlot={forbidden}/>);
      expect(screen.getByRole('alert')).toBeTruthy();
      expect(forbidden).not.toHaveBeenCalled();
      result.unmount();
    }
    const unauthorized=vi.fn(()=> <p>Protected data</p>);
    render(<R3SplitWorkspace layout={p} context={{...context,workstationId:null}} renderSlot={unauthorized}/>);
    expect(screen.getByRole('alert')).toBeTruthy();
    expect(unauthorized).not.toHaveBeenCalled();
  });

  it('immediately unmounts T2 patient content on patient switch, logout and module revocation', () => {
    const p=getPreset('consultation')!;
    const {rerender}=render(<R3SplitWorkspace layout={p} context={context} renderSlot={renderSlot}/>);
    expect(screen.getAllByText(/T2 uniquement/)).toHaveLength(2);
    rerender(<R3SplitWorkspace layout={p} context={{...context,patientId:null}} renderSlot={renderSlot}/>);
    expect(screen.queryByText(/T2 uniquement/)).toBeNull();
    expect(screen.getByRole('alert')).toBeTruthy();
    rerender(<R3SplitWorkspace layout={p} context={{...context,authenticated:false}} renderSlot={renderSlot}/>);
    expect(screen.queryByRole('region')).toBeNull();
    rerender(<R3SplitWorkspace layout={p} context={{...context,allowedModules:['dossier']}} renderSlot={renderSlot}/>);
    expect(screen.queryByText(/T2 uniquement/)).toBeNull();
  });

  it('preserves last safe ratio when a module would fall below its certified width', () => {
    const p: Layout = {id:'t2-scientific-pair',label:'Céphalo + Photos',geometry:'two-columns',
      slots:[{id:'scientific',module:'cephalo'},{id:'photographic',module:'photos'}]};
    render(<R3SplitWorkspace layout={p} context={{...context,cssViewportWidth:1280,
      allowedModules:[...context.allowedModules,'cephalo']}} renderSlot={renderSlot}/>);
    const separator=screen.getByRole('separator');
    // 50% of 1268px is wide enough for the 560px cephalo module.
    expect(separator.getAttribute('aria-valuenow')).toBe('50');
    fireEvent.keyDown(separator,{key:'Home'});
    // 37% would leave only 469px, so the gesture is rejected, not allowed to blank clinical data.
    expect(separator.getAttribute('aria-valuenow')).toBe('50');
    fireEvent.keyDown(separator,{key:'End'});
    expect(separator.getAttribute('aria-valuenow')).toBe('63');
  });
});
