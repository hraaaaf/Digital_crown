import { useEffect, useMemo, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertCircle, Eye, Layers3, RefreshCw, X } from 'lucide-react';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { API_BASE } from '../../services/api';
import { cephaloRepository } from './cephaloRepository';
import {
  estimateOrthoSuperimposition,
  fetchOrthoSuperimpositionContext,
  type OrthoSuperimpositionRegistration,
  type SuperimpositionPixelROI,
} from './orthoSuperimposition';

interface TimepointRef {
  id: number;
  ordinal: number;
  occurred_at: string;
}

interface Props {
  patientId: number;
  caseId: number;
  fromTimepoint: TimepointRef;
  toTimepoint: TimepointRef;
  onClose: () => void;
}

const resolveImageSrc = (imagePath?: string) => {
  if (!imagePath) return undefined;
  const normalized = imagePath.replace(/^\/+/, '');
  if (!normalized.startsWith('api/static/uploads/radios/')) return undefined;
  return `${API_BASE.replace(/\/$/, '')}/${normalized}`;
};

const RoiPicker = ({
  src,
  label,
  roi,
  onChange,
  dataKey,
}: {
  src: string;
  label: string;
  roi: SuperimpositionPixelROI | null;
  onChange: (roi: SuperimpositionPixelROI) => void;
  dataKey: string;
}) => {
  const boxRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const [natural, setNatural] = useState({ width: 0, height: 0 });
  const [drag, setDrag] = useState<{ start: { x: number; y: number }; current: { x: number; y: number } } | null>(null);

  const pointFromEvent = (clientX: number, clientY: number) => {
    const box = boxRef.current;
    const image = imageRef.current;
    if (!box || !image || !natural.width || !natural.height) return null;
    const rect = box.getBoundingClientRect();
    const scale = Math.min(rect.width / natural.width, rect.height / natural.height);
    const renderedWidth = natural.width * scale;
    const renderedHeight = natural.height * scale;
    const offsetX = (rect.width - renderedWidth) / 2;
    const offsetY = (rect.height - renderedHeight) / 2;
    const x = (clientX - rect.left - offsetX) / scale;
    const y = (clientY - rect.top - offsetY) / scale;
    if (x < 0 || y < 0 || x > natural.width || y > natural.height) return null;
    return {
      x: Math.max(0, Math.min(natural.width, x)),
      y: Math.max(0, Math.min(natural.height, y)),
    };
  };

  const finishDrag = () => {
    if (!drag) return;
    const left = Math.round(Math.min(drag.start.x, drag.current.x));
    const top = Math.round(Math.min(drag.start.y, drag.current.y));
    const right = Math.round(Math.max(drag.start.x, drag.current.x));
    const bottom = Math.round(Math.max(drag.start.y, drag.current.y));
    setDrag(null);
    if (right - left >= 8 && bottom - top >= 8) {
      onChange({ x: left, y: top, width: right - left, height: bottom - top });
    }
  };

  const active = drag
    ? {
        x: Math.min(drag.start.x, drag.current.x),
        y: Math.min(drag.start.y, drag.current.y),
        width: Math.abs(drag.current.x - drag.start.x),
        height: Math.abs(drag.current.y - drag.start.y),
      }
    : roi;

  return (
    <div className="min-w-0">
      <div className="mb-2 flex items-center justify-between gap-2">
        <p className="text-xs font-black text-main">{label}</p>
        <span className="text-[10px] font-bold text-text-muted">
          {roi ? `${roi.width}×${roi.height}px` : 'Zone non définie'}
        </span>
      </div>
      <div
        ref={boxRef}
        data-f5-roi={dataKey}
        className="relative aspect-[4/3] w-full touch-none overflow-hidden rounded-2xl border border-border-main bg-slate-950"
        onPointerDown={(event) => {
          const point = pointFromEvent(event.clientX, event.clientY);
          if (!point) return;
          event.currentTarget.setPointerCapture(event.pointerId);
          setDrag({ start: point, current: point });
        }}
        onPointerMove={(event) => {
          if (!drag) return;
          const point = pointFromEvent(event.clientX, event.clientY);
          if (point) setDrag((current) => current ? { ...current, current: point } : current);
        }}
        onPointerUp={finishDrag}
        onPointerCancel={() => setDrag(null)}
      >
        <img
          ref={imageRef}
          src={src}
          alt=""
          draggable={false}
          onLoad={(event) => setNatural({
            width: event.currentTarget.naturalWidth,
            height: event.currentTarget.naturalHeight,
          })}
          className="absolute inset-0 h-full w-full select-none object-contain"
        />
        {natural.width > 0 && natural.height > 0 && (
          <svg
            className="pointer-events-none absolute inset-0 h-full w-full"
            viewBox={`0 0 ${natural.width} ${natural.height}`}
            preserveAspectRatio="xMidYMid meet"
            aria-hidden="true"
          >
            {active && (
              <rect
                x={active.x}
                y={active.y}
                width={active.width}
                height={active.height}
                fill="none"
                stroke="currentColor"
                strokeWidth={Math.max(2, natural.width / 400)}
                strokeDasharray="10 6"
                className="text-white"
              />
            )}
          </svg>
        )}
        {!roi && !drag && (
          <div className="pointer-events-none absolute inset-x-3 bottom-3 rounded-xl bg-black/65 px-3 py-2 text-center text-[11px] font-bold text-white">
            Tracez la région stable de la base crânienne antérieure
          </div>
        )}
      </div>
    </div>
  );
};

