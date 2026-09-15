import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, CheckCircle2, Clock3, LockKeyhole, RefreshCw, ShieldCheck } from 'lucide-react';
import { api } from '../../../services/api';

interface ProvenanceRef { label: string; value: string; }
interface ClinicianAction { available: boolean; audit_required: boolean; label: string; reason: string; }
interface ClinicalStage {
  stage_id: 'R11' | 'R12' | 'R13' | 'R14';
  title: string;
  presentation_state: 'BLOCKED' | 'AWAITING_CLINICIAN' | 'EVALUABLE' | 'VALIDATED' | 'REJECTED';
  authoritative_status: string | null;
  summary: string;
  blocking_gates: string[];
  missing_data_refs: string[];
  contradictions: string[];
  contraindications: string[];
  provenance: ProvenanceRef[];
  clinician_action: ClinicianAction;
}
interface StudioSnapshot {
  contract_version: string;
  patient_id: number;
  analysis_id: number | null;
  evidence_graph_present: boolean;
  active_runtime_chain_verified: boolean;
  blocking_gate_count: number;
  blocking_gates: string[];
  stages: ClinicalStage[];
  clinical_validation_available: boolean;
  clinical_validation_reason: string;
}
interface Props { patientId: number; analysisId?: number; P: any; }

const LABELS: Record<string, string> = {
  cephalo_analysis_missing: 'Analyse céphalométrique absente',
  typed_evidence_graph_missing: 'Données d’analyse incomplètes',
  active_runtime_chain_unverified: 'Vérification clinique incomplète',
  active_runtime_chain_incoherent: 'Données cliniques incohérentes',
  diagnostic_rule_registry_empty: 'Critères diagnostiques insuffisants',
  r11_authoritative_snapshot_not_persisted: 'Diagnostic scientifique à confirmer',
  r11_not_authoritative: 'Diagnostic scientifique à confirmer',
  r12_authoritative_snapshot_not_persisted: 'Problèmes et objectifs à confirmer',
  r12_not_authoritative: 'Problèmes et objectifs à confirmer',
  therapeutic_rule_registry_empty: 'Critères thérapeutiques insuffisants',
  r13_authoritative_snapshot_not_persisted: 'Options thérapeutiques à confirmer',
  r13_no_clinician_selected_option: 'Aucune option thérapeutique sélectionnée par le praticien',
  r14_authoritative_snapshot_not_persisted: 'Validation clinique finale à confirmer',
  clinician_selection_required: 'Sélection explicite du praticien requise',
};
const SHORT_TITLES: Record<ClinicalStage['stage_id'], string> = { R11: 'Diagnostic', R12: 'Objectifs', R13: 'Options', R14: 'Validation' };
const stateLabel = (state: ClinicalStage['presentation_state']) => {
  if (state === 'BLOCKED') return 'À compléter';
  if (state === 'AWAITING_CLINICIAN') return 'Action praticien requise';
  if (state === 'EVALUABLE') return 'À évaluer';
  if (state === 'VALIDATED') return 'Validé';
  return 'Rejeté';
};

const EvidenceRefs: React.FC<{ title: string; items: string[]; authoritative: boolean; P: any }> = ({ title, items, authoritative, P }) => (
  <div className="min-w-0 rounded-lg border px-2.5 py-2" style={{ borderColor: P.border, background: P.bgInput }}>
    <div className="flex items-start justify-between gap-2">
      <div className="text-[8px] font-black uppercase tracking-[0.09em]" style={{ color: P.text }}>{title}</div>
      {items.length > 0 && <span className="shrink-0 rounded-full px-1.5 py-0.5 text-[8px] font-black" style={{ background: `${P.accentWarning}14`, color: P.accentWarning }}>{items.length}</span>}
    </div>
    <p className="mt-1 text-[9px] leading-3.5" style={{ color: P.textDim }}>{items.length ? `${items.length} élément${items.length === 1 ? '' : 's'} à examiner.` : authoritative ? 'Aucun élément déclaré.' : 'Informations cliniques insuffisantes.'}</p>
  </div>
);

const StageStatusIcon: React.FC<{ stage: ClinicalStage; color: string }> = ({ stage, color }) => {
  if (stage.presentation_state === 'VALIDATED') return <CheckCircle2 size={13} style={{ color }} />;
  if (stage.presentation_state === 'AWAITING_CLINICIAN') return <Clock3 size={13} style={{ color }} />;
  return <LockKeyhole size={13} style={{ color }} />;
};

