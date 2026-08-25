import { useEffect, useRef, useState } from 'react';

export interface SignaturePadProps {
  onSave: (dataUrl: string) => void;
  onCancel: () => void;
}

const configureContext = (ctx: CanvasRenderingContext2D, dpr: number) => {
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.strokeStyle = '#1e1b4b';
  ctx.lineWidth = 3.5;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
};

export function SignaturePad({ onSave, onCancel: _onCancel }: SignaturePadProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const drawingRef = useRef(false);
  const [hasInk, setHasInk] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const resizeCanvas = () => {
      const rect = canvas.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      const dpr = Math.max(1, window.devicePixelRatio || 1);
      const targetWidth = Math.max(1, Math.round(rect.width * dpr));
      const targetHeight = Math.max(1, Math.round(rect.height * dpr));
      if (canvas.width === targetWidth && canvas.height === targetHeight) {
        const current = canvas.getContext('2d');
        if (current) configureContext(current, dpr);
        return;
      }

      const snapshot = document.createElement('canvas');
      snapshot.width = canvas.width;
      snapshot.height = canvas.height;
      const snapshotCtx = snapshot.getContext('2d');
      if (snapshotCtx && canvas.width && canvas.height) snapshotCtx.drawImage(canvas, 0, 0);

      canvas.width = targetWidth;
      canvas.height = targetHeight;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      configureContext(ctx, dpr);
      if (snapshot.width && snapshot.height) {
        ctx.drawImage(snapshot, 0, 0, snapshot.width, snapshot.height, 0, 0, rect.width, rect.height);
      }
    };

    resizeCanvas();
    const observer = new ResizeObserver(resizeCanvas);
    observer.observe(canvas);
    window.addEventListener('orientationchange', resizeCanvas);
    return () => {
      observer.disconnect();
      window.removeEventListener('orientationchange', resizeCanvas);
    };
  }, []);

  const point = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  };

  const startDrawing = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    const p = point(e);
    if (!canvas || !p) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    canvas.setPointerCapture(e.pointerId);
    ctx.beginPath();
    ctx.moveTo(p.x, p.y);
    drawingRef.current = true;
  };

  const draw = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!drawingRef.current) return;
    const canvas = canvasRef.current;
    const p = point(e);
    if (!canvas || !p) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.lineTo(p.x, p.y);
    ctx.stroke();
    if (!hasInk) setHasInk(true);
  };

  const stopDrawing = (e?: React.PointerEvent<HTMLCanvasElement>) => {
    if (e?.currentTarget.hasPointerCapture(e.pointerId)) e.currentTarget.releasePointerCapture(e.pointerId);
    drawingRef.current = false;
  };

  const clear = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.restore();
    setHasInk(false);
  };

  const save = () => {
    const canvas = canvasRef.current;
    if (!canvas || !hasInk) return;
    onSave(canvas.toDataURL('image/png'));
  };

  return (
    <div className="space-y-4">
      <div className="border border-border-main rounded-2xl bg-white overflow-hidden shadow-inner relative">
        <canvas
          ref={canvasRef}
          className="w-full h-[210px] bg-slate-50 touch-none cursor-crosshair"
          aria-label="Zone de signature du patient"
          onPointerDown={startDrawing}
          onPointerMove={draw}
          onPointerUp={stopDrawing}
          onPointerCancel={stopDrawing}
        />
        <div className="absolute bottom-2 left-4 right-4 pointer-events-none text-center">
          <p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Signez avec votre doigt ici</p>
        </div>
      </div>
      <p className="text-[10px] text-center font-bold text-text-muted" aria-live="polite">
        {hasInk ? 'Signature prête à enregistrer' : 'Tracez la signature avant de l’enregistrer'}
      </p>
      <div className="flex gap-2">
        <button type="button" onClick={clear} className="flex-1 min-h-12 border border-border-main text-xs font-bold rounded-xl active:scale-95 transition-transform text-slate-600 bg-white">Effacer</button>
        <button type="button" onClick={save} disabled={!hasInk} className="flex-1 min-h-12 bg-primary text-white text-xs font-bold rounded-xl active:scale-95 transition-all shadow-md disabled:opacity-40 disabled:shadow-none disabled:active:scale-100">Enregistrer</button>
      </div>
    </div>
  );
}
