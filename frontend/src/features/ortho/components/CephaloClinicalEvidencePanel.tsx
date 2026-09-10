import React from 'react';
import { Activity, CheckCircle2, Clock3, RotateCcw, ShieldCheck, X } from 'lucide-react';
import { useOrthoStore } from '../stores/useOrthoStore';
import { cephaloRepository } from '../cephaloRepository';

const GRAPH_KEY = '_evidence_graph_v1';

type EvidenceLandmark = {
  evidence_id?: string;
  landmark_id?: string;
  x?: number;
  y?: number;
  origin?: string;
  original_auto_x?: number | null;
  original_auto_y?: number | null;
  validated_by?: string | null;
  validated_at?: string | null;
  evidence_status?: string;
};

type MeasurementEvidence = {
  measurement_id?: string;
  method_id?: string;
  value?: number | null;
  unit?: string;
  landmark_refs?: string[];
  availability_status?: string;
  requires_calibration?: boolean;
};

function currentLandmarks(graph: any): EvidenceLandmark[] {
  const landmarks: EvidenceLandmark[] = Array.isArray(graph?.landmarks) ? graph.landmarks : [];
  const refs: string[] | undefined = Array.isArray(graph?.current_landmark_refs)
    ? graph.current_landmark_refs
    : undefined;
  if (refs) {
    const byRef = new Map(landmarks.map(item => [item.evidence_id, item]));
    return refs.map(ref => byRef.get(ref)).filter(Boolean) as EvidenceLandmark[];
  }

  const grouped = new Map<string, EvidenceLandmark[]>();
  landmarks.forEach(item => {
    if (!item.landmark_id) return;
    grouped.set(item.landmark_id, [...(grouped.get(item.landmark_id) || []), item]);
  });
  return [...grouped.values()].map(items => {
    const manual = items.find(item => item.origin && item.origin !== 'SRPOSE38_AUTO');
    return manual || items[0];
  }).filter(Boolean);
}

function calibrationSource(graph: any) {
  const sources = Array.isArray(graph?.sources) ? graph.sources : [];
  return sources.find((source: any) => source?.kind === 'calibration');
}

function formatTimestamp(value?: string | null) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' });
}

