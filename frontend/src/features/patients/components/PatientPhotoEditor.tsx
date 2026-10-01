import { useEffect, useMemo, useRef, useState } from 'react';
import type { KeyboardEvent } from 'react';
import { createPortal } from 'react-dom';
import { Camera, ImagePlus, Loader2, Trash2, X, Check, ZoomIn } from 'lucide-react';
import { api } from '../../../services/api';

type PatientPhotoEditorProps = {
  patientId: string | number;
  firstName: string;
  lastName: string;
  initialHasPhoto?: boolean;
};

type CropState = {
  src: string;
  sourceName: string;
};

const MAX_CLIENT_BYTES = 12 * 1024 * 1024;
const ACCEPTED_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp']);

function revokeObjectUrl(url: string | null) {
  if (url?.startsWith('blob:')) URL.revokeObjectURL(url);
}

async function imageFromSource(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error('Image illisible'));
    image.src = src;
  });
}

async function cropToJpeg(
  src: string,
  zoom: number,
  offsetX: number,
  offsetY: number,
): Promise<Blob> {
  const image = await imageFromSource(src);
  const size = 768;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('Recadrage indisponible');

  const baseScale = Math.max(size / image.naturalWidth, size / image.naturalHeight);
  const scale = baseScale * zoom;
  const drawnWidth = image.naturalWidth * scale;
  const drawnHeight = image.naturalHeight * scale;
  const overflowX = Math.max(0, drawnWidth - size);
  const overflowY = Math.max(0, drawnHeight - size);
  const x = (size - drawnWidth) / 2 + (offsetX / 100) * (overflowX / 2);
  const y = (size - drawnHeight) / 2 + (offsetY / 100) * (overflowY / 2);

  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, size, size);
  ctx.drawImage(image, x, y, drawnWidth, drawnHeight);

  return new Promise((resolve, reject) => {
    canvas.toBlob(
      blob => blob ? resolve(blob) : reject(new Error('Recadrage indisponible')),
      'image/jpeg',
      0.9,
    );
  });
}

