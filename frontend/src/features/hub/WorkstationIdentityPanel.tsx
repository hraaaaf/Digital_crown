import { useEffect, useState } from 'react';
import { Link2, Pencil, RefreshCw, ShieldX } from 'lucide-react';
import {
  workstationModeService,
  type WorkstationRegistryEntry,
  type WorkstationState,
} from '../../services/workstationMode';

const shortId = (value: string) => value.slice(0, 8);

export const WorkstationIdentityPanel = ({ current }: { current: WorkstationState }) => {
  const [items, setItems] = useState<WorkstationRegistryEntry[]>([]);
  const [names, setNames] = useState<Record<string, string>>({});
  const [ownerPin, setOwnerPin] = useState('');
  const [pairing, setPairing] = useState<{ code: string; expiresAt: string } | null>(null);
  const [confirmRevokeId, setConfirmRevokeId] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [feedback, setFeedback] = useState('');

  const refresh = async () => {
    const next = await workstationModeService.listWorkstations();
    setItems(next);
    setNames(Object.fromEntries(next.map((item) => [item.workstationId, item.displayName || ''])));
  };

  useEffect(() => {
    void refresh().catch(() => {
      setFeedback('Impossible de charger la liste des postes.');
    });
  }, []);

  const requirePin = () => {
    if (!/^\d{4,8}$/.test(ownerPin)) {
      setFeedback('Saisissez le PIN propriétaire (4 à 8 chiffres).');
      return false;
    }
    return true;
  };

  const issuePairingCode = async () => {
    if (!requirePin()) return;
    setBusy('pairing');
    setFeedback('');
    try {
      const result = await workstationModeService.issuePairingCode(ownerPin);
      setPairing(result);
      setFeedback('Code généré. Il est à usage unique et expire dans 10 minutes.');
    } catch {
      setFeedback('Impossible de générer le code d’appairage.');
    } finally {
      setBusy(null);
    }
  };

  const rename = async (item: WorkstationRegistryEntry) => {
    if (!requirePin()) return;
    const nextName = (names[item.workstationId] || '').trim();
    if (!nextName) {
      setFeedback('Le nom du poste est requis.');
      return;
    }
    setBusy(`rename:${item.workstationId}`);
    setFeedback('');
    try {
      await workstationModeService.renameWorkstation(item.workstationId, nextName, ownerPin);
      await refresh();
      setFeedback('Nom du poste mis à jour. Son identifiant technique reste inchangé.');
    } catch {
      setFeedback('Renommage refusé.');
    } finally {
      setBusy(null);
    }
  };

  const revoke = async (item: WorkstationRegistryEntry) => {
    if (!requirePin()) return;
    if (confirmRevokeId !== item.workstationId) {
      setConfirmRevokeId(item.workstationId);
      setFeedback('Confirmez la révocation de ce poste.');
      return;
    }
    setBusy(`revoke:${item.workstationId}`);
    setFeedback('');
    try {
      await workstationModeService.revokeWorkstation(item.workstationId, ownerPin);
      setConfirmRevokeId(null);
      await refresh();
      setFeedback(item.workstationId === current.workstationId
        ? 'Ce poste a été révoqué. Il devra être appairé de nouveau.'
        : 'Poste révoqué.');
    } catch {
      setFeedback('Révocation refusée.');
    } finally {
      setBusy(null);
    }
  };

  return (
    <section data-workstation-identity className="mt-6 rounded-elite-lg border border-border-main bg-card-bg p-5 shadow-elite sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-primary">
            <Link2 size={18} aria-hidden="true" />
            <span className="text-xs font-black uppercase tracking-widest">Identité des postes</span>
          </div>
          <h2 className="mt-2 font-outfit text-lg font-black">Bornes et tablettes autorisées</h2>
          <p className="mt-1 text-sm font-semibold text-text-muted">
            Le nom est librement modifiable. L’identifiant technique reste stable et sert à la sécurité du poste.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void refresh()}
          className="inline-flex min-h-11 items-center gap-2 self-start rounded-elite-sm border border-border-main bg-main-bg px-3 text-xs font-black text-main"
        >
          <RefreshCw size={15} aria-hidden="true" /> Actualiser
        </button>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]">
        <label className="text-xs font-black uppercase tracking-wide text-text-muted">
          PIN propriétaire pour les actions sensibles
          <input
            type="password"
            inputMode="numeric"
            pattern="[0-9]*"
            value={ownerPin}
            onChange={(event) => setOwnerPin(event.target.value.replace(/\D/g, '').slice(0, 8))}
            className="mt-2 min-h-11 w-full rounded-elite-sm border border-border-main bg-main-bg px-3 text-sm font-semibold text-main outline-none focus:border-primary"
          />
        </label>
        <button
          type="button"
          disabled={busy !== null || !current.pinConfigured}
          onClick={issuePairingCode}
          className="self-end min-h-11 rounded-elite-sm bg-primary px-4 text-sm font-black text-card-bg disabled:opacity-50"
        >
          {busy === 'pairing' ? 'Génération…' : 'Nouveau code d’appairage'}
        </button>
      </div>

      {pairing && (
        <div className="mt-4 rounded-elite-sm border border-primary/20 bg-primary/5 p-4">
          <p className="text-xs font-black uppercase tracking-widest text-primary">Code temporaire</p>
          <p className="mt-2 font-outfit text-3xl font-black tracking-widest text-main">{pairing.code}</p>
          <p className="mt-1 text-xs font-semibold text-text-muted">Usage unique · expiration automatique dans 10 minutes.</p>
        </div>
      )}

      <div className="mt-5 space-y-3">
        {items.map((item) => (
          <article key={item.workstationId} className="rounded-elite-sm border border-border-main bg-main-bg p-4">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-black text-main">
                    {item.displayName || (item.workstationId === current.workstationId ? 'Ce poste' : 'Poste sans nom')}
                  </span>
                  {item.workstationId === current.workstationId && (
                    <span className="rounded-full border border-primary/20 bg-primary/5 px-2 py-1 text-xs font-black text-primary">Ce poste</span>
                  )}
                  <span className="text-xs font-bold text-text-muted">#{shortId(item.workstationId)}</span>
                  <span className="text-xs font-bold text-text-muted">
                    {item.status === 'revoked' ? 'Révoqué' : item.status === 'online' ? 'En ligne' : 'Hors ligne'}
                  </span>
                </div>
                <p className="mt-1 text-xs font-semibold text-text-muted">
                  Mode : {item.defaultExperience || 'Hub'} · ID technique inchangé lors d’un renommage
                  {item.lastSeenAt ? ` · Dernière activité : ${new Date(item.lastSeenAt).toLocaleString()}` : ''}
                </p>
              </div>

              {!item.revoked && (
                <div className="flex flex-col gap-2 sm:flex-row">
                  <label className="sr-only" htmlFor={`station-name-${item.workstationId}`}>Nom du poste</label>
                  <input
                    id={`station-name-${item.workstationId}`}
                    value={names[item.workstationId] || ''}
                    maxLength={80}
                    onChange={(event) => setNames((currentNames) => ({ ...currentNames, [item.workstationId]: event.target.value }))}
                    placeholder="Ex. Accueil 1"
                    className="min-h-11 min-w-0 rounded-elite-sm border border-border-main bg-card-bg px-3 text-sm font-semibold text-main outline-none focus:border-primary"
                  />
                  <button
                    type="button"
                    disabled={busy !== null}
                    onClick={() => void rename(item)}
                    className="inline-flex min-h-11 items-center justify-center gap-2 rounded-elite-sm border border-border-main bg-card-bg px-3 text-xs font-black text-main disabled:opacity-50"
                  >
                    <Pencil size={14} aria-hidden="true" /> Renommer
                  </button>
                  <button
                    type="button"
                    disabled={busy !== null}
                    onClick={() => void revoke(item)}
                    className="inline-flex min-h-11 items-center justify-center gap-2 rounded-elite-sm border border-border-main bg-card-bg px-3 text-xs font-black text-main disabled:opacity-50"
                  >
                    <ShieldX size={14} aria-hidden="true" />
                    {confirmRevokeId === item.workstationId ? 'Confirmer la révocation' : 'Révoquer'}
                  </button>
                  {confirmRevokeId === item.workstationId && (
                    <button
                      type="button"
                      disabled={busy !== null}
                      onClick={() => {
                        setConfirmRevokeId(null);
                        setFeedback('');
                      }}
                      className="inline-flex min-h-11 items-center justify-center rounded-elite-sm border border-border-main bg-card-bg px-3 text-xs font-black text-main disabled:opacity-50"
                    >
                      Annuler
                    </button>
                  )}
                </div>
              )}
            </div>
          </article>
        ))}
      </div>

      {feedback && <p role="status" className="mt-4 text-sm font-bold text-text-muted">{feedback}</p>}
    </section>
  );
};
