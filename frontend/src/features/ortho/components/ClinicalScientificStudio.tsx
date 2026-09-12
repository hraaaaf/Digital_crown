import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
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
  r11_authoritative_snapshot_not_persisted: 'Snapshot R11 autoritaire non persisté',
  r11_not_authoritative: 'R11 non autoritaire',
  r12_authoritative_snapshot_not_persisted: 'Snapshot R12 autoritaire non persisté',
  r12_not_authoritative: 'R12 non autoritaire',
  therapeutic_rule_registry_empty: 'Aucune règle thérapeutique source-lockée active',
  r13_authoritative_snapshot_not_persisted: 'Snapshot R13 autoritaire non persisté',
  r13_no_clinician_selected_option: 'Aucune option R13 sélectionnée par le praticien',
  r14_authoritative_snapshot_not_persisted: 'Snapshot R14 autoritaire non persisté',
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
  <div className="rounded-xl border p-3" style={{ borderColor: P.border, background: P.bgInput }}>
    <div className="mb-2 text-[10px] font-black uppercase tracking-wider" style={{ color: P.text }}>{title}</div>
    {items.length ? (
      <ul className="space-y-1.5">
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
        const { data } = await api.get<StudioSnapshot>(`/patients/${patientId}/cephalo-clinical-studio`);
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
      className="mb-6 overflow-hidden rounded-2xl border"
      style={{ background: P.bgPanel, borderColor: P.border, boxShadow: P.shadow }}
    >
      <div className="border-b p-4 sm:p-5" style={{ borderColor: P.border }}>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex min-w-0 gap-3">
            <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl" style={{ background: `${P.accent}18`, color: P.accent }}>
              <ShieldCheck size={20} />
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-sm font-black uppercase tracking-[0.12em]" style={{ color: P.text }}>Chaîne clinique scientifique</h3>
                <span className="rounded-full px-2 py-1 text-[9px] font-black tracking-widest" style={{ background: `${P.accent}18`, color: P.accent }}>
                  R11 → R14
                </span>
              </div>
              <p className="mt-1 max-w-2xl text-xs leading-5" style={{ color: P.textMuted }}>
                Lecture des états autoritaires, de leur provenance et des blocages. Une mesure calculable n'est ni un diagnostic, ni une indication, ni un traitement.
              </p>
            </div>
          </div>
          {snapshot && (
            <div className="flex shrink-0 items-center gap-2 rounded-xl border px-3 py-2" style={{ borderColor: P.border, background: P.bgCard }}>
              <LockKeyhole size={14} style={{ color: snapshot.blocking_gate_count ? P.accentWarning : P.accentSuccess }} />
              <span className="text-[10px] font-black uppercase tracking-wider" style={{ color: P.textMuted }}>
                {snapshot.blocking_gate_count} blocage{snapshot.blocking_gate_count === 1 ? '' : 's'} actif{snapshot.blocking_gate_count === 1 ? '' : 's'}
              </span>
            </div>
          )}
        </div>
      </div>

      {loading && (
        <div className="flex items-center gap-3 p-5 text-xs font-bold" style={{ color: P.textMuted }}>
          <RefreshCw size={16} className="animate-spin" /> Vérification de l'autorité scientifique…
        </div>
      )}

      {!loading && error && (
        <div className="m-4 flex gap-3 rounded-xl border p-4" style={{ borderColor: `${P.accentError}55`, background: `${P.accentError}10` }}>
          <AlertTriangle className="mt-0.5 shrink-0" size={18} style={{ color: P.accentError }} />
          <div>
            <p className="text-xs font-black" style={{ color: P.text }}>Fail-closed</p>
            <p className="mt-1 text-xs leading-5" style={{ color: P.textMuted }}>{error}</p>
          </div>
        </div>
      )}

      {!loading && snapshot && (
        <div className="p-4 sm:p-5">
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {snapshot.stages.map(stage => {
              const active = selected?.stage_id === stage.stage_id;
              const color = statusColor(stage.presentation_state);
              return (
                <button
                  key={stage.stage_id}
                  type="button"
                  onClick={() => setSelectedId(stage.stage_id)}
                  className="min-w-0 rounded-xl border p-3 text-left transition-all hover:-translate-y-0.5"
                  style={{
                    background: active ? `${P.accent}12` : P.bgCard,
                    borderColor: active ? `${P.accent}80` : P.border,
                    boxShadow: active ? `0 0 0 1px ${P.accent}20` : 'none',
                  }}
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-[10px] font-black tracking-[0.16em]" style={{ color: P.accent }}>{stage.stage_id}</span>
                    {stage.presentation_state === 'VALIDATED'
                      ? <CheckCircle2 size={15} style={{ color }} />
                      : stage.presentation_state === 'AWAITING_CLINICIAN'
                        ? <Clock3 size={15} style={{ color }} />
                        : <LockKeyhole size={15} style={{ color }} />}
                  </div>
                  <p className="mt-2 text-xs font-black leading-4" style={{ color: P.text }}>{stage.title}</p>
                  <p className="mt-2 text-[10px] font-bold leading-4" style={{ color }}>{stateLabel(stage.presentation_state)}</p>
                </button>
              );
            })}
          </div>

          {selected && (
            <div className="mt-4 rounded-2xl border p-4" style={{ borderColor: P.border, background: P.bgCard }}>
              <div className="grid gap-4 lg:grid-cols-[1.25fr_0.75fr]">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[10px] font-black tracking-[0.18em]" style={{ color: P.accent }}>{selected.stage_id}</span>
                    <ChevronRight size={13} style={{ color: P.textDim }} />
                    <span className="text-xs font-black" style={{ color: P.text }}>{selected.title}</span>
                  </div>
                  <p className="mt-2 text-xs leading-5" style={{ color: P.textMuted }}>{selected.summary}</p>

                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    <div className="rounded-xl border p-3" style={{ borderColor: P.border, background: P.bgInput }}>
                      <div className="mb-2 flex items-center gap-2">
                        <AlertTriangle size={14} style={{ color: P.accentWarning }} />
                        <span className="text-[10px] font-black uppercase tracking-wider" style={{ color: P.text }}>Blocages visibles</span>
                      </div>
                      {selected.blocking_gates.length ? (
                        <ul className="space-y-2">
                          {selected.blocking_gates.map(gate => (
                            <li key={gate} className="text-[11px] leading-4" style={{ color: P.textMuted }}>
                              <span className="font-bold" style={{ color: P.text }}>{LABELS[gate] ?? gate}</span>
                              <span className="mt-0.5 block font-mono text-[9px]" style={{ color: P.textDim }}>{gate}</span>
                            </li>
                          ))}
                        </ul>
                      ) : <p className="text-[11px]" style={{ color: P.accentSuccess }}>Aucun gate bloquant.</p>}
                    </div>

                    <div className="rounded-xl border p-3" style={{ borderColor: P.border, background: P.bgInput }}>
                      <div className="mb-2 flex items-center gap-2">
                        <Database size={14} style={{ color: P.accent }} />
                        <span className="text-[10px] font-black uppercase tracking-wider" style={{ color: P.text }}>Provenance</span>
                      </div>
                      <dl className="space-y-2">
                        {selected.provenance.map(item => (
                          <div key={`${item.label}-${item.value}`} className="flex items-start justify-between gap-3 text-[10px]">
                            <dt style={{ color: P.textMuted }}>{item.label}</dt>
                            <dd className="max-w-[55%] break-words text-right font-bold" style={{ color: P.text }}>{item.value}</dd>
                          </div>
                        ))}
                      </dl>
                    </div>
                  </div>
                </div>

                <aside className="rounded-xl border p-3" style={{ borderColor: `${P.accentWarning}45`, background: `${P.accentWarning}09` }}>
                  <div className="flex items-center gap-2">
                    <LockKeyhole size={15} style={{ color: P.accentWarning }} />
                    <span className="text-[10px] font-black uppercase tracking-wider" style={{ color: P.text }}>Action praticien</span>
                  </div>
                  <p className="mt-2 text-xs font-black" style={{ color: P.text }}>
                    {selected.clinician_action.available ? selected.clinician_action.label : 'Aucune validation disponible'}
                  </p>
                  <p className="mt-2 text-[11px] leading-5" style={{ color: P.textMuted }}>{selected.clinician_action.reason}</p>
                  <div className="mt-3 rounded-lg border px-3 py-2 text-[9px] font-bold leading-4" style={{ borderColor: P.border, color: P.textDim }}>
                    Toute validation visible doit créer une preuve backend résolue avec cible, clinicien et horodatage. Aucun état local ne vaut validation clinique.
                  </div>
                </aside>
              </div>

              <div className="mt-3 grid gap-3 sm:grid-cols-3" data-testid="r15-scientific-exceptions">
                <EvidenceRefs title="Données manquantes" items={selected.missing_data_refs} authoritative={Boolean(selected.authoritative_status)} P={P} />
                <EvidenceRefs title="Contradictions" items={selected.contradictions} authoritative={Boolean(selected.authoritative_status)} P={P} />
                <EvidenceRefs title="Contre-indications" items={selected.contraindications} authoritative={Boolean(selected.authoritative_status)} P={P} />
              </div>
            </div>
          )}

          <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-[9px]" style={{ color: P.textDim }}>
            <span>Contrat {snapshot.contract_version}</span>
            <span>Analyse {snapshot.analysis_id ?? 'absente'} · graphe typé {snapshot.evidence_graph_present ? 'présent' : 'absent'} · chaîne active {snapshot.active_runtime_chain_verified ? 'vérifiée' : 'non vérifiée'}</span>
          </div>
        </div>
      )}
    </section>
  );
};

export default ClinicalScientificStudio;
