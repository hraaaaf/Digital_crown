export type CephaloAnalysisMode = 'all' | 'steiner' | 'tweed' | 'mcnamara' | 'com' | 'ricketts';

export interface CephaloMetricFocus {
  key: string;
  points: string[];
  lines: string[];
}

export const CEPHALO_ANALYSIS_CHANGE_EVENT = 'digital-crown:cephalo-analysis';
export const CEPHALO_METRIC_FOCUS_EVENT = 'digital-crown:cephalo-metric';

export const publishCephaloAnalysis = (analysis: CephaloAnalysisMode) => {
  window.dispatchEvent(new CustomEvent(CEPHALO_ANALYSIS_CHANGE_EVENT, { detail: analysis }));
};

export const publishCephaloMetricFocus = (focus: CephaloMetricFocus | null) => {
  window.dispatchEvent(new CustomEvent(CEPHALO_METRIC_FOCUS_EVENT, { detail: focus }));
};