export const ClinicalScientificStudio: React.FC<Props> = ({ patientId, analysisId, P }) => {
  const [snapshot, setSnapshot] = useState<StudioSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<ClinicalStage['stage_id']>('R11');

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true); setError(null);
      try {
        const analysisQuery = analysisId != null ? `?analysis_id=${encodeURIComponent(String(analysisId))}` : '';
        const { data } = await api.get<StudioSnapshot>(`/patients/${patientId}/cephalo-clinical-studio${analysisQuery}`);
        if (!cancelled) setSnapshot(data);
      } catch (err) {
        console.error('R15 clinical studio snapshot unavailable:', err);
        if (!cancelled) setError("Les informations cliniques ne sont pas disponibles. Aucune validation n'est autorisée.");
      } finally { if (!cancelled) setLoading(false); }
    };
    void load();
    return () => { cancelled = true; };
  }, [patientId, analysisId]);

  const selected = useMemo(() => snapshot?.stages.find(stage => stage.stage_id === selectedId) ?? snapshot?.stages[0] ?? null, [snapshot, selectedId]);
  const statusColor = (state: ClinicalStage['presentation_state']) => {
    if (state === 'VALIDATED') return P.accentSuccess;
    if (state === 'REJECTED') return P.accentError;
    if (state === 'AWAITING_CLINICIAN' || state === 'EVALUABLE') return P.accentWarning;
    return P.accentError;
  };

  return (
    <section data-testid="r15-clinical-studio" className="mb-5 overflow-hidden rounded-[20px] border" style={{ background: P.bgPanel, borderColor: P.border, boxShadow: P.shadow }}>
      <div className="border-b px-3 py-3 sm:px-4" style={{ borderColor: P.border }}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-start gap-2.5">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[10px]" style={{ background: `${P.accent}12`, color: P.accent }}><ShieldCheck size={16} /></div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-x-2 gap-y-1"><h3 className="text-[11px] font-black uppercase tracking-[0.1em]" style={{ color: P.text }}>Parcours clinique</h3><span className="rounded-full px-2 py-0.5 text-[8px] font-black tracking-wide" style={{ background: `${P.accent}10`, color: P.accent }}>Diagnostic → décision clinique</span></div>
              <p className="mt-1 max-w-3xl text-[10px] leading-4" style={{ color: P.textMuted }}>Les mesures guident l’analyse, mais la validation clinique reste sous la responsabilité du praticien.</p>
            </div>
          </div>
          {snapshot && snapshot.blocking_gate_count > 0 && <div className="flex min-h-8 shrink-0 items-center gap-1.5 rounded-lg border px-2.5 py-1.5" style={{ borderColor: P.border, background: P.bgCard }}><LockKeyhole size={12} style={{ color: P.accentWarning }} /><span className="text-[8px] font-black uppercase tracking-wider" style={{ color: P.textMuted }}>{snapshot.blocking_gate_count} point{snapshot.blocking_gate_count === 1 ? '' : 's'} à vérifier</span></div>}
        </div>
      </div>

      {loading && <div className="flex items-center gap-3 px-4 py-4 text-xs font-bold" style={{ color: P.textMuted }}><RefreshCw size={15} className="animate-spin" /> Vérification des informations cliniques…</div>}
      {!loading && error && <div className="m-3 flex gap-3 rounded-xl border p-3.5" style={{ borderColor: `${P.accentError}55`, background: `${P.accentError}10` }}><AlertTriangle className="mt-0.5 shrink-0" size={17} style={{ color: P.accentError }} /><div><p className="text-xs font-black" style={{ color: P.text }}>Validation indisponible</p><p className="mt-1 text-xs leading-5" style={{ color: P.textMuted }}>{error}</p></div></div>}

      {!loading && snapshot && <div className="p-3 sm:p-4">
        <div data-testid="r15-stage-rail" className="grid grid-cols-4 gap-1.5 sm:gap-2" aria-label="Étapes du parcours clinique">
          {snapshot.stages.map(stage => { const active = selected?.stage_id === stage.stage_id; const color = statusColor(stage.presentation_state); return <button key={stage.stage_id} type="button" aria-pressed={active} aria-label={`${SHORT_TITLES[stage.stage_id]} — ${stateLabel(stage.presentation_state)}`} onClick={() => setSelectedId(stage.stage_id)} className="min-h-[58px] min-w-0 rounded-[11px] border px-2 py-2 text-left transition-all hover:-translate-y-0.5 sm:min-h-[62px] sm:px-3" style={{ background: active ? `${P.accent}0F` : P.bgCard, borderColor: active ? `${P.accent}70` : P.border, boxShadow: active ? `0 0 0 1px ${P.accent}14` : 'none' }}><div className="flex items-center justify-between gap-1"><span className="truncate text-[9px] font-black sm:text-[10px]" style={{ color: P.text }}>{SHORT_TITLES[stage.stage_id]}</span><StageStatusIcon stage={stage} color={color} /></div><div className="mt-1 truncate text-[8px] font-bold" style={{ color }}>{stateLabel(stage.presentation_state)}</div></button>; })}
        </div>

        {selected && <div className="mt-2.5 overflow-hidden rounded-[16px] border" style={{ borderColor: P.border, background: P.bgCard }}>
          <div className="border-b px-3 py-2.5 sm:px-4" style={{ borderColor: P.border }}><div className="flex min-w-0 flex-wrap items-center gap-2"><span className="text-[11px] font-black" style={{ color: P.text }}>{SHORT_TITLES[selected.stage_id]}</span><span className="rounded-full px-2 py-0.5 text-[8px] font-black" style={{ background: `${statusColor(selected.presentation_state)}12`, color: statusColor(selected.presentation_state) }}>{stateLabel(selected.presentation_state)}</span></div></div>
          <div className="grid gap-2.5 p-2.5 sm:p-3 lg:grid-cols-[minmax(0,1fr)_minmax(250px,0.82fr)]">
            <div className="rounded-xl border px-3 py-2.5" style={{ borderColor: P.border, background: P.bgInput }}><div className="mb-1.5 flex items-center gap-2"><AlertTriangle size={12} style={{ color: P.accentWarning }} /><span className="text-[8px] font-black uppercase tracking-wider" style={{ color: P.text }}>Points à résoudre</span></div>{selected.blocking_gates.length ? <ul className="space-y-1">{selected.blocking_gates.map((gate, index) => <li key={`${gate}-${index}`} className="text-[9px] leading-3.5" style={{ color: P.textMuted }}><span className="font-bold" style={{ color: P.text }}>{LABELS[gate] ?? 'Vérification clinique requise'}</span></li>)}</ul> : <p className="text-[9px]" style={{ color: P.accentSuccess }}>Aucun point bloquant.</p>}</div>
            <aside className="rounded-xl border px-3 py-2.5" style={{ borderColor: `${P.accentWarning}40`, background: `${P.accentWarning}07` }}><div className="flex items-center gap-2"><LockKeyhole size={12} style={{ color: P.accentWarning }} /><span className="text-[8px] font-black uppercase tracking-wider" style={{ color: P.text }}>Action praticien</span></div><p className="mt-1.5 text-[10px] font-black" style={{ color: P.text }}>{selected.clinician_action.available ? selected.clinician_action.label : 'Aucune validation disponible'}</p>{!selected.clinician_action.available && <p className="mt-1 text-[9px] leading-4" style={{ color: P.textMuted }}>Cette action sera disponible lorsque les informations nécessaires auront été confirmées.</p>}<div className="mt-2 border-t pt-2 text-[8px] font-bold leading-3.5" style={{ borderColor: P.border, color: P.textDim }}>La validation clinique nécessite une confirmation explicite du praticien.</div></aside>
          </div>
          <div className="grid gap-1.5 border-t px-2.5 py-2.5 sm:grid-cols-3 sm:px-3" data-testid="r15-scientific-exceptions" style={{ borderColor: P.border }}><EvidenceRefs title="Données manquantes" items={selected.missing_data_refs} authoritative={Boolean(selected.authoritative_status)} P={P} /><EvidenceRefs title="Contradictions" items={selected.contradictions} authoritative={Boolean(selected.authoritative_status)} P={P} /><EvidenceRefs title="Contre-indications" items={selected.contraindications} authoritative={Boolean(selected.authoritative_status)} P={P} /></div>
        </div>}
        <div className="mt-2 text-[8px] leading-3.5" style={{ color: P.textDim }}>Analyse liée au dossier patient · validation clinique contrôlée par le praticien.</div>
      </div>}
    </section>
  );
};

export default ClinicalScientificStudio;
