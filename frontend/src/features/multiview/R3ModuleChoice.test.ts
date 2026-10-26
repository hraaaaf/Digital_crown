import { describe, expect, it } from 'vitest';
import { chooseR3Module, r3ModuleOptions, R3_REAL_MODULES } from './R3ModuleChoice';
import type { Layout, WorkspaceContext } from './studioLayouts';

const context: WorkspaceContext = {
  authenticated:true,userId:'synthetic-user',tenantId:'synthetic-tenant',
  workstationId:'synthetic-station',patientId:17,cssViewportWidth:1920,
  allowedModules:['dossier','imagerie','suivi'],
};
const columns:Layout = {
  id:'dossier-media-2cols',label:'Deux modules',geometry:'two-columns',
  slots:[{id:'dossier',module:'dossier'},{id:'imagerie',module:'imagerie'}],
};
const three:Layout = {
  id:'dossier-media-suivi-3cols',label:'Trois modules',geometry:'three-columns',
  slots:[{id:'dossier',module:'dossier'},{id:'imagerie',module:'imagerie'},
    {id:'suivi',module:'suivi'}],
};

describe('LOT07 R3 panel module chooser — real adapters only',()=>{
  it('only offers existing authenticated read-only clinical modules',()=>{
    expect(R3_REAL_MODULES).toEqual(['dossier','imagerie','suivi','agenda','photos','galerie']);
    expect(r3ModuleOptions(columns,0,context)).toEqual(['dossier','imagerie','suivi']);
    expect(r3ModuleOptions(columns,0,{...context,allowedModules:['dossier','imagerie']}))
      .toEqual(['dossier','imagerie']);
    expect(chooseR3Module(columns,0,'agenda',context)).toBeNull();
    expect(chooseR3Module(columns,0,'documents',context)).toBeNull();
    expect(chooseR3Module(columns,0,'cephalo',context)).toBeNull();
    const agendaContext={...context,allowedModules:['dossier','imagerie','suivi','agenda'] as const};
    expect(chooseR3Module(columns,0,'agenda',agendaContext)?.slots.map(slot=>slot.module))
      .toEqual(['agenda','imagerie']);
    expect(r3ModuleOptions(columns,0,agendaContext)).toContain('agenda');
    const photoContext={...agendaContext,allowedModules:['dossier','imagerie','suivi','agenda','photos'] as const};
    expect(chooseR3Module(columns,0,'photos',photoContext)?.slots.map(slot=>slot.module))
      .toEqual(['photos','imagerie']);
    expect(r3ModuleOptions(columns,0,photoContext)).toContain('photos');
    const galleryContext={...photoContext,allowedModules:['dossier','imagerie','suivi','agenda','photos','galerie'] as const};
    expect(chooseR3Module(columns,0,'galerie',galleryContext)?.slots.map(slot=>slot.module))
      .toEqual(['galerie','imagerie']);
    const imagerieLayout={...columns,id:'imagerie',
      slots:[{id:'radio',module:'imagerie' as const},{id:'photos',module:'galerie' as const}]};
    expect(chooseR3Module(imagerieLayout,0,'galerie',galleryContext)?.slots.map(slot=>slot.module))
      .toEqual(['galerie','imagerie']);
    expect(chooseR3Module(columns,0,'photos',galleryContext)?.slots.map(slot=>slot.module))
      .toEqual(['photos','imagerie']);
  });

  it('permutes existing modules rather than mounting a second media or cephalo viewer',()=>{
    const swapped=chooseR3Module(three,0,'suivi',context);
    expect(swapped?.slots.map(slot=>slot.module)).toEqual(['suivi','imagerie','dossier']);
    expect(swapped?.slots.map(slot=>slot.id)).toEqual(['dossier','imagerie','suivi']);
    expect(swapped?.slots.every(slot=>slot.access==='R')).toBe(true);
    expect(new Set(swapped?.slots.map(slot=>slot.module)).size).toBe(3);
    expect(chooseR3Module(three,1,'dossier',context)?.slots.map(slot=>slot.module))
      .toEqual(['imagerie','dossier','suivi']);
  });

  it('can choose a third real adapter in a two-pane layout without persistence',()=>{
    const changed=chooseR3Module(columns,0,'suivi',context);
    expect(changed?.slots.map(slot=>slot.module)).toEqual(['suivi','imagerie']);
    expect(changed?.id).toBe(columns.id);
    expect(columns.slots.map(slot=>slot.module)).toEqual(['dossier','imagerie']);
    expect(JSON.stringify(changed)).not.toContain('synthetic-tenant');
    expect(JSON.stringify(changed)).not.toContain('patientId');
  });

  it('denies unverified context, revoked roles, inappropriate width and W/X slots',()=>{
    const denied=[
      {...context,authenticated:false},
      {...context,tenantId:null},
      {...context,workstationId:null},
      {...context,patientId:null},
      {...context,cssViewportWidth:1279},
      {...context,allowedModules:['dossier','imagerie'] as const},
    ];
    for(const c of denied) expect(chooseR3Module(columns,0,'suivi',c)).toBeNull();
    expect(chooseR3Module({...columns,slots:[{...columns.slots[0],access:'W'},columns.slots[1]]},0,'suivi',context)).toBeNull();
    expect(chooseR3Module({...columns,slots:[columns.slots[0],{...columns.slots[1],access:'X'}]},0,'suivi',context)).toBeNull();
    expect(chooseR3Module(columns,-1,'suivi',context)).toBeNull();
    expect(chooseR3Module(columns,2,'suivi',context)).toBeNull();
    expect(chooseR3Module({...columns,slots:[columns.slots[0],{id:'agenda',module:'agenda'}]},0,'suivi',context)).toBeNull();
  });

  it('keeps the exact existing layout for unchanged module and works for two rows',()=>{
    expect(chooseR3Module(columns,0,'dossier',context)?.slots.map(slot=>slot.module))
      .toEqual(['dossier','imagerie']);
    expect(chooseR3Module({...columns,geometry:'two-rows'},0,'suivi',context)?.slots.map(slot=>slot.module))
      .toEqual(['suivi','imagerie']);
    expect(chooseR3Module({...columns,geometry:'single',slots:[columns.slots[0]]},0,'imagerie',context)).toBeNull();
  });
});
