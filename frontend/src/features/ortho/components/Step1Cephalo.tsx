import React from 'react';
import { Step1Cephalo as Step1CephaloBase } from './Step1CephaloBase';
import { CephaloAnalysisWorkbenchPanel } from './CephaloAnalysisWorkbenchPanel';
import { useOrthoStore } from '../stores/useOrthoStore';
import {
  CEPHALO_ANALYSIS_CHANGE_EVENT,
  type CephaloAnalysisMode,
} from '../cephaloAnalysisBridge';

interface ThemePalette {
  bg: string;
  bgPanel: string;
  bgCard: string;
  bgInput: string;
  border: string;
  borderFocus: string;
  text: string;
  textMuted: string;
  textDim: string;
  accent: string;
  accentSuccess: string;
  accentWarning: string;
  accentError: string;
  shadow: string;
  shadowLg: string;
}

interface Step1CephaloProps {
  P: ThemePalette;
  fileRef: React.RefObject<HTMLInputElement | null>;
  step1ContainerRef: React.RefObject<HTMLDivElement | null>;
}

/**
 * R19 layout controller.
 *
 * The R18 Step1 implementation is preserved unchanged in Step1CephaloBase.tsx.
 * This wrapper only changes page composition: tracing on the left, analysis
 * measurements/details on the right at desktop widths, stacked on smaller
 * screens. All visual styling in the analysis panel comes from Digital Crown
 * theme tokens supplied by CephaloWorkspace.
 */
export const Step1Cephalo: React.FC<Step1CephaloProps> = (props) => {
  const hasImage = useOrthoStore(state => Boolean(state.imageSrc));
  const [analysis, setAnalysis] = React.useState<CephaloAnalysisMode>('all');

  React.useEffect(() => {
    const onAnalysis = (event: Event) => {
      const value = (event as CustomEvent<CephaloAnalysisMode>).detail;
      if (value) setAnalysis(value);
    };
    window.addEventListener(CEPHALO_ANALYSIS_CHANGE_EVENT, onAnalysis as EventListener);
    return () => window.removeEventListener(CEPHALO_ANALYSIS_CHANGE_EVENT, onAnalysis as EventListener);
  }, []);

  if (!hasImage) return <Step1CephaloBase {...props} />;

  return (
    <div data-r19-reference-layout className="grid min-w-0 grid-cols-1 gap-3 xl:grid-cols-[minmax(0,1.55fr)_minmax(330px,0.82fr)] xl:items-stretch">
      <div className="min-w-0">
        <Step1CephaloBase {...props} />
      </div>
      <div className="min-w-0 h-[68vh] xl:h-[80vh]">
        <CephaloAnalysisWorkbenchPanel P={props.P} analysis={analysis} />
      </div>
    </div>
  );
};
