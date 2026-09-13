import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Database,
  LockKeyhole,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react';
import { api } from '../../../services/api';

interface ProvenanceRef {
  label: string;
  value: string;
}

interface ClinicianAction {
  available: boolean;
  audit_required: boolean;
  label: string;
  reason: string;
}

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

interface Props {
  patientId: number;
  analysisId?: number;
  P: any;
}

const LABELS: Record<string, string> = {
  cephalo_analysis_missing: 'Analyse céphalométrique absente',
  typed_evidence_graph_missing: 'Graphe de preuve typé absent',
  active_runtime_chain_unverified: 'Chaîne de preuve active non vérifiée',
  active_runtime_chain_incoherent: 'Chaîne de preuve active incohérente',
  diagnostic_rule_registry_empty: 'Aucune règle diagnostique source-lockée active',
  r11_authoritative_snapshot_not_persisted: 'Diagnostic scientifique autoritaire non persisté',
  r11_not_authoritative: 'Diagnostic scientifique non autoritaire',
  r12_authoritative_snapshot_not_persisted: 'Problèmes et objectifs autoritaires non persistés',
  r12_not_authoritative: 'Problèmes et objectifs non autoritaires',
  therapeutic_rule_registry_empty: 'Aucune règle thérapeutique source-lockée active',
  r13_authoritative_snapshot_not_persisted: 'Options thérapeutiques autoritaires non persistées',
  r13_no_clinician_selected_option: 'Aucune option thérapeutique sélectionnée par le praticien',
  r14_authoritative_snapshot_not_persisted: 'Décision clinique finale autoritaire non persistée',
  clinician_selection_required: 'Sélection explicite du praticien requise',
};

const stateLabel = (state: ClinicalStage['presentation_state']) => {
  if (state === 'BLOCKED') return 'Bloqué';
  if (state === 'AWAITING_CLINICIAN') return 'Action praticien requise';
  if (state === 'EVALUABLE') return 'Évaluable · non sélectionné';
  if (state === 'VALIDATED') return 'Validé avec preuve';
  return 'Rejeté avec preuve';
};

const EvidenceRefs: React.FC<{
  title: string;
  items: string[];
  authoritative: boolean;
  P: any;
}> = ({ title, items, authoritative, P }) => (
  <div className="min-w-0 rounded-xl border px-3 py-2.5" style={{ borderColor: P.border, background: P.bgInput }}>
    <div className="mb-1.5 text-[9px] font-black uppercase tracking-[0.1em]" style={{ color: P.text }}>{title}</div>
    {items.length ? (
      <ul className="space-y-1">
        {items.map(item => (
          <li key={item} className="break-words font-mono text-[9px] leading-4" style={{ color: P.textMuted }}>{item}</li>
        ))}
      </ul>
    ) : (
      <p className="text-[10px] leading-4" style={{ color: P.textDim }}>
        {authoritative ? 'Aucun élément déclaré dans le snapshot autoritaire.' : 'Non résolu : aucun snapshot autoritaire persistant.'}
      </p>
    )}
  </div>
);

const StageStatusIcon: React.FC<{ stage: ClinicalStage; color: string }> = ({ stage, color }) => {
  if (stage.presentation_state === 'VALIDATED') return <CheckCircle2 size={14} style={{ color }} />;
  if (stage.presentation_state === 'AWAITING_CLINICIAN') return <Clock3 size={14} style={{ color }} />;
  return <LockKeyhole size={14} style={{ color }} />;
};

