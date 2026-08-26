import { useEffect, useRef, useState, type PointerEvent as ReactPointerEvent } from 'react';
import { createPortal } from 'react-dom';
import { Maximize2, Minus, Plus, RotateCcw, X } from 'lucide-react';

import {
  PANORAMIC_MAX_SCALE,
  PANORAMIC_MIN_SCALE,
  PANORAMIC_RESET,
  PANORAMIC_SCALE_STEP,
  panPanoramicBy,
  zoomPanoramicAt,
  type PanoramicGeometry,
  type PanoramicTransform,
} from './mobilePanoramicGeometry';

type Point = { x: number; y: number };
type Gesture = { points: Point[]; transform: PanoramicTransform };

const midpoint = (a: Point, b: Point): Point => ({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 });
const distance = (a: Point, b: Point): number => Math.hypot(a.x - b.x, a.y - b.y);

interface MobilePanoramicViewerProps {
  src: string;
  alt: string;
}

export const MobilePanoramicViewer = ({ src, alt }: MobilePanoramicViewerProps) => {
  const [open, setOpen] = useState(false);
  const [transform, setTransform] = useState<PanoramicTransform>({ ...PANORAMIC_RESET });
  const transformRef = useRef<PanoramicTransform>({ ...PANORAMIC_RESET });
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const closeRef = useRef<HTMLButtonElement | null>(null);
  const openRef = useRef<HTMLButtonElement | null>(null);
  const pointersRef = useRef(new Map<number, Point>());
  const gestureRef = useRef<Gesture | null>(null);

  const applyTransform = (next: PanoramicTransform) => {
    transformRef.current = next;
    setTransform(next);
  };

  const geometry = (): PanoramicGeometry | null => {
    const viewport = viewportRef.current;
    const image = imageRef.current;
    if (!viewport || !image) return null;
    const rect = viewport.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0 || image.naturalWidth <= 0 || image.naturalHeight <= 0) return null;
    return { width: rect.width, height: rect.height, imageWidth: image.naturalWidth, imageHeight: image.naturalHeight };
  };

  const snapshotGesture = () => {
    gestureRef.current = {
      points: [...pointersRef.current.values()].slice(0, 2).map(point => ({ ...point })),
      transform: { ...transformRef.current },
    };
  };

  const reset = () => applyTransform({ ...PANORAMIC_RESET });

  const close = () => {
    reset();
    pointersRef.current.clear();
    gestureRef.current = null;
    setOpen(false);
    window.setTimeout(() => openRef.current?.focus(), 0);
  };

  const openViewer = () => {
    reset();
    setOpen(true);
  };

  const zoomBy = (delta: number) => {
    const currentGeometry = geometry();
    if (!currentGeometry) return;
    const center = { x: currentGeometry.width / 2, y: currentGeometry.height / 2 };
    applyTransform(zoomPanoramicAt(transformRef.current, transformRef.current.scale + delta, center, currentGeometry));
  };

  const onPointerDown = (event: ReactPointerEvent<HTMLDivElement>) => {
    pointersRef.current.set(event.pointerId, { x: event.clientX, y: event.clientY });
    try { event.currentTarget.setPointerCapture?.(event.pointerId); } catch { /* synthetic/test pointers may not be capturable */ }
    snapshotGesture();
  };

  const onPointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (!pointersRef.current.has(event.pointerId)) return;
    pointersRef.current.set(event.pointerId, { x: event.clientX, y: event.clientY });
    const currentGeometry = geometry();
    const gesture = gestureRef.current;
    if (!currentGeometry || !gesture) return;
    const currentPoints = [...pointersRef.current.values()].slice(0, 2);

    if (currentPoints.length === 1 && gesture.points.length === 1 && gesture.transform.scale > PANORAMIC_MIN_SCALE) {
      const dx = currentPoints[0].x - gesture.points[0].x;
      const dy = currentPoints[0].y - gesture.points[0].y;
      applyTransform(panPanoramicBy(gesture.transform, dx, dy, currentGeometry));
      return;
    }

    if (currentPoints.length >= 2 && gesture.points.length >= 2) {
      const startDistance = Math.max(1, distance(gesture.points[0], gesture.points[1]));
      const currentDistance = Math.max(1, distance(currentPoints[0], currentPoints[1]));
      const startMid = midpoint(gesture.points[0], gesture.points[1]);
      const currentMid = midpoint(currentPoints[0], currentPoints[1]);
      const rect = viewportRef.current!.getBoundingClientRect();
      const anchor = { x: startMid.x - rect.left, y: startMid.y - rect.top };
      let next = zoomPanoramicAt(gesture.transform, gesture.transform.scale * (currentDistance / startDistance), anchor, currentGeometry);
      next = panPanoramicBy(next, currentMid.x - startMid.x, currentMid.y - startMid.y, currentGeometry);
      applyTransform(next);
    }
  };

  const onPointerEnd = (event: ReactPointerEvent<HTMLDivElement>) => {
    pointersRef.current.delete(event.pointerId);
    try { event.currentTarget.releasePointerCapture?.(event.pointerId); } catch { /* capture may already be released */ }
    snapshotGesture();
  };

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    const appRoot = document.getElementById('root');
    const rootWasInert = appRoot?.hasAttribute('inert') ?? false;
    document.body.style.overflow = 'hidden';
    appRoot?.setAttribute('inert', '');
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') close();
    };
    window.addEventListener('keydown', onKeyDown);
    window.setTimeout(() => closeRef.current?.focus(), 0);
    return () => {
      document.body.style.overflow = previousOverflow;
      if (appRoot && !rootWasInert) appRoot.removeAttribute('inert');
      window.removeEventListener('keydown', onKeyDown);
    };
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  const viewer = open ? (
    <div data-m6h-viewer role="dialog" aria-modal="true" aria-labelledby="m6h-viewer-title" className="fixed inset-0 z-[100] flex h-[100dvh] flex-col overscroll-none bg-black text-white">
      <header className="flex shrink-0 items-center gap-3 px-4 pb-3 pt-[max(1rem,env(safe-area-inset-top))]">
        <button ref={closeRef} data-m6h-touch type="button" onClick={close} aria-label="Fermer la radio plein écran" className="grid min-h-[52px] min-w-[52px] place-items-center rounded-2xl border border-slate-700 bg-slate-900 text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/70"><X size={22} /></button>
        <div className="min-w-0"><p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Panoramique</p><h2 id="m6h-viewer-title" className="truncate text-sm font-black text-white">Vue plein écran</h2></div>
      </header>

      <div ref={viewportRef} data-m6h-viewport onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerEnd} onPointerCancel={onPointerEnd} className="relative mx-3 min-h-0 flex-1 touch-none select-none overflow-hidden rounded-2xl bg-[#02050a]">
        <img ref={imageRef} data-m6h-image src={src} alt={alt} draggable={false} className="pointer-events-none absolute inset-0 h-full w-full object-contain will-change-transform" style={{ transform: `translate3d(${transform.x}px, ${transform.y}px, 0) scale(${transform.scale})`, transformOrigin: 'center center' }} />
      </div>

      <footer className="shrink-0 px-3 pb-[max(1rem,env(safe-area-inset-bottom))] pt-3">
        <div className="mx-auto grid max-w-md grid-cols-[52px_1fr_52px_92px] gap-2 rounded-[1.35rem] border border-slate-700 bg-slate-900/95 p-2">
          <button data-m6h-touch type="button" aria-label="Réduire le zoom" disabled={transform.scale <= PANORAMIC_MIN_SCALE} onClick={() => zoomBy(-PANORAMIC_SCALE_STEP)} className="grid min-h-[52px] min-w-[52px] place-items-center rounded-2xl bg-slate-800 text-white disabled:opacity-35"><Minus size={20} /></button>
          <div data-m6h-scale className="flex min-h-[52px] items-center justify-center rounded-2xl bg-slate-800 px-3 text-sm font-black text-white" aria-live="polite">{transform.scale.toFixed(transform.scale % 1 ? 1 : 0)}×</div>
          <button data-m6h-touch type="button" aria-label="Augmenter le zoom" disabled={transform.scale >= PANORAMIC_MAX_SCALE} onClick={() => zoomBy(PANORAMIC_SCALE_STEP)} className="grid min-h-[52px] min-w-[52px] place-items-center rounded-2xl bg-primary text-white disabled:opacity-35"><Plus size={20} /></button>
          <button data-m6h-touch type="button" aria-label="Réinitialiser le zoom à 1×" onClick={reset} className="inline-flex min-h-[52px] items-center justify-center gap-1.5 rounded-2xl bg-slate-800 px-3 text-[11px] font-black text-white"><RotateCcw size={15} /> 1×</button>
        </div>
        <p className="mt-2 text-center text-[10px] font-bold text-slate-400">Pincer pour zoomer · glisser pour déplacer</p>
      </footer>
    </div>
  ) : null;

  return (
    <>
      <div data-m6h-preview className="relative h-full w-full">
        <img src={src} alt={alt} className="block h-full max-h-[52dvh] min-h-[230px] w-full object-contain bg-black" />
        <button ref={openRef} data-m4b-touch data-m6h-touch data-m6h-open type="button" onClick={openViewer} aria-label="Agrandir la radio panoramique" className="absolute right-3 top-3 grid min-h-[52px] min-w-[52px] place-items-center rounded-2xl border border-white/30 bg-slate-950/75 text-white shadow-lg backdrop-blur-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/80"><Maximize2 size={20} /></button>
      </div>
      {viewer && createPortal(viewer, document.body)}
    </>
  );
};
