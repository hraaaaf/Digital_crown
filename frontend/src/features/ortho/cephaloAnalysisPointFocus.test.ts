import { describe, expect, it } from 'vitest';
import { countDefaultVisiblePointMarkers, resolveCephaloAnalysisPointContract } from './cephaloAnalysisPointFocus';

const present=['S','N','A','B','Po','Or','Go','Me','Co','Gn','ANS',
  'U1_incisal','U1_apex','L1_incisal','L1_apex','Ls_soft','Li_soft','Prn','Pog_soft'];

describe('R23-F read-only clinical per-analysis landmark focus',()=>{
  it('never filters all-mode source points or labels an absent position',()=>{
    const result=resolveCephaloAnalysisPointContract('all',[],present);
    expect(result.ids).toBeNull();
    expect(result.count).toBe(present.length);
    expect(result.missing).toEqual([]);
  });
  it('derives ALL 15 Steiner metrics from pinned LOT06, including manual identities',()=>{
    const keys=['M_SNA_DEG_V1','M_SNB_DEG_V1','M_ANB_DEG_V1','M_U1_NA_DEG_V1',
      'M_U1_NA_MM_V1','M_L1_NB_DEG_V1','M_L1_NB_MM_V1','M_INTERINCISAL_DEG_V1',
      'M_OCCLUSAL_PLANE_SN_DEG_V1','M_SN_GOGN_DEG_V1','M_L1_GOGN_DEG_V1',
      'M_SND_DEG_V1','M_POG_NB_MM_V1','M_L1_DLINE_MM_V1','M_L1_DLINE_DEG_V1'];
    const result=resolveCephaloAnalysisPointContract('steiner',keys,present);
    expect(result.source).toBe('LOT06');
    expect(result.ids).toHaveLength(16);
    expect(result.ids).toContain('Occ_Steiner_Ant');
    expect(result.ids).toContain('Occ_Steiner_Post');
    expect(result.ids).toContain('Pog_hard');
    expect(result.missing).toContain('U1_facial_surface');
    expect(result.missing).toContain('Pog_hard');
    expect(result.ids).not.toContain('Prn');
  });
  it('preserves Tweed source-locked Po_anatomic and never substitutes generic Po',()=>{
    const keys=['M_FH_GOME_DEG_V1','M_IMPA_GOME_DEG_V1',
      'M_FMIA_L1_FH_DEG_V1','M_MERRIFIELD_Z_FH_DEG_V1'];
    const result=resolveCephaloAnalysisPointContract('tweed',keys,present);
    expect(result.source).toBe('LOT06');
    expect(result.ids).toHaveLength(9);
    expect(result.ids).toContain('Po_anatomic');
    expect(result.ids).not.toContain('Po');
    expect(result.missing).toContain('Po_anatomic');
  });
  it('refuses unknown/uncovered LOT06 metrics without hiding any point',()=>{
    const result=resolveCephaloAnalysisPointContract('steiner',['M_ANB_DEG_V1','UNKNOWN'],present);
    expect(result.ids).toBeNull();
    expect(result.source).toBe('unverified');
    expect(result.count).toBe(present.length);
  });
  it('explicitly bounds legacy workbench display anchors without invented positions',()=>{
    const m=resolveCephaloAnalysisPointContract('mcnamara',['Co_A','Co_Gn','ANS_Me'],present);
    const comMetrics=['Surplomb','Recouvrement','IMPA','I_Francfort','Inter_Incisif',
      'Angle_de_Tweed','Decalage_A_B','Situation_A','Situation_B','Profondeur_Faciale'];
    const c=resolveCephaloAnalysisPointContract('com',comMetrics,present);
    expect(resolveCephaloAnalysisPointContract('com',['Surplomb'],present).ids).toBeNull();
    const r=resolveCephaloAnalysisPointContract('ricketts',['Ligne_E_Ls','Ligne_E_Li'],present);
    expect(m.ids).toEqual(['Co','A','Gn','ANS','Me']);
    expect(c.ids).toContain('U1_incisal');
    // COM draws N/A/B on its independent construction layer, not as duplicate
    // editable dots. The visible counter must match the real SVG handle count.
    const allRelated=['S','N','A','B','Po','Or','Go','Me','U1_incisal','U1_apex','L1_incisal','L1_apex'];
    expect(countDefaultVisiblePointMarkers('com',c,allRelated)).toBe(9);
    expect(countDefaultVisiblePointMarkers('mcnamara',m,present)).toBe(5);
    expect(r.ids).toContain('Prn');
    expect(r.ids).toContain('Pog_soft');
    expect(r.ids).not.toContain('U1_apex');
    expect(r.ids).toContain('Po');
    expect(r.ids).toContain('Or');
    expect(r.ids).not.toContain('A');
    expect(r.ids).not.toContain('B');
    expect(new Set(r.ids).size).toBe(r.ids?.length);
    expect(resolveCephaloAnalysisPointContract('ricketts',['Ligne_E_Ls','UNKNOWN'],present).ids).toBeNull();
  });
});