export const ClinicalScientificStudio: React.FC<Props> = ({ patientId, analysisId, P }) => {
  const [snapshot, setSnapshot] = useState<StudioSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<ClinicalStage['stage_id']>('R11');

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const analysisQuery = analysisId != null ? `?analysis_id=${encodeURIComponent(String(analysisId))}` : '';
        const { data } = await api.get<StudioSnapshot>(`/patients/${patientId}/cephalo-clinical-studio${analysisQuery}`);
        if (!cancelled) setSnapshot(data);
      } catch (err) {
        console.error('R15 clinical studio snapshot unavailable:', err);
        if (!cancelled) setError("La chaîne clinique scientifique n'est pas disponible. Aucune validation n'est autorisée.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => { cancelled = true; };
  }, [patientId, analysisId]);

  const selected = useMemo(
    () => snapshot?.stages.find(stage => stage.stage_id === selectedId) ?? snapshot?.stages[0] ?? null,
    [snapshot, selectedId],
  );

  const statusColor = (state: ClinicalStage['presentation_state']) => {
    if (state === 'VALIDATED') return P.accentSuccess;
    if (state === 'REJECTED') return P.accentError;
    if (state === 'AWAITING_CLINICIAN' || state === 'EVALUABLE') return P.accentWarning;
    return P.accentError;
  };

  return (
    <section
      data-testid="r15-clinical-studio"
      className="mb-5 overflow-hidden rounded-2xl border"
      style={{ background: P.bgPanel, borderColor: P.border, boxShadow: P.shadow }}
    >
      <div className="border-b px-3.5 py-3.5 sm:px-4 lg:px-5" style={{ borderColor: P.border }}>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex min-w-0 items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl" style={{ background: `${P.accent}14`, color: P.accent }}>
              <ShieldCheck size={18} />
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                <h3 className="text-[12px] font-black uppercase tracking-[0.11em]" style={{ color: P.text }}>Chaîne clinique scientifique</h3>
                <span className="rounded-full px-2 py-0.5 text-[9px] font-black tracking-wide" style={{ background: `${P.accent}12`, color: P.accent }}>
                  Diagnostic → décision clinique
                </span>
              </div>
              <p className="mt-1 max-w-3xl text-[11px] leading-[18px]" style={{ color: P.textMuted }}>
                États autoritaires, provenance et blocages. Une mesure calculable n'est ni un diagnostic, ni une indication, ni un traitement.
              </p>
            </div>
          </div>
          {snapshot && (
            <div className="flex min-h-9 shrink-0 items-center gap-2 self-start rounded-xl border px-3 py-2 sm:self-auto" style={{ borderColor: P.border, background: P.bgCard }}>
              <LockKeyhole size={13} style={{ color: snapshot.blocking_gate_count ? P.accentWarning : P.accentSuccess }} />
              <span className="text-[9px] font-black uppercase tracking-wider" style={{ color: P.textMuted }}>
                {snapshot.blocking_gate_count} blocage{snapshot.blocking_gate_count === 1 ? '' : 's'} actif{snapshot.blocking_gate_count === 1 ? '' : 's'}
              </span>
            </div>
          )}
        </div>
      </div>

      {loading && (
        <div className="flex items-center gap-3 px-4 py-4 text-xs font-bold" style={{ color: P.textMuted }}>
          <RefreshCw size={15} className="animate-spin" /> Vérification de l'autorité scientifique…
        </div>
      )}

      {!loading && error && (
        <div className="m-3 flex gap-3 rounded-xl border p-3.5 sm:m-4" style={{ borderColor: `${P.accentError}55`, background: `${P.accentError}10` }}>
          <AlertTriangle className="mt-0.5 shrink-0" size={17} style={{ color: P.accentError }} />
          <div>
            <p className="text-xs font-black" style={{ color: P.text }}>Fail-closed</p>
            <p className="mt-1 text-xs leading-5" style={{ color: P.textMuted }}>{error}</p>
          </div>
        </div>
      )}

      {!loading && snapshot && (
        <div className="p-3 sm:p-4 lg:p-5">
          <div
            data-testid="r15-stage-rail"
            className="-mx-1 flex snap-x gap-2 overflow-x-auto px-1 pb-1 lg:mx-0 lg:grid lg:grid-cols-4 lg:overflow-visible lg:px-0"
            aria-label="Étapes de la chaîne clinique scientifique"
          >
            {snapshot.stages.map(stage => {
              const active = selected?.stage_id === stage.stage_id;
              const color = statusColor(stage.presentation_state);
              return (
                <button
                  key={stage.stage_id}
                  type="button"
                  aria-pressed={active}
                  onClick={() => setSelectedId(stage.stage_id)}
                  className="min-h-[64px] min-w-[168px] snap-start rounded-xl border px-3 py-2.5 text-left transition-all hover:-translate-y-0.5 sm:min-w-[210px] lg:min-w-0"
                  style={{
                    background: active ? `${P.accent}10` : P.bgCard,
                    borderColor: active ? `${P.accent}70` : P.border,
                    boxShadow: active ? `0 0 0 1px ${P.accent}18` : 'none',
                  }}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="mb-1 flex items-center gap-1.5">
                        <span className="rounded-md px-1.5 py-0.5 text-[8px] font-black tracking-[0.1em]" style={{ background: `${P.accent}10`, color: P.textDim }}>
                          {stage.stage_id}
                        </span>
                        <span className="text-[9px] font-bold leading-4" style={{ color }}>{stateLabel(stage.presentation_state)}</span>
                      </div>
                      <p className="line-clamp-2 text-[11px] font-black leading-4" style={{ color: P.text }}>{stage.title}</p>
                    </div>
                    <StageStatusIcon stage={stage} color={color} />
                  </div>
                </button>
              );
            })}
          </div>

          {selected && (
            <div className="mt-3 overflow-hidden rounded-2xl border" style={{ borderColor: P.border, background: P.bgCard }}>
              <div className="border-b px-3.5 py-3 sm:px-4" style={{ borderColor: P.border }}>
                <div className="flex min-w-0 flex-wrap items-center gap-2">
                  <span className="text-xs font-black" style={{ color: P.text }}>{selected.title}</span>
                  <span className="rounded-full border px-2 py-0.5 text-[8px] font-bold uppercase tracking-[0.12em]" style={{ borderColor: P.border, color: P.textDim }}>
                    Réf. technique {selected.stage_id}
                  </span>
                </div>
                <p className="mt-1.5 max-w-4xl text-[11px] leading-[18px]" style={{ color: P.textMuted }}>{selected.summary}</p>
              </div>

              <div className="grid gap-3 p-3 sm:p-4 xl:grid-cols-[minmax(0,1.45fr)_minmax(250px,0.55fr)]">
                <div className="min-w-0">
                  <div className="grid gap-2.5 md:grid-cols-2">
                    <div className="rounded-xl border px-3 py-2.5" style={{ borderColor: P.border, background: P.bgInput }}>
                      <div className="mb-2 flex items-center gap-2">
                        <AlertTriangle size={13} style={{ color: P.accentWarning }} />
                        <span className="text-[9px] font-black uppercase tracking-wider" style={{ color: P.text }}>Blocages visibles</span>
                      </div>
                      {selected.blocking_gates.length ? (
                        <ul className="space-y-1.5">
                          {selected.blocking_gates.map(gate => (
                            <li key={gate} className="text-[10px] leading-4" style={{ color: P.textMuted }}>
                              <span className="font-bold" style={{ color: P.text }}>{LABELS[gate] ?? gate}</span>
                              <span className="mt-0.5 block break-words font-mono text-[8px]" style={{ color: P.textDim }}>{gate}</span>
                            </li>
                          ))}
                        </ul>
                      ) : <p className="text-[10px]" style={{ color: P.accentSuccess }}>Aucun gate bloquant.</p>}
                    </div>

                    <div className="rounded-xl border px-3 py-2.5" style={{ borderColor: P.border, background: P.bgInput }}>
                      <div className="mb-2 flex items-center gap-2">
                        <Database size={13} style={{ color: P.accent }} />
                        <span className="text-[9px] font-black uppercase tracking-wider" style={{ color: P.text }}>Provenance</span>
                      </div>
                      <dl className="space-y-1.5">
                        {selected.provenance.map(item => (
                          <div key={`${item.label}-${item.value}`} className="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-2 text-[9px] leading-4">
                            <dt className="break-words" style={{ color: P.textMuted }}>{item.label}</dt>
                            <dd className="break-words text-right font-bold" style={{ color: P.text }}>{item.value}</dd>
                          </div>
                        ))}
                      </dl>
                    </div>
                  </div>

                  <div className="mt-2.5 grid gap-2 sm:grid-cols-3" data-testid="r15-scientific-exceptions">
                    <EvidenceRefs title="Données manquantes" items={selected.missing_data_refs} authoritative={Boolean(selected.authoritative_status)} P={P} />
                    <EvidenceRefs title="Contradictions" items={selected.contradictions} authoritative={Boolean(selected.authoritative_status)} P={P} />
                    <EvidenceRefs title="Contre-indications" items={selected.contraindications} authoritative={Boolean(selected.authoritative_status)} P={P} />
                  </div>
                </div>

                <aside className="rounded-xl border px-3 py-3" style={{ borderColor: `${P.accentWarning}45`, background: `${P.accentWarning}08` }}>
                  <div className="flex items-center gap-2">
                    <LockKeyhole size={14} style={{ color: P.accentWarning }} />
                    <span className="text-[9px] font-black uppercase tracking-wider" style={{ color: P.text }}>Action praticien</span>
                  </div>
                  <p className="mt-2 text-[11px] font-black" style={{ color: P.text }}>
                    {selected.clinician_action.available ? selected.clinician_action.label : 'Aucune validation disponible'}
                  </p>
                  <p className="mt-1.5 text-[10px] leading-[18px]" style={{ color: P.textMuted }}>{selected.clinician_action.reason}</p>
                  <div className="mt-2.5 rounded-lg border px-2.5 py-2 text-[9px] font-bold leading-4" style={{ borderColor: P.border, color: P.textDim }}>
                    Toute validation visible doit créer une preuve backend résolue avec cible, clinicien et horodatage. Aucun état local ne vaut validation clinique.
                  </div>
                </aside>
              </div>
            </div>
          )}

          <div className="mt-2.5 flex flex-wrap items-center justify-between gap-x-3 gap-y-1 text-[8px] leading-4" style={{ color: P.textDim }}>
            <span>Contrat {snapshot.contract_version} · traçabilité interne R11 → R14</span>
            <span>Analyse {snapshot.analysis_id ?? 'absente'} · graphe typé {snapshot.evidence_graph_present ? 'présent' : 'absent'} · chaîne active {snapshot.active_runtime_chain_verified ? 'vérifiée' : 'non vérifiée'}</span>
          </div>
        </div>
      )}
    </section>
  );
};

export default ClinicalScientificStudio;
