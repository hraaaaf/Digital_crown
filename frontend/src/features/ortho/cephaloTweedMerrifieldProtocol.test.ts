import { describe, expect, it } from 'vitest';
import {
  hasCertifiedTweedPoAnatomic,
  readTweedMerrifieldProtocolProjection,
  tweedMerrifieldProtocolRow,
} from './cephaloTweedMerrifieldProtocol';

const profile = {
  protocol_profile_id: 'TWEED_MERRIFIELD_DC_PROTOCOL_PROFILE_V1',
  source_lock_gate: { status: 'SATISFIED' },
  final_gate: { status: 'OPEN' },
  rows: [
    {
      canonical_measurement_id: 'M_FH_GOME_DEG_V1',
      label: 'FMA',
      profile_section: 'TWEED_1954_TRIANGLE_DC_PO_OR_V1',
      value: 24.5,
      unit: 'deg',
      availability_status: 'AVAILABLE',
      measurement_refs: ['m:fma'],
      reference_authority: 'CONTEXT_ONLY_NO_RUNTIME_DELTA',
      classification_authority: false,
      interpretation_status: 'RAW_MEASUREMENT_WITH_SOURCE_CONTEXT_ONLY',
    },
  ],
};

describe('Tweed-Merrifield protocol projection reader', () => {
  it('requires verified evidence authority', () => {
    expect(readTweedMerrifieldProtocolProjection({ scientific_read_path: { protocol_profiles: { tweed_merrifield: profile } } })).toBeNull();
  });

  it('reads only the source-locked profile identity', () => {
    const anglesData = {
      scientific_read_path: {
        authority: 'EVIDENCE_GRAPH_V1',
        active_chain: 'VERIFIED',
        protocol_profiles: { tweed_merrifield: profile },
      },
    };
    expect(readTweedMerrifieldProtocolProjection(anglesData)?.protocol_profile_id).toBe('TWEED_MERRIFIELD_DC_PROTOCOL_PROFILE_V1');
    expect(tweedMerrifieldProtocolRow(anglesData, 'M_FH_GOME_DEG_V1')?.value).toBe(24.5);
    expect(hasCertifiedTweedPoAnatomic(anglesData)).toBe(true);
  });

  it('fails closed for the visual Po bridge without a verified available Po-dependent canonical row', () => {
    const unavailable = {
      ...profile,
      rows: profile.rows.map(row => ({ ...row, availability_status: 'NOT_COMPUTABLE', value: null })),
    };
    expect(hasCertifiedTweedPoAnatomic({
      scientific_read_path: {
        authority: 'EVIDENCE_GRAPH_V1',
        active_chain: 'VERIFIED',
        protocol_profiles: { tweed_merrifield: unavailable },
      },
    })).toBe(false);
    expect(hasCertifiedTweedPoAnatomic({
      scientific_read_path: {
        authority: 'LEGACY',
        active_chain: 'VERIFIED',
        protocol_profiles: { tweed_merrifield: profile },
      },
    })).toBe(false);
  });
});