export function PatientPhotoEditor({
  patientId,
  firstName,
  lastName,
  initialHasPhoto = false,
}: PatientPhotoEditorProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const importButtonRef = useRef<HTMLButtonElement>(null);
  const cameraButtonRef = useRef<HTMLButtonElement>(null);
  const cameraDialogRef = useRef<HTMLDivElement>(null);
  const cropDialogRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const previewUrlRef = useRef<string | null>(null);

  const [hasPhoto, setHasPhoto] = useState(initialHasPhoto);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [crop, setCrop] = useState<CropState | null>(null);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraError, setCameraError] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [zoom, setZoom] = useState(1);
  const [offsetX, setOffsetX] = useState(0);
  const [offsetY, setOffsetY] = useState(0);
  const lastTriggerRef = useRef<'import' | 'camera'>('import');

  const returnFocus = () => {
    requestAnimationFrame(() => {
      (lastTriggerRef.current === 'camera' ? cameraButtonRef.current : importButtonRef.current)?.focus();
    });
  };

  const trapDialogKey = (event: KeyboardEvent<HTMLDivElement>, close: () => void) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      close();
      returnFocus();
      return;
    }
    if (event.key !== 'Tab') return;
    const focusable = Array.from(
      event.currentTarget.querySelectorAll<HTMLElement>(
        'button:not([disabled]), input:not([disabled]), [href], [tabindex]:not([tabindex="-1"])',
      ),
    ).filter(node => !node.hasAttribute('aria-hidden'));
    if (!focusable.length) return;
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

  const initials = useMemo(() => {
    const first = firstName.trim().charAt(0);
    const last = lastName.trim().charAt(0);
    return (first + last).toUpperCase() || 'P';
  }, [firstName, lastName]);

  useEffect(() => {
    setHasPhoto(initialHasPhoto);
  }, [initialHasPhoto]);

  useEffect(() => {
    let cancelled = false;
    if (!hasPhoto) {
      revokeObjectUrl(previewUrlRef.current);
      previewUrlRef.current = null;
      setPreviewUrl(null);
      return;
    }

    api.get(`/patients/${patientId}/photo`, { responseType: 'blob' })
      .then(response => {
        if (cancelled) return;
        const next = URL.createObjectURL(response.data);
        revokeObjectUrl(previewUrlRef.current);
        previewUrlRef.current = next;
        setPreviewUrl(next);
      })
      .catch(() => {
        if (!cancelled) {
          setPreviewUrl(null);
          setHasPhoto(false);
        }
      });

    return () => { cancelled = true; };
  }, [hasPhoto, patientId]);

  useEffect(() => () => {
    streamRef.current?.getTracks().forEach(track => track.stop());
    revokeObjectUrl(previewUrlRef.current);
  }, []);

  useEffect(() => {
    if (cameraOpen) cameraDialogRef.current?.focus();
  }, [cameraOpen]);

  useEffect(() => {
    if (crop) cropDialogRef.current?.focus();
  }, [crop]);

  const resetCropControls = () => {
    setZoom(1);
    setOffsetX(0);
    setOffsetY(0);
  };

  const closeCrop = () => {
    if (crop?.src.startsWith('blob:')) URL.revokeObjectURL(crop.src);
    setCrop(null);
    resetCropControls();
  };

  const openCropFromBlob = (blob: Blob, sourceName: string) => {
    const src = URL.createObjectURL(blob);
    lastTriggerRef.current = sourceName === 'camera.jpg' ? 'camera' : 'import';
    setCrop({ src, sourceName });
    resetCropControls();
    setError('');
  };

  const handleFile = (file?: File) => {
    if (!file) return;
    setError('');
    if (!ACCEPTED_TYPES.has(file.type)) {
      setError('Format non pris en charge. Utilisez JPEG, PNG ou WebP.');
      return;
    }
    if (file.size > MAX_CLIENT_BYTES) {
      setError('La photo dépasse la limite de 12 MiB.');
      return;
    }
    openCropFromBlob(file, file.name);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach(track => track.stop());
    streamRef.current = null;
    setCameraOpen(false);
  };

  const closeCamera = () => {
    stopCamera();
    returnFocus();
  };

  const openCamera = async () => {
    lastTriggerRef.current = 'camera';
    setCameraError('');
    setError('');
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError('Aucune caméra accessible depuis ce poste.');
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 1280 } },
        audio: false,
      });
      streamRef.current = stream;
      setCameraOpen(true);
      requestAnimationFrame(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          void videoRef.current.play();
        }
      });
    } catch {
      setCameraError('Accès caméra refusé ou indisponible. Vous pouvez importer une photo.');
    }
  };

  const captureCamera = async () => {
    const video = videoRef.current;
    if (!video || !video.videoWidth || !video.videoHeight) {
      setCameraError('La caméra n’est pas encore prête.');
      return;
    }
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      setCameraError('Capture caméra indisponible.');
      return;
    }
    ctx.drawImage(video, 0, 0);
    const blob = await new Promise<Blob | null>(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.92));
    if (!blob) {
      setCameraError('Capture caméra indisponible.');
      return;
    }
    stopCamera();
    openCropFromBlob(blob, 'camera.jpg');
  };

  const saveCrop = async () => {
    if (!crop || busy) return;
    setBusy(true);
    setError('');
    try {
      const jpeg = await cropToJpeg(crop.src, zoom, offsetX, offsetY);
      const data = new FormData();
      data.append('file', new File([jpeg], 'patient-profile.jpg', { type: 'image/jpeg' }));
      await api.post(`/patients/${patientId}/photo`, data);
      closeCrop();
      setHasPhoto(true);
      returnFocus();
    } catch {
      setError('La photo n’a pas pu être enregistrée. Réessayez.');
    } finally {
      setBusy(false);
    }
  };

  const removePhoto = async () => {
    if (!hasPhoto || busy) return;
    setBusy(true);
    setError('');
    try {
      await api.delete(`/patients/${patientId}/photo`);
      setHasPhoto(false);
      revokeObjectUrl(previewUrlRef.current);
      previewUrlRef.current = null;
      setPreviewUrl(null);
    } catch {
      setError('La photo n’a pas pu être supprimée.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <section
      aria-labelledby="patient-photo-title"
      data-patient-photo-editor
      className="rounded-[2rem] border border-blue-100 bg-gradient-to-br from-blue-50/70 via-white to-white p-5 sm:p-6"
    >
      <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
        <div className="mx-auto shrink-0 sm:mx-0">
          <div className="relative h-28 w-28 overflow-hidden rounded-full border-4 border-white bg-[#003380] shadow-xl shadow-[#003380]/15">
            {previewUrl ? (
              <img
                src={previewUrl}
                alt={`Photo de ${firstName} ${lastName}`}
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="flex h-full w-full items-center justify-center text-3xl font-black tracking-tight text-white" aria-label="Initiales du patient">
                {initials}
              </div>
            )}
          </div>
        </div>

        <div className="min-w-0 flex-1 text-center sm:text-left">
          <h3 id="patient-photo-title" className="text-lg font-black text-[#003380]">Photo du patient</h3>
          <p className="mt-1 text-sm leading-relaxed text-slate-500">
            Une photo récente facilite l’identification au cabinet. Elle reste privée et liée au dossier.
          </p>

          <div className="mt-4 grid grid-cols-1 gap-2 sm:flex sm:flex-wrap">
            <button
              ref={importButtonRef}
              type="button"
              onClick={() => {
                lastTriggerRef.current = 'import';
                fileInputRef.current?.click();
              }}
              disabled={busy}
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-[#003380] px-4 py-2.5 text-xs font-black uppercase tracking-wider text-white shadow-md transition hover:bg-blue-900 disabled:opacity-50"
            >
              <ImagePlus size={16} /> Importer
            </button>
            <button
              ref={cameraButtonRef}
              type="button"
              onClick={openCamera}
              disabled={busy}
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-blue-200 bg-white px-4 py-2.5 text-xs font-black uppercase tracking-wider text-[#003380] transition hover:bg-blue-50 disabled:opacity-50"
            >
              <Camera size={16} /> Prendre une photo
            </button>
            {hasPhoto && (
              <button
                type="button"
                onClick={removePhoto}
                disabled={busy}
                className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-xs font-black uppercase tracking-wider text-rose-600 transition hover:bg-rose-50 disabled:opacity-50"
              >
                <Trash2 size={16} /> Supprimer
              </button>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="sr-only"
            aria-label="Importer une photo du patient"
            onChange={event => handleFile(event.target.files?.[0])}
          />
        </div>
      </div>

      {(error || cameraError) && (
        <p role="alert" className="mt-4 rounded-xl bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700">
          {error || cameraError}
        </p>
      )}

      {cameraOpen && createPortal(
        <div
          ref={cameraDialogRef}
          tabIndex={-1}
          onKeyDown={event => trapDialogKey(event, closeCamera)}
          className="fixed inset-0 z-[90] flex items-center justify-center bg-slate-950/70 p-4 outline-none"
          role="dialog"
          aria-modal="true"
          aria-label="Prendre une photo"
        >
          <div className="w-full max-w-lg rounded-[2rem] bg-white p-4 shadow-2xl sm:p-6">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h3 className="text-xl font-black text-[#003380]">Prendre une photo</h3>
                <p className="text-sm text-slate-500">Placez le visage au centre du cadre.</p>
              </div>
              <button type="button" aria-label="Fermer la caméra" onClick={closeCamera} className="rounded-full p-2 text-slate-500 hover:bg-slate-100">
                <X size={20} />
              </button>
            </div>
            <div className="aspect-square overflow-hidden rounded-2xl bg-slate-950">
              <video ref={videoRef} autoPlay muted playsInline className="h-full w-full object-cover" />
            </div>
            <button type="button" onClick={captureCamera} className="mt-4 flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-[#003380] font-black text-white">
              <Camera size={18} /> Capturer
            </button>
          </div>
        </div>,
        document.body,
      )}

      {crop && createPortal(
        <div
          ref={cropDialogRef}
          tabIndex={-1}
          onKeyDown={event => trapDialogKey(event, () => { closeCrop(); returnFocus(); })}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/70 p-3 sm:p-5 outline-none"
          role="dialog"
          aria-modal="true"
          aria-label="Recadrer la photo"
        >
          <div className="max-h-[96vh] w-full max-w-xl overflow-y-auto rounded-[2rem] bg-white p-4 shadow-2xl sm:p-6">
            <div className="mb-4 flex items-start justify-between gap-4">
              <div>
                <h3 className="text-xl font-black text-[#003380]">Recadrer la photo</h3>
                <p className="mt-1 text-sm text-slate-500">Ajustez le visage dans le cadre carré.</p>
              </div>
              <button type="button" aria-label="Annuler le recadrage" onClick={() => { closeCrop(); returnFocus(); }} disabled={busy} className="rounded-full p-2 text-slate-500 hover:bg-slate-100">
                <X size={20} />
              </button>
            </div>

            <div className="mx-auto aspect-square w-full max-w-sm overflow-hidden rounded-2xl bg-slate-100">
              <img
                src={crop.src}
                alt="Aperçu à recadrer"
                className="h-full w-full object-cover"
                style={{
                  transform: `scale(${zoom}) translate(${offsetX / zoom}%, ${offsetY / zoom}%)`,
                  transformOrigin: 'center',
                }}
              />
            </div>

            <div className="mt-5 space-y-4">
              <label className="block">
                <span className="mb-2 flex items-center gap-2 text-xs font-black uppercase tracking-wider text-slate-500"><ZoomIn size={14}/> Zoom</span>
                <input aria-label="Zoom de la photo" type="range" min="1" max="2.5" step="0.05" value={zoom} onChange={e => setZoom(Number(e.target.value))} className="w-full" />
              </label>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <label>
                  <span className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Horizontal</span>
                  <input aria-label="Position horizontale" type="range" min="-100" max="100" value={offsetX} onChange={e => setOffsetX(Number(e.target.value))} className="w-full" />
                </label>
                <label>
                  <span className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-500">Vertical</span>
                  <input aria-label="Position verticale" type="range" min="-100" max="100" value={offsetY} onChange={e => setOffsetY(Number(e.target.value))} className="w-full" />
                </label>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-2 sm:grid-cols-2">
              <button type="button" onClick={() => { closeCrop(); returnFocus(); }} disabled={busy} className="min-h-12 rounded-xl border border-slate-200 font-black text-slate-600 hover:bg-slate-50 disabled:opacity-50">
                Annuler
              </button>
              <button type="button" onClick={saveCrop} disabled={busy} className="flex min-h-12 items-center justify-center gap-2 rounded-xl bg-[#003380] font-black text-white disabled:opacity-50">
                {busy ? <Loader2 className="animate-spin" size={18}/> : <Check size={18}/>}
                {busy ? 'Enregistrement…' : 'Enregistrer la photo'}
              </button>
            </div>
          </div>
        </div>,
        document.body,
      )}
    </section>
  );
}
