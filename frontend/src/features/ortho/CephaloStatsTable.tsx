/**
 * CephaloStatsTable.tsx  ·  v4.0  ·  Digital Crown
 * ─────────────────────────────────────────────────────────────────────────────
 * Table de résultats céphalométriques — alignée strictement sur cephalo_engine.py
 *
 * Pipeline backend consommé :
 *   metrics.analyse_dentaire  → Surplomb, Recouvrement, IMPA(90°), I_Francfort(107°),
 *                               Inter_Incisif(131°)
 *   metrics.analyse_osseuse   → Angle_de_Tweed(26°), Decalage_A_B, Situation_A,
 *                               Situation_B, Profondeur_Faciale
 *   chaque métrique           → { value, norm_mean, norm_min, norm_max,
 *                                  plage_compensation, status, interpretation, z_score }
 *   ai_narrative              → { diagnostic_squelettique, analyse_dentaire,
 *                                  strategie_therapeutique }
 *   analysis_metadata         → { unit, pixel_ratio, type, cohort, age?,
 *                                  maturation_stage? }
 *
 * Design :
 *   uiMode='pro'      → fond #050505, accents cyan/lime, typographie monospace
 *   uiMode='standard' → fond blanc, accents bleu médical
 *
 *   • Jauge de déviation avec zones (vert norme / ambre compensation)
 *   • Z-score badge (écart à la norme en σ)
 *   • Fantômes T1 (flèche prédiction → valeur future)
 *   • Bandeau narratif IA (ai_narrative)
 *   • Hover → onHoverMetric (connexion avec le SVG TracingLayer)
 *   • Synthèse vocale clinique (SpeechSynthesis)
 *   • Accordéon sections pour économiser l'espace vertical
 * ─────────────────────────────────────────────────────────────────────────────
 */

