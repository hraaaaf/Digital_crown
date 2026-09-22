import { useEffect, useRef, useState } from 'react';
import { Camera, CheckCircle2, RotateCcw, Send, ShieldCheck } from 'lucide-react';

import {
  PatientCompanionStorage,
  type PatientEmergencyPhotoQueueState,
  type PatientPairing,
} from './PatientCompanionStorage';
import { prepareEmergencyPhoto } from './PatientCompanionEmergencyPhotoPrep';
import { uploadEmergencyPhoto } from './PatientCompanionEmergencyPhotoTransport';

type State = 'idle' | 'preview' | 'sending' | 'pending' | 'success' | 'error';

export const PatientCompanionEmergencyPhoto = ({
  pairing,
  enabled,
}: {
  pairing: PatientPairing;
  enabled: boolean;
}) => {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [state, setState] = useState<State>('idle');
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [bytes, setBytes] = useState<Uint8Array<ArrayBuffer> | null>(null);
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [capturedAt, setCapturedAt] = useState<string | null>(null);
  const [progress, setProgress] = useState<{ sent: number; total: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const queueUpsert = async (item: PatientEmergencyPhotoQueueState) => {
    const vault = await PatientCompanionStorage.load();
    const accessId = pairing.context.access_id;
    const existing = vault.cache[accessId]?.emergencyPhotos || [];
    await PatientCompanionStorage.saveEmergencyPhotoQueue(
      accessId,
      [...existing.filter(entry => entry.uploadId !== item.uploadId), item],
    );
  };

  const queueRemove = async (id: string) => {
    const vault = await PatientCompanionStorage.load();
    const accessId = pairing.context.access_id;
    const existing = vault.cache[accessId]?.emergencyPhotos || [];
    await PatientCompanionStorage.saveEmergencyPhotoQueue(
      accessId,
      existing.filter(entry => entry.uploadId !== id),
    );
  };

  const clearVisual = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setBytes(null);
    setUploadId(null);
    setCapturedAt(null);
    setProgress(null);
    setError(null);
    setState('idle');
    if (inputRef.current) inputRef.current.value = '';
  };

  const discardCurrent = async () => {
    const current = uploadId;
    clearVisual();
    if (!current) return;
    await PatientCompanionStorage.deleteEmergencyPhotoBytes(current).catch(() => undefined);
    await queueRemove(current).catch(() => undefined);
  };

  useEffect(() => {
    let cancelled = false;
    const restore = async () => {
      try {
        const vault = await PatientCompanionStorage.load();
        const pending = (vault.cache[pairing.context.access_id]?.emergencyPhotos || [])
          .find(item => item.state !== 'received' && item.state !== 'rejected');
        if (!pending) return;
        const stored = await PatientCompanionStorage.readEmergencyPhotoBytes(
          pairing.context.access_id,
          pending.uploadId,
        );
        if (!stored || cancelled) return;
        const url = URL.createObjectURL(new Blob([stored], { type: 'image/jpeg' }));
        setPreviewUrl(url);
        setBytes(stored);
        setUploadId(pending.uploadId);
        setCapturedAt(pending.capturedAt);
        setState(pending.state === 'local_pending' ? 'preview' : 'pending');
      } catch {
        // Local recovery is best-effort; never invent a delivered state.
      }
    };
    void restore();
    return () => { cancelled = true; };
  }, [pairing.context.access_id]);

  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
  }, [previewUrl]);

  const choose = async (file?: File) => {
    if (!file) return;
    setError(null);
    try {
      const prepared = await prepareEmergencyPhoto(file);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      const id = crypto.randomUUID();
      const captured = new Date().toISOString();
      await PatientCompanionStorage.saveEmergencyPhotoBytes(
        pairing.context.access_id,
        id,
        prepared.bytes,
      );
      const now = new Date().toISOString();
      await queueUpsert({
        uploadId: id,
        state: 'local_pending',
        byteSize: prepared.byteSize,
        capturedAt: captured,
        createdAt: now,
        updatedAt: now,
      });
      setPreviewUrl(prepared.previewUrl);
      setBytes(prepared.bytes);
      setUploadId(id);
      setCapturedAt(captured);
      setProgress(null);
      setState('preview');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Photo impossible à préparer.');
      setState('error');
    }
  };

  const send = async () => {
    if (!enabled || !uploadId || !capturedAt) return;
    let source = bytes;
    if (!source) {
      source = await PatientCompanionStorage.readEmergencyPhotoBytes(
        pairing.context.access_id,
        uploadId,
      );
    }
    if (!source) {
      setState('error');
      setError('La copie locale de la photo est introuvable.');
      return;
    }

    const now = new Date().toISOString();
    await queueUpsert({
      uploadId,
      state: 'remote_uploading',
      byteSize: source.byteLength,
      capturedAt,
      createdAt: now,
      updatedAt: now,
    });
    setState('sending');
    setError(null);

    try {
      const result = await uploadEmergencyPhoto(
        pairing,
        uploadId,
        source,
        capturedAt,
        current => setProgress({ sent: current.sentChunks, total: current.totalChunks }),
      );
      await queueUpsert({
        uploadId,
        state: 'received',
        byteSize: source.byteLength,
        capturedAt,
        createdAt: now,
        updatedAt: new Date().toISOString(),
      });
      await PatientCompanionStorage.deleteEmergencyPhotoBytes(uploadId);
      setState('success');
      setProgress(null);
    } catch (cause) {
      const tagged = cause as Error & { remotePending?: boolean };
      if (tagged.remotePending) {
        await queueUpsert({
          uploadId,
          state: 'remote_pending_ack',
          byteSize: source.byteLength,
          capturedAt,
          createdAt: now,
          updatedAt: new Date().toISOString(),
        });
        setState('pending');
        setError(null);
        return;
      }
      await queueUpsert({
        uploadId,
        state: 'local_pending',
        byteSize: source.byteLength,
        capturedAt,
        createdAt: now,
        updatedAt: new Date().toISOString(),
        errorCode: 'UPLOAD_FAILED',
      });
      setState('error');
      setError(tagged.message || 'Envoi impossible.');
    }
  };

  return (
    <section
      data-pc07-emergency-photo
      className="mt-4 rounded-[28px] border border-border-main bg-card-bg p-5 shadow-sm"
      aria-labelledby="pc07-title"
    >
      <div className="flex items-start gap-3">
        <div className="rounded-2xl bg-rose-50 p-2.5 text-rose-700">
          <Camera size={20} aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <h2 id="pc07-title" className="text-base font-black">Photo d’urgence</h2>
          <p className="mt-1 text-xs font-bold text-text-muted">
            Envoyez une photo au cabinet sans diagnostic automatique.
          </p>
        </div>
      </div>

      {!enabled && (
        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-3 text-xs font-bold text-amber-900">
          Reconnexion sécurisée au cabinet requise avant l’envoi.
        </div>
      )}

      {enabled && state === 'idle' && (
        <>
          <input
            ref={inputRef}
            className="sr-only"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            capture="environment"
            onChange={event => void choose(event.target.files?.[0])}
          />
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="mt-4 min-h-[48px] w-full rounded-2xl bg-primary px-4 text-sm font-black text-white"
          >
            <Camera size={17} className="mr-2 inline" aria-hidden="true" />
            Prendre ou choisir une photo
          </button>
          <p className="mt-3 flex items-start gap-2 text-[11px] font-bold text-text-muted">
            <ShieldCheck size={15} className="mt-0.5 shrink-0" aria-hidden="true" />
            La photo est chiffrée pendant le transport et enregistrée uniquement après confirmation du cabinet.
          </p>
        </>
      )}

      {previewUrl && ['preview', 'sending', 'pending', 'error', 'success'].includes(state) && (
        <div className="mt-4">
          <img
            src={previewUrl}
            alt="Aperçu de la photo à envoyer"
            className="max-h-72 w-full rounded-2xl border border-border-main bg-background object-contain"
          />

          {enabled && state === 'preview' && (
            <div className="mt-3 grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => void discardCurrent()}
                className="min-h-[48px] rounded-2xl border border-border-main bg-background px-3 text-xs font-black"
              >
                <RotateCcw size={15} className="mr-2 inline" aria-hidden="true" />
                Reprendre
              </button>
              <button
                type="button"
                onClick={() => void send()}
                className="min-h-[48px] rounded-2xl bg-primary px-3 text-xs font-black text-white"
              >
                <Send size={15} className="mr-2 inline" aria-hidden="true" />
                Envoyer au cabinet
              </button>
            </div>
          )}

          {enabled && state === 'sending' && (
            <div role="status" className="mt-3 rounded-2xl bg-background p-3 text-xs font-black text-text-muted">
              Envoi sécurisé au cabinet…
              {progress && <span className="ml-1">({progress.sent}/{progress.total})</span>}
            </div>
          )}

          {enabled && state === 'pending' && (
            <div role="status" className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 p-3 text-xs font-black text-amber-900">
              <p>Envoi en attente · aucune réception cabinet n’est encore confirmée.</p>
              <button
                type="button"
                onClick={() => void send()}
                className="mt-3 min-h-[44px] w-full rounded-xl border border-amber-200 bg-white px-3 text-xs font-black text-amber-900"
              >
                Reprendre l’envoi
              </button>
            </div>
          )}

          {state === 'success' && (
            <div role="status" className="mt-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-xs font-black text-emerald-900">
              <p>
                <CheckCircle2 size={16} className="mr-2 inline" aria-hidden="true" />
                Photo reçue par le cabinet.
              </p>
              <button
                type="button"
                onClick={() => void discardCurrent()}
                className="mt-3 min-h-[44px] w-full rounded-xl border border-emerald-200 bg-white px-3 text-xs font-black text-emerald-900"
              >
                Envoyer une autre photo
              </button>
            </div>
          )}

          {enabled && state === 'error' && error && (
            <div role="alert" className="mt-3 rounded-2xl border border-rose-200 bg-rose-50 p-3">
              <p className="text-xs font-black text-rose-800">{error}</p>
              <button
                type="button"
                onClick={() => void send()}
                className="mt-3 min-h-[44px] w-full rounded-xl border border-rose-200 bg-white px-3 text-xs font-black text-rose-800"
              >
                Réessayer
              </button>
            </div>
          )}
        </div>
      )}
    </section>
  );
};
