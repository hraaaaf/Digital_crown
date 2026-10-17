import { describe, expect, it } from 'vitest';
import { findR23G8W2DentalRequirements as get } from './cephaloR23G8W2DentalRequirements';
import { findR23G3PinnedRequirements } from './cephaloR23G3PinnedRequirements';
import { resolveR23G3RuntimeFocus, type R23G2ProtocolRow } from './cephaloR23G2ClinicalProfiles';

const atlas='RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1';
const ids=[
  'M_RICKETTS_MOLAR_RELATION_FOP_MM_V1',
  'M_RICKETTS_CANINE_RELATION_FOP_MM_V1',
  'M_RICKETTS_OVERJET_FOP_MM_V1',
  'M_RICKETTS_L1_OCCLUSAL_EXTRUSION_MM_V1',
  'M_U6_PTV_MM_V1',
  'M_RICKETTS_OCCLUSAL_PLANE_XIPM_DEG_V1',
  'M_RICKETTS_UPPER_LIP_LENGTH_ANS_COMMISSURE_MM_V1',
] as const;

describe('W2 Atlas 2009 dental/manual source obligations, clinical fail-closed',()=>{
  it('contains seven exact source-only Atlas descriptors and never promotes LOT06 Focus',()=>{
    for(const id of ids){
      const d=get(atlas,id,[]);
      expect(d?.clinicalEvidenceVerifiedByThisPreview).toBe(false);
      expect(d?.requiresSameImageSource).toBe(true);
      expect(findR23G3PinnedRequirements(id,[])).toBeNull();
    }
    expect(get(atlas,'M_UNKNOWN_MM_V1',[])).toBeNull();
  });
  it('keeps molar distal and canine cusp identities distinct from generic teeth',()=>{
    const molar=get(atlas,ids[0],['L6','U6','L6_CUSP','U6_CUSP']);
    expect(molar?.missingLandmarks).toEqual(['L6_DISTAL_Ricketts','U6_DISTAL_Ricketts']);
    expect(molar?.requiredManualLandmarks).toEqual(['L6_DISTAL_Ricketts','U6_DISTAL_Ricketts']);
    expect(get(atlas,ids[1],[])?.requiredManualLandmarks).toEqual(['L3_CUSP_Ricketts','U3_CUSP_Ricketts']);
  });
  it('keeps source Ricketts FOP and incisor long axis, no guessed plan',()=>{
    const overjet=get(atlas,ids[2],[]);
    expect(overjet?.requiredLandmarks).toEqual(['L1_incisal','U1_incisal']);
    expect(overjet?.requiredConstructions).toEqual(['RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_BICUSPID_MOLAR_V1']);
    expect(overjet?.requiresCalibration).toBe(true);
    expect(overjet?.constructionUpstreamLandmarks['RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_BICUSPID_MOLAR_V1'])
      .toEqual(['FOP_PREMOLAR_Ricketts','FOP_MOLAR_Ricketts']);
    expect(get(atlas,ids[3],[])?.requiredLandmarks).toEqual(['L1_incisal','L1_apex']);
  });
  it('requires U6 distal, canonical PTV and upstream manual PR identity',()=>{
    const u6=get(atlas,ids[4],['U6']);
    expect(u6?.missingLandmarks).toEqual(['U6_DISTAL_Ricketts']);
    expect(u6?.requiredConstructions).toEqual(['RICKETTS_PTV_PR_POSTERIOR_PPF_PERP_FH_V1']);
    expect(u6?.indirectConstructionManualLandmarks).toEqual(['PR_Ricketts_PTV']);
    expect(u6?.constructionUpstreamLandmarks['RICKETTS_PTV_PR_POSTERIOR_PPF_PERP_FH_V1'])
      .toEqual(['PR_Ricketts_PTV','Po_anatomic','Or']);
  });
  it('requires manual Pm, source Xi and manual Xi upstream R1-R4',()=>{
    const angle=get(atlas,ids[5],['Pm']);
    expect(angle?.missingLandmarks).toEqual(['Pm_Ricketts']);
    expect(angle?.requiredManualLandmarks).toEqual(['Pm_Ricketts']);
    expect(angle?.indirectConstructionManualLandmarks).toEqual([
      'R1_Ricketts','R2_Ricketts','R3_Ricketts','R4_Ricketts'
    ]);
    expect(angle?.requiresCalibration).toBe(false);
    expect(angle?.constructionUpstreamLandmarks['RICKETTS_XI_RAMAL_RECTANGLE_R1_R4_FH_V1'])
      .toEqual(['R1_Ricketts','R2_Ricketts','R3_Ricketts','R4_Ricketts','Po_anatomic','Or']);
  });
  it('requires exact labial commissure, never replaces with Stomion',()=>{
    const lip=get(atlas,ids[6],['ANS','Stomion']);
    expect(lip?.missingLandmarks).toEqual(['LABIAL_COMMISSURE_Ricketts']);
    expect(lip?.requiredManualLandmarks).toEqual(['LABIAL_COMMISSURE_Ricketts']);
  });
  it('refuses profile substitution or phantom Focus even if all IDs are listed',()=>{
    expect(get('RICKETTS_GREGORET_1997_SUMMARIZED_13_PROTOCOL_V1',ids[0],[])).toBeNull();
    expect(get('MCNAMARA_1984_SINGLE_FILM_V1',ids[0],[])).toBeNull();
    const all=get(atlas,ids[6],['ANS','LABIAL_COMMISSURE_Ricketts']);
    expect(all?.missingLandmarks).toEqual([]);
    const row={
      order:17,canonical_measurement_id:ids[6],label:'Longueur lèvre',unit:'mm',
      contract_state:'CONDITIONAL_EXECUTABLE',availability_status:'NOT_COMPUTABLE',value:null,
      source_contract:atlas,classification_authority:false,
    } as R23G2ProtocolRow;
    expect(resolveR23G3RuntimeFocus(row)).toBeNull();
    expect(resolveR23G3RuntimeFocus({...row,availability_status:'AVAILABLE',value:19.2})).toBeNull();
  });
});
