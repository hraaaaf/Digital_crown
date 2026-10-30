import React from 'react';
import {G5_VISUAL_REFERENCE,g5ReferenceSvgPath} from '../utils/g5VisualReference';

/**
 * READ-ONLY study-matched QA guide. Never passed to onSampledChange,
 * saveAnatomicalTraceDraft or approveAnatomicalTrace.
 */
export const G5VisualReferenceOverlay:React.FC<{focusId?:string|null}>=({focusId=null})=>{
  if(G5_VISUAL_REFERENCE.clinical_approval !== false) return null;
  return <g data-testid="g5-visual-reference-overlay"
    aria-label="Calques de référence de revue, non cliniques"
    pointerEvents="none" aria-hidden="true">
    {G5_VISUAL_REFERENCE.curves.filter(curve=>!focusId||curve.id===focusId).map(curve=><path
      key={curve.id} data-testid={`g5-reference-${curve.id}`}
      d={g5ReferenceSvgPath(curve.points)}
      fill="none" stroke={curve.color} strokeWidth={5}
      strokeDasharray={curve.style==='dashed'?'18 18':undefined}
      strokeLinecap="round" strokeLinejoin="round"
      opacity={0.9} pointerEvents="none"/>)}
  </g>;
};
