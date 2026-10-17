import { describe, expect, it } from 'vitest';
import type { Landmark } from './cephaloShared';
import { filterCephaloAnalysisLandmarks } from './CephaloTracingLayer';
import { findR23G3PinnedRequirements } from './cephaloR23G3PinnedRequirements';

const points = ['Co','Co_anatomic','Po','Po_anatomic','Pog','Pog_hard','Pt_Ricketts','PTM_McNamara','A','N','Or','Prn','Li_soft'].map(id => ({ id, x: 12, y: 20 })) as Landmark[];

describe('R23-G3 strict anatomical identity and responsive source visibility', () => {
  it('does not hide the full source landmarks for McNamara/Ricketts on legacy mobile or compact desktop', () => {
    for (const mode of ['mcnamara','ricketts'] as const) {
      expect(filterCephaloAnalysisLandmarks(points, mode)).toEqual(points);
    }
    expect(filterCephaloAnalysisLandmarks(points, 'com').length).toBeLessThan(points.length);
  });
  it('never substitutes generic Co for source-locked Co_anatomic', () => {
    const found = findR23G3PinnedRequirements('M_CO_A_MM_V1', ['Co','A']);
    expect(found?.requiredLandmarks).toContain('Co_anatomic');
    expect(found?.missingLandmarks).toContain('Co_anatomic');
    expect(found?.missingLandmarks).not.toContain('Co');
  });
  it('keeps Pt_Ricketts and Pog_hard distinct from PTM_McNamara/Pog', () => {
    const found = findR23G3PinnedRequirements('M_FACIAL_AXIS_RICKETTS_DEG_V1',
      ['Ba','N','PTM_McNamara','Pog','Go','Me']);
    expect(found?.missingLandmarks).toContain('Pt_Ricketts');
    expect(found?.missingLandmarks).toContain('Pog_hard');
    expect(found?.missingLandmarks).not.toContain('PTM_McNamara');
  });
  it('refuses manual dependencies not published in LOT06', () => {
    expect(findR23G3PinnedRequirements('M_U6_PTV_MM_V1', [])).toBeNull();
    expect(findR23G3PinnedRequirements('M_FACIAL_AXIS_MCNAMARA_DEG_V1', [])).toBeNull();
  });
});