export const CephaloClinicalEvidencePanel: React.FC = () => {
  const store = useOrthoStore();
  const [drawerOpen, setDrawerOpen] = React.useState(true);
  const graph = store.anglesData?.[GRAPH_KEY];
  const evidenceLandmarks = React.useMemo(() => currentLandmarks(graph), [graph]);
  const calibration = calibrationSource(graph);
  const measurements: MeasurementEvidence[] = Array.isArray(graph?.measurements) ? graph.measurements : [];
  const mmMeasurements = measurements.filter(item => item.requires_calibration || item.unit === 'mm');
  const availableMm = mmMeasurements.filter(item => item.availability_status === 'AVAILABLE').length;
  const unavailableMm = mmMeasurements.filter(item => item.availability_status && item.availability_status !== 'AVAILABLE').length;
  const correctedCount = evidenceLandmarks.filter(item => item.origin === 'MANUAL_CORRECTED' || item.origin === 'MANUAL').length;

  const runtimePoint = store.local.landmarks.find(item => item.id === store.activePointId);
  const evidencePoint = evidenceLandmarks.find(item => item.landmark_id === store.activePointId);
  const point = evidencePoint || runtimePoint;

  React.useEffect(() => {
    if (store.activePointId) setDrawerOpen(true);
  }, [store.activePointId]);

  React.useEffect(() => {
    if (!store.analysisId) return;
    if (graph && store.syncState !== 'success' && !store.isCalibrated) return;

    let cancelled = false;
    void cephaloRepository.getAnalysis(store.analysisId)
      .then(loaded => {
        if (cancelled || !loaded?.angles_data) return;
        store.setAnglesData(loaded.angles_data);
      })
      .catch(error => {
        if (!cancelled) console.warn('Typed cephalo evidence refresh failed:', error);
      });
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [store.analysisId, store.syncState, store.isCalibrated]);

  const dependentMeasurements = React.useMemo(() => {
    if (!evidencePoint?.evidence_id) return [];
    return measurements.filter(item => item.landmark_refs?.includes(evidencePoint.evidence_id as string));
  }, [evidencePoint, measurements]);

  const calibrationLabel = store.isCalibrated && store.mmPerPixel
    ? `${store.mmPerPixel.toFixed(4)} mm/px`
    : 'Non calibré';

  return (
    <>
      <button
        type="button"
        onClick={() => setDrawerOpen(open => !open)}
        className="absolute left-1/2 top-20 z-30 flex max-w-[calc(100%-2rem)] -translate-x-1/2 flex-wrap items-center justify-center gap-x-3 gap-y-1 rounded-2xl border border-slate-700/70 bg-slate-900/85 px-3 py-2 text-[9px] font-black uppercase tracking-wider text-slate-300 shadow-2xl backdrop-blur-xl sm:px-4 sm:text-[10px] lg:bottom-6 lg:top-auto lg:max-w-[calc(100%-9rem)] lg:gap-x-4 lg:px-5 lg:py-2.5"
        aria-label="Afficher l'état scientifique de l'analyse"
      >
        <span className="flex items-center gap-1.5 text-emerald-300"><Activity size={12} />{store.local.landmarks.length} points</span>
        <span className={store.isCalibrated ? 'text-indigo-300' : 'text-amber-300'}>{calibrationLabel}</span>
        {mmMeasurements.length > 0 && <span className="text-emerald-300">{availableMm} mm calculables</span>}
        {unavailableMm > 0 && <span className="text-amber-300">{unavailableMm} NC</span>}
        {correctedCount > 0 && <span className="text-violet-300">{correctedCount} correction{correctedCount > 1 ? 's' : ''}</span>}
      </button>

      {drawerOpen && store.activePointId && point && (
        <aside className="absolute bottom-20 left-3 right-3 top-auto z-40 max-h-[55%] w-auto overflow-y-auto rounded-3xl border border-slate-700/70 bg-slate-900/95 p-4 text-slate-200 shadow-2xl backdrop-blur-2xl sm:left-4 sm:right-4 sm:max-h-[58%] sm:p-5 lg:bottom-20 lg:left-auto lg:right-6 lg:top-20 lg:max-h-none lg:w-[21rem]">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-[9px] font-black uppercase tracking-[0.18em] text-slate-500">Point sélectionné</p>
              <h3 className="mt-1 text-lg font-black text-white">{store.activePointId}</h3>
            </div>
            <button type="button" onClick={() => setDrawerOpen(false)} className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white" aria-label="Fermer le panneau clinique"><X size={16} /></button>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {evidencePoint?.origin === 'MANUAL_CORRECTED' || evidencePoint?.origin === 'MANUAL' ? (
              <span className="rounded-full border border-violet-500/40 bg-violet-500/15 px-3 py-1 text-[9px] font-black uppercase tracking-wider text-violet-200">Corrigé manuellement</span>
            ) : (
              <span className="rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1 text-[9px] font-black uppercase tracking-wider text-sky-200">Automatique</span>
            )}
            {evidencePoint?.evidence_status === 'CLINICIAN_VALIDATED' && (
              <span className="flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-[9px] font-black uppercase tracking-wider text-emerald-200"><ShieldCheck size={11} /> Validé</span>
            )}
          </div>

          <section className="mt-6">
            <p className="text-[9px] font-black uppercase tracking-[0.18em] text-slate-500">Position</p>
            <div className="mt-2 rounded-2xl bg-slate-800/80 p-3 text-xs">
              <div className="flex justify-between gap-4"><span className="text-slate-400">Actuelle</span><strong className="font-mono text-white">{Number(point.x).toFixed(1)} px · {Number(point.y).toFixed(1)} px</strong></div>
              {evidencePoint?.original_auto_x != null && evidencePoint?.original_auto_y != null && (
                <div className="mt-2 flex justify-between gap-4"><span className="text-slate-400">Auto origine</span><span className="font-mono text-slate-300">{evidencePoint.original_auto_x.toFixed(1)} px · {evidencePoint.original_auto_y.toFixed(1)} px</span></div>
              )}
            </div>
          </section>

          <section className="mt-5">
            <p className="text-[9px] font-black uppercase tracking-[0.18em] text-slate-500">Provenance</p>
            <div className="mt-2 space-y-1 text-xs text-slate-300">
              <p>{evidencePoint?.origin || 'Provenance typée indisponible'}</p>
              {evidencePoint?.validated_by && <p>Opérateur : <span className="font-mono text-white">{evidencePoint.validated_by}</span></p>}
              {formatTimestamp(evidencePoint?.validated_at) && <p className="flex items-center gap-1 text-slate-400"><Clock3 size={12} />{formatTimestamp(evidencePoint?.validated_at)}</p>}
            </div>
          </section>

          <section className="mt-5">
            <p className="text-[9px] font-black uppercase tracking-[0.18em] text-slate-500">Mesures dépendantes</p>
            <div className="mt-2 space-y-2">
              {dependentMeasurements.length === 0 ? (
                <p className="rounded-xl border border-slate-800 bg-slate-950/30 p-3 text-xs text-slate-500">Aucune dépendance typée disponible pour ce point.</p>
              ) : dependentMeasurements.map(item => (
                <div key={item.measurement_id} className="flex items-center justify-between gap-3 rounded-xl bg-slate-800/60 px-3 py-2 text-[10px]">
                  <span className="truncate font-bold text-slate-300">{item.method_id}</span>
                  {item.availability_status === 'AVAILABLE' && item.value != null ? (
                    <span className="shrink-0 font-mono font-bold text-emerald-300">{item.value} {item.unit}</span>
                  ) : (
                    <span className="shrink-0 font-black text-amber-300">NC</span>
                  )}
                </div>
              ))}
            </div>
          </section>

          <section className="mt-5 border-t border-slate-800 pt-4">
            <p className="text-[9px] font-black uppercase tracking-[0.18em] text-slate-500">Calibration</p>
            {store.isCalibrated && store.mmPerPixel ? (
              <div className="mt-2 flex items-start gap-2 text-xs text-emerald-300"><CheckCircle2 className="mt-0.5 shrink-0" size={14} /><div><strong>{store.mmPerPixel.toFixed(4)} mm/px</strong><p className="mt-1 text-[10px] font-normal text-slate-400">{calibration?.quality_status || 'Validation enregistrée'}</p></div></div>
            ) : (
              <p className="mt-2 text-xs text-amber-300">Mesures millimétriques non autorisées tant que la calibration n'est pas vérifiée.</p>
            )}
          </section>

          {evidencePoint?.original_auto_x != null && evidencePoint?.original_auto_y != null && (
            <div className="mt-5 flex items-center gap-2 rounded-xl border border-slate-800 px-3 py-2 text-[10px] text-slate-500"><RotateCcw size={12} /> Coordonnées automatiques conservées dans la provenance.</div>
          )}
        </aside>
      )}
    </>
  );
};

export default CephaloClinicalEvidencePanel;
