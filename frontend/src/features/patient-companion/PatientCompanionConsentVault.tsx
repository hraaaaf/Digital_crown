import { useEffect, useMemo, useState } from 'react';
import { FileCheck2, Loader2 } from 'lucide-react';
import { API_BASE } from '../../services/api';
import { SignaturePad } from '../mobile/Dashboard/components/SignaturePad';
import type { PatientPairing } from './PatientCompanionStorage';
import { PatientCompanionConsentTransport } from './PatientCompanionConsentTransport';

type ConsentItem = {
  consent_id: string;
  share_id: string;
  title: string;
  document_type: string;
  document_version: number;
  state: 'PENDING' | 'SIGNED' | 'EXPIRED' | 'REVOKED';
  created_at: string;
  expires_at?: string | null;
  signed_at?: string | null;
  evidence_ref?: string | null;
  qualified_electronic_signature: false;
};

const stateLabel = (state: ConsentItem['state']) => {
  if (state === 'PENDING') return 'À signer';
  if (state === 'SIGNED') return 'Signature enregistrée';
  if (state === 'EXPIRED') return 'Expiré';
  return 'Révoqué';
};

export function PatientCompanionConsentVault({
  pairing,
  enabled,
}: {
  pairing: PatientPairing;
  enabled: boolean;
}) {
  const [items, setItems] = useState<ConsentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [openId, setOpenId] = useState<string | null>(null);
  const [readIds, setReadIds] = useState<Set<string>>(() => new Set());
  const [signing, setSigning] = useState(false);

  const openItem = useMemo(
    () => items.find(item => item.consent_id === openId) || null,
    [items, openId],
  );

  const load = async () => {
    setLoading(true);
    setMessage('');
    try {
      const accessId = encodeURIComponent(pairing.context.access_id);
      const response = await fetch(
        `${API_BASE}/api/patient-companion/contexts/${accessId}/consents`,
        {
          headers: { Authorization: `Bearer ${pairing.accessToken}` },
          cache: 'no-store',
        },
      );
      const body = await response.json().catch(() => ({}));
      if (!response.ok || !Array.isArray(body.items)) {
        throw new Error(body.detail || 'Consentements indisponibles.');
      }
      setItems(body.items);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Consentements indisponibles.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!enabled) return;
    void load();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, pairing.context.access_id, pairing.accessToken]);

  const readDocument = async (item: ConsentItem) => {
    setMessage('');
    const accessId = encodeURIComponent(pairing.context.access_id);
    const consentId = encodeURIComponent(item.consent_id);
    try {
      const response = await fetch(
        `${API_BASE}/api/patient-companion/contexts/${accessId}/consents/${consentId}/document`,
        {
          headers: { Authorization: `Bearer ${pairing.accessToken}` },
          cache: 'no-store',
        },
      );
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || 'Document indisponible.');
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank', 'noopener,noreferrer');
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
      setReadIds(current => new Set(current).add(item.consent_id));
      setOpenId(item.consent_id);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Document indisponible.');
    }
  };

  const sign = async (signatureBase64: string) => {
    if (!openItem || openItem.state !== 'PENDING' || !readIds.has(openItem.consent_id)) return;
    setSigning(true);
    setMessage('');
    try {
      const result = await PatientCompanionConsentTransport.sendConsentCommand(pairing, {
        consent_id: openItem.consent_id,
        signature_base64: signatureBase64,
      });
      if (
        result.status !== 'ACCEPTED'
        || result.result.code !== 'CONSENT_SIGNED'
        || result.result.status !== 'SIGNED'
        || result.result.qualified_electronic_signature !== false
      ) {
        throw new Error(String(result.result.code || 'Signature refusée par le cabinet.'));
      }
      setOpenId(null);
      await load();
      setMessage('Signature enregistrée par le cabinet pour cette version exacte du document.');
    } catch (error) {
      const pending = Boolean((error as { remotePending?: boolean } | null)?.remotePending);
      setMessage(
        pending
          ? 'Signature transmise · confirmation cabinet encore en attente. Le document reste affiché comme non signé.'
          : error instanceof Error
            ? error.message
            : 'Signature non envoyée.',
      );
    } finally {
      setSigning(false);
    }
  };

  return (
    <section data-pc04-consent-vault className="mt-4 rounded-[1.5rem] border border-border-main bg-card-bg p-4" aria-label="Consentements">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.14em] text-primary">Consent Vault</p>
          <h3 className="mt-0.5 text-lg font-black">Consentements</h3>
        </div>
        <FileCheck2 className="text-primary" size={22} />
      </div>

      <p className="mt-2 text-[11px] font-bold text-text-muted">
        Votre signature sera liée à la version exacte du document présenté.
      </p>
      <p className="mt-1 text-[10px] font-bold text-text-muted">
        Preuve applicative Digital Crown — ce statut n’est pas présenté comme une signature électronique qualifiée.
      </p>

      {!enabled && (
        <p className="mt-3 text-xs font-bold text-text-muted">
          Synchronisez votre espace pour vérifier les consentements à signer.
        </p>
      )}

      {enabled && loading && (
        <div className="mt-3 flex min-h-[48px] items-center gap-2 text-xs font-black text-text-muted">
          <Loader2 className="animate-spin" size={16} /> Chargement…
        </div>
      )}

      {enabled && !loading && items.length === 0 && !message && (
        <p className="mt-3 text-xs font-bold text-text-muted">Aucun consentement à signer.</p>
      )}

      <div className="mt-3 grid gap-2">
        {items.map(item => (
          <article key={item.consent_id} className="rounded-2xl border border-border-main bg-background p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="break-words text-sm font-black">{item.title}</p>
                <p className="mt-1 text-[10px] font-bold text-text-muted">
                  Version {item.document_version}
                </p>
              </div>
              <span className="max-w-[48%] rounded-full bg-primary/5 px-2.5 py-1 text-right text-[10px] font-black text-primary">
                {stateLabel(item.state)}
              </span>
            </div>

            {item.state === 'PENDING' && (
              <button
                type="button"
                onClick={() => void readDocument(item)}
                className="mt-3 min-h-[48px] w-full rounded-xl border border-primary/20 bg-card-bg text-xs font-black text-primary"
              >
                Lire le document
              </button>
            )}

            {item.state === 'SIGNED' && item.signed_at && (
              <p className="mt-2 text-[10px] font-bold text-text-muted">
                Enregistrée le {new Date(item.signed_at).toLocaleString()}
              </p>
            )}
          </article>
        ))}
      </div>

      {openItem && openItem.state === 'PENDING' && readIds.has(openItem.consent_id) && (
        <div data-pc04-signature className="mt-3 rounded-2xl border border-primary/15 bg-primary/5 p-4">
          <p className="text-sm font-black">{openItem.title}</p>
          <p className="mt-1 text-[11px] font-bold text-text-muted">
            Confirmez uniquement après lecture du document affiché.
          </p>
          {signing ? (
            <div className="mt-3 flex min-h-[96px] items-center justify-center gap-2 text-xs font-black text-text-muted">
              <Loader2 className="animate-spin" size={18} /> Enregistrement…
            </div>
          ) : (
            <div className="mt-3">
              <SignaturePad onSave={signature => void sign(signature)} onCancel={() => setOpenId(null)} />
              <button
                type="button"
                onClick={() => setOpenId(null)}
                className="mt-2 min-h-[48px] w-full rounded-xl border border-border-main bg-card-bg text-xs font-black text-text-muted"
              >
                Fermer sans signer
              </button>
            </div>
          )}
        </div>
      )}

      {message && (
        <p role="status" className="mt-3 rounded-xl bg-amber-50 px-3 py-2.5 text-[11px] font-black text-amber-800">
          {message}
        </p>
      )}
    </section>
  );
}
