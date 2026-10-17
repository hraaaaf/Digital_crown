import { describe, expect, it } from 'vitest';
import { findR23G3PinnedRequirements } from './cephaloR23G3PinnedRequirements';
import { findR23G7AtlasSourceRequirements, R23G7_ATLAS_PROFILE_ID } from './cephaloR23G7AtlasSourceRequirements';
import { resolveR23G3RuntimeFocus, type R23G2ProtocolRow } from './cephaloR23G2ClinicalProfiles';

const get = (id: string, present: string[] = []) =>
  findR23G7AtlasSourceRequirements(R23G7_ATLAS_PROFILE_ID, id, present);

describe('R23-G7 source contracts are read-only, Atlas-specific and never clinical evidence', () => {
  it('shows exact hard-tissue IDs for U1 protrusion, without Pog/Po aliasing', () => {
    const dep=get('M_RICKETTS_U1_APOG_PROTRUSION_MM_V1',
      ['U1_incisal','A','Pog','Po','Or']);
    expect(dep?.requiredLandmarks).toEqual(['U1_incisal','A','Pog_hard','Po_anatomic','Or']);
    expect(dep?.missingLandmarks).toEqual(['Pog_hard','Po_anatomic']);
    expect(dep?.availabilityGate).toContain('VERIFIED_CALIBRATION_REQUIRED');
  });
  it('keeps U1 apex and incisal tip separate for Atlas U1 inclination', () => {
    const dep=get('M_RICKETTS_U1_APOG_INCLINATION_DEG_V1',
      ['U1_incisal','A','Pog_hard']);
    expect(dep?.missingLandmarks).toEqual(['U1_apex']);
  });
  it('uses Ba N and anatomical Frankfort, no generic Po for cranial deflection', () => {
    const dep=get('M_RICKETTS_CRANIAL_DEFLECTION_FH_BAN_DEG_V1',
      ['Po','Or','Ba','N']);
    expect(dep?.missingLandmarks).toEqual(['Po_anatomic']);
    expect(dep?.requiredLandmarks).toEqual(['Po_anatomic','Or','Ba','N']);
  });
  it('rejects the other 22 unregistered Atlas rows, Gregoret, McNamara and arbitrary IDs', () => {
    for (const id of ['M_U6_PTV_MM_V1','M_RICKETTS_OVERBITE_FOP_MM_V1','M_UNKNOWN_MM_V1'])
      expect(get(id,['U1_incisal','A'])).toBeNull();
    expect(findR23G7AtlasSourceRequirements('RICKETTS_GREGORET_1997_SUMMARIZED_13_PROTOCOL_V1',
      'M_RICKETTS_U1_APOG_PROTRUSION_MM_V1',[])).toBeNull();
    expect(findR23G7AtlasSourceRequirements('MCNAMARA_1984_SINGLE_FILM_V1',
      'M_RICKETTS_CRANIAL_DEFLECTION_FH_BAN_DEG_V1',[])).toBeNull();
    // The LOT06 generated registry is NOT silently altered by G7.
    expect(findR23G3PinnedRequirements('M_RICKETTS_U1_APOG_PROTRUSION_MM_V1',[])).toBeNull();
  });
  it('never emits active Focus merely because all declared anatomical points are present', () => {
    const id='M_RICKETTS_U1_APOG_INCLINATION_DEG_V1';
    const deps=get(id,['U1_incisal','U1_apex','A','Pog_hard']);
    expect(deps?.missingLandmarks).toEqual([]);
    const row={
      order:13,canonical_measurement_id:id,label:'U1/A-Pog',unit:'deg',
      contract_state:'EXECUTABLE',availability_status:'NOT_COMPUTABLE',
      value:null,source_contract:R23G7_ATLAS_PROFILE_ID,classification_authority:false,
    } as R23G2ProtocolRow;
    expect(resolveR23G3RuntimeFocus(row)).toBeNull();
    expect(resolveR23G3RuntimeFocus({...row,availability_status:'AVAILABLE',value:12.5})).toBeNull();
  });
});
