import { describe, expect, it } from 'vitest';
import { findR23G8W1OrientationRequirements as lookup } from './cephaloR23G8W1OrientationRequirements';
import { findR23G3PinnedRequirements } from './cephaloR23G3PinnedRequirements';
import { resolveR23G3RuntimeFocus, type R23G2ProtocolRow } from './cephaloR23G2ClinicalProfiles';

const atlas = 'RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1';
const rows = [
  'M_RICKETTS_OVERBITE_FOP_MM_V1',
  'M_RICKETTS_OCCLUSAL_PLANE_XI_MM_V1',
  'M_RICKETTS_COMMISSURE_FOP_MM_V1',
  'M_RICKETTS_PALATAL_PLANE_FH_DEG_V1',
] as const;

describe('R23-G8 W1 signed orientation contracts cannot forge clinical evidence', () => {
  it('enumerates exactly four Atlas33 orientation-only previews', () => {
    for (const mid of rows) {
      const dep = lookup(atlas, mid, []);
      expect(dep?.sameImageOrientationEvidenceRequired).toBe(true);
      expect(dep?.orientationEvidenceVerifiedByThisPreview).toBe(false);
      expect(dep?.availabilityGate).toBe('VERSIONED_IMAGE_ORIENTATION_EVIDENCE_REQUIRED');
      expect(findR23G3PinnedRequirements(mid, [])).toBeNull();
    }
    expect(lookup(atlas, 'M_RICKETTS_U1_APOG_INCLINATION_DEG_V1', [])).toBeNull();
  });
  it('requires precise anatomical FH/ANS/PNS and refuses generic Po', () => {
    const d=lookup(atlas,rows[3],['Po','Or','ANS','PNS_Ricketts']);
    expect(d?.missingLandmarks).toEqual(['Po_anatomic']);
    expect(d?.requiredManualLandmarks).toEqual(['PNS_Ricketts']);
    expect(d?.requiresCalibration).toBe(false);
  });
  it('differentiates FOP construction, Xi construction and manual commissure', () => {
    const d=lookup(atlas,rows[1],[]);
    expect(d?.requiredLandmarks).toEqual([]);
    expect(d?.requiredConstructions).toEqual([
      'RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_BICUSPID_MOLAR_V1',
      'RICKETTS_XI_RAMAL_RECTANGLE_R1_R4_FH_V1',
    ]);
    expect(d?.requiresCalibration).toBe(true);
    expect(lookup(atlas,rows[2],[])?.missingLandmarks).toEqual(['LABIAL_COMMISSURE_Ricketts']);
    expect(lookup(atlas,rows[2],[])?.requiredManualLandmarks).toEqual(['LABIAL_COMMISSURE_Ricketts']);
    expect(lookup(atlas,rows[0],[])?.requiredLandmarks).toEqual(['U1_incisal','L1_incisal']);
  });
  it('rejects Gregoret and McNamara without source-authorized aliases', () => {
    expect(lookup('RICKETTS_GREGORET_1997_SUMMARIZED_13_PROTOCOL_V1',rows[0],[])).toBeNull();
    expect(lookup('MCNAMARA_1984_SINGLE_FILM_V1',rows[0],[])).toBeNull();
  });
  it('present coordinates alone never authorize a signed numeric measurement or SVG Focus', () => {
    const complete=lookup(atlas,rows[3],['Po_anatomic','Or','ANS','PNS_Ricketts']);
    expect(complete?.missingLandmarks).toEqual([]);
    expect(complete?.orientationEvidenceVerifiedByThisPreview).toBe(false);
    const row={order:24,canonical_measurement_id:rows[3],label:'Palatal plane',unit:'deg',
      contract_state:'CONDITIONAL_EXECUTABLE',availability_status:'NOT_COMPUTABLE',
      value:null,source_contract:atlas,classification_authority:false} as R23G2ProtocolRow;
    expect(resolveR23G3RuntimeFocus(row)).toBeNull();
    expect(resolveR23G3RuntimeFocus({...row,availability_status:'AVAILABLE',value:10})).toBeNull();
  });
});
