import {describe,expect,it} from 'vitest';
import {PRESETS,type WorkspaceContext} from './studioLayouts';
import {applyR5Preview,beginR5Preview,cancelR5Preview,createR5Preference,
  previewR5Preference,readR5Preference,rollbackR5Preference,
  type R5VerifiedScope} from './R5PreferencesPolicy';

const scope: R5VerifiedScope = {
  authenticated:true,workstationVerified:true,tenantId:'tenant-A',userId:'user-A',
  workstationId:'station-01',patientId:17,cssViewportWidth:1920,
  allowedModules:['dossier','agenda','imagerie','galerie','photos','suivi'],
};
const consultation=PRESETS.find(p=>p.id==='consultation')!;

describe('LOT07 R5 07-D isolated safe preference contract (NOT persistent storage)',()=>{
  it('projects only allowlisted, non-clinical layout metadata and theme mode',()=>{
    const draft=createR5Preference(scope,'iconic',consultation,54)!;
    expect(draft).toMatchObject({version:1,signature:'iconic',
      tenantId:'tenant-A',userId:'user-A',workstationId:'station-01',
      layout:{id:'consultation',ratio:54,geometry:'two-columns'}});
    expect(draft.layout?.slots).toEqual([
      {id:'slot-1',module:'dossier'},{id:'slot-2',module:'agenda'}]);
    expect(readR5Preference(JSON.parse(JSON.stringify(draft)),scope)).toEqual(draft);
    expect(JSON.stringify(draft)).not.toMatch(/patientId|patientName|token|clinical|image|draft|photoUrl/i);
  });

  it('supports signature-only Core and Iconic without any saved patient selection',()=>{
    const record=createR5Preference(scope,'core',null)!;
    expect(record.layout).toBeNull();
    expect(readR5Preference(record,scope)).toEqual(record);
    expect(createR5Preference(scope,'iconic',null)?.signature).toBe('iconic');
  });

  it('never reuses an A preference in user B, station B, tenant B or unverified session',()=>{
    const record=createR5Preference(scope,'iconic',consultation)!;
    for(const other of [
      {...scope,userId:'user-B'},{...scope,workstationId:'station-02'},
      {...scope,tenantId:'tenant-B'},{...scope,workstationVerified:false},
      {...scope,authenticated:false},{...scope,workstationId:null},
    ]){
      expect(readR5Preference(record,other)).toBeNull();
      expect(beginR5Preview(record,other)).toBeNull();
    }
    expect(readR5Preference(record,scope)).toEqual(record); // A→B→A remains isolated
  });

  it('fails closed on extra PHI and unknown keys at every JSON level',()=>{
    const record=createR5Preference(scope,'iconic',consultation)!;
    expect(readR5Preference({...record,patientId:17},scope)).toBeNull();
    expect(readR5Preference({...record,token:'x'},scope)).toBeNull();
    expect(readR5Preference({...record,layout:{...record.layout,patientId:17}},scope)).toBeNull();
    expect(readR5Preference({...record,layout:{...record.layout,slots:[
      {...record.layout!.slots[0],patientName:'Private'},record.layout!.slots[1],
    ]}},scope)).toBeNull();
    expect(readR5Preference({...record,signature:'auto'},scope)).toBeNull();
  });

  it('rechecks permissions and layout safety; never authorizes W or X',()=>{
    const record=createR5Preference(scope,'iconic',consultation)!;
    expect(readR5Preference(record,{...scope,allowedModules:['agenda']})).toBeNull();
    expect(readR5Preference(record,{...scope,patientId:null})).toBeNull();
    expect(readR5Preference(record,{...scope,cssViewportWidth:900})).toBeNull();
    expect(createR5Preference(scope,'iconic',{
      ...consultation,slots:[{...consultation.slots[0],access:'W'},consultation.slots[1]],
    })).toBeNull();
    expect(createR5Preference(scope,'iconic',{
      ...consultation,slots:[consultation.slots[0],{...consultation.slots[1],access:'X'}],
    })).toBeNull();
  });

  it('cannot smuggle patient names in custom layout identifiers or labels',()=>{
    const record=createR5Preference(scope,'core',{
      ...consultation,id:'patient-private-123',label:'Patient Secret Nom',
    })!;
    expect(record.layout?.id).toBe('custom-two-columns-dossier-agenda');
    expect(JSON.stringify(record)).not.toContain('Secret');
    expect(readR5Preference(record,scope)).toEqual(record);
  });

  it('rejects modified ratio, modules, slots and unexpected sensitive fields',()=>{
    const record=createR5Preference(scope,'iconic',consultation)!;
    expect(readR5Preference({...record,layout:{...record.layout,ratio:97}},scope)).toBeNull();
    expect(readR5Preference({...record,layout:{...record.layout,id:'fake'}},scope)).toBeNull();
    expect(readR5Preference({...record,layout:{...record.layout,slots:[
      {id:'slot-1',module:'unknown'},record.layout!.slots[1]]}},scope)).toBeNull();
    expect(readR5Preference({...record,layout:{...record.layout,slots:[
      {id:'patient-17',module:'dossier'},record.layout!.slots[1]]}},scope)).toBeNull();
  });

  it('previews, cancels, applies, and rolls back without persistence or cross-scope actions',()=>{
    const core=createR5Preference(scope,'core',consultation)!;
    const iconic=createR5Preference(scope,'iconic',consultation,55)!;
    const started=beginR5Preview(core,scope)!;
    const shown=previewR5Preference(started,iconic,scope)!;
    expect(shown.applied).toEqual(core);
    expect(shown.preview).toEqual(iconic);
    expect(cancelR5Preview(shown,scope)).toEqual(started);
    const applied=applyR5Preview(shown,scope)!;
    expect(applied.applied).toEqual(iconic);
    expect(applied.previous).toEqual(core);
    expect(rollbackR5Preference(applied,scope)).toEqual(started);
    expect(previewR5Preference(started,iconic,{...scope,userId:'user-B'})).toBeNull();
    expect(applyR5Preview(shown,{...scope,workstationVerified:false})).toBeNull();
  });
});