const RegistrationCanvas = ({
  referenceSrc,
  movingSrc,
  registration,
  opacity,
  mode,
}: {
  referenceSrc: string;
  movingSrc: string;
  registration: OrthoSuperimpositionRegistration;
  opacity: number;
  mode: 'overlay' | 'reference' | 'moving';
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    let cancelled = false;
    const reference = new Image();
    const moving = new Image();
    const draw = () => {
      if (cancelled || !reference.complete || !moving.complete || !canvasRef.current) return;
      const width = registration.reference_size_px.width || reference.naturalWidth;
      const height = registration.reference_size_px.height || reference.naturalHeight;
      const canvas = canvasRef.current;
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      ctx.clearRect(0, 0, width, height);

      if (mode !== 'moving') {
        ctx.globalAlpha = 1;
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.drawImage(reference, 0, 0);
      }

      if (mode !== 'reference') {
        const [[m00, m01, m02], [m10, m11, m12]] = registration.matrix;
        ctx.globalAlpha = mode === 'overlay' ? opacity : 1;
        ctx.setTransform(m00, m10, m01, m11, m02, m12);
        ctx.drawImage(moving, 0, 0);
      }

      ctx.globalAlpha = 1;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
    };
    let loaded = 0;
    const onLoad = () => {
      loaded += 1;
      if (loaded === 2) draw();
    };
    reference.onload = onLoad;
    moving.onload = onLoad;
    reference.src = referenceSrc;
    moving.src = movingSrc;
    return () => { cancelled = true; };
  }, [referenceSrc, movingSrc, registration, opacity, mode]);

  return (
    <canvas
      ref={canvasRef}
      data-f5-overlay-canvas
      className="max-h-[58vh] w-full rounded-2xl bg-slate-950 object-contain"
      aria-label="Superposition géométrique des céphalogrammes"
    />
  );
};

