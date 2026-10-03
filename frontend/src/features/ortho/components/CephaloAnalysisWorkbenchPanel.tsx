import React from 'react';
import { Info, Crosshair, CheckCircle2, AlertTriangle, MapPin, ShieldCheck } from 'lucide-react';
import { useOrthoStore } from '../stores/useOrthoStore';
import {
  CEPHALO_METRIC_FOCUS_EVENT,
  publishCephaloMetricFocus,
  type CephaloAnalysisMode,
  type CephaloMetricFocus,
} from '../cephaloAnalysisBridge';
import {
  CEPHALO_SCIENTIFIC_COLORS,
  cephaloMetricColor,
} from '../cephaloVisualSemantics';
import {
  describeCanonicalMetricFocus,
  resolveCanonicalMetricFocus,
} from '../cephaloCanonicalFocusAdapter';
import {
  readSteinerProtocolProjection,
  STEINER_EXPLICIT_IDENTITIES,
  steinerAvailabilityLabel,
  steinerProtocolRow,
} from '../cephaloSteinerProtocol';

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
  measurement_id?: string | null;
  canonical_measurement_id?: string | null;
  availability_status?: string | null;
  reference_delta?: number | null;
  reference_authority?: string | null;
  classification_authority?: boolean | null;
  interpretation_status?: string | null;
};

type MetricDefinition = {
  key: string;
  label: string;
  unit: '\u00b0' | 'mm';
  section: 'analyse_dentaire' | 'analyse_osseuse' | 'analyse_esthetique';
};

