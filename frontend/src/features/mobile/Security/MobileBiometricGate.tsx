import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { Fingerprint, LockKeyhole, ShieldAlert } from 'lucide-react';
import { MobileStorage } from '../../../services/zka/MobileStorage';
import {
  getMobilePasskeyStatus,
  isStablePasskeyOrigin,
  unlockMobilePasskey,
  type MobilePasskeyStatus,
} from '../../../services/zka/mobilePasskey';

interface Props {
  children: ReactNode;
}

type GateState = 'loading' | 'allow' | 'locked' | 'origin-error' | 'error';

export function MobileBiometricGate({ children }: Props) {
  const [state, setState] = useState<GateState>('loading');
  const [status, setStatus] = useState<MobilePasskeyStatus | null>(null);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  const inspect = useCallback(async () => {
    try {
      const next = await getMobilePasskeyStatus();
      setStatus(next);
      const vault = await MobileStorage.getBiometricVaultEnvelope();
      if (next.state === 'disabled') {
        if (vault) {
          setMessage('Finalisez la désactivation biométrique pour restaurer le coffre local.');
          setState('locked');
        } else {
          setState('allow');
        }
        return;
      }
      if (next.state === 'pending' && !vault) {
        // Registration exists but local sealing has not happened yet. Keep the app
        // usable so Security can resume or cancel the pending ceremony.
        setState('allow');
        return;
      }
      if (!isStablePasskeyOrigin(next.expected_origin)) {
        setState('origin-error');
        return;
      }
      if (await MobileStorage.isBiometricVaultUnlocked() && MobileStorage.getBiometricAccessToken()) {
        setState('allow');
        return;
      }
      setState('locked');
    } catch (error) {
      const vault = await MobileStorage.getBiometricVaultEnvelope().catch(() => null);
      if (vault && isStablePasskeyOrigin('https://digitalcrown.local:8005')) {
        setStatus({
          state: 'enabled', credential_id: vault.credential_id, rp_id: 'digitalcrown.local',
          expected_origin: 'https://digitalcrown.local:8005', origin_ready: true,
          user_verification: 'required', server_gate: true,
        });
        setState('locked');
        return;
      }
      setMessage(error instanceof Error ? error.message : 'État biométrique indisponible.');
      setState('error');
    }
  }, []);

  useEffect(() => { void inspect(); }, [inspect]);

  useEffect(() => {
    const lock = () => {
      MobileStorage.lockBiometricVault();
      setState('locked');
    };
    window.addEventListener('digitalcrown:mobile-biometric-locked', lock);
    return () => window.removeEventListener('digitalcrown:mobile-biometric-locked', lock);
  }, []);

  useEffect(() => {
    if (state !== 'allow') return;
    const timer = window.setTimeout(() => {
      void MobileStorage.getBiometricVaultEnvelope().then((vault) => {
        if (!vault) return;
        MobileStorage.lockBiometricVault();
        setState('locked');
      });
    }, 5 * 60 * 1000);
    return () => window.clearTimeout(timer);
  }, [state]);

  useEffect(() => {
    const onVisibility = () => {
      if (!document.hidden) return;
      void MobileStorage.getBiometricVaultEnvelope().then((vault) => {
        if (!vault) return;
        MobileStorage.lockBiometricVault();
        setState('locked');
      });
    };
    document.addEventListener('visibilitychange', onVisibility);
    return () => document.removeEventListener('visibilitychange', onVisibility);
  }, []);

  const unlock = async () => {
    setBusy(true);
    setMessage('');
    try {
      await unlockMobilePasskey();
      setState('allow');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Déverrouillage refusé.');
    } finally {
      setBusy(false);
    }
  };

  if (state === 'loading') {
    return (
      <div className="min-h-[100dvh] bg-background flex items-center justify-center px-6">
        <div className="w-10 h-10 rounded-full border-4 border-primary/20 border-t-primary animate-spin" aria-label="Vérification biométrique" />
      </div>
    );
  }
  if (state === 'allow') return <>{children}</>;

  const originError = state === 'origin-error';
  return (
    <main className="min-h-[100dvh] bg-background text-text-main flex items-center justify-center px-6 py-10">
      <section className="w-full max-w-md bg-glass-bg border border-glass-border backdrop-blur-xl rounded-[32px] p-7 shadow-elite text-center">
        <div className={`mx-auto w-20 h-20 rounded-[24px] flex items-center justify-center ${originError ? 'bg-amber-500/10 text-amber-600' : 'bg-primary/10 text-primary'}`}>
          {originError ? <ShieldAlert size={38} /> : <Fingerprint size={40} />}
        </div>
        <p className="mt-5 text-[10px] font-black uppercase tracking-[0.22em] text-text-muted">Terminal protégé</p>
        <h1 className="mt-2 text-2xl font-black font-outfit">
          {originError ? 'Adresse sécurisée requise' : 'Déverrouiller Digital Crown'}
        </h1>
        <p className="mt-3 text-sm leading-relaxed text-text-muted font-semibold">
          {originError
            ? `La biométrie est liée à ${status?.expected_origin || 'digitalcrown.local'}. Ouvrez cette adresse sur le réseau du cabinet.`
            : 'Utilisez Face ID, votre empreinte ou le verrouillage sécurisé de cet appareil. Aucune donnée biométrique n’est transmise à Digital Crown.'}
        </p>
        {!originError && (
          <button
            type="button"
            disabled={busy}
            onClick={unlock}
            className="mt-7 min-h-[56px] w-full rounded-[20px] bg-primary text-white font-black text-sm flex items-center justify-center gap-3 shadow-lg active:scale-[0.98] transition-transform disabled:opacity-60"
          >
            <LockKeyhole size={20} /> {busy ? 'Vérification…' : 'Déverrouiller'}
          </button>
        )}
        {message && <p role="alert" className="mt-4 text-xs font-bold text-rose-600">{message}</p>}
        <p className="mt-6 text-[10px] leading-relaxed text-text-muted font-semibold">
          Le QR d’appairage et la révocation du cabinet restent obligatoires. La passkey ne remplace jamais l’identité serveur.
        </p>
      </section>
    </main>
  );
}