export const OrthoSuperimpositionViewer = ({
  patientId,
  caseId,
  fromTimepoint,
  toTimepoint,
  onClose,
}: Props) => {
  const [referenceRoi, setReferenceRoi] = useState<SuperimpositionPixelROI | null>(null);
  const [movingRoi, setMovingRoi] = useState<SuperimpositionPixelROI | null>(null);
  const [registration, setRegistration] = useState<OrthoSuperimpositionRegistration | null>(null);
  const [estimateError, setEstimateError] = useState<string | null>(null);
  const [estimating, setEstimating] = useState(false);
  const [opacity, setOpacity] = useState(0.5);
  const [mode, setMode] = useState<'overlay' | 'reference' | 'moving'>('overlay');
  const dialogRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const contextQuery = useQuery({
    queryKey: ['ortho-f5-context', patientId, caseId, fromTimepoint.id, toTimepoint.id],
    queryFn: () => fetchOrthoSuperimpositionContext(
      patientId,
      caseId,
      fromTimepoint.id,
      toTimepoint.id,
    ),
  });

  const context = contextQuery.data;
  const analysesQuery = useQuery({
    queryKey: [
      'ortho-f5-analyses',
      context?.from_source.cephalo_analysis_id,
      context?.to_source.cephalo_analysis_id,
    ],
    queryFn: async () => {
      const [reference, moving] = await Promise.all([
        cephaloRepository.getAnalysis(context!.from_source.cephalo_analysis_id),
        cephaloRepository.getAnalysis(context!.to_source.cephalo_analysis_id),
      ]);
      return { reference, moving };
    },
    enabled: Boolean(context),
  });

  const referenceSrc = useMemo(
    () => resolveImageSrc(analysesQuery.data?.reference?.image_original_path),
    [analysesQuery.data?.reference?.image_original_path],
  );
  const movingSrc = useMemo(
    () => resolveImageSrc(analysesQuery.data?.moving?.image_original_path),
    [analysesQuery.data?.moving?.image_original_path],
  );

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    const previousFocused = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null;
    document.body.style.overflow = 'hidden';
    closeButtonRef.current?.focus();

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== 'Tab' || !dialogRef.current) return;

      const focusable = Array.from(
        dialogRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), input:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])',
        ),
      ).filter((element) => !element.hasAttribute('hidden') && element.getAttribute('aria-hidden') !== 'true');

      if (!focusable.length) {
        event.preventDefault();
        dialogRef.current.focus();
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', onKeyDown);
      previousFocused?.focus();
    };
  }, [onClose]);

  const estimate = async () => {
    if (!referenceRoi || !movingRoi) return;
    setEstimating(true);
    setEstimateError(null);
    try {
      const result = await estimateOrthoSuperimposition(patientId, caseId, {
        from_timepoint_id: fromTimepoint.id,
        to_timepoint_id: toTimepoint.id,
        reference_roi: referenceRoi,
        moving_roi: movingRoi,
      });
      setRegistration(result.registration);
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      setEstimateError(detail?.message || 'Superposition non calculable avec ces sources.');
      setRegistration(null);
    } finally {
      setEstimating(false);
    }
  };

  const date = (value: string) => format(new Date(value), 'd MMM yyyy', { locale: fr });

  return (
    <div
      ref={dialogRef}
      tabIndex={-1}
      className="fixed inset-0 z-[1000] bg-slate-950/55 p-0 sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Superposition scientifique"
      data-ortho-f5-viewer
    >
      <div className="mx-auto flex h-full w-full max-w-6xl flex-col overflow-hidden bg-card shadow-2xl sm:rounded-[2rem] sm:border sm:border-border-main">
        <header className="flex shrink-0 items-start justify-between gap-3 border-b border-border-main px-4 py-3 sm:px-6 sm:py-4">
          <div className="min-w-0">
            <p className="text-[9px] font-black uppercase tracking-[0.16em] text-text-muted sm:text-[10px]">F5 · Superposition structurale</p>
            <h2 className="mt-1 text-base font-black text-main sm:text-xl">
              T{fromTimepoint.ordinal} · {date(fromTimepoint.occurred_at)} ↔ T{toTimepoint.ordinal} · {date(toTimepoint.occurred_at)}
            </h2>
            <p className="mt-1 text-[11px] font-bold text-text-muted sm:text-xs">
              Estimation géométrique uniquement · interprétation clinique par le praticien.
            </p>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-border-main text-text-muted hover:text-main focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30"
            aria-label="Fermer la superposition"
          >
            <X size={18} />
          </button>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3 sm:px-6 sm:py-5">
          {contextQuery.isLoading || analysesQuery.isLoading ? (
            <div className="flex min-h-[320px] items-center justify-center text-sm font-black text-text-muted">Chargement des sources canoniques…</div>
          ) : contextQuery.isError || analysesQuery.isError || !context || !referenceSrc || !movingSrc ? (
            <div className="mx-auto mt-8 max-w-xl rounded-2xl border border-border-main bg-slate-50 p-5 text-center">
              <AlertCircle className="mx-auto text-text-muted" size={24} />
              <p className="mt-3 text-sm font-black text-main">Superposition indisponible dans cet environnement</p>
              <p className="mt-1 text-xs font-bold text-text-muted">Le moteur F5 reste soumis à son gate scientifique et peut être désactivé hors environnement d’ingénierie.</p>
            </div>
          ) : registration ? (
            <div className="space-y-4">
              <RegistrationCanvas
                referenceSrc={referenceSrc}
                movingSrc={movingSrc}
                registration={registration}
                opacity={opacity}
                mode={mode}
              />

              <div className="grid gap-3 rounded-2xl border border-border-main bg-slate-50/70 p-3 sm:grid-cols-[1fr_auto] sm:items-center">
                <label className="min-w-0">
                  <span className="text-[10px] font-black uppercase tracking-wide text-text-muted">Opacité T{toTimepoint.ordinal}</span>
                  <input
                    aria-label="Opacité de la céphalométrie comparée"
                    type="range"
                    min="0"
                    max="100"
                    value={Math.round(opacity * 100)}
                    onChange={(event) => setOpacity(Number(event.target.value) / 100)}
                    className="mt-2 w-full"
                  />
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {([
                    ['overlay', 'Superposé'],
                    ['reference', `T${fromTimepoint.ordinal}`],
                    ['moving', `T${toTimepoint.ordinal}`],
                  ] as const).map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setMode(value)}
                      className={`min-h-10 rounded-xl border px-3 text-[10px] font-black uppercase tracking-wide focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30 ${
                        mode === value ? 'border-primary/30 bg-primary/5 text-primary' : 'border-border-main bg-card text-main'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid gap-2 rounded-2xl border border-border-main bg-card p-3 text-[11px] sm:grid-cols-3">
                <div><span className="font-black text-main">Méthode</span><p className="mt-0.5 font-bold text-text-muted">{context.method_id} v{context.method_version}</p></div>
                <div><span className="font-black text-main">Calibration</span><p className="mt-0.5 font-bold text-text-muted">T{fromTimepoint.ordinal} {context.from_source.is_calibrated ? 'calibrée' : 'non calibrée'} · T{toTimepoint.ordinal} {context.to_source.is_calibrated ? 'calibrée' : 'non calibrée'}</p></div>
                <div><span className="font-black text-main">Statut</span><p className="mt-0.5 font-bold text-text-muted">ENGINE_ESTIMATE_ONLY · validation clinique non établie</p></div>
              </div>

              <button
                type="button"
                onClick={() => {
                  setRegistration(null);
                  setEstimateError(null);
                }}
                className="inline-flex min-h-10 items-center gap-1.5 rounded-xl border border-border-main px-3 text-[10px] font-black uppercase tracking-wide text-main hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30"
              >
                <RefreshCw size={13} /> Modifier les zones
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="rounded-2xl border border-border-main bg-slate-50/70 p-3 sm:p-4">
                <div className="flex items-start gap-2">
                  <Eye size={16} className="mt-0.5 shrink-0 text-primary" />
                  <div>
                    <p className="text-xs font-black text-main">Confirmer la région stable sur chaque cliché</p>
                    <p className="mt-1 text-[11px] font-bold leading-4 text-text-muted">
                      Tracez la zone de base crânienne antérieure utilisée pour le matching structural. Aucune zone n’est inventée automatiquement.
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid gap-4 lg:grid-cols-2">
                <RoiPicker
                  src={referenceSrc}
                  label={`T${fromTimepoint.ordinal} · référence`}
                  roi={referenceRoi}
                  onChange={setReferenceRoi}
                  dataKey="from"
                />
                <RoiPicker
                  src={movingSrc}
                  label={`T${toTimepoint.ordinal} · comparé`}
                  roi={movingRoi}
                  onChange={setMovingRoi}
                  dataKey="to"
                />
              </div>

              {estimateError && (
                <div role="alert" className="rounded-xl border border-border-main bg-slate-50 p-3 text-xs font-bold text-text-muted">
                  {estimateError}
                </div>
              )}

              <div className="flex flex-col gap-2 border-t border-border-main pt-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-[10px] font-bold text-text-muted">
                  {context.quantitative_mm_allowed ? 'Deux calibrations présentes.' : 'Affichage visuel uniquement : sortie millimétrique bloquée.'}
                </p>
                <button
                  type="button"
                  onClick={estimate}
                  disabled={!referenceRoi || !movingRoi || estimating}
                  className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-primary px-4 text-xs font-black text-white disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30"
                >
                  <Layers3 size={15} /> {estimating ? 'Calcul…' : 'Calculer la superposition'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
