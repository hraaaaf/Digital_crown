import { describe, expect, it } from 'vitest';
import { readSteinerProtocolProjection, STEINER_EXPLICIT_ID_SET, steinerProtocolRow } from './cephaloSteinerProtocol';

const anglesData = {
  scientific_read_path: {
    authority: 'EVIDENCE_GRAPH_V1',
    active_chain: 'VERIFIED',
    protocol_profiles: {
      steiner: {
        protocol_profile_id: 'STEINER_STATIC_PROTOCOL_PROFILE_V1',
        source_lock_gate: { status: 'SATISFIED' },
        final_gate: { status: 'OPEN' },
        norm_set: { authority: 'REFERENCE_DISPLAY_ONLY' },
        rows: [{
          canonical_measurement_id: 'M_SNA_DEG_V1',
          label: 'SNA',
          layer: 'STEINER_1953_BASE',
          value: 83.5,
          unit: '\u00b0',
          availability_status: 'AVAILABLE',
          measurement_refs: ['m:1'],
          historical_reference: 82,
          reference_delta: 1.5,
          reference_authority: 'REFERENCE_DISPLAY_ONLY',
          classification_authority: false,
          interpretation_status: 'REFERENCE_DISPLAY_ONLY_NO_CLASSIFICATION',
        }],
      },
    },
  },
};

describe('Steiner protocol projection',()=>{
  it('accepts only verified evidence-graph authority',()=>{
    expect(readSteinerProtocolProjection(anglesData)?.protocol_profile_id).toBe('STEINER_STATIC_PROTOCOL_PROFILE_V1');
    expect(readSteinerProtocolProjection({scientific_read_path:{authority:'LEGACY'}})).toBeNull();
  });
  it('reads backend-projected values without frontend formula',()=>{
    const row=steinerProtocolRow(anglesData,'M_SNA_DEG_V1');
    expect(row?.value).toBe(83.5);
    expect(row?.reference_delta).toBe(1.5);
    expect(row?.classification_authority).toBe(false);
  });
  it('keeps explicit identities distinct from legacy aliases',()=>{
    expect(STEINER_EXPLICIT_ID_SET.has('D_Steiner_1959')).toBe(true);
    expect(STEINER_EXPLICIT_ID_SET.has('D_point')).toBe(false);
    expect(STEINER_EXPLICIT_ID_SET.has('Gn_anatomic')).toBe(true);
  });
});