// Presentation metadata only. Scientific geometry is resolved exclusively through
// cephaloCanonicalFocusAdapter from LOT06 canonical measurement identities.
const DEFINITIONS: Record<string, MetricDefinition> = {
  SNA: { key: 'SNA', label: 'SNA', unit: '\u00b0', section: 'analyse_osseuse' },
  SNB: { key: 'SNB', label: 'SNB', unit: '\u00b0', section: 'analyse_osseuse' },
  ANB: { key: 'ANB', label: 'ANB', unit: '\u00b0', section: 'analyse_osseuse' },
  'M_SNA_DEG_V1': { key: 'M_SNA_DEG_V1', label: 'SNA', unit: '\u00b0', section: 'analyse_osseuse' },
  'M_SNB_DEG_V1': { key: 'M_SNB_DEG_V1', label: 'SNB', unit: '\u00b0', section: 'analyse_osseuse' },
  'M_ANB_DEG_V1': { key: 'M_ANB_DEG_V1', label: 'ANB', unit: '\u00b0', section: 'analyse_osseuse' },
  'M_U1_NA_DEG_V1': { key: 'M_U1_NA_DEG_V1', label: 'U1\u2013NA angulaire', unit: '\u00b0', section: 'analyse_dentaire' },
  'M_U1_NA_MM_V1': { key: 'M_U1_NA_MM_V1', label: 'U1\u2013NA lin\u00e9aire', unit: 'mm', section: 'analyse_dentaire' },
  'M_L1_NB_DEG_V1': { key: 'M_L1_NB_DEG_V1', label: 'L1\u2013NB angulaire', unit: '\u00b0', section: 'analyse_dentaire' },
  'M_L1_NB_MM_V1': { key: 'M_L1_NB_MM_V1', label: 'L1\u2013NB lin\u00e9aire', unit: 'mm', section: 'analyse_dentaire' },
  'M_INTERINCISAL_DEG_V1': { key: 'M_INTERINCISAL_DEG_V1', label: 'Angle inter-incisif', unit: '\u00b0', section: 'analyse_dentaire' },
  'M_OCCLUSAL_PLANE_SN_DEG_V1': { key: 'M_OCCLUSAL_PLANE_SN_DEG_V1', label: 'Plan occlusal\u2013SN', unit: '\u00b0', section: 'analyse_osseuse' },
  'M_SN_GOGN_DEG_V1': { key: 'M_SN_GOGN_DEG_V1', label: 'GoGn\u2013SN', unit: '\u00b0', section: 'analyse_osseuse' },
  'M_L1_GOGN_DEG_V1': { key: 'M_L1_GOGN_DEG_V1', label: 'L1\u2013GoGn', unit: '\u00b0', section: 'analyse_dentaire' },
  'M_SND_DEG_V1': { key: 'M_SND_DEG_V1', label: 'SND', unit: '\u00b0', section: 'analyse_osseuse' },
  'M_POG_NB_MM_V1': { key: 'M_POG_NB_MM_V1', label: 'Pog\u2013NB', unit: 'mm', section: 'analyse_osseuse' },
  'M_L1_DLINE_MM_V1': { key: 'M_L1_DLINE_MM_V1', label: 'L1\u2013D line lin\u00e9aire', unit: 'mm', section: 'analyse_dentaire' },
  'M_L1_DLINE_DEG_V1': { key: 'M_L1_DLINE_DEG_V1', label: 'L1\u2013D line angulaire', unit: '\u00b0', section: 'analyse_dentaire' },
  IMPA: { key: 'IMPA', label: 'I / Mandibulaire', unit: '\u00b0', section: 'analyse_dentaire' },
  I_Francfort: { key: 'I_Francfort', label: 'I / Francfort', unit: '\u00b0', section: 'analyse_dentaire' },
  Inter_Incisif: { key: 'Inter_Incisif', label: 'Angle inter-incisif', unit: '\u00b0', section: 'analyse_dentaire' },
  Surplomb: { key: 'Surplomb', label: 'Surplomb', unit: 'mm', section: 'analyse_dentaire' },
  Recouvrement: { key: 'Recouvrement', label: 'Recouvrement', unit: 'mm', section: 'analyse_dentaire' },
  Angle_de_Tweed: { key: 'Angle_de_Tweed', label: 'Angle de Tweed', unit: '\u00b0', section: 'analyse_osseuse' },
  Decalage_A_B: { key: 'Decalage_A_B', label: "Décalage osseux A'B'", unit: 'mm', section: 'analyse_osseuse' },
  Situation_A: { key: 'Situation_A', label: 'Pt A → verticale Nasion', unit: 'mm', section: 'analyse_osseuse' },
  Situation_B: { key: 'Situation_B', label: 'Pt B → verticale Nasion', unit: 'mm', section: 'analyse_osseuse' },
  Profondeur_Faciale: { key: 'Profondeur_Faciale', label: 'Profondeur faciale', unit: 'mm', section: 'analyse_osseuse' },
  Ligne_E_Ls: { key: 'Ligne_E_Ls', label: 'Lèvre sup. / ligne E', unit: 'mm', section: 'analyse_esthetique' },
  Ligne_E_Li: { key: 'Ligne_E_Li', label: 'Lèvre inf. / ligne E', unit: 'mm', section: 'analyse_esthetique' },
  Co_A: { key: 'Co_A', label: 'Co–A', unit: 'mm', section: 'analyse_osseuse' },
  Co_Gn: { key: 'Co_Gn', label: 'Co–Gn', unit: 'mm', section: 'analyse_osseuse' },
  ANS_Me: { key: 'ANS_Me', label: 'ANS–Me', unit: 'mm', section: 'analyse_osseuse' },
};

