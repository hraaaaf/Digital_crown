import { useEffect, useRef, useState } from 'react';
import { Camera, CheckCircle2, RotateCcw, Send, ShieldCheck } from 'lucide-react';

import type { PatientPairing } from './PatientCompanionStorage';
import { prepareEmergencyPhoto } from './PatientCompanionEmergencyPhotoPrep';
import { sendRemoteCommand } from './PatientCompanionRemoteCommandTransport';

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
  const [candidates, setCandidates] = useState<Array<{ imageB64: string; byteSize: number }>>([]);
  const [error, setError] = useState<string | null>(null);
  const [idempotencyKey, setIdempotencyKey] = useState<string | null>(null);

  const clearPreview = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setCandidates([]);
    setError(null);
    setIdempotencyKey(null);
    setState('idle');
    if (inputRef.current) inputRef.current.value = '';
  };

  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
  }, [previewUrl]);

  useEffect(() => {
    if (!enabled && state !== 'idle') clearPreview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled]);

  const choose = async (file?: File) => {
    if (!file) return;
    setError(null);
    try {
      const prepared = await prepareEmergencyPhoto(file);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(prepared.previewUrl);
      setCandidates(prepared.candidates);
      setIdempotencyKey(crypto.randomUUID());
      setState('preview');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Photo impossible à préparer.');
      setState('error');
    }
  };

  const send = async () => {
    if (!enabled || !candidates.length) return;
    const key = idempotencyKey || crypto.randomUUID();
    setIdempotencyKey(key);
    setState('sending');
    setError(null);

    for (const candidate of candidates) {
      try {
        const result = await sendRemoteCommand(
          pairing,
          'emergency-photo',
          'emergency_photo.submit',
          {
            image_b64: candidate.imageB64,
            captured_at: new Date().toISOString(),
          },
          key,
        );
        if (result.status !== 'ACCEPTED' || result.result.state !== 'received') {
          setState('error');
          setError('Le cabinet n’a pas accepté cette photo.');
          return;
        }
        setState('success');
        return;
      } catch (cause) {
        const tagged = cause as Error & { remotePayloadTooLarge?: boolean; remotePending?: boolean };
        if (tagged.remotePayloadTooLarge) continue;
        if (tagged.remotePending) {
          setState('pending');
          setError(null);
          return;
        }
        setState('error');
        setError(tagged.message || 'Envoi impossible.');
        return;
      }
    }

    setState('error');
    setError('La photo reste trop volumineuse pour le canal sécurisé.');
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

      {enabled && previewUrl && ['preview', 'sending', 'pending', 'error', 'success'].includes(state) && (
        <div className="mt-4">
          <img
            src={previewUrl}
            alt="Aperçu de la photo à envoyer"
            className="max-h-72 w-full rounded-2xl border border-border-main object-contain bg-background"
          />

          {state === 'preview' && (
            <div className="mt-3 grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={clearPreview}
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

          {state === 'sending' && (
            <div role="status" className="mt-3 rounded-2xl bg-background p-3 text-xs font-black text-text-muted">
              Envoi sécurisé au cabinet…
            </div>
          )}

          {state === 'pending' && (
            <div role="status" className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 p-3 text-xs font-black text-amber-900">
              Envoi transmis · confirmation du cabinet encore en attente.
            </div>
          )}

          {state === 'success' && (
            <div role="status" className="mt-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-xs font-black text-emerald-900">
              <CheckCircle2 size={16} className="mr-2 inline" aria-hidden="true" />
              Photo reçue par le cabinet.
            </div>
          )}

          {state === 'error' && error && (
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
