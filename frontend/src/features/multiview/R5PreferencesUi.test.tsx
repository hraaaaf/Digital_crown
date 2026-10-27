import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {useState} from 'react';
import type {AppUser} from '../../types';
import {R5SignaturePreferencesPanel} from '../desktop-experience/R5SignaturePreferencesPanel';
import {R5MultiViewPreferencesPanel} from './R5MultiViewPreferencesPanel';
import {PRESETS,type WorkspaceContext} from './studioLayouts';
import {createR5Preference} from './R5PreferencesPolicy';

const store=vi.hoisted(()=>({
  load:vi.fn(),save:vi.fn(),rollback:vi.fn(),
  bootstrap:vi.fn(),isAuthenticated:true,user:{id:10},
}));
vi.mock('./R5PreferencesService',()=>({r5PreferencesService:{
  load:store.load,save:store.save,rollback:store.rollback,
}}));
vi.mock('../../services/workstationMode',()=>({workstationModeService:{
  getBootstrapState:store.bootstrap,subscribe:()=>()=>undefined,
}}));
vi.mock('../../stores/useAuthStore',()=>({useAuthStore:{
  getState:()=>({isAuthenticated:store.isAuthenticated,user:store.user}),
}}));

const mockUser={id:10,employer_id:10,role:'DENTISTE'} as unknown as AppUser;
const scope={
  authenticated:true,workstationVerified:true,userId:'10',tenantId:'10',
  workstationId:'station-test',patientId:17,cssViewportWidth:1920,
  allowedModules:['dossier','agenda','imagerie','galerie'],
} as const;
const options=PRESETS.filter(p=>['consultation','imagerie'].includes(p.id));

beforeEach(()=>{
  vi.clearAllMocks();
  store.isAuthenticated=true;store.user={id:10};
  store.bootstrap.mockResolvedValue({
    authenticated:true,enrollmentRequired:false,stationLocked:false,
    defaultExperience:'cabinet',workstationId:'station-test',
  });
  store.load.mockResolvedValue({record:null,revision:0,canRollback:false});
});
afterEach(()=>cleanup());

function SignatureHarness(){
  const [mode,setMode]=useState<'core'|'iconic'>('core');
  return <><output data-testid="live-signature">{mode}</output>
    <R5SignaturePreferencesPanel user={mockUser} mode={mode} onChange={setMode}/></>;
}

describe('LOT07 R5 07-D — actual buttons, server-saved preferences (DEV only)',()=>{
  it('re-hydrates signature from server and persists only after Appliquer',async()=>{
    const record=createR5Preference(scope,'iconic',null)!;
    store.save.mockResolvedValue({record,revision:1,canRollback:false});
    render(<SignatureHarness/>);
    await screen.findByTestId('r5-signature-prefs');
    fireEvent.click(screen.getByRole('button',{name:'Signature Iconic'}));
    expect(screen.getByTestId('live-signature').textContent).toBe('core');
    fireEvent.click(screen.getByRole('button',{name:'Aperçu'}));
    expect(screen.getByTestId('live-signature').textContent).toBe('iconic');
    expect(store.save).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button',{name:'Appliquer et enregistrer'}));
    await waitFor(()=>expect(store.save).toHaveBeenCalledWith(
      expect.objectContaining({signature:'iconic',userId:'10',workstationId:'station-test'}),0));
  });

  it('never mounts restored controls for unverified workstations',async()=>{
    store.bootstrap.mockResolvedValue({authenticated:true,enrollmentRequired:true,
      stationLocked:false,workstationId:null});
    render(<SignatureHarness/>);
    await waitFor(()=>expect(store.bootstrap).toHaveBeenCalled());
    expect(screen.queryByTestId('r5-signature-prefs')).toBeNull();
    expect(store.save).not.toHaveBeenCalled();
  });

  it('shows PHI-free layout schematic and saves on confirmed click; restores scope only',async()=>{
    const onApply=vi.fn();
    const record=createR5Preference(scope,'core',options[0])!;
    store.save.mockResolvedValue({record,revision:1,canRollback:false});
    render(<R5MultiViewPreferencesPanel context={scope} layouts={options}
      ratio={50} onApply={onApply}/>);
    await screen.findByTestId('r5-multiview-prefs');
    fireEvent.click(screen.getByRole('button',{name:'Aperçu'}));
    expect(screen.getByTestId('r5-multiview-preview').textContent).toContain('dossier');
    expect(screen.getByTestId('r5-multiview-preview').textContent).not.toMatch(/patientId|17|token/i);
    expect(store.save).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button',{name:'Appliquer'}));
    await waitFor(()=>expect(store.save).toHaveBeenCalledWith(
      expect.objectContaining({layout:expect.objectContaining({id:'consultation'})}),0));
    await waitFor(()=>expect(onApply).toHaveBeenCalled());
  });

  it('rejects cross-user restore without rendering saved preferences',async()=>{
    const fromA=createR5Preference(scope,'core',options[0])!;
    store.load.mockResolvedValue({record:fromA,revision:1,canRollback:false});
    const bScope={...scope,userId:'20'};
    render(<R5MultiViewPreferencesPanel context={bScope} layouts={options}
      ratio={50} onApply={vi.fn()}/>);
    await waitFor(()=>expect(store.load).toHaveBeenCalled());
    expect(screen.queryByTestId('r5-multiview-prefs')).toBeNull();
  });
});