const ANALYSIS_METRICS: Record<CephaloAnalysisMode, string[]> = {
  all: ['SNA','SNB','ANB','IMPA','I_Francfort','Inter_Incisif','Surplomb','Recouvrement','Angle_de_Tweed','Decalage_A_B','Situation_A','Situation_B','Profondeur_Faciale','Ligne_E_Ls','Ligne_E_Li'],
  steiner: ['M_SNA_DEG_V1','M_SNB_DEG_V1','M_ANB_DEG_V1','M_U1_NA_DEG_V1','M_U1_NA_MM_V1','M_L1_NB_DEG_V1','M_L1_NB_MM_V1','M_INTERINCISAL_DEG_V1','M_OCCLUSAL_PLANE_SN_DEG_V1','M_SN_GOGN_DEG_V1','M_L1_GOGN_DEG_V1','M_SND_DEG_V1','M_POG_NB_MM_V1','M_L1_DLINE_MM_V1','M_L1_DLINE_DEG_V1'],
  tweed: ['IMPA','Angle_de_Tweed'],
  mcnamara: ['Co_A','Co_Gn','ANS_Me'],
  com: ['Surplomb','Recouvrement','IMPA','I_Francfort','Inter_Incisif','Angle_de_Tweed','Decalage_A_B','Situation_A','Situation_B','Profondeur_Faciale'],
  ricketts: ['Ligne_E_Ls','Ligne_E_Li'],
};

const ANALYSIS_LABELS: Record<CephaloAnalysisMode, string> = {
  all: 'Toutes analyses', steiner: 'Steiner', tweed: 'Tweed', mcnamara: 'McNamara', com: 'COM', ricketts: 'Ricketts',
};

const FAMILY_LEGEND = [
  ['skeletal', 'Squelettique'],
  ['dental', 'Dentaire'],
  ['soft_tissue', 'Tissus mous'],
  ['reference', 'Référence'],
] as const;

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
  if (definition.key.startsWith('M_')) {
    const row = steinerProtocolRow(anglesData, definition.key);
    if (!row) return undefined;
    return {
      value: row.value,
      norm_mean: row.historical_reference,
      status: steinerAvailabilityLabel(row.availability_status),
      interpretation: row.interpretation_status === 'REFERENCE_DISPLAY_ONLY_NO_CLASSIFICATION'
        ? 'R\u00e9f\u00e9rence historique affich\u00e9e sans classification clinique.'
        : null,
      unit: row.unit,
      measurement_id: row.measurement_refs?.[0] ?? null,
      canonical_measurement_id: row.canonical_measurement_id,
      availability_status: row.availability_status,
      reference_delta: row.reference_delta,
      reference_authority: row.reference_authority,
      classification_authority: row.classification_authority,
      interpretation_status: row.interpretation_status,
    };
  }
  const metrics = anglesData?.metrics ?? anglesData?.result?.metrics ?? {};
  const section = metrics?.[definition.section] ?? {};
  return section?.[definition.key];
};

const makeFocus = (anglesData: any, definition: MetricDefinition, metric?: MetricRecord): CephaloMetricFocus | null =>
  resolveCanonicalMetricFocus(definition.key, metric, anglesData);

export interface CephaloAnalysisWorkbenchPanelProps {
  P: ThemePalette;
  analysis: CephaloAnalysisMode;
}

