import { describe, expect, it } from 'vitest';
import type { OrthoLongitudinalCompare, OrthoTimepointSummary } from './orthoLongitudinalCompare';
import { gateR6ThreeTimepoints, trustedR6Comparison } from './r6ThreeTimepoints';

const patientId=915, caseId=12;
const at = (ordinal: number, id=ordinal+100): OrthoTimepointSummary => ({
  id, ordinal, patient_id:patientId, ortho_case_id:caseId,
  occurred_at:['2024-01-02T09:00:00Z','2024-06-02T09:00:00Z','2025-01-02T09:00:00Z'][ordinal],
  note:'SYNTHETIC PRIVATE NOTE, NEVER DISPLAY',
  evidences:[{
    id:id+1000,clinical_asset_id:null,cephalo_analysis_id:id+2000,
    panoramic_analysis_id:null,created_by:11,created_at:'2025-01-03T10:00:00Z',
  }],
});
const triple = () => [at(0),at(1),at(2)];

describe('LOT07 R6 07.1.C — real T0/T1/T2 fail-closed source projection',()=>{
  it('accepts three chronological canonical points with independent linked cephalo sources',()=>{
    const gate=gateR6ThreeTimepoints(patientId,caseId,triple().reverse());
    expect(gate.ok).toBe(true);
    if(gate.ok) {
      expect(gate.trajectory.points.map(p=>p.ordinal)).toEqual([0,1,2]);
      expect(gate.trajectory.points[0].sources).toEqual([{kind:'CEPHALO',refId:2100}]);
      expect(JSON.stringify(gate.trajectory)).not.toContain('SYNTHETIC PRIVATE NOTE');
      expect(JSON.stringify(gate.trajectory)).not.toContain('created_by');
      expect(JSON.stringify(gate.trajectory)).not.toContain('interpretation');
    }
  });
  it('rejects missing T2 without inventing a comparison',()=>{
    expect(gateR6ThreeTimepoints(patientId,caseId,triple().slice(0,2)))
      .toEqual({ok:false,reason:'T0_T1_T2_INCOMPLETE'});
  });
  it('rejects wrong patient or foreign ortho case despite matching ordinal',()=>{
    expect(gateR6ThreeTimepoints(patientId,caseId,
      [at(0),{...at(1),patient_id:916},at(2)]))
      .toEqual({ok:false,reason:'TIMEPOINT_SCOPE_MISMATCH'});
    expect(gateR6ThreeTimepoints(patientId,caseId,
      [at(0),{...at(1),ortho_case_id:13},at(2)]))
      .toEqual({ok:false,reason:'TIMEPOINT_SCOPE_MISMATCH'});
  });
  it('denies duplicates and a reused image source between timepoints',()=>{
    expect(gateR6ThreeTimepoints(patientId,caseId,[at(0),at(1),at(1),at(2)]))
      .toEqual({ok:false,reason:'TIMEPOINT_DUPLICATED'});
    const reuse=triple();
    reuse[2].evidences[0].cephalo_analysis_id=reuse[0].evidences[0].cephalo_analysis_id;
    expect(gateR6ThreeTimepoints(patientId,caseId,reuse))
      .toEqual({ok:false,reason:'SOURCE_REUSED'});
  });
  it('denies missing, malformed, or multiple canonical evidence bindings',()=>{
    expect(gateR6ThreeTimepoints(patientId,caseId,[at(0),{...at(1),evidences:[]},at(2)]))
      .toEqual({ok:false,reason:'CANONICAL_SOURCE_MISSING'});
    const ambiguous=triple();
    ambiguous[1].evidences[0].panoramic_analysis_id=333;
    expect(gateR6ThreeTimepoints(patientId,caseId,ambiguous))
      .toEqual({ok:false,reason:'CANONICAL_SOURCE_MISSING'});
    const invalid=triple();
    invalid[1].evidences[0].cephalo_analysis_id=-2;
    expect(gateR6ThreeTimepoints(patientId,caseId,invalid))
      .toEqual({ok:false,reason:'CANONICAL_SOURCE_MISSING'});
  });
  it('denies invalid dates, nonchronological dates, missing verified scope',()=>{
    const reversed=triple();
    reversed[2].occurred_at='2024-01-01T09:00:00Z';
    expect(gateR6ThreeTimepoints(patientId,caseId,reversed))
      .toEqual({ok:false,reason:'DATE_OR_ORDER_INVALID'});
    const malformed=triple();
    malformed[0].occurred_at='not-a-date';
    expect(gateR6ThreeTimepoints(patientId,caseId,malformed))
      .toEqual({ok:false,reason:'DATE_OR_ORDER_INVALID'});
    expect(gateR6ThreeTimepoints(0,caseId,triple()))
      .toEqual({ok:false,reason:'SESSION_SCOPE_INVALID'});
  });
});

const response = (from: number, to:number): OrthoLongitudinalCompare => ({
  patient_id:patientId,ortho_case_id:caseId,
  from_timepoint:{id:from+100,ordinal:from,occurred_at:'2024-01-02T09:00:00Z',note:null,evidences:[]},
  to_timepoint:{id:to+100,ordinal:to,occurred_at:'2025-01-02T09:00:00Z',note:null,evidences:[]},
  measurements:[],measurement_status:'NO_COMMON_MEASUREMENTS',
  interpretation_policy:'NUMERIC_ONLY_CLINICIAN_INTERPRETATION',
});
describe('LOT07 R6 — stale / unauthorized compare results are never rendered',()=>{
  it('accepts only same-patient/case and explicitly selected pair',()=>{
    expect(trustedR6Comparison(response(0,2),patientId,caseId,0,2)).toBe(true);
    expect(trustedR6Comparison(response(0,2),patientId,caseId,1,2)).toBe(false);
    expect(trustedR6Comparison({...response(0,2),patient_id:999},patientId,caseId,0,2)).toBe(false);
    expect(trustedR6Comparison({...response(0,2),ortho_case_id:50},patientId,caseId,0,2)).toBe(false);
  });
  it('rejects unsigned/unapproved claims, repeated same point and null',()=>{
    expect(trustedR6Comparison(null,patientId,caseId,0,2)).toBe(false);
    expect(trustedR6Comparison(response(0,0),patientId,caseId,0,0)).toBe(false);
    expect(trustedR6Comparison({...response(0,2),interpretation_policy:'AUTOMATIC_SUCCESS' as any},
      patientId,caseId,0,2)).toBe(false);
  });
});
