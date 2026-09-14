import React from 'react';
import { Info, Crosshair, CheckCircle2, AlertTriangle } from 'lucide-react';
import { useOrthoStore } from '../stores/useOrthoStore';
import {
  CEPHALO_METRIC_FOCUS_EVENT,
  publishCephaloMetricFocus,
  type CephaloAnalysisMode,
  type CephaloMetricFocus,
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

type MetricRecord = {
  value?: number | null;
  valeur?: number | null;
  norm_mean?: number | null;
  norm_min?: number | null;
  norm_max?: number | null;
  normale?: string | null;
  plage_compensation?: [number, number] | null;
  status?: string | null;
  interpretation?: string | null;
  z_score?: number | null;
  unit?: string | null;
  involved_points?: string[];
  involved_lines?: string[];
};

type MetricDefinition = {
  key: string;
  label: string;
  unit: '°' | 'mm';
  section: 'analyse_dentaire' | 'analyse_osseuse' | 'analyse_esthetique';
  points: string[];
  lines: string[];
  construction: string;
};

const DEFINITIONS: Record<string, MetricDefinition> = {
  SNA: { key: 'SNA', label: 'SNA', unit: '°', section: 'analyse_osseuse', points: ['S','N','A'], lines: ['sn','na'], construction: 'Angle entre la base crânienne S–N et la ligne N–A.' },
  SNB: { key: 'SNB', label: 'SNB', unit: '°', section: 'analyse_osseuse', points: ['S','N','B'], lines: ['sn','nb'], construction: 'Angle entre la base crânienne S–N et la ligne N–B.' },
  ANB: { key: 'ANB', label: 'ANB', unit: '°', section: 'analyse_osseuse', points: ['N','A','B'], lines: ['na','nb'], construction: 'Différence angulaire SNA–SNB, visualisée par les lignes N–A et N–B.' },
  IMPA: { key: 'IMPA', label: 'I / Mandibulaire', unit: '°', section: 'analyse_dentaire', points: ['L1_incisal','L1_apex','Go','Me'], lines: ['l1','mp'], construction: 'Angle entre l’axe de l’incisive inférieure et le plan mandibulaire Go–Me.' },
  I_Francfort: { key: 'I_Francfort', label: 'I / Francfort', unit: '°', section: 'analyse_dentaire', points: ['U1_incisal','U1_apex','Po','Or'], lines: ['u1','fh'], construction: 'Angle entre l’axe de l’incisive supérieure et le plan de Francfort Po–Or.' },
  Inter_Incisif: { key: 'Inter_Incisif', label: 'Angle inter-incisif', unit: '°', section: 'analyse_dentaire', points: ['U1_incisal','U1_apex','L1_incisal','L1_apex'], lines: ['u1','l1'], construction: 'Angle formé par les axes des incisives supérieure et inférieure.' },
  Surplomb: { key: 'Surplomb', label: 'Surplomb', unit: 'mm', section: 'analyse_dentaire', points: ['U1_incisal','L1_incisal','Po','Or'], lines: ['fh'], construction: 'Composante U1–L1 mesurée parallèlement au plan de Francfort.' },
  Recouvrement: { key: 'Recouvrement', label: 'Recouvrement', unit: 'mm', section: 'analyse_dentaire', points: ['U1_incisal','L1_incisal','Po','Or'], lines: ['fh'], construction: 'Composante U1–L1 mesurée perpendiculairement au plan de Francfort.' },
  Angle_de_Tweed: { key: 'Angle_de_Tweed', label: 'Angle de Tweed', unit: '°', section: 'analyse_osseuse', points: ['Go','Me','Po','Or'], lines: ['mp','fh'], construction: 'Angle entre le plan mandibulaire Go–Me et le plan de Francfort Po–Or.' },
  Decalage_A_B: { key: 'Decalage_A_B', label: "Décalage osseux A’B’", unit: 'mm', section: 'analyse_osseuse', points: ['A','B','Po','Or'], lines: ['fh'], construction: 'A’ et B’ sont les projections orthogonales de A et B sur Francfort ; A’B’ est leur séparation antéro-postérieure signée.' },
  Situation_A: { key: 'Situation_A', label: 'Pt A → verticale Nasion', unit: 'mm', section: 'analyse_osseuse', points: ['A','N','Po','Or'], lines: ['fh'], construction: 'Distance antéro-postérieure signée du point A à la verticale passant par Nasion, perpendiculaire à Francfort.' },
  Situation_B: { key: 'Situation_B', label: 'Pt B → verticale Nasion', unit: 'mm', section: 'analyse_osseuse', points: ['B','N','Po','Or'], lines: ['fh'], construction: 'Distance antéro-postérieure signée du point B à la verticale passant par Nasion, perpendiculaire à Francfort.' },
  Profondeur_Faciale: { key: 'Profondeur_Faciale', label: 'Profondeur faciale', unit: 'mm', section: 'analyse_osseuse', points: ['S','N','Po','Or'], lines: ['fh'], construction: 'Magnitude de la distance de S à la verticale de Nasion, perpendiculaire à Francfort, selon la construction COM versionnée.' },
  Ligne_E_Ls: { key: 'Ligne_E_Ls', label: 'Lèvre sup. / ligne E', unit: 'mm', section: 'analyse_esthetique', points: ['Prn','Pog_soft','Ls'], lines: ['eline'], construction: 'Distance signée de la lèvre supérieure à la ligne esthétique Prn–Pog′.' },
  Ligne_E_Li: { key: 'Ligne_E_Li', label: 'Lèvre inf. / ligne E', unit: 'mm', section: 'analyse_esthetique', points: ['Prn','Pog_soft','Li'], lines: ['eline'], construction: 'Distance signée de la lèvre inférieure à la ligne esthétique Prn–Pog′.' },
  Co_A: { key: 'Co_A', label: 'Co–A', unit: 'mm', section: 'analyse_osseuse', points: ['Co','A'], lines: ['coa'], construction: 'Longueur géométrique Co–A. Cette valeur n’est affichée que si un résultat backend versionné la fournit.' },
  Co_Gn: { key: 'Co_Gn', label: 'Co–Gn', unit: 'mm', section: 'analyse_osseuse', points: ['Co','Gn'], lines: ['cogn'], construction: 'Longueur géométrique Co–Gn. Cette valeur n’est affichée que si un résultat backend versionné la fournit.' },
  ANS_Me: { key: 'ANS_Me', label: 'ANS–Me', unit: 'mm', section: 'analyse_osseuse', points: ['ANS','Me'], lines: ['ansme'], construction: 'Hauteur ANS–Me. Cette valeur n’est affichée que si un résultat backend versionné la fournit.' },
};

const ANALYSIS_METRICS: Record<CephaloAnalysisMode, string[]> = {
  all: ['SNA','SNB','ANB','IMPA','I_Francfort','Inter_Incisif','Surplomb','Recouvrement','Angle_de_Tweed','Decalage_A_B','Situation_A','Situation_B','Profondeur_Faciale','Ligne_E_Ls','Ligne_E_Li'],
  steiner: ['SNA','SNB','ANB'],
  tweed: ['IMPA','Angle_de_Tweed'],
  mcnamara: ['Co_A','Co_Gn','ANS_Me'],
  com: ['Surplomb','Recouvrement','IMPA','I_Francfort','Inter_Incisif','Angle_de_Tweed','Decalage_A_B','Situation_A','Situation_B','Profondeur_Faciale'],
  ricketts: ['Ligne_E_Ls','Ligne_E_Li'],
};

const ANALYSIS_LABELS: Record<CephaloAnalysisMode, string> = {
  all: 'Toutes analyses', steiner: 'Steiner', tweed: 'Tweed', mcnamara: 'McNamara', com: 'COM', ricketts: 'Ricketts',
};

const readValue = (metric?: MetricRecord): number | null => {
  const value = metric?.value ?? metric?.valeur;
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
};

const formatNumber = (value: number) => `${value >= 0 ? '' : '−'}${Math.abs(value).toFixed(1).replace('.', ',')}`;

const normText = (metric: MetricRecord | undefined, unit: string) => {
  if (!metric) return '—';
  if (typeof metric.norm_min === 'number' && typeof metric.norm_max === 'number') {
    return `${formatNumber(metric.norm_min)} à ${formatNumber(metric.norm_max)} ${unit}`;
  }
  if (metric.normale) return metric.normale;
  if (typeof metric.norm_mean === 'number') return `${formatNumber(metric.norm_mean)} ${unit}`;
  return '—';
};

const statusLabel = (metric?: MetricRecord) => {
  if (!metric || readValue(metric) === null) return 'Non calculable';
  const status = (metric.status || '').trim();
  if (!status || status.toLowerCase() === 'n/a') return 'Mesure brute';
  return status;
};

const metricFromResults = (anglesData: any, definition: MetricDefinition): MetricRecord | undefined => {
  const metrics = anglesData?.metrics ?? anglesData?.result?.metrics ?? {};
  const section = metrics?.[definition.section] ?? {};
  return section?.[definition.key];
};

const makeFocus = (definition: MetricDefinition, metric?: MetricRecord): CephaloMetricFocus => ({
  key: definition.key,
  points: metric?.involved_points?.length ? metric.involved_points : definition.points,
  lines: metric?.involved_lines?.length ? metric.involved_lines : definition.lines,
});

export interface CephaloAnalysisWorkbenchPanelProps {
  P: ThemePalette;
  analysis: CephaloAnalysisMode;
}

export const CephaloAnalysisWorkbenchPanel: React.FC<CephaloAnalysisWorkbenchPanelProps> = ({ P, analysis }) => {
  const anglesData = useOrthoStore(state => state.anglesData);
  const definitions = React.useMemo(() => ANALYSIS_METRICS[analysis].map(key => DEFINITIONS[key]), [analysis]);
  const [selectedKey, setSelectedKey] = React.useState(definitions[0]?.key ?? '');
  const [hoverKey, setHoverKey] = React.useState<string | null>(null);

  React.useEffect(() => {
    setSelectedKey(definitions[0]?.key ?? '');
    setHoverKey(null);
  }, [analysis, definitions]);

  const activeKey = hoverKey ?? selectedKey;
  const activeDefinition = DEFINITIONS[activeKey] ?? definitions[0];
  const activeMetric = activeDefinition ? metricFromResults(anglesData, activeDefinition) : undefined;

  React.useEffect(() => {
    if (!activeDefinition) {
      publishCephaloMetricFocus(null);
      return;
    }
    publishCephaloMetricFocus(makeFocus(activeDefinition, activeMetric));
    return () => window.dispatchEvent(new CustomEvent(CEPHALO_METRIC_FOCUS_EVENT, { detail: null }));
  }, [activeDefinition, activeMetric]);

  const tone = (metric?: MetricRecord) => {
    if (!metric || readValue(metric) === null) return P.textDim;
    const status = (metric.status || '').toLowerCase();
    if (status.includes('normal')) return P.accentSuccess;
    if (status.includes('high') || status.includes('low') || status.includes('compens')) return P.accentWarning;
    if (status.includes('missing')) return P.textDim;
    return P.accent;
  };

  return (
    <aside
      data-r19-analysis-panel={analysis}
      className="flex min-h-0 flex-col overflow-hidden rounded-3xl border"
      style={{ background: P.bgPanel, borderColor: P.border, boxShadow: P.shadowLg }}
    >
      <div className="border-b px-4 py-4 sm:px-5" style={{ borderColor: P.border }}>
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl" style={{ background: `${P.accent}18`, color: P.accent }}>
            <Crosshair size={17} />
          </div>
          <div className="min-w-0">
            <h3 className="truncate text-sm font-black" style={{ color: P.text }}>Analyse {ANALYSIS_LABELS[analysis]}</h3>
            <p className="mt-0.5 text-[11px]" style={{ color: P.textMuted }}>Mesure ↔ construction géométrique</p>
          </div>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-auto">
        <table className="w-full table-fixed border-collapse text-left" aria-label={`Mesures ${ANALYSIS_LABELS[analysis]}`}>
          <thead className="sticky top-0 z-10" style={{ background: P.bgPanel }}>
            <tr className="border-b text-[9px] font-black uppercase tracking-[0.12em]" style={{ borderColor: P.border, color: P.textDim }}>
              <th className="w-[39%] px-4 py-3">Mesure</th>
              <th className="w-[20%] px-2 py-3">Valeur</th>
              <th className="w-[25%] px-2 py-3">Norme</th>
              <th className="w-[16%] px-2 py-3 text-right">Écart</th>
            </tr>
          </thead>
          <tbody>
            {definitions.map(definition => {
              const metric = metricFromResults(anglesData, definition);
              const value = readValue(metric);
              const selected = activeKey === definition.key;
              const deviation = value !== null && typeof metric?.norm_mean === 'number' ? value - metric.norm_mean : null;
              const rowTone = tone(metric);
              return (
                <tr
                  key={definition.key}
                  data-r19-metric={definition.key}
                  aria-selected={selected}
                  tabIndex={0}
                  onClick={() => setSelectedKey(definition.key)}
                  onFocus={() => setSelectedKey(definition.key)}
                  onMouseEnter={() => setHoverKey(definition.key)}
                  onMouseLeave={() => setHoverKey(null)}
                  className="cursor-pointer border-b transition-colors outline-none"
                  style={{ borderColor: P.border, background: selected ? `${P.accent}12` : 'transparent' }}
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: rowTone }} />
                      <span className="truncate text-[11px] font-semibold" style={{ color: selected ? P.text : P.textMuted }}>{definition.label}</span>
                    </div>
                  </td>
                  <td className="px-2 py-3 font-mono text-[11px] font-black tabular-nums" style={{ color: value === null ? P.textDim : P.text }}>
                    {value === null ? 'NC' : `${formatNumber(value)} ${definition.unit}`}
                  </td>
                  <td className="px-2 py-3 text-[10px]" style={{ color: P.textMuted }}>{normText(metric, definition.unit)}</td>
                  <td className="px-2 py-3 text-right font-mono text-[10px]" style={{ color: deviation === null ? P.textDim : rowTone }}>
                    {deviation === null ? '—' : `${deviation > 0 ? '+' : ''}${formatNumber(deviation)}`}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {activeDefinition && (
        <div data-r19-measure-detail={activeDefinition.key} className="m-3 rounded-2xl border p-4 sm:m-4" style={{ background: P.bgCard, borderColor: P.border }}>
          <div className="flex items-start gap-3">
            <Info size={16} className="mt-0.5 shrink-0" style={{ color: P.accent }} />
            <div className="min-w-0">
              <div className="text-[10px] font-black uppercase tracking-[0.12em]" style={{ color: P.accent }}>Détail de la mesure sélectionnée</div>
              <div className="mt-1 text-sm font-black" style={{ color: P.text }}>{activeDefinition.label}</div>
              <p className="mt-2 text-[11px] leading-relaxed" style={{ color: P.textMuted }}>{activeDefinition.construction}</p>
              <div className="mt-3 flex items-start gap-2 rounded-xl px-3 py-2" style={{ background: `${tone(activeMetric)}12`, color: tone(activeMetric) }}>
                {readValue(activeMetric) === null ? <AlertTriangle size={13} className="mt-0.5 shrink-0" /> : <CheckCircle2 size={13} className="mt-0.5 shrink-0" />}
                <span className="text-[10px] font-bold leading-relaxed">{statusLabel(activeMetric)}{activeMetric?.interpretation ? ` · ${activeMetric.interpretation}` : ''}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
};

export const cephaloAnalysisMetricKeys = ANALYSIS_METRICS;
export { readValue as readCephaloMetricValue, normText as formatCephaloNormText };
