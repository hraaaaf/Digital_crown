import React from 'react';
import { ShieldAlert } from 'lucide-react';
import { cephaloRepository } from '../cephaloRepository';
import { publishCephaloMetricFocus } from '../cephaloAnalysisBridge';
import { useOrthoStore } from '../stores/useOrthoStore';
import {
  isR23G4ReferenceBound,
  readCephaloR23G2Protocol,
  resolveR23G3RuntimeFocus,
  type R23G2Analysis,
  type R23G2RickettsVersion,
} from '../cephaloR23G4ReferenceProfiles';

/** R23-G4 read-only clinical-reference UI. Not a clinically approved protocol.
 * Never use legacy `anglesData.metrics`, norms, inferred landmarks or SVG lines.
 */
interface Palette {
  bgPanel: string;
  bgCard: string;
  border: string;
  text: string;
  textMuted: string;
  accent: string;
  accentSuccess: string;
  accentWarning: string;
  shadowLg: string;
}

type BoundReference = {
  patientId: number | null;
  analysisId: number | undefined;
  revision: number;
  imageSrc: string | undefined;
  anglesData: unknown;
  localVersion: number;
  data: unknown;
};

const NAME: Record<R23G2Analysis, string> = {
  com: 'COM historique — 10 facteurs',
  mcnamara: 'McNamara — 13 facteurs',
  ricketts: 'Ricketts',
};
const explanation = (state: string) =>
  state.includes('PENDING_EQUIVALENCE') ? 'Équivalence non démontrée'
  : state.includes('BLOCKED') ? 'Source anatomique bloquée'
  : state.includes('LEGACY_TO_AUDIT') ? 'Mesure historique à auditer'
  : state.includes('IMPLEMENTATION_MISSING') ? 'Méthode en cours de construction'
  : state.includes('CONDITIONAL') ? 'Preuves complémentaires nécessaires'
  : 'Preuve active insuffisante';

