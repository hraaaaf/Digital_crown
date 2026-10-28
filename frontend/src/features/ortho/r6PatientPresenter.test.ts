import {describe,expect,it} from 'vitest';
import type {OrthoLongitudinalCompare} from './orthoLongitudinalCompare';
import {type R6Trajectory} from './r6ThreeTimepoints';
import {projectR6Presenter} from './r6PatientPresenter';

const base:R6Trajectory={
  patientId:22,caseId:44,
  points:[
    {id:100,ordinal:0,occurred_at:'2026-01-02T09:00:00Z',sources:[{kind:'CLINICAL_ASSET',refId:301}]},
    {id:101,ordinal:1,occurred_at:'2026-04-02T09:00:00Z',sources:[{kind:'CEPHALO',refId:302}]},
    {id:102,ordinal:2,occurred_at:'2026-07-02T09:00:00Z',sources:[{kind:'PANORAMIC',refId:303}]},
  ],
};
const compare:OrthoLongitudinalCompare={
  patient_id:22,ortho_case_id:44,
  from_timepoint:{id:100,ordinal:0,occurred_at:'2026-01-02T09:00:00Z',note:'SECRET FROM DO NOT SHOW',evidences:[]},
  to_timepoint:{id:102,ordinal:2,occurred_at:'2026-07-02T09:00:00Z',note:'SECRET TO DO NOT SHOW',evidences:[]},
  measurements:[{key:'SNA',label:'Personal measure',unit:'°',from_value:70,to_value:72,delta:2}],
  measurement_status:'AVAILABLE',interpretation_policy:'NUMERIC_ONLY_CLINICIAN_INTERPRETATION',
};
describe('LOT07 R6 07.1.D — patient-facing read-only strict projection',()=>{
  it('projects only canonical ordinal, dates and source IDs, no PHI or clinical claims',()=>{
    const snap=projectR6Presenter(base,compare,7,0,2);
    expect(snap?.pair).toEqual([0,2]);
    expect(snap?.points.map(p=>p.sources[0].refId)).toEqual([301,302,303]);
    const serialized=JSON.stringify(snap);
    for(const forbidden of ['SECRET FROM','SECRET TO','Personal measure','SNA','interpretation_policy','note','created_by','token','email','patientName']){
      expect(serialized).not.toContain(forbidden);
    }
  });
  it('refuses missing identity, foreign case, stale pair and unsupported order',()=>{
    expect(projectR6Presenter(base,compare,null,0,2)).toBeNull();
    expect(projectR6Presenter(base,compare,0,0,2)).toBeNull();
    expect(projectR6Presenter(base,{...compare,patient_id:23},7,0,2)).toBeNull();
    expect(projectR6Presenter(base,{...compare,ortho_case_id:45},7,0,2)).toBeNull();
    expect(projectR6Presenter(base,compare,7,0,1)).toBeNull();
    expect(projectR6Presenter(base,compare,7,2,0)).toBeNull();
    expect(projectR6Presenter(null,compare,7,0,2)).toBeNull();
  });
  it('refuses mismatched canonical timepoint IDs/dates and automatic clinical interpretation',()=>{
    const wrongId={...compare,to_timepoint:{...compare.to_timepoint,id:999}};
    const wrongDate={...compare,to_timepoint:{...compare.to_timepoint,occurred_at:'2026-10-02T09:00:00Z'}};
    expect(projectR6Presenter(base,wrongId,7,0,2)).toBeNull();
    expect(projectR6Presenter(base,wrongDate,7,0,2)).toBeNull();
    expect(projectR6Presenter(base,{...compare,interpretation_policy:'AI_IMPROVEMENT' as any},7,0,2)).toBeNull();
  });
});
