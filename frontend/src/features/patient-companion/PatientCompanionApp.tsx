import { useEffect, useMemo, useRef, useState } from 'react';
import { Camera, CheckCircle2, KeyRound, Loader2, ShieldCheck, Smartphone, Trash2 } from 'lucide-react';
import { API_BASE } from '../../services/api';
import {
  PatientCompanionStorage,
  type PatientCompanionVaultState,
  type PatientPairing,
  type PatientRemoteTransportBinding,
  type PatientWalletSnapshot,
} from './PatientCompanionStorage';
import { PatientCompanionSync } from './PatientCompanionSync';
import { PatientCompanionRemoteCrypto } from './PatientCompanionRemoteCrypto';

type Phase = 'loading' | 'welcome' | 'scanning' | 'pairing' | 'home' | 'error';

const emptyVault: PatientCompanionVaultState = {
  version: 1,
  activeAccessId: null,
  pairings: [],
  cache: {},
};

const RELATIONSHIP_LABELS: Record<string, string> = {
  SELF: 'Patient',
  PARENT: 'Parent',
  GUARDIAN: 'Tuteur',
  CAREGIVER: 'Aidant',
};

const relationshipLabel = (value: string) => RELATIONSHIP_LABELS[value] || value;

export const PatientCompanionApp = () => {
  const scannerRef = useRef<{ clear: () => Promise<void> } | null>(null);
  const [phase, setPhase] = useState<Phase>('loading');
  const [vault, setVault] = useState<PatientCompanionVaultState>(emptyVault);
  const [manualCode, setManualCode] = useState('');
  const [error, setError] = useState('');
  const [selectingContext, setSelectingContext] = useState(false);
  const [cabinetReachability, setCabinetReachability] = useState<'unknown' | 'checking' | 'online' | 'offline'>('unknown');
  const [syncState, setSyncState] = useState<'idle' | 'syncing' | 'synced' | 'offline' | 'expired'>('idle');

  const activePairing = useMemo(
    () => vault.pairings.find(item => item.context.access_id === vault.activeAccessId) || null,
    [vault],
  );

  const activeWallet = useMemo(
    () => (vault.activeAccessId ? vault.cache[vault.activeAccessId] as PatientWalletSnapshot | undefined : undefined),
    [vault],
  );

  const sessionExpired = useMemo(
    () => Boolean(activePairing?.expiresAt && new Date(activePairing.expiresAt).getTime() <= Date.now()),
    [activePairing],
  );

  useEffect(() => {
    let cancelled = false;
    PatientCompanionStorage.load()
      .then(state => {
        if (cancelled) return;
        setVault(state);
        setSelectingContext(state.pairings.length > 1);
        const urlToken = new URLSearchParams(window.location.search).get('token')?.trim();
        if (urlToken) {
          window.history.replaceState({}, '', '/companion');
          setPhase('pairing');
          void pairDevice(urlToken, false);
          return;
        }
        setPhase(state.pairings.length ? 'home' : 'welcome');
      })
      .catch(() => {
        if (!cancelled) {
          setError('Le coffre local Patient Companion est indisponible sur cet appareil.');
          setPhase('error');
        }
      });
    return () => { cancelled = true; };
  // Pairing is intentionally resolved once at entry.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (phase !== 'scanning') return undefined;
    if (!window.isSecureContext && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      setError('La caméra nécessite une connexion sécurisée. Utilisez le code manuel remis par le cabinet.');
      setPhase('error');
      return undefined;
    }

    let cancelled = false;
    void import('html5-qrcode').then(({ Html5QrcodeScanner, Html5QrcodeSupportedFormats }) => {
      if (cancelled) return;
      const scanner = new Html5QrcodeScanner(
        'patient-companion-reader',
        {
          fps: 10,
          qrbox: { width: 250, height: 250 },
          aspectRatio: 1,
          formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE],
        },
        false,
      );
      scannerRef.current = scanner;
      scanner.render(
        decoded => {
          void scanner.clear().catch(() => null);
          const credential = extractCredential(decoded);
          if (!credential) {
            setError('QR Patient Companion non reconnu.');
            setPhase('error');
            return;
          }
          setPhase('pairing');
          void pairDevice(credential, false);
        },
        () => undefined,
      );
    }).catch(() => {
      if (!cancelled) {
        setError('Le scanner QR est indisponible sur cet appareil. Utilisez le code manuel.');
        setPhase('error');
      }
    });
    return () => {
      cancelled = true;
      scannerRef.current?.clear().catch(() => null);
      scannerRef.current = null;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase]);

  function extractCredential(decoded: string): string {
    const trimmed = decoded.trim();
    if (!trimmed) return '';
    try {
      const url = new URL(trimmed);
      return url.searchParams.get('token')?.trim() || '';
    } catch {
      return trimmed.length <= 256 ? trimmed : '';
    }
  }

  async function pairDevice(credential: string, manual: boolean) {
    setError('');
    let preparedRemote = null as Awaited<ReturnType<typeof PatientCompanionRemoteCrypto.prepareEnrollment>>;
    try {
      const loopback = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      if (!window.isSecureContext && !loopback) {
        throw new Error('Appairage refusé : ouvrez Patient Companion via la connexion HTTPS sécurisée du cabinet.');
      }

      try {
        preparedRemote = await PatientCompanionRemoteCrypto.prepareEnrollment();
      } catch {
        preparedRemote = null;
      }

      const baseBody = manual ? { manual_code: credential } : { token: credential };
      const response = await fetch(`${API_BASE}/api/patient-companion/pair`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(
          preparedRemote
            ? { ...baseBody, remote_keys: preparedRemote.request }
            : baseBody,
        ),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || 'Appairage impossible.');
      if (!payload.access_token || !payload.context?.access_id) throw new Error('Réponse d’appairage incomplète.');

      let remoteTransport: PatientRemoteTransportBinding | undefined;
      const remote = payload.remote_transport;
      if (
        preparedRemote
        && remote?.status === 'enrolled'
        && remote.protocol_version === 'dc-pc-remote-v1'
        && typeof remote.keyset_id === 'string'
        && remote.patient_signing_kid === preparedRemote.signingKid
        && remote.patient_encryption_kid === preparedRemote.encryptionKid
        && typeof remote.cabinet?.signing?.kid === 'string'
        && remote.cabinet.signing.public_jwk
        && typeof remote.cabinet?.encryption?.kid === 'string'
        && remote.cabinet.encryption.public_jwk
      ) {
        remoteTransport = {
          version: 1,
          keysetId: remote.keyset_id,
          signingKid: preparedRemote.signingKid,
          encryptionKid: preparedRemote.encryptionKid,
          cabinetSigningKid: remote.cabinet.signing.kid,
          cabinetSigningPublicJwk: remote.cabinet.signing.public_jwk,
          cabinetEncryptionKid: remote.cabinet.encryption.kid,
          cabinetEncryptionPublicJwk: remote.cabinet.encryption.public_jwk,
        };
      } else if (preparedRemote) {
        await PatientCompanionRemoteCrypto.discardEnrollment(preparedRemote);
        preparedRemote = null;
      }

      const pairing: PatientPairing = {
        accessToken: payload.access_token,
        context: payload.context,
        pairedAt: payload.paired_at || new Date().toISOString(),
        remoteTransport,
      };
      const next = await PatientCompanionStorage.savePairing(pairing);
      window.history.replaceState({}, '', '/companion');
      setVault(next);
      setSelectingContext(false);
      setManualCode('');
      setPhase('home');
    } catch (err) {
      if (preparedRemote) {
        await PatientCompanionRemoteCrypto.discardEnrollment(preparedRemote).catch(() => undefined);
      }
      setError(err instanceof Error ? err.message : 'Invitation invalide ou expirée.');
      setPhase('error');
    }
  }

  const checkCabinet = async () => {
    if (!activePairing) return;
    setCabinetReachability('checking');
    try {
      const response = await fetch(`${API_BASE}/api/patient-companion/me`, {
        headers: { Authorization: `Bearer ${activePairing.accessToken}` },
        cache: 'no-store',
      });
      setCabinetReachability(response.ok ? 'online' : 'offline');
    } catch {
      setCabinetReachability('offline');
    }
  };

  const syncWallet = async () => {
    if (!activePairing) return;
    if (sessionExpired) {
      setSyncState('expired');
      return;
    }
    setSyncState('syncing');
    try {
      const snapshot = await PatientCompanionSync.sync(activePairing);
      const next = await PatientCompanionStorage.load();
      setVault(next);
      setCabinetReachability('online');
      setSyncState(snapshot ? 'synced' : 'idle');
    } catch (err) {
      const status = typeof err === 'object' && err && 'status' in err ? Number((err as { status?: number }).status) : 0;
      if (status === 401 || status === 403) {
        setSyncState('expired');
      } else {
        setSyncState('offline');
      }
      setCabinetReachability('offline');
    }
  };

  const submitManual = () => {
    const code = manualCode.trim();
    if (!code) {
      setError('Saisissez le code remis par le cabinet.');
      setPhase('error');
      return;
    }
    setPhase('pairing');
    void pairDevice(code, true);
  };

  const selectContext = async (accessId: string) => {
    try {
      const next = await PatientCompanionStorage.setActive(accessId);
      setVault(next);
      setSelectingContext(false);
    } catch {
      setError('Impossible d’ouvrir ce contexte patient.');
      setPhase('error');
    }
  };

  const clearDevice = async () => {
    await PatientCompanionStorage.clear();
    setVault(emptyVault);
    setSelectingContext(false);
    setManualCode('');
    setPhase('welcome');
  };

  return (
    <main data-pc00-shell className="min-h-[100dvh] bg-background text-text-main font-outfit px-4 pt-[max(1rem,env(safe-area-inset-top))] pb-[max(1.5rem,env(safe-area-inset-bottom))]">
      <div className="mx-auto max-w-md">
        <header className="pt-5 pb-6">
          <div className="flex items-center gap-2 text-primary">
            <ShieldCheck size={19} />
            <span className="text-[10px] font-black uppercase tracking-[0.18em]">Digital Crown</span>
          </div>
          <h1 className="mt-2 text-3xl font-black tracking-tight">Patient Companion</h1>
          <p className="mt-2 text-sm font-bold text-text-muted">Vos informations restent dans votre cabinet et sur cet appareil.</p>
        </header>

        {phase === 'loading' && <Card title="Ouverture du coffre" icon={<Loader2 className="animate-spin" size={20} />}><p className="text-sm font-bold text-text-muted">Lecture locale sécurisée…</p></Card>}

        {phase === 'welcome' && (
          <Card title="Appairer ce téléphone" icon={<Smartphone size={20} />}>
            <p className="text-sm font-medium text-text-muted">Scannez le QR à usage unique affiché par votre cabinet. Après appairage, votre espace est conservé localement sur ce téléphone.</p>
            <button data-pc00-scan onClick={() => setPhase('scanning')} className="mt-5 min-h-[56px] w-full rounded-2xl bg-primary text-white font-black inline-flex items-center justify-center gap-2"><Camera size={18} /> Scanner le QR</button>
            <div className="my-4 flex items-center gap-3 text-[10px] font-black uppercase tracking-widest text-text-muted"><span className="h-px flex-1 bg-border-main" />ou<span className="h-px flex-1 bg-border-main" /></div>
            <label className="block">
              <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Code manuel</span>
              <input data-pc00-manual-code aria-label="Code manuel" value={manualCode} onChange={event => setManualCode(event.target.value)} autoComplete="one-time-code" className="mt-2 h-12 w-full rounded-2xl border border-border-main bg-background px-4 text-center text-lg font-black tracking-[0.12em] uppercase" />
            </label>
            <button data-pc00-pair-manual onClick={submitManual} className="mt-3 min-h-[52px] w-full rounded-2xl border border-primary/25 bg-primary/5 text-primary font-black inline-flex items-center justify-center gap-2"><KeyRound size={17} /> Appairer avec le code</button>
            <p className="mt-4 text-[11px] font-bold text-text-muted">Le QR/code expire et ne sert qu’une fois. Il n’est jamais conservé après l’appairage.</p>
          </Card>
        )}

        {phase === 'scanning' && (
          <Card title="Scanner le QR cabinet" icon={<Camera size={20} />}>
            <div id="patient-companion-reader" className="overflow-hidden rounded-2xl" />
            <button onClick={() => setPhase('welcome')} className="mt-4 min-h-[48px] w-full rounded-2xl border border-border-main font-black">Utiliser le code manuel</button>
          </Card>
        )}

        {phase === 'pairing' && <Card title="Appairage sécurisé" icon={<Loader2 className="animate-spin" size={20} />}><p className="text-sm font-bold text-text-muted">Le cabinet vérifie le QR puis prépare votre coffre local…</p></Card>}

        {phase === 'error' && (
          <Card title="Appairage non validé" icon={<ShieldCheck size={20} />}>
            <p role="alert" className="text-sm font-bold text-rose-700">{error}</p>
            <button onClick={() => { setError(''); setPhase(vault.pairings.length ? 'home' : 'welcome'); }} className="mt-4 min-h-[52px] w-full rounded-2xl border border-border-main font-black">Réessayer</button>
          </Card>
        )}

        {phase === 'home' && vault.pairings.length > 1 && selectingContext && (
          <Card title="Choisir un dossier" icon={<ShieldCheck size={20} />}>
            {vault.pairings.map(pairing => (
              <button key={pairing.context.access_id} data-pc00-context onClick={() => void selectContext(pairing.context.access_id)} className="mb-2 min-h-[62px] w-full rounded-2xl border border-border-main bg-card-bg px-4 text-left">
                <span className="block font-black">{pairing.context.patient.display_name || `${pairing.context.patient.prenom || ''} ${pairing.context.patient.nom || ''}`.trim()}</span>
                <span className="text-xs font-bold text-text-muted">{relationshipLabel(pairing.context.relationship_type)}</span>
              </button>
            ))}
          </Card>
        )}

        {phase === 'home' && activePairing && !selectingContext && (
          <>
            <Card title="Mon espace" icon={<CheckCircle2 size={20} />}>
              <p className="text-xl font-black">{activePairing.context.patient.display_name || `${activePairing.context.patient.prenom || ''} ${activePairing.context.patient.nom || ''}`.trim()}</p>
              <p className="mt-1 text-xs font-bold text-text-muted">{relationshipLabel(activePairing.context.relationship_type)}</p>
              <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-3 py-2.5 text-[11px] font-black text-emerald-800">Coffre local actif · utilisable même si le cabinet est momentanément hors ligne</div>
              <button data-pc00-cabinet-link onClick={() => void checkCabinet()} className="mt-3 min-h-[48px] w-full rounded-2xl border border-border-main bg-background px-3 text-xs font-black">
                {cabinetReachability === 'checking' ? 'Vérification du cabinet…' : cabinetReachability === 'online' ? 'Cabinet joignable ✓' : cabinetReachability === 'offline' ? 'Cabinet hors ligne · coffre local disponible' : 'Vérifier la connexion au cabinet'}
              </button>
              <button data-pc01-sync onClick={() => void syncWallet()} disabled={syncState === 'syncing'} className="mt-2 min-h-[48px] w-full rounded-2xl bg-primary text-white px-3 text-xs font-black disabled:opacity-60">
                {syncState === 'syncing' ? 'Synchronisation…' : 'Synchroniser mon espace'}
              </button>
              {activeWallet?.syncedAt && <p className="mt-2 text-[10px] font-bold text-text-muted">Dernière synchronisation : {new Date(activeWallet.syncedAt).toLocaleString()}</p>}
              {syncState === 'offline' && <p className="mt-2 text-[11px] font-black text-amber-700">Cabinet non joignable · dernière copie locale conservée.</p>}
              {(syncState === 'expired' || sessionExpired) && <p className="mt-2 text-[11px] font-black text-rose-700">Connexion au cabinet expirée · votre copie locale reste disponible. Un nouvel appairage sera nécessaire pour synchroniser.</p>}
            </Card>
            <section className="mt-4 grid gap-3" aria-label="Portefeuille Patient Companion">
              <WalletSection title="Mes rendez-vous" empty="Aucun rendez-vous synchronisé.">
                {activeWallet?.appointments.map((item, index) => (
                  <div key={`${item.datetime_start}-${item.motif}-${index}`} className="rounded-2xl border border-border-main bg-card-bg p-4">
                    <p className="font-black">{item.motif}</p>
                    <p className="mt-1 text-xs font-bold text-text-muted">{new Date(item.datetime_start).toLocaleString()} · {item.status}</p>
                  </div>
                ))}
              </WalletSection>
              <WalletSection title="Mes documents & médias" empty="Aucun document ou média partagé.">
                {activeWallet?.shares.map(item => (
                  <div key={item.share_id} className="rounded-2xl border border-border-main bg-card-bg p-4">
                    <p className="font-black">{item.title || (item.resource_type === 'media' ? 'Média clinique partagé' : 'Document partagé')}</p>
                    <p className="mt-1 text-xs font-bold text-text-muted">{item.resource_type === 'media' ? 'Média' : item.document_type || 'Document'}</p>
                  </div>
                ))}
              </WalletSection>
            </section>
            {vault.pairings.length > 1 && <button onClick={() => setSelectingContext(true)} className="mt-4 min-h-[48px] w-full rounded-2xl border border-primary/20 bg-primary/5 text-primary text-xs font-black">Changer de dossier</button>}
            <div className="mt-3 grid grid-cols-2 gap-3">
              <button onClick={() => setPhase('welcome')} className="min-h-[48px] rounded-2xl border border-border-main text-xs font-black">Ajouter un dossier</button>
              <button onClick={() => void clearDevice()} className="min-h-[48px] rounded-2xl border border-rose-200 bg-rose-50 text-rose-700 text-xs font-black inline-flex items-center justify-center gap-2"><Trash2 size={15} /> Effacer ce téléphone</button>
            </div>
          </>
        )}
      </div>
    </main>
  );
};

const Card = ({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) => (
  <section className="rounded-[1.75rem] border border-border-main bg-card-bg p-5 shadow-elite">
    <div className="flex items-center gap-2 text-primary">{icon}<h2 className="font-black text-text-main">{title}</h2></div>
    <div className="mt-4">{children}</div>
  </section>
);

const WalletSection = ({ title, empty, children }: { title: string; empty: string; children: React.ReactNode }) => {
  const hasItems = Array.isArray(children) ? children.length > 0 : Boolean(children);
  return (
    <section className="rounded-[1.5rem] border border-border-main bg-card-bg p-4">
      <h3 className="font-black">{title}</h3>
      <div className="mt-3 grid gap-2">{hasItems ? children : <p className="text-xs font-bold text-text-muted">{empty}</p>}</div>
    </section>
  );
};