const CephaloR23G4ReferencePanel: React.FC<{ P: Palette; analysis: R23G2Analysis }> = ({ P, analysis }) => {
  const patientId = useOrthoStore(s => s.patientId);
  const analysisId = useOrthoStore(s => s.analysisId);
  const imageSrc = useOrthoStore(s => s.imageSrc);
  const anglesData = useOrthoStore(s => s.anglesData);
  const localVersion = useOrthoStore(s => s.local?.version ?? 0);
  const syncState = useOrthoStore(s => s.syncState ?? 'idle');
  const revision = anglesData?.scientific_read_path?.revision;
  const [version, setVersion] = React.useState<R23G2RickettsVersion>('atlas');
  const [loaded, setLoaded] = React.useState<BoundReference | null>(null);
  const [requestState, setRequestState] = React.useState<'loading' | 'error' | 'idle'>('idle');
  const [selection, setSelection] = React.useState<{ id: string; bound: BoundReference; analysis: R23G2Analysis; version: R23G2RickettsVersion } | null>(null);

  React.useEffect(() => {
    setLoaded(null);
    setSelection(null);
    if (!imageSrc || !Number.isSafeInteger(patientId) || !Number.isSafeInteger(analysisId)
        || !Number.isSafeInteger(revision) || revision <= 0) {
      setRequestState('idle');
      return;
    }
    let active = true;
    const abort = new AbortController();
    setRequestState('loading');
    cephaloRepository.getR23G4ReferenceProfiles(analysisId!, revision, abort.signal)
      .then(data => {
        if (!active) return;
        setLoaded({ data, patientId, analysisId, revision, imageSrc, anglesData, localVersion });
        setRequestState('idle');
      })
      .catch(() => {
        if (!active) return;
        setLoaded(null);
        setRequestState('error');
      });
    return () => { active = false; abort.abort(); };
  }, [patientId, analysisId, imageSrc, revision, anglesData]);

  // A local landmark edit invalidates the old pixel-to-evidence Focus immediately.
  // Deliberately do NOT refetch merely because localVersion changed: only a new
  // authoritative anglesData snapshot after PUT may regain source authority.
  const bound = loaded
    && syncState !== 'syncing' && syncState !== 'error'
    && loaded.localVersion === localVersion
    && loaded.patientId === patientId && loaded.analysisId === analysisId
    && loaded.revision === revision && loaded.imageSrc === imageSrc
    && loaded.anglesData === anglesData
    && isR23G4ReferenceBound(loaded.data, patientId, analysisId, revision)
    ? loaded : null;

  const profile = bound ? readCephaloR23G2Protocol(bound.data, analysis, version) : null;
  const rows = profile?.rows ?? [];
  const selectedId = selection && bound && selection.bound === bound
    && selection.analysis === analysis && selection.version === version
    ? selection.id : null;
  const selectedRow = rows.find(row => row.canonical_measurement_id === selectedId);
  const focus = resolveR23G3RuntimeFocus(selectedRow);

  // Unconditionally clear a prior study's Focus on change or unmount.
  React.useEffect(() => {
    publishCephaloMetricFocus(focus);
    return () => publishCephaloMetricFocus(null);
  }, [focus, patientId, analysisId, imageSrc, revision, bound, analysis, version]);

  const count = rows.filter(row => row.availability_status === 'AVAILABLE' && row.value !== null).length;
  return (
    <aside data-r23g4-reference-panel={analysis} data-r23g4-com-compact={analysis === 'com' ? 'true' : undefined}
      className="flex h-full min-h-0 min-w-0 flex-col overflow-hidden rounded-3xl border"
      style={{ background: P.bgPanel, borderColor: P.border, boxShadow: P.shadowLg }}>
      <header className="shrink-0 border-b p-3 sm:p-4" style={{ borderColor: P.border }}>
        <h3 className="text-sm font-extrabold" style={{ color: P.text }}>Analyse {NAME[analysis]}</h3>
        <p className="mt-1 text-xs leading-snug" style={{ color: P.textMuted }}>
          Référence source en lecture seule, non certifiée cliniquement. Aucune norme ni classification déduite.
        </p>
        {analysis === 'ricketts' && (
          <div className="mt-2 flex flex-wrap gap-2" aria-label="Version Ricketts" role="group">
            {([['atlas', 'Atlas 2009 · 33'], ['gregoret', 'Gregoret · 13']] as const).map(([id, label]) => (
              <button key={id} type="button" aria-pressed={version === id} data-r23g4-version={id}
                className="min-h-10 rounded-lg border px-2 py-1.5 text-xs"
                onClick={() => { setSelection(null); setVersion(id); }}
                style={{ borderColor: version === id ? P.accent : P.border, color: P.text }}>
                {label}
              </button>
            ))}
          </div>
        )}
        <p className="mt-2 text-xs font-bold" data-r23g4-coverage style={{ color: P.textMuted }}>
          {profile ? `${count}/${rows.length} valeurs prouvées · ${rows.length} facteurs documentés` : 'Lecture protégée · aucune valeur de remplacement'}
        </p>
      </header>
      {!profile ? (
        <div role="status" data-r23g4-refusal className="flex gap-2 p-4 text-xs leading-relaxed"
          style={{ color: P.accentWarning }}>
          <ShieldAlert size={18} className="shrink-0" aria-hidden="true" />
          {requestState === 'loading' ? 'Vérification des références de cette étude…'
            : requestState === 'error' ? 'Lecture source en cours de construction : chaîne indisponible ou révision modifiée. Aucune valeur affichée.'
            : 'Chaîne ou identité du protocole non vérifiée pour cette étude. Aucun chiffre clinique de remplacement.'}
        </div>
      ) : (
        <div className="min-h-0 flex-1 overflow-auto overscroll-contain">
          <table className="w-full table-fixed text-left text-xs" aria-label={`Mesures ${profile.protocol_profile_id}`}
            data-r23g4-row-count={rows.length}>
            <thead className="sticky top-0 z-10" style={{ background: P.bgPanel, color: P.textMuted }}>
              <tr className="border-b" style={{ borderColor: P.border }}>
                <th scope="col" className="w-[48%] px-2 py-2">Facteur source</th>
                <th scope="col" className="w-[22%] px-1 py-2">Valeur</th>
                <th scope="col" className="w-[30%] px-1 py-2">Statut</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(row => (
                <tr key={row.canonical_measurement_id} data-r23g4-factor={row.canonical_measurement_id}
                  className="border-b align-top" style={{ borderColor: P.border }}>
                  <th scope="row" className="min-w-0 break-words px-2 py-1.5 font-semibold" style={{ color: P.text }}>
                    <button type="button" className="min-h-9 w-full rounded-md text-left focus-visible:outline-2"
                      data-r23g4-focus-select={row.canonical_measurement_id}
                      aria-pressed={selectedId === row.canonical_measurement_id}
                      onClick={() => {
                        if (!bound) return;
                        setSelection(selectedId === row.canonical_measurement_id ? null
                          : { id: row.canonical_measurement_id, bound, analysis, version });
                      }}>
                      {row.label || row.canonical_measurement_id}
                    </button>
                    {selectedId === row.canonical_measurement_id && (
                      <span className="block break-all font-mono text-[9px] font-normal" style={{ color: P.textMuted }}>
                        {row.canonical_measurement_id}
                      </span>
                    )}
                  </th>
                  <td className="px-1 py-2 font-mono text-[11px] font-bold tabular-nums"
                    style={{ color: row.value === null ? P.textMuted : P.accentSuccess }}>
                    {row.value === null ? 'NC' : `${row.value.toFixed(1).replace('.', ',')} ${row.unit === 'deg' ? '°' : (row.unit || '')}`}
                  </td>
                  <td className="break-words px-1 py-2 text-[10px] leading-snug" style={{ color: P.textMuted }}>
                    {row.value === null ? 'Non calculable' : 'Preuve mesurée'}
                    {selectedId === row.canonical_measurement_id && (
                      <div className="mt-1" data-r23g4-focus-authority={focus ? 'verified-runtime' : 'refused'}>
                        {focus ? `Focus prouvé : ${focus.points.join(', ')}. Aucun tracé inventé.`
                          : `Focus non autorisé. ${explanation(row.contract_state)}.`}
                        <div className="mt-1 break-words">Contrat : {row.contract_state}</div>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </aside>
  );
};

export default CephaloR23G4ReferencePanel;
