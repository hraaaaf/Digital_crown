import { describe, it, expect } from 'vitest';
import { findR23G8W3CranioRequirements as get } from './cephaloR23G8W3CranioRequirements';
import { findR23G3PinnedRequirements } from './cephaloR23G3PinnedRequirements';
import { resolveR23G3RuntimeFocus, type R23G2ProtocolRow } from './cephaloR23G2ClinicalProfiles';

const A='RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1';
const IDs=[
  'M_ORAL_GNOMON_ANS_XI_PM_DEG_V1',
  'M_RICKETTS_FACIAL_TAPER_NPOG_MP_DEG_V1',
  'M_RICKETTS_MAXILLARY_HEIGHT_NCFA_DEG_V1',
  'M_RICKETTS_MANDIBULAR_PLANE_FH_DEG_V1',
  'M_RICKETTS_ANTERIOR_CRANIAL_LENGTH_CC_N_MM_V1',
  'M_RICKETTS_POSTERIOR_FACIAL_HEIGHT_GO_CF_MM_V1',
  'M_RICKETTS_TOTAL_FACIAL_HEIGHT_BAN_XIPM_DEG_V1',
  'M_RICKETTS_RAMUS_POSITION_FH_CFXI_DEG_V1',
  'M_RICKETTS_PORION_LOCATION_PTV_MM_V1',
  'M_RICKETTS_MANDIBULAR_ARC_DCXI_XIPM_DEG_V1',
  'M_RICKETTS_CORPUS_LENGTH_XI_PM_MM_V1',
] as const;
const CF='RICKETTS_CF_FH_PTV_INTERSECTION_V1';
const CC='RICKETTS_CC_ATLAS2009_BAN_PTGN_INTERSECTION_V1';
const XI='RICKETTS_XI_RAMAL_RECTANGLE_R1_R4_FH_V1';

describe('W3 Atlas33 cranio-mandibular source contract ONLY, clinical NO-GO',()=>{
  it('publishes exactly 11 Atlas-only descriptions; no generated LOT06 or numeric Focus',()=>{
    for(const id of IDs){
      const d=get(A,id,[]);
      expect(d?.clinicalEvidenceVerifiedByThisPreview).toBe(false);
      expect(d?.requiresSameImageSource).toBe(true);
      expect(findR23G3PinnedRequirements(id,[])).toBeNull();
    }
    expect(get(A,'M_UNKNOWN_MM_V1',[])).toBeNull();
    expect(get('RICKETTS_GREGORET_1997_SUMMARIZED_13_PROTOCOL_V1',IDs[0],[])).toBeNull();
  });
  it('CF requires actual canonical PTV, not a generic CF point',()=>{
    const x=get(A,IDs[2],['N','A','CF']);
    expect(x?.requiredConstructions).toEqual([CF]);
    expect(x?.constructionTransitiveLandmarks[CF]).toEqual(['PR_Ricketts_PTV','Po_anatomic','Or']);
    expect(x?.constructionDependencyChain[CF]).toEqual([CF,'RICKETTS_PTV_PR_POSTERIOR_PPF_PERP_FH_V1']);
  });
  it('CC uses manual Pt_Ricketts plus constructed Gn, not PR_Ricketts_PTV',()=>{
    const x=get(A,IDs[4],['N','Pt','PR_Ricketts_PTV']);
    expect(x?.requiredConstructions).toEqual([CC]);
    expect(x?.constructionTransitiveLandmarks[CC]).toEqual(['Ba','N','Pt_Ricketts','Pog_hard','Go','Me']);
    expect(x?.constructionDependencyChain[CC]).toEqual([CC,'RICKETTS_GN_CONSTRUCTED_NPOG_GOME_V1']);
    expect(x?.requiresCalibration).toBe(true);
  });
  it('Xi must use R1-R4 and anatomic FH, not direct generic Xi',()=>{
    const x=get(A,IDs[0],['ANS','Xi','Pm']);
    expect(x?.missingLandmarks).toEqual(['Pm_Ricketts']);
    expect(x?.requiredConstructions).toEqual([XI]);
    expect(x?.constructionTransitiveLandmarks[XI]).toEqual([
      'R1_Ricketts','R2_Ricketts','R3_Ricketts','R4_Ricketts','Po_anatomic','Or']);
    expect(x?.requiredManualLandmarks).toEqual(['Pm_Ricketts']);
  });
  it('keeps factor 28 linear posterior facial height and 29 angular TOTAL facial height',()=>{
    const linear=get(A,IDs[5],[]);
    const angular=get(A,IDs[6],[]);
    expect(linear?.requiresCalibration).toBe(true);
    expect(linear?.requiredManualLandmarks).toEqual(['GO_Ricketts_PFH']);
    expect(angular?.requiresCalibration).toBe(false);
    expect(angular?.requiredManualLandmarks).toEqual(['Pm_Ricketts']);
  });
  it('refuses manual DC and generic mandibular plane substitution',()=>{
    expect(get(A,IDs[9],['DC','Pm','Xi'])?.missingLandmarks).toEqual(['DC_Ricketts','Pm_Ricketts']);
    expect(get(A,IDs[1],[])?.requiredConstructions).toEqual(['RICKETTS_MANDIBULAR_PLANE_ANGLE_MENTON_V1']);
    expect(get(A,IDs[7],[])?.requiredConstructions).toEqual([CF,XI]);
  });
  it('even all direct landmark IDs and a value cannot create Focus',()=>{
    const id=IDs[8];const d=get(A,id,['Po_anatomic']);
    expect(d?.missingLandmarks).toEqual([]);
    expect(d?.clinicalEvidenceVerifiedByThisPreview).toBe(false);
    const row={
      order:31,canonical_measurement_id:id,label:'Porion to PTV',unit:'mm',
      contract_state:'CONDITIONAL_EXECUTABLE',availability_status:'AVAILABLE',
      value:3.8,source_contract:A,classification_authority:false
    } as R23G2ProtocolRow;
    expect(resolveR23G3RuntimeFocus(row)).toBeNull();
  });
});
