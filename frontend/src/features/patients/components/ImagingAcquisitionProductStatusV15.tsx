import { useEffect, useState } from 'react';
import { api } from '../../../services/api';

type ClosedStatus = {
  schema_version: 'dc06-product-status-v1';
  state: 'NATIVE_IPC_NOT_CONNECTED';
  read_only: true;
  acquisition_enabled: false;
  clinical_receipt_authorized: false;
  pending_captures: null;
  reason: 'WINDOWS_IPC_AND_TPM_PRODUCT_GATE_NOT_VERIFIED';
};

const isClosed = (input: unknown): input is ClosedStatus => {
  if (!input || typeof input !== 'object') return false;
  const v = input as Record<string, unknown>;
  return v.schema_version === 'dc06-product-status-v1' &&
    v.state === 'NATIVE_IPC_NOT_CONNECTED' &&
    v.read_only === true && v.acquisition_enabled === false &&
    v.clinical_receipt_authorized === false && v.pending_captures === null &&
    v.reason === 'WINDOWS_IPC_AND_TPM_PRODUCT_GATE_NOT_VERIFIED';
};

/** Mounted on the real patient screen, never calls the isolated LAB endpoints. */
export function ImagingAcquisitionProductStatusV15({ patientId }: { patientId: number }) {
  const [result, setResult] = useState<'loading' | 'blocked' | 'unavailable'>('loading');
  useEffect(() => {
    let current = true;
    setResult('loading');
    void api.get(`/patients/${patientId}/acquisition/status`)
      .then(reply => { if (current) setResult(isClosed(reply.data) ? 'blocked' : 'unavailable'); })
      .catch(() => { if (current) setResult('unavailable'); });
    return () => { current = false; };
  }, [patientId]);

  return (
    <section aria-label="Acquisition depuis appareil" data-testid="dc06-acquisition-status"
      className="mx-1 mb-3 rounded-xl border border-border-main bg-card px-3 py-2.5 sm:px-4">
      <h3 className="text-sm font-bold text-text-main">Acquisition depuis appareil</h3>
      {result === 'loading' ? (
        <p role="status" className="mt-1 text-xs text-text-muted">Vérification sécurisée de la connexion…</p>
      ) : result === 'blocked' ? (
        <p role="status" className="mt-1 text-xs text-text-muted">
          Connexion appareil non activée. Aucune image ne peut être associée automatiquement à ce dossier.
        </p>
      ) : (
        <p role="alert" className="mt-1 text-xs text-text-muted">
          État d'acquisition indisponible. Aucune capture ni association patient n'est autorisée.
        </p>
      )}
    </section>
  );
}
