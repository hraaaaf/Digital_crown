import type { CephaloAnalysisMode } from './cephaloAnalysisBridge';
import { CEPHALO_LOT06_FOCUS_REGISTRY } from './cephaloLot06FocusRegistry.generated';

/**
 * R23-F: point VISIBILITY only, never measurement execution or anatomical truth.
 * Steiner/Tweed depend exclusively on pinned LOT06 measurement contracts;
 * legacy workbench modes use explicitly documented on-screen construction
 * anchors because their presentation keys are not in LOT06. The Ricketts
 * workbench currently lists only two E-line measurements: DO NOT claim a
 * complete Ricketts 32-point clinical protocol from this display.
 */
const LEGACY_DISPLAY_METRICS: Partial<Record<CephaloAnalysisMode, readonly string[]>> = {
  mcnamara:['Co_A','Co_Gn','ANS_Me'],
  com:['Surplomb','Recouvrement','IMPA','I_Francfort','Inter_Incisif','Angle_de_Tweed',
    'Decalage_A_B','Situation_A','Situation_B','Profondeur_Faciale'],
  ricketts:['Ligne_E_Ls','Ligne_E_Li'],
};

const LEGACY_DISPLAY_ANCHORS: Partial<Record<CephaloAnalysisMode, readonly string[]>> = {
  mcnamara: ['Co','A','Gn','ANS','Me'],
  com: ['S','N','A','B','Po','Or','Go','Me','U1_incisal','U1_apex','L1_incisal','L1_apex'],
  ricketts: [
    // Current workbench exposes only the E-line pair; keep hard Po/Or to
    // anchor its Ricketts Frankfurt overlay. Adding A/B/N here would also
    // reveal unrelated A′/B′ base-projection labels, falsely implying those
    // are requested E-line measures. The full atlas is NOT certified.
    'Po','Or','Prn','Pog_soft','Ls_soft','Li_soft',
  ],
};

/** COM anatomical references drawn on the construction layer, not duplicate edit dots. */
export const CEPHALO_COM_CONSTRUCTION_ONLY_IDS = ['N','A','B'] as const;

export const countDefaultVisiblePointMarkers = (
  mode: CephaloAnalysisMode,
  contract: CephaloAnalysisPointContract,
  presentIds: readonly string[],
): number => {
  if (!contract.ids) return presentIds.length;
  const allowed=new Set(contract.ids);
  const hiddenConstructionIds=mode==='com' ? new Set<string>(CEPHALO_COM_CONSTRUCTION_ONLY_IDS) : null;
  return presentIds.filter(id=>allowed.has(id)&&!hiddenConstructionIds?.has(id)).length;
};

export type CephaloAnalysisPointContract = {
  /** null = fail-open full radiograph, not a guessed partial set. */
  ids: readonly string[] | null;
  source: 'all' | 'LOT06' | 'legacy-display' | 'unverified';
  missing: readonly string[];
  count: number;
};

/** Exact IDs: Po is never silently interchangeable with Po_anatomic. */
export const resolveCephaloAnalysisPointContract = (
  mode: CephaloAnalysisMode,
  measurementKeys: readonly string[],
  presentPointIds: readonly string[],
): CephaloAnalysisPointContract => {
  if (mode==='all') return {ids:null,source:'all',missing:[],count:presentPointIds.length};
  let ids: string[] = [];
  let source: CephaloAnalysisPointContract['source'] = 'unverified';
  if (mode==='steiner'||mode==='tweed') {
    const entries = measurementKeys.map(key=>Object.prototype.hasOwnProperty.call(CEPHALO_LOT06_FOCUS_REGISTRY,key)
      ? CEPHALO_LOT06_FOCUS_REGISTRY[key as keyof typeof CEPHALO_LOT06_FOCUS_REGISTRY]
      : null);
    // A single uncovered measure would make the filtered view misleading.
    if (entries.some(entry=>!entry)||entries.length===0)
      return {ids:null,source:'unverified',missing:[],count:presentPointIds.length};
    ids = [...new Set(entries.flatMap(entry=>[...(entry?.requiredLandmarks??[])]))];
    source='LOT06';
  } else {
    const anchors=LEGACY_DISPLAY_ANCHORS[mode];
    const expected=LEGACY_DISPLAY_METRICS[mode];
    // Fail OPEN to all markers if the panel changes its clinical metric menu:
    // a stale hand-listed anchor set must never silently hide new dependencies.
    if(!anchors?.length||!expected?.length||measurementKeys.length!==expected.length
      ||expected.some(key=>!measurementKeys.includes(key)))
      return {ids:null,source:'unverified',missing:[],count:presentPointIds.length};
    ids=[...anchors];
    source='legacy-display';
  }
  const present=new Set(presentPointIds);
  return {ids,source,missing:ids.filter(id=>!present.has(id)),count:ids.filter(id=>present.has(id)).length};
};