import React, { useEffect, useCallback, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../utils/cn';
import {
  Activity, ShieldCheck, AlertTriangle, Scale,
  Crosshair, Fingerprint, History, Brain,
  Target, TrendingUp, ChevronDown, ChevronUp,
  Sigma, Stethoscope, Zap,
} from 'lucide-react';

// ─────────────────────────────────────────────────────────────────────────────
// TYPES — alignés sur la sortie de _evaluate_metric() du cephalo_engine
// ─────────────────────────────────────────────────────────────────────────────

export interface MetricData {
  value:              number | null;
  norm_mean?:         number;
  norm_min?:          number;
  norm_max?:          number;
  plage_compensation?: [number, number] | null;
  status:             string;           // "Normal" | "High" | "Low" | "Compensated" | "Missing"
  interpretation?:    string;
  z_score?:           number;
  // Champs legacy (ancienne version)
  normale?:           string;
  unit?:              string;
  involved_points?:   string[];
  involved_lines?:    string[];
  tolerance_min?:     number;
  tolerance_max?:     number;
}

export interface CephaloStatsProps {
  patientName?: string;
  date?:        string;
  results?: {
    analysis_metadata?: {
      unit:              string;
      pixel_ratio:       number;
      type:              string;
      cohort?:           string;
      maturation_stage?: string;
      age?:              string;
    };
    metrics?: {
      analyse_osseuse?:  Record<string, MetricData>;
      analyse_dentaire?: Record<string, MetricData>;
    };
    ai_narrative?: {
      diagnostic_squelettique?:  string;
      analyse_dentaire?:         string;
      strategie_therapeutique?:  string;
    };
    calibration_status?: string;
  };
  ghostResults?: {
    metrics?: {
      analyse_osseuse?:  Record<string, MetricData>;
      analyse_dentaire?: Record<string, MetricData>;
    };
  };
  uiMode?:       'standard' | 'pro';
  onHoverMetric?: (data: { key: string; points: string[]; lines: string[] } | null) => void;
}

// ─────────────────────────────────────────────────────────────────────────────
// MÉTADONNÉES DES MÉTRIQUES
// Correspondance clé → points SVG + lignes + unité + label
// Aligné sur les IDs vision_service.py et cephalo_engine.py
// ─────────────────────────────────────────────────────────────────────────────

const METRIC_META: Record<string, {
  label:   string;
  unit:    string;
  points:  string[];
  lines:   string[];
  abbrev:  string;
}> = {
  // Analyse Dentaire
  IMPA:          { label: 'IMPA',                       unit: '°',  points: ['L1_incisal','L1_apex','Go','Me'],            lines: ['l1','mp'],    abbrev: 'IMPA'  },
  I_Francfort:   { label: 'I / Plan de Francfort',      unit: '°',  points: ['U1_incisal','U1_apex','Po','Or'],             lines: ['u1','fh'],    abbrev: 'I/F'   },
  Inter_Incisif: { label: 'Angle inter-incisif',        unit: '°',  points: ['U1_incisal','U1_apex','L1_incisal','L1_apex'], lines: ['u1','l1'],   abbrev: 'I↕I'   },
  Surplomb:      { label: 'Surplomb (overjet)',         unit: 'mm', points: ['U1_incisal','L1_incisal'],                    lines: ['fh'],         abbrev: 'OJ'    },
  Recouvrement:  { label: 'Recouvrement (overbite)',    unit: 'mm', points: ['U1_incisal','L1_incisal'],                    lines: ['fh'],         abbrev: 'OB'    },
  // Analyse Osseuse
  Angle_de_Tweed: { label: 'Angle de Tweed (FMA)',      unit: '°',  points: ['Go','Me','Po','Or'],                          lines: ['mp','fh'],    abbrev: 'FMA'   },
  Decalage_A_B:   { label: "Décalage A'B' (sagittal)",  unit: 'mm', points: ['A','B'],                                      lines: ['na','nb','ab'], abbrev: "A'B'" },
  Situation_A:    { label: "Position Point A (mxl.)",   unit: 'mm', points: ['A','N','Po','Or'],                            lines: ['na','fh'],    abbrev: 'sit.A' },
  Situation_B:    { label: "Position Point B (mdb.)",   unit: 'mm', points: ['B','N','Po','Or'],                            lines: ['nb','fh'],    abbrev: 'sit.B' },
  Profondeur_Faciale: { label: 'Profondeur Faciale',   unit: 'mm', points: ['S','N','Po','Or'],                            lines: ['sn','fh'],    abbrev: 'PF'    },
};

// ─────────────────────────────────────────────────────────────────────────────
// STATUT → TOKENS VISUELS
// ─────────────────────────────────────────────────────────────────────────────

type StatusToken = {
  hex:      string;
  textCls:  string;
  bgCls:    string;
  Icon:     React.FC<any>;
  label:    string;
};

function getStatusToken(status: string, isPro: boolean): StatusToken {
  const s = (status || '').toLowerCase();

  if (s.includes('normal')) return {
    hex:     isPro ? '#32cd32' : '#10b981',
    textCls: isPro ? 'text-[#32cd32]' : 'text-emerald-500',
    bgCls:   isPro ? 'bg-[#32cd32]/10 border-[#32cd32]/30' : 'bg-emerald-50 border-emerald-200 text-emerald-700',
    Icon:    ShieldCheck,
    label:   'Normal',
  };
  if (s.includes('compens')) return {
    hex:     isPro ? '#fbbf24' : '#f59e0b',
    textCls: isPro ? 'text-[#fbbf24]' : 'text-amber-600',
    bgCls:   isPro ? 'bg-[#fbbf24]/10 border-[#fbbf24]/30' : 'bg-amber-50 border-amber-200 text-amber-700',
    Icon:    Scale,
    label:   'Compensé',
  };
  if (s.includes('missing')) return {
    hex:     isPro ? '#6b7280' : '#94a3b8',
    textCls: isPro ? 'text-gray-500' : 'text-slate-400',
    bgCls:   isPro ? 'bg-gray-800 border-gray-700 text-gray-500' : 'bg-slate-50 border-slate-200 text-slate-400',
    Icon:    Crosshair,
    label:   'Manquant',
  };
  if (s.includes('high') || s.includes('low')) return {
    hex:     isPro ? '#fb923c' : '#f97316',
    textCls: isPro ? 'text-orange-400' : 'text-orange-500',
    bgCls:   isPro ? 'bg-orange-400/10 border-orange-400/30' : 'bg-orange-50 border-orange-200 text-orange-700',
    Icon:    AlertTriangle,
    label:   status === 'High' ? 'Élevé' : 'Bas',
  };
  // Pathologique par défaut
  return {
    hex:     isPro ? '#ef4444' : '#dc2626',
    textCls: isPro ? 'text-red-400' : 'text-red-600',
    bgCls:   isPro ? 'bg-red-400/10 border-red-400/30' : 'bg-red-50 border-red-200 text-red-700',
    Icon:    AlertTriangle,
    label:   status,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// SOUS-COMPOSANT : JAUGE DE DÉVIATION
// ─────────────────────────────────────────────────────────────────────────────
//
// Affiche 3 couches superposées sur une barre horizontale :
//   1. Zone de compensation (fond ambre semi-transparent)
//   2. Zone normale        (fond vert semi-transparent)
//   3. Curseur T0          (point coloré animé spring)
//   4. Curseur T1 fantôme  (point violet si ghost disponible)
//

interface GaugeProps {
  value:       number;
  normMin:     number;
  normMax:     number;
  compMin?:    number;
  compMax?:    number;
  statusHex:   string;
  ghostValue?: number | null;
  isPro:       boolean;
}

const DeviationGauge: React.FC<GaugeProps> = ({
  value, normMin, normMax, compMin, compMax,
  statusHex, ghostValue, isPro,
}) => {
  if (isNaN(value)) return null;

  const hasComp = compMin !== undefined && compMax !== undefined;

  // Fenêtre visuelle : compensation ± 50% de range de chaque côté
  const cMin = hasComp ? compMin! : normMin;
  const cMax = hasComp ? compMax! : normMax;
  const range = (cMax - cMin) === 0 ? 10 : (cMax - cMin);
  const vMin  = cMin - range * 0.8;
  const vMax  = cMax + range * 0.8;
  const span  = vMax - vMin;

  const pct = (v: number) => Math.max(3, Math.min(97, ((v - vMin) / span) * 100));

  const normStart = pct(normMin);
  const normEnd   = pct(normMax);
  const normW     = normEnd - normStart;
  const compStart = hasComp ? pct(cMin) : 0;
  const compW     = hasComp ? pct(cMax) - compStart : 0;

  const valPct   = pct(value);
  const ghostPct = ghostValue !== null && ghostValue !== undefined && !isNaN(ghostValue!)
    ? pct(ghostValue)
    : null;

  return (
    <div className={cn(
      'w-full h-1.5 rounded-full relative overflow-visible mt-1.5',
      isPro ? 'bg-gray-800' : 'bg-slate-200'
    )}>
      {/* Zone compensation */}
      {hasComp && (
        <div
          className={cn('absolute inset-y-0 rounded-sm', isPro ? 'bg-[#fbbf24]/18' : 'bg-amber-300/30')}
          style={{ left: `${compStart}%`, width: `${compW}%` }}
        />
      )}
      {/* Zone normale */}
      <div
        className={cn('absolute inset-y-0 rounded-sm', isPro ? 'bg-[#32cd32]/28' : 'bg-emerald-400/45')}
        style={{ left: `${normStart}%`, width: `${normW}%` }}
      />
      {/* Bornes normales (ticks) */}
      <div className={cn('absolute w-px h-3 top-1/2 -translate-y-1/2', isPro ? 'bg-[#32cd32]/60' : 'bg-emerald-500')} style={{ left: `${normStart}%` }} />
      <div className={cn('absolute w-px h-3 top-1/2 -translate-y-1/2', isPro ? 'bg-[#32cd32]/60' : 'bg-emerald-500')} style={{ left: `${normEnd}%` }} />

      {/* Curseur T1 fantôme */}
      {ghostPct !== null && (
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 0.55 }}
          className="absolute top-1/2 -translate-y-1/2 w-1.5 h-4 rounded-full bg-violet-400 z-0"
          style={{ left: `calc(${ghostPct}% - 3px)` }}
        />
      )}

      {/* Curseur T0 */}
      <motion.div
        initial={{ left: '50%' }}
        animate={{ left: `calc(${valPct}% - 3px)` }}
        transition={{ type: 'spring', stiffness: 55, damping: 14 }}
        className="absolute top-1/2 -translate-y-1/2 w-1.5 h-4 rounded-full z-10"
        style={{
          backgroundColor: statusHex,
          boxShadow: isPro ? `0 0 8px ${statusHex}` : 'none',
        }}
      />
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// SOUS-COMPOSANT : Z-SCORE BADGE
// ─────────────────────────────────────────────────────────────────────────────

const ZScoreBadge: React.FC<{ zScore: number; isPro: boolean }> = ({ zScore, isPro }) => {
  const z = Math.abs(zScore);
  const color = z <= 1 ? (isPro ? '#32cd32' : '#10b981')
              : z <= 2 ? (isPro ? '#fbbf24' : '#f59e0b')
              :           (isPro ? '#ef4444' : '#dc2626');
  return (
    <span
      className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[9px] font-black font-mono border"
      style={{ color, borderColor: `${color}40`, background: `${color}10` }}
    >
      <Sigma size={8} />
      {zScore.toFixed(1)}σ
    </span>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// SOUS-COMPOSANT : SECTION HEADER avec accordéon + badges globaux
// ─────────────────────────────────────────────────────────────────────────────

interface SectionHeaderProps {
  title:     string;
  icon:      React.FC<any>;
  metrics?:  Record<string, MetricData>;
  color:     string;
  isOpen:    boolean;
  onToggle:  () => void;
  isPro:     boolean;
}

const SectionHeader: React.FC<SectionHeaderProps> = ({
  title, icon: Icon, metrics, color, isOpen, onToggle, isPro,
}) => {
  const allNormal = !metrics || Object.values(metrics).every(
    m => !m.status || m.status.toLowerCase() === 'normal' || m.status.toLowerCase() === 'missing'
  );
  const hasCompensated = metrics && Object.values(metrics).some(m => m.status?.toLowerCase().includes('compens'));
  const hasPathological = metrics && Object.values(metrics).some(
    m => ['high','low','pathologique'].some(k => m.status?.toLowerCase().includes(k))
  );

  return (
    <button
      onClick={onToggle}
      className={cn(
        'w-full flex items-center justify-between px-5 py-3.5 rounded-xl transition-all',
        isPro ? 'hover:bg-gray-900/50' : 'hover:bg-slate-50'
      )}
    >
      <div className="flex items-center gap-3">
        <Icon size={15} style={{ color }} />
        <h3 className="text-xs font-black uppercase tracking-[0.18em]" style={{ color }}>
          {title}
        </h3>
        {/* Badge synthétique section */}
        <div className="flex items-center gap-1.5 ml-2">
          {allNormal && (
            <span className={cn('px-2.5 py-0.5 rounded text-[10px] font-black uppercase tracking-widest flex items-center gap-1 border',
              isPro ? 'bg-[#32cd32]/10 text-[#32cd32] border-[#32cd32]/30' : 'bg-emerald-50 text-emerald-600 border-emerald-200'
            )}>
              <ShieldCheck size={11} /> Normocclusion
            </span>
          )}
          {hasCompensated && (
            <span className={cn('px-2.5 py-0.5 rounded text-[10px] font-black uppercase tracking-widest flex items-center gap-1 border',
              isPro ? 'bg-[#fbbf24]/10 text-[#fbbf24] border-[#fbbf24]/30' : 'bg-amber-50 text-amber-600 border-amber-200'
            )}>
              <Scale size={11} /> Compensé
            </span>
          )}
          {hasPathological && (
            <span className={cn('px-2.5 py-0.5 rounded text-[10px] font-black uppercase tracking-widest flex items-center gap-1 border',
              isPro ? 'bg-red-500/10 text-red-400 border-red-500/30' : 'bg-red-50 text-red-600 border-red-200'
            )}>
              <AlertTriangle size={11} /> Anomalie
            </span>
          )}
        </div>
      </div>
      {isOpen ? <ChevronUp size={14} style={{ color, opacity: 0.6 }} /> : <ChevronDown size={14} style={{ color, opacity: 0.6 }} />}
    </button>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// COMPOSANT PRINCIPAL
// ─────────────────────────────────────────────────────────────────────────────

export const CephaloStatsTable: React.FC<CephaloStatsProps> = ({
  patientName,
  date,
  results,
  ghostResults,
  uiMode = 'standard',
  onHoverMetric,
}) => {
  const isPro        = uiMode === 'pro';
  const isUncalibr   = results?.calibration_status === 'unverified';
  const hasGhost     = !!ghostResults;
  const aiNarrative  = results?.ai_narrative;

  // Sections accordéons
  const [openOss,  setOpenOss]  = useState(true);
  const [openDent, setOpenDent] = useState(true);
  const [openNarr, setOpenNarr] = useState(true);

  // ── Moteur audio ────────────────────────────────────────────────────────────
  const announce = useCallback((name: string, data: MetricData) => {
    if (!('speechSynthesis' in window) || data.value === null || data.value === undefined) return;
    window.speechSynthesis.cancel();
    const meta  = METRIC_META[name];
    const unit  = meta?.unit ?? '';
    const text  = `${meta?.label ?? name}. ${data.value} ${unit}. ${data.interpretation ?? data.status}`;
    const utt   = new SpeechSynthesisUtterance(text);
    utt.lang    = 'fr-FR';
    utt.rate    = 1.1;
    window.speechSynthesis.speak(utt);
  }, []);

  useEffect(() => () => { if ('speechSynthesis' in window) window.speechSynthesis.cancel(); }, []);

  // ─────────────────────────────────────────────────────────────────────────
  // RENDU D'UNE LIGNE DE MÉTRIQUE
  // ─────────────────────────────────────────────────────────────────────────

  const renderRow = (key: string, data: MetricData, ghostData?: MetricData) => {
    if (!data) return null;

    const meta      = METRIC_META[key];
    const val       = data.value ?? null;
    const ghostVal  = ghostData?.value ?? null;
    const unit      = meta?.unit ?? data.unit ?? '°';
    const label     = meta?.label ?? key.replace(/_/g, ' ');
    const abbrev    = meta?.abbrev ?? key;
    const isMissing = val === null || data.status?.toLowerCase() === 'missing';
    const isUncMm   = isUncalibr && unit === 'mm';

    // Norme textuelle
    const hasNormBounds = data.norm_min !== undefined && data.norm_max !== undefined;
    const normText      = hasNormBounds
      ? `${data.norm_min} – ${data.norm_max} ${unit}`
      : (data.normale ?? '—');

    // Compensation (plage_compensation engine OU tolerance legacy)
    const compMin = data.plage_compensation?.[0] ?? data.tolerance_min;
    const compMax = data.plage_compensation?.[1] ?? data.tolerance_max;

    const tok = getStatusToken(data.status, isPro);

    return (
      <tr
        key={key}
        onMouseEnter={() => {
          onHoverMetric?.({
            key,
            points: meta?.points ?? data.involved_points ?? [],
            lines:  meta?.lines  ?? data.involved_lines  ?? [],
          });
          if (!isMissing) announce(key, data);
        }}
        onMouseLeave={() => onHoverMetric?.(null)}
        className={cn(
          'group transition-colors cursor-crosshair',
          isPro
            ? 'border-b border-white/5 hover:bg-white/[0.02]'
            : 'border-b border-slate-100 hover:bg-blue-50/40'
        )}
      >
        {/* ── Colonne 1 : Label ──────────────────────────────────────── */}
        <td className="py-4 px-5 w-[28%]">
          <div className="flex flex-col gap-0.5">
            <span className={cn(
              'text-xs font-semibold capitalize leading-snug transition-colors',
              isPro
                ? 'text-gray-300 group-hover:text-[#00f5ff]'
                : 'text-slate-700 group-hover:text-blue-700'
            )}>
              {label}
            </span>
            <span className={cn('text-[10px] font-mono uppercase tracking-widest', isPro ? 'text-gray-600' : 'text-slate-400')}>
              {abbrev}
            </span>
          </div>
        </td>

        {/* ── Colonne 2 : Norme ─────────────────────────────────────── */}
        <td className="py-4 px-5 text-center w-[18%]">
          <div className="flex flex-col items-center gap-1">
            <span className={cn('font-mono text-[11px] font-semibold', isPro ? 'text-gray-500' : 'text-slate-500')}>
              {normText}
            </span>
            {data.norm_mean !== undefined && (
              <span className={cn('text-[10px] font-mono', isPro ? 'text-gray-700' : 'text-slate-300')}>
                moy. {data.norm_mean}{unit}
              </span>
            )}
          </div>
        </td>

        {/* ── Colonne 3 : Valeur + jauge ────────────────────────────── */}
        <td className="py-4 px-5 w-[34%]">
          {isMissing ? (
            /* État manquant */
            <div className={cn(
              'flex items-center gap-2 text-[10px] font-black uppercase tracking-widest px-3 py-2 rounded-lg border animate-pulse',
              isPro ? 'bg-red-500/10 text-red-400 border-red-500/30' : 'bg-red-50 text-red-600 border-red-200'
            )}>
              <Crosshair size={11} />
              Points requis manquants
              {meta?.points && meta.points.length > 0 && (
                <span className="ml-1 opacity-70">→ {meta.points.join(' · ')}</span>
              )}
            </div>
          ) : (
            <div className="flex flex-col gap-1 w-full">
              {/* Valeur + delta T1 */}
              <div className="flex items-baseline gap-3">
                <span className={cn(
                  'font-black font-mono text-[17px] tabular-nums',
                  isUncMm ? 'line-through opacity-40' : '',
                  isPro ? 'text-white' : 'text-[#0f172a]'
                )}>
                  {val!.toFixed(unit === 'mm' ? 1 : 1)}
                  <span className={cn('text-[10px] ml-0.5', isPro ? 'text-gray-500' : 'text-slate-400')}>
                    {unit}
                  </span>
                </span>

                {/* Flèche T1 prédiction */}
                {hasGhost && ghostVal !== null && !isNaN(ghostVal!) && (
                  <span className="font-mono text-[12px] text-violet-400 font-bold flex items-center gap-1 opacity-75">
                    <TrendingUp size={10} />
                    {ghostVal!.toFixed(1)}{unit}
                  </span>
                )}

                {/* Z-score */}
                {data.z_score !== undefined && !isUncMm && (
                  <ZScoreBadge zScore={data.z_score} isPro={isPro} />
                )}
              </div>

              {/* Alerte calibration mm */}
              {isUncMm && (
                <span className={cn(
                  'text-[9px] font-black uppercase tracking-wider px-2 py-0.5 rounded border flex items-center gap-1 w-fit',
                  isPro ? 'bg-red-500/20 text-red-400 border-red-500/30' : 'bg-red-50 text-red-600 border-red-200'
                )}>
                  ⚠ Calibration requise
                </span>
              )}

              {/* Jauge */}
              {hasNormBounds && !isUncMm && (
                <DeviationGauge
                  value={val!}
                  normMin={data.norm_min!}
                  normMax={data.norm_max!}
                  compMin={compMin}
                  compMax={compMax}
                  statusHex={tok.hex}
                  ghostValue={ghostVal}
                  isPro={isPro}
                />
              )}
            </div>
          )}
        </td>

        {/* ── Colonne 4 : Statut + Interprétation ──────────────────── */}
        <td className="py-4 px-5 text-center w-[20%]">
          {isMissing ? (
            <span className={cn('text-[10px] font-mono', isPro ? 'text-gray-700' : 'text-slate-300')}>—</span>
          ) : (
            <div className="flex flex-col items-center gap-1.5">
              <span className={cn(
                'flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-lg border',
                tok.bgCls
              )}>
                <tok.Icon size={11} strokeWidth={2.5} />
                {tok.label}
              </span>
              {data.interpretation && (
                <span className={cn('text-[9px] italic text-center leading-snug max-w-[140px]', isPro ? 'text-gray-500' : 'text-slate-400')}>
                  {data.interpretation}
                </span>
              )}
            </div>
          )}
        </td>
      </tr>
    );
  };

  // ─────────────────────────────────────────────────────────────────────────
  // BANDEAU IA NARRATIF
  // ─────────────────────────────────────────────────────────────────────────

  const narrativeItems = aiNarrative ? [
    { icon: Target,       label: 'Diagnostic Squelettique', key: 'diagnostic_squelettique' as const, color: isPro ? '#00f5ff' : '#2563eb' },
    { icon: Stethoscope,  label: 'Analyse Dentaire',        key: 'analyse_dentaire'        as const, color: isPro ? '#32cd32' : '#059669' },
    { icon: Zap,          label: 'Stratégie Thérapeutique', key: 'strategie_therapeutique'  as const, color: isPro ? '#fbbf24' : '#d97706' },
  ] : [];

  // ─────────────────────────────────────────────────────────────────────────
  // THEAD RÉUTILISABLE
  // ─────────────────────────────────────────────────────────────────────────

  const renderThead = (accentBg: string) => (
    <thead>
      <tr className={cn('text-[10px] uppercase tracking-[0.14em]', isPro ? 'text-gray-500 border-b border-white/8' : 'text-white')}
        style={!isPro ? { background: accentBg } : {}}>
        <th className={cn('py-3 px-5 text-left rounded-tl-lg', isPro ? 'bg-white/[0.02]' : '')}>Mesure</th>
        <th className={cn('py-3 px-5 text-center',               isPro ? 'bg-white/[0.02]' : '')}>Norme</th>
        <th className={cn('py-3 px-5 text-center',               isPro ? 'bg-white/[0.02]' : '')}>{hasGhost ? 'T0 → T1 Prédit' : 'Résultat & Déviation'}</th>
        <th className={cn('py-3 px-5 text-center rounded-tr-lg', isPro ? 'bg-white/[0.02]' : '')}>Diagnostic</th>
      </tr>
    </thead>
  );

  // ─────────────────────────────────────────────────────────────────────────
  // RENDER PRINCIPAL
  // ─────────────────────────────────────────────────────────────────────────

  return (
    <div className={cn(
      'relative rounded-2xl overflow-hidden border mx-auto max-w-5xl mb-10 shadow-2xl transition-colors duration-300',
      isPro ? 'bg-[#050505] border-white/[0.06]' : 'bg-white border-slate-200'
    )}>

      {/* Watermark DC */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-[0.015] z-0 select-none">
        <div className={cn('w-[500px] h-[500px] border-[20px] rounded-full flex items-center justify-center', isPro ? 'border-white' : 'border-[#003380]')}>
          <span className={cn('text-8xl font-black -rotate-12', isPro ? 'text-white' : 'text-[#003380]')}>DC</span>
        </div>
      </div>

      <div className="relative z-10">

        {/* ── EN-TÊTE PATIENT ────────────────────────────────────────── */}
        <div className={cn(
          'flex justify-between items-end px-8 py-6 border-b',
          isPro ? 'bg-black/30 border-white/[0.06]' : 'bg-slate-50 border-slate-100'
        )}>
          <div className="space-y-2">
            <div>
              <span className={cn('text-[10px] font-black uppercase tracking-[0.16em] block mb-0.5', isPro ? 'text-gray-600' : 'text-slate-400')}>
                Dossier Patient
              </span>
              <span className={cn('text-xl font-bold', isPro ? 'text-[#00f5ff] font-mono tracking-tight' : 'text-[#003380]')}>
                {patientName ?? 'Non spécifié'}
              </span>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {results?.analysis_metadata?.age && (
                <span className={cn('px-2.5 py-1 rounded text-[10px] font-black uppercase tracking-widest flex items-center gap-1.5 border',
                  isPro ? 'bg-gray-800 text-gray-300 border-gray-700' : 'bg-white text-slate-600 border-slate-200 shadow-sm'
                )}>
                  <Fingerprint size={11} className={isPro ? 'text-[#00f5ff]' : 'text-[#003380]'} />
                  {results.analysis_metadata.age}
                </span>
              )}
              {results?.analysis_metadata?.cohort && (
                <span className={cn('px-2.5 py-1 rounded text-[10px] font-black uppercase tracking-widest flex items-center gap-1.5 border',
                  isPro ? 'bg-gray-800 text-gray-400 border-gray-700' : 'bg-white text-slate-500 border-slate-200 shadow-sm'
                )}>
                  <Activity size={11} />
                  {results.analysis_metadata.cohort}
                </span>
              )}
              {results?.analysis_metadata?.maturation_stage && (
                <span className={cn('px-2.5 py-1 rounded text-[10px] font-black uppercase tracking-widest flex items-center gap-1.5 border',
                  isPro ? 'bg-[#a855f7]/10 text-[#a855f7] border-[#a855f7]/30' : 'bg-purple-50 text-purple-700 border-purple-100'
                )}>
                  <Brain size={11} /> {results.analysis_metadata.maturation_stage}
                </span>
              )}
              {hasGhost && (
                <span className={cn('px-2.5 py-1 rounded text-[10px] font-black uppercase tracking-widest flex items-center gap-1.5 border',
                  isPro ? 'bg-violet-500/10 text-violet-400 border-violet-500/30' : 'bg-violet-50 text-violet-600 border-violet-200'
                )}>
                  <History size={11} /> Morphing T1 actif
                </span>
              )}
            </div>
          </div>

          <div className="text-right">
            <span className={cn('text-[10px] font-black uppercase tracking-[0.16em] block mb-0.5', isPro ? 'text-gray-600' : 'text-slate-400')}>
              Date du Bilan
            </span>
            <span className={cn('text-lg font-mono font-bold', isPro ? 'text-white' : 'text-slate-700')}>
              {date ?? '——'}
            </span>
            {results?.analysis_metadata?.type && (
              <span className={cn('text-[10px] font-mono uppercase tracking-widest block mt-1', isPro ? 'text-gray-600' : 'text-slate-400')}>
                {results.analysis_metadata.type}
              </span>
            )}
          </div>
        </div>

        {/* ── CORPS ──────────────────────────────────────────────────── */}
        <div className="px-4 py-6 space-y-6">

          {/* ═══════════════════════════════════════════════════════════
              I. ANALYSE OSSEUSE
              ═══════════════════════════════════════════════════════════ */}
          <section className={cn('rounded-xl overflow-hidden border', isPro ? 'border-white/[0.06]' : 'border-slate-200')}>
            <SectionHeader
              title="I. Analyse Osseuse"
              icon={Activity}
              metrics={results?.metrics?.analyse_osseuse}
              color={isPro ? '#00f5ff' : '#1d4ed8'}
              isOpen={openOss}
              onToggle={() => setOpenOss(v => !v)}
              isPro={isPro}
            />
            <AnimatePresence initial={false}>
              {openOss && (
                <motion.div
                  key="oss-body"
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.22, ease: 'easeInOut' }}
                  style={{ overflow: 'hidden' }}
                >
                  <table className="w-full">
                    {renderThead(isPro ? 'transparent' : '#1d4ed8')}
                    <tbody>
                      {results?.metrics?.analyse_osseuse && Object.keys(results.metrics.analyse_osseuse).length > 0
                        ? Object.entries(results.metrics.analyse_osseuse).map(([k, d]) =>
                            renderRow(k, d, ghostResults?.metrics?.analyse_osseuse?.[k])
                          )
                        : (
                          <tr><td colSpan={4} className={cn('py-8 text-center text-sm font-mono italic', isPro ? 'text-gray-700' : 'text-slate-400')}>
                            En attente des points osseux…
                          </td></tr>
                        )
                      }
                    </tbody>
                  </table>
                </motion.div>
              )}
            </AnimatePresence>
          </section>

          {/* ═══════════════════════════════════════════════════════════
              II. ANALYSE DENTAIRE
              ═══════════════════════════════════════════════════════════ */}
          <section className={cn('rounded-xl overflow-hidden border', isPro ? 'border-white/[0.06]' : 'border-slate-200')}>
            <SectionHeader
              title="II. Analyse Dentaire"
              icon={Activity}
              metrics={results?.metrics?.analyse_dentaire}
              color={isPro ? '#32cd32' : '#059669'}
              isOpen={openDent}
              onToggle={() => setOpenDent(v => !v)}
              isPro={isPro}
            />
            <AnimatePresence initial={false}>
              {openDent && (
                <motion.div
                  key="dent-body"
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.22, ease: 'easeInOut' }}
                  style={{ overflow: 'hidden' }}
                >
                  <table className="w-full">
                    {renderThead(isPro ? 'transparent' : '#059669')}
                    <tbody>
                      {results?.metrics?.analyse_dentaire && Object.keys(results.metrics.analyse_dentaire).length > 0
                        ? Object.entries(results.metrics.analyse_dentaire).map(([k, d]) =>
                            renderRow(k, d, ghostResults?.metrics?.analyse_dentaire?.[k])
                          )
                        : (
                          <tr><td colSpan={4} className={cn('py-8 text-center text-sm font-mono italic', isPro ? 'text-gray-700' : 'text-slate-400')}>
                            En attente des apex dentaires…
                          </td></tr>
                        )
                      }
                    </tbody>
                  </table>
                </motion.div>
              )}
            </AnimatePresence>
          </section>

          {/* ═══════════════════════════════════════════════════════════
              III. INTELLIGENCE NARRATIVE (ai_narrative)
              ═══════════════════════════════════════════════════════════ */}
          {aiNarrative && (
            <section className={cn('rounded-xl overflow-hidden border', isPro ? 'border-white/[0.06]' : 'border-slate-200')}>
              {/* Header accordéon narratif */}
              <button
                onClick={() => setOpenNarr(v => !v)}
                className={cn(
                  'w-full flex items-center justify-between px-5 py-3.5 transition-all',
                  isPro ? 'hover:bg-gray-900/50' : 'hover:bg-slate-50'
                )}
              >
                <div className="flex items-center gap-3">
                  <Brain size={15} style={{ color: isPro ? '#a855f7' : '#7c3aed' }} />
                  <h3 className="text-xs font-black uppercase tracking-[0.18em]"
                    style={{ color: isPro ? '#a855f7' : '#7c3aed' }}>
                    III. Synthèse Clinique IA
                  </h3>
                </div>
                {openNarr
                  ? <ChevronUp  size={14} style={{ color: isPro ? '#a855f7' : '#7c3aed', opacity: 0.6 }} />
                  : <ChevronDown size={14} style={{ color: isPro ? '#a855f7' : '#7c3aed', opacity: 0.6 }} />
                }
              </button>

              <AnimatePresence initial={false}>
                {openNarr && (
                  <motion.div
                    key="narr-body"
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.22, ease: 'easeInOut' }}
                    style={{ overflow: 'hidden' }}
                  >
                    <div className="px-5 pb-5 grid grid-cols-1 gap-3">
                      {narrativeItems.map(({ icon: NIcon, label, key, color }) => {
                        const text = aiNarrative[key];
                        if (!text) return null;
                        return (
                          <div key={key}
                            className={cn('rounded-xl p-4 border transition-colors', isPro ? 'bg-white/[0.02] border-white/[0.05]' : 'bg-slate-50 border-slate-100')}
                          >
                            <div className="flex items-center gap-2 mb-2">
                              <NIcon size={12} style={{ color }} />
                              <span className="text-[10px] font-black uppercase tracking-[0.16em]" style={{ color }}>
                                {label}
                              </span>
                            </div>
                            <p className={cn('text-xs leading-relaxed', isPro ? 'text-gray-300' : 'text-slate-600')}>
                              {text}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </section>
          )}

        </div>
      </div>
    </div>
  );
};