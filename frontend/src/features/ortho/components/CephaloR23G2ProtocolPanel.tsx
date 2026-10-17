import React from 'react';
import { ShieldAlert } from 'lucide-react';
import { useOrthoStore } from '../stores/useOrthoStore';
import { findR23G3PinnedRequirements } from '../cephaloR23G3PinnedRequirements';
import { findR23G7AtlasSourceRequirements } from '../cephaloR23G7AtlasSourceRequirements';
import { findR23G8W1OrientationRequirements } from '../cephaloR23G8W1OrientationRequirements';
import { findR23G8W2DentalRequirements } from '../cephaloR23G8W2DentalRequirements';
import { publishCephaloMetricFocus } from '../cephaloAnalysisBridge';
import {
  readCephaloR23G2Protocol,
  resolveR23G3RuntimeFocus,
  type R23G2Analysis,
  type R23G2ProtocolRow,
  type R23G2RickettsVersion,
} from '../cephaloR23G2ClinicalProfiles';

interface R23G2Palette {
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

const AVAILABILITY_LABELS: Record<string, string> = {
  AVAILABLE: 'Calculée',
  MISSING: 'Source manquante',
  INVALID: 'Preuve invalide',
  NOT_APPLICABLE: 'Non applicable',
  NOT_COMPUTABLE: 'Non calculable',
};

const ANALYSIS_NAMES = {
  mcnamara: 'McNamara 1984',
  com: 'COM historique DC',
  ricketts: 'Ricketts',
} as const;

const statusExplanation = (row: R23G2ProtocolRow) => {
  if (row.contract_state.includes('PENDING_EQUIVALENCE')) return 'Équivalence non démontrée : aucune valeur promue.';
  if (row.contract_state.includes('BLOCKED')) return 'Contrat bloqué : aucune valeur déduite.';
  if (row.contract_state.includes('IMPLEMENTATION_MISSING')) return 'Méthode manquante dans ce profil.';
  if (row.contract_state.includes('LEGACY_TO_AUDIT')) return 'Mesure historique non rapprochée au moteur canonique.';
  if (row.contract_state.includes('CONDITIONAL')) return 'Calcul conditionnel aux preuves et repères exigés.';
  if (row.availability_status === 'MISSING') return 'Source ou repère requis manquant.';
  if (row.availability_status === 'INVALID') return 'Preuve invalide ou non exploitable.';
  return 'Aucune valeur calculable attestée pour cette étude.';
};

const prettyUnit = (unit: string | null) => unit === 'deg' ? '°' : unit || '';

const CephaloR23G2ProtocolPanel: React.FC<{ P: R23G2Palette; analysis: R23G2Analysis }> = ({ P, analysis }) => {
  const anglesData = useOrthoStore(state => state.anglesData);
  const landmarks = useOrthoStore(state => state.local.landmarks);
  const [version, setVersion] = React.useState<R23G2RickettsVersion>('atlas');
  const profile = React.useMemo(
    () => readCephaloR23G2Protocol(anglesData, analysis, version),
    [anglesData, analysis, version],
  );
  const rows = profile?.rows ?? [];
  const [selectedMeasurementId, setSelectedMeasurementId] = React.useState<string | null>(null);
  // A factor selected under McNamara or Atlas must never remain the focus
  // after the analysis/profile identity changes.
  React.useEffect(() => setSelectedMeasurementId(null), [analysis, version]);
  const selectedRow = rows.find(row => row.canonical_measurement_id === selectedMeasurementId);
  const requirements = selectedRow ? findR23G3PinnedRequirements(
    selectedRow.canonical_measurement_id,
    landmarks.map(item => item.id),
  ) : null;
  // Atlas source-contract preview, never a source of SVG Focus or clinical values.
  const atlasRequirements = analysis === 'ricketts' && version === 'atlas' && selectedRow
    ? findR23G7AtlasSourceRequirements(
        profile?.protocol_profile_id ?? '',
        selectedRow.canonical_measurement_id,
        landmarks.map(item => item.id),
      )
    : null;
  const orientationRequirements = analysis === 'ricketts' && version === 'atlas' && selectedRow
    ? findR23G8W1OrientationRequirements(
        profile?.protocol_profile_id ?? '',
        selectedRow.canonical_measurement_id,
        landmarks.map(item => item.id),
      )
    : null;
  const dentalRequirements = analysis === 'ricketts' && version === 'atlas' && selectedRow
    ? findR23G8W2DentalRequirements(
        profile?.protocol_profile_id ?? '',
        selectedRow.canonical_measurement_id,
        landmarks.map(item => item.id),
      )
    : null;
  const currentFocus = resolveR23G3RuntimeFocus(selectedRow);
  // Same semantic event already observed by CephaloTracingLayer; no
  // invented SVG geometry is emitted. A blocked factor clears old focus.
  React.useEffect(() => {
    publishCephaloMetricFocus(currentFocus);
    return () => publishCephaloMetricFocus(null);
  }, [currentFocus?.canonicalMeasurementId, currentFocus?.points.join('|'), currentFocus?.constructionIds?.join('|')]);
  const available = rows.filter(row => row.availability_status === 'AVAILABLE' && row.value !== null).length;
  return (
    <aside
      data-r23g2-protocol-panel={analysis}
      data-r23g2-protocol-id={profile?.protocol_profile_id ?? 'UNVERIFIED'}
      className="flex h-full min-h-0 flex-col overflow-hidden rounded-3xl border"
      style={{ background: P.bgPanel, borderColor: P.border, boxShadow: P.shadowLg }}
    >
      <div className="shrink-0 border-b px-3 py-3 sm:px-4" style={{ borderColor: P.border }}>
        <h3 className="text-base font-extrabold" style={{ color: P.text }}>Analyse {ANALYSIS_NAMES[analysis]}</h3>
        {analysis === 'ricketts' && (
          <div className="mt-2 flex flex-wrap gap-2" role="group" aria-label="Version du protocole Ricketts">
            {([
              ['atlas', 'Atlas 2009 · 33 facteurs'],
              ['gregoret', 'Gregoret · 13 facteurs'],
            ] as const).map(([id, label]) => (
              <button
                key={id}
                type="button"
                data-r23g2-ricketts-version={id}
                aria-pressed={version === id}
                className="min-h-10 rounded-lg border px-2 py-1.5 text-xs font-semibold"
                onClick={() => { setSelectedMeasurementId(null); setVersion(id); }}
                style={{ borderColor: version === id ? P.accent : P.border, background: version === id ? P.bgCard : P.bgPanel, color: P.text }}
              >{label}</button>
            ))}
          </div>
        )}
        <p className="mt-2 text-xs leading-relaxed" style={{ color: P.textMuted }}>
          {analysis === 'ricketts'
            ? 'Composition et contrats source-lockés. Exécutable/conditionnel ne signifie pas disponible sur cette radiographie.'
            : 'Profil historique de présentation, non certifié comme autorité scientifique globale. Aucune norme ni classification calculée.'}
        </p>
        <p className="mt-1 text-xs font-bold" style={{ color: P.textMuted }} data-r23g2-coverage>
          {profile ? String(available) + '/' + String(rows.length) + ' valeurs disponibles · ' + String(rows.length) + ' facteurs documentés' : 'Profil non vérifié — mesures désactivées'}
        </p>
        <p className="mt-1 text-[11px]" style={{ color: P.textMuted }}>
          Sélectionnez un facteur pour cibler ses repères seulement si les preuves actives les identifient. Tracés complets en cours de construction ; aucun plan n’est simulé.
        </p>
      </div>
      {!profile ? (
        <div role="status" className="flex items-start gap-2 p-4 text-sm" style={{ color: P.accentWarning }}>
          <ShieldAlert size={18} className="mt-0.5 shrink-0" />
          Impossible de vérifier la chaîne d’évidence ou l’identité complète du protocole. Aucun chiffre clinique de remplacement n’est affiché.
        </div>
      ) : (
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
          <table className="w-full table-fixed text-left" aria-label={'Mesures ' + profile.protocol_profile_id} data-r23g2-row-count={rows.length}>
            <thead className="sticky top-0 z-10" style={{ background: P.bgPanel }}>
              <tr className="border-b text-[11px]" style={{ color: P.textMuted, borderColor: P.border }}>
                <th scope="col" className="w-[49%] px-3 py-2">Mesure source</th>
                <th scope="col" className="w-[22%] px-1 py-2">Valeur</th>
                <th scope="col" className="w-[29%] px-1 py-2">Évidence</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(row => (
                <tr key={row.canonical_measurement_id} data-r23g2-measurement-id={row.canonical_measurement_id} className="border-b" style={{ borderColor: P.border }}>
                  <th scope="row" className="break-words px-3 py-2 align-top text-[11px] font-semibold" style={{ color: P.text }}>
                    <button type="button"
                      data-r23g3-focus-select={row.canonical_measurement_id}
                      aria-pressed={selectedMeasurementId === row.canonical_measurement_id}
                      onClick={() => setSelectedMeasurementId(row.canonical_measurement_id)}
                      className="min-h-9 w-full rounded-md text-left focus-visible:outline-2 focus-visible:outline-offset-1"
                      style={{ color: selectedMeasurementId === row.canonical_measurement_id ? P.accent : P.text }}>
                    <span className="block break-words">{row.label === row.canonical_measurement_id
                      ? row.canonical_measurement_id.replace(/^M_/, '').replace(/_(?:DEG|MM)_V\d+$/, '').replaceAll('_', ' ').toLowerCase()
                      : row.label}</span>
                    </button>
                    <span className="block break-all font-mono text-[9px] font-normal" style={{ color: P.textMuted }} title={row.canonical_measurement_id}>{row.canonical_measurement_id}</span>
                  </th>
                  <td className="px-1 py-2 align-top text-xs font-semibold tabular-nums" style={{ color: row.value === null ? P.textMuted : P.accentSuccess }}>
                    {row.value === null ? 'NC' : row.value.toFixed(1).replace('.', ',') + ' ' + prettyUnit(row.unit)}
                  </td>
                  <td className="break-words px-1 py-2 align-top text-[11px] leading-relaxed" style={{ color: P.textMuted }}>
                    <span className="block font-semibold">{AVAILABILITY_LABELS[row.availability_status] ?? 'Non calculable'}</span>
                    {row.value === null && <span className="block">{statusExplanation(row)}</span>}
                    {row.contract_gate && <span className="block break-all text-[10px]" title={row.contract_gate}>Gate : {row.contract_gate}</span>}
                    <span className="block text-[10px]">Contrat : {row.contract_state}</span>
                    {selectedMeasurementId === row.canonical_measurement_id && (
                      <span data-r23g3-focus-source={currentFocus ? 'active-runtime' : 'not-authorized'}
                        className="mt-1 block font-semibold">
                        {currentFocus
                          ? 'Focus prouvé : ' + currentFocus.points.join(', ') + (currentFocus.constructionIds?.length ? ' · constructions : ' + currentFocus.constructionIds.join(', ') : '')
                          : 'Focus géométrique non autorisé sans preuve active exacte.'}
                        {requirements ? (
                          <span className="mt-1 block" data-r23g3-pinned-gate={requirements.measurementId}>
                            Contrat LOT06 · repères requis : {requirements.requiredLandmarks.join(', ')}
                            {requirements.missingLandmarks.length > 0
                              ? ' · absents : ' + requirements.missingLandmarks.join(', ')
                              : ' · tous les repères listés sont présents'}
                            {' · gate : ' + requirements.availabilityGate}
                          </span>
                        ) : atlasRequirements ? (
                          <span className="mt-1 block" data-r23g7-atlas-gate={atlasRequirements.measurementId}>
                            Contrat Atlas 2009 (repères à vérifier, sans autorisation de mesure) :
                            {' ' + atlasRequirements.requiredLandmarks.join(', ')}
                            {atlasRequirements.missingLandmarks.length > 0
                              ? ' · absents : ' + atlasRequirements.missingLandmarks.join(', ')
                              : ' · repères listés présents (insuffisant pour calcul/Focus)'}
                            {' · gate : ' + atlasRequirements.availabilityGate}
                            {' · valeur et tracé toujours soumis à la preuve active.'}
                          </span>
                        ) : orientationRequirements ? (
                          <span className="mt-1 block" data-r23g8-w1-orientation-gate={orientationRequirements.measurementId}>
                            Contrat Atlas W1 — orientation anatomique obligatoire et NON vérifiée dans cet aperçu.
                            {' · Repères directs : ' + (orientationRequirements.requiredLandmarks.join(', ') || 'aucun (constructions uniquement)')}
                            {orientationRequirements.missingLandmarks.length
                              ? ' · absents : ' + orientationRequirements.missingLandmarks.join(', ')
                              : ' · repères déclarés présents (preuve clinique insuffisante)'}
                            {' · constructions exigées : ' + (orientationRequirements.requiredConstructions.join(', ') || 'aucune')}
                            {orientationRequirements.requiredManualLandmarks.length
                              ? ' · validation manuelle : ' + orientationRequirements.requiredManualLandmarks.join(', ')
                              : ''}
                            {orientationRequirements.requiresCalibration ? ' · calibration mm vérifiée requise' : ''}
                            {' · ImageOrientationEvidence de la MÊME image, axes antérieur/supérieur explicites, miroir et provenance audités.'}
                            {' · gate : ' + orientationRequirements.availabilityGate}
                            {' · Aucune valeur ni Focus autorisé par cet aperçu.'}
                          </span>
                        ) : dentalRequirements ? (
                          <span className="mt-1 block" data-r23g8-w2-dental-gate={dentalRequirements.measurementId}>
                            Contrat Atlas W2 — obligations dentaires et manuelles non validées pour cette étude.
                            {' · Repères directs : ' + dentalRequirements.requiredLandmarks.join(', ')}
                            {dentalRequirements.missingLandmarks.length
                              ? ' · absents : ' + dentalRequirements.missingLandmarks.join(', ')
                              : ' · repères déclarés présents (preuve clinique insuffisante)'}
                            {' · constructions : ' + (dentalRequirements.requiredConstructions.join(', ') || 'aucune')}
                            {dentalRequirements.requiredManualLandmarks.length
                              ? ' · origine manuelle obligatoire : ' + dentalRequirements.requiredManualLandmarks.join(', ')
                              : ''}
                            {dentalRequirements.indirectConstructionManualLandmarks.length
                              ? ' · repères manuels nécessaires aux constructions : ' + dentalRequirements.indirectConstructionManualLandmarks.join(', ')
                              : ''}
                            {dentalRequirements.requiresCalibration ? ' · calibration millimétrique vérifiée obligatoire' : ''}
                            {' · même image, provenance et validité du graphe à vérifier.'}
                            {' · gate : ' + dentalRequirements.availabilityGate}
                            {' · Aucune valeur ni Focus autorisé par cette description.'}
                          </span>
                        ) : (
                          <span className="mt-1 block">Hors registre de dépendances LOT06 ou extension Atlas publiée : aucun repère requis supplémentaire n’est supposé.</span>
                        )}
                      </span>
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

export default CephaloR23G2ProtocolPanel;