export const CephaloAnalysisWorkbenchPanel: React.FC<CephaloAnalysisWorkbenchPanelProps> = ({ P, analysis }) => {
  const anglesData = useOrthoStore(state => state.anglesData);
  const landmarks = useOrthoStore(state => state.local.landmarks);
  const activePointId = useOrthoStore(state => state.activePointId);
  const setActivePointId = useOrthoStore(state => state.setActivePointId);
  const steinerProfile = React.useMemo(() => readSteinerProtocolProjection(anglesData), [anglesData]);
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
  const activeFocus = React.useMemo(
    () => activeDefinition ? makeFocus(anglesData, activeDefinition, activeMetric) : null,
    [anglesData, activeDefinition, activeMetric],
  );

  React.useEffect(() => {
    if (!activeDefinition || !activeFocus) {
      publishCephaloMetricFocus(null);
      return;
    }
    publishCephaloMetricFocus(activeFocus);
    return () => {
      window.dispatchEvent(new CustomEvent(CEPHALO_METRIC_FOCUS_EVENT, { detail: null }));
    };
  }, [activeDefinition, activeFocus]);

  const statusTone = (metric?: MetricRecord) => {
    if (!metric || readValue(metric) === null) return P.textDim;
    if (metric.availability_status === 'AVAILABLE') return P.accentSuccess;
    const status = (metric.status || '').trim().toLowerCase();
    if (!status || status === 'n/a') return P.textMuted;
    if (status.includes('missing') || status.includes('non calcul')) return P.textDim;
    if (status.includes('normal') || status.includes('valid')) return P.accentSuccess;
    if (
      status.includes('high') || status.includes('low') || status.includes('compens') ||
      status.includes('limit') || status.includes('borderline') || status.includes('vigil') ||
      status.includes('warning')
    ) return P.accentWarning;
    if (
      status.includes('hors') || status.includes('abnormal') || status.includes('severe') ||
      status.includes('critical') || status.includes('error') || status.includes('invalid')
    ) return P.accentError;
    return P.textMuted;
  };

  return (
    <aside
      data-r19-analysis-panel={analysis}
      data-lot08-protocol-profile={analysis === 'steiner' ? steinerProfile?.protocol_profile_id ?? 'UNAVAILABLE' : undefined}
      className="flex min-h-0 flex-col overflow-hidden rounded-3xl border"
      style={{ background: P.bgPanel, borderColor: P.border, boxShadow: P.shadowLg }}
    >
      <div className="border-b px-4 py-4 sm:px-5" style={{ borderColor: P.border }}>
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl" style={{ background: `${P.accent}18`, color: P.accent }}>
            <Crosshair size={17} />
          </div>
          <div className="min-w-0">
            <h3 className="break-words text-sm font-black leading-tight" style={{ color: P.text }}>Analyse {ANALYSIS_LABELS[analysis]}</h3>
            <p className="mt-0.5 text-[11px]" style={{ color: P.textMuted }}>{analysis === 'steiner' ? 'Profil source-lock\u00e9 1953 + extension 1959' : 'Mesure \u2194 construction g\u00e9om\u00e9trique'}</p>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1.5" aria-label="Code couleur céphalométrique">
          {FAMILY_LEGEND.map(([family, label]) => (
            <span key={family} className="inline-flex items-center gap-1.5 text-[9px] font-bold" style={{ color: P.textMuted }}>
              <span className="h-2 w-2 rounded-full" style={{ background: CEPHALO_SCIENTIFIC_COLORS[family] }} />
              {label}
            </span>
          ))}
        </div>
        {analysis === 'steiner' && (
          <div className="mt-3 space-y-2" data-lot08-steiner-contract>
            <div className="flex flex-wrap items-center gap-2 rounded-xl border px-3 py-2" style={{ borderColor: P.border, background: `${P.accent}0d` }}>
              <span className="inline-flex items-center gap-1.5 text-[9px] font-black uppercase tracking-[0.1em]" style={{ color: steinerProfile?.source_lock_gate?.status === 'SATISFIED' ? P.accentSuccess : P.accentWarning }}>
                <ShieldCheck size={12} /> Source-lock {steinerProfile?.source_lock_gate?.status === 'SATISFIED' ? 'valid\u00e9' : 'non v\u00e9rifi\u00e9'}
              </span>
              <span className="text-[9px]" style={{ color: P.textMuted }}>R&eacute;f&eacute;rences historiques &middot; affichage sans classification universelle</span>
            </div>
            <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2" aria-label="Points explicites Steiner">
              {STEINER_EXPLICIT_IDENTITIES.map(identity => {
                const present = landmarks.some(point => point.id === identity.id);
                const placing = activePointId === identity.id;
                return (
                  <button
                    key={identity.id}
                    type="button"
                    data-steiner-place={identity.id}
                    aria-pressed={placing}
                    onClick={() => setActivePointId(placing ? null : identity.id)}
                    className="flex min-h-9 items-center justify-between gap-2 rounded-lg border px-2.5 py-2 text-left"
                    style={{ borderColor: placing ? P.accent : P.border, background: placing ? `${P.accent}18` : P.bgInput }}
                    title={identity.help}
                  >
                    <span className="min-w-0">
                      <span className="block break-words text-[9px] font-black leading-tight" style={{ color: P.text }}>{identity.label}</span>
                      <span className="mt-0.5 block break-words text-[8px] leading-tight" style={{ color: present ? P.accentSuccess : P.textDim }}>{placing ? 'Cliquez sur la t\u00e9l\u00e9radio' : (present ? 'Plac\u00e9e \u00b7 cliquer pour replacer' : '\u00c0 placer')}</span>
                    </span>
                    <MapPin size={12} style={{ color: placing ? P.accent : (present ? P.accentSuccess : P.textDim) }} />
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <div className="min-h-0 flex-1 overflow-auto">
        <table className="w-full table-fixed border-collapse text-left" aria-label={`Mesures ${ANALYSIS_LABELS[analysis]}`}>
          <thead className="sticky top-0 z-10" style={{ background: P.bgPanel }}>
            <tr className="border-b text-[9px] font-black uppercase tracking-[0.12em]" style={{ borderColor: P.border, color: P.textDim }}>
              <th className="w-[39%] px-4 py-3">Mesure</th>
              <th className="w-[20%] px-2 py-3">Valeur</th>
              <th className="w-[25%] px-2 py-3">{analysis === 'steiner' ? 'R\u00e9f. hist.' : 'Norme'}</th>
              <th className="w-[16%] px-2 py-3 text-right">{analysis === 'steiner' ? '\u0394 r\u00e9f.' : '\u00c9cart'}</th>
            </tr>
          </thead>
          <tbody>
            {definitions.map(definition => {
              const metric = metricFromResults(anglesData, definition);
              const value = readValue(metric);
              const selected = activeKey === definition.key;
              const deviation = analysis === 'steiner'
                ? (typeof metric?.reference_delta === 'number' ? metric.reference_delta : null)
                : (value !== null && typeof metric?.norm_mean === 'number' ? value - metric.norm_mean : null);
              const familyTone = cephaloMetricColor(definition.key);
              const clinicalTone = statusTone(metric);
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
                      <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: familyTone }} />
                      <span className="break-words text-[11px] font-semibold leading-tight" style={{ color: selected ? P.text : P.textMuted }}>{definition.label}</span>
                    </div>
                  </td>
                  <td className="px-2 py-3 font-mono text-[11px] font-black tabular-nums" style={{ color: value === null ? P.textDim : P.text }}>
                    {value === null ? 'NC' : `${formatNumber(value)} ${definition.unit}`}
                  </td>
                  <td className="px-2 py-3 text-[10px]" style={{ color: P.textMuted }}>{normText(metric, definition.unit)}{analysis === 'steiner' && metric?.reference_authority === 'REFERENCE_DISPLAY_ONLY' && metric?.norm_mean != null ? ' \u00b7 hist.' : ''}</td>
                  <td className="px-2 py-3 text-right font-mono text-[10px]" style={{ color: deviation === null ? P.textDim : (analysis === 'steiner' ? P.textMuted : clinicalTone) }}>
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
            <Info size={16} className="mt-0.5 shrink-0" style={{ color: cephaloMetricColor(activeDefinition.key) }} />
            <div className="min-w-0">
              <div className="text-[10px] font-black uppercase tracking-[0.12em]" style={{ color: P.accent }}>Détail de la mesure sélectionnée</div>
              <div className="mt-1 flex items-center gap-2 text-sm font-black" style={{ color: P.text }}>
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: cephaloMetricColor(activeDefinition.key) }} />
                {activeDefinition.label}
              </div>
              <p className="mt-2 text-[11px] leading-relaxed" style={{ color: P.textMuted }}>{describeCanonicalMetricFocus(activeFocus)}</p>
              <div className="mt-3 flex items-start gap-2 rounded-xl px-3 py-2" style={{ background: `${statusTone(activeMetric)}12`, color: statusTone(activeMetric) }}>
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
