import { useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import axios from 'axios';
import { ArrowLeft, Crown, Fingerprint, LockKeyhole, LogOut, ShieldCheck } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
  PLATFORM_API_BASE,
  clearMobilePlatformAccessToken,
  getMobilePlatformAccessToken,
  setMobilePlatformAccessToken,
} from '../../../../services/api';
import { getPlatformTopology } from '../../../../services/platformTopology';
import { SuperAdminAccessBoundary } from '../../../superadmin/SuperAdminAccessBoundary';

type GateState = 'login' | 'authorized';

type PasskeyStatus = {
  expected_origin?: string;
  origin_ready?: boolean;
};

const errorDetail = (error: unknown): string => {
  const candidate = error as { response?: { status?: number; data?: { detail?: string } } };
  const status = candidate?.response?.status;
  if (status === 401) return 'Email ou mot de passe plateforme incorrect.';
  if (status === 403) return 'Compte valide, mais autorité plateforme refusée.';
  if (candidate?.response?.data?.detail) return candidate.response.data.detail;
  if (error instanceof Error && error.message) return error.message;
  return 'Control-plane indisponible. Réessayez depuis une connexion sécurisée.';
};

export function MobileSuperAdminView() {
  const navigate = useNavigate();
  const topology = useMemo(() => getPlatformTopology(PLATFORM_API_BASE), []);
  const [gate, setGate] = useState<GateState>(() => (
    topology.ready && getMobilePlatformAccessToken() ? 'authorized' : 'login'
  ));
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(() => (
    topology.ready
      ? ''
      : 'Ouvrez la Tour de contrôle depuis son origine HTTPS dédiée. Le frontend et l’API plateforme doivent partager exactement la même origine.'
  ));

  const goBack = () => {
    if (window.history.length > 1) {
      window.history.back();
      return;
    }
    navigate('/mobile/dashboard?tab=securite');
  };

  useEffect(() => {
    if (!topology.ready) {
      clearMobilePlatformAccessToken();
      setGate('login');
    }

    const expire = () => {
      clearMobilePlatformAccessToken();
      setGate('login');
      setPassword('');
      setError('Session plateforme expirée. Reconnectez-vous.');
    };
    window.addEventListener('digitalcrown:mobile-platform-session-expired', expire);
    return () => window.removeEventListener('digitalcrown:mobile-platform-session-expired', expire);
  }, [topology.ready]);

  const login = async (event: FormEvent) => {
    event.preventDefault();
    if (!email.trim() || !password) return;
    if (!topology.ready) {
      clearMobilePlatformAccessToken();
      setError('Origine plateforme invalide. Ouvrez la Tour depuis son URL HTTPS dédiée.');
      return;
    }

    setBusy(true);
    setError('');
    clearMobilePlatformAccessToken();

    try {
      const form = new URLSearchParams();
      form.set('username', email.trim().toLowerCase());
      form.set('password', password);
      const loginResponse = await axios.post(`${PLATFORM_API_BASE}/api/auth/login`, form, {
        withCredentials: true,
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      const token = String(loginResponse.data?.access_token || '').trim();
      if (!token) throw new Error('Session plateforme invalide.');

      // Autorisation serveur ET origine WebAuthn exacte AVANT toute persistance
      // de la session plateforme côté téléphone.
      const statusResponse = await axios.get(`${PLATFORM_API_BASE}/api/superadmin/passkey/status`, {
        withCredentials: true,
        headers: { Authorization: `Bearer ${token}` },
      });
      const passkeyStatus = statusResponse.data as PasskeyStatus;
      const expectedOrigin = String(passkeyStatus.expected_origin || '').replace(/\/$/, '').toLowerCase();
      if (!passkeyStatus.origin_ready || !expectedOrigin || expectedOrigin !== window.location.origin.toLowerCase()) {
        throw new Error(
          expectedOrigin
            ? `Ouvrez la Tour de contrôle depuis ${expectedOrigin}.`
            : 'Origine WebAuthn plateforme non configurée.'
        );
      }

      setMobilePlatformAccessToken(token);
      setPassword('');
      setGate('authorized');
    } catch (caught) {
      clearMobilePlatformAccessToken();
      setError(errorDetail(caught));
    } finally {
      setBusy(false);
    }
  };

  const logoutPlatform = async () => {
    const token = getMobilePlatformAccessToken();
    clearMobilePlatformAccessToken();
    setGate('login');
    setPassword('');
    setError('');
    if (!token) return;
    try {
      await axios.post(
        `${PLATFORM_API_BASE}/api/auth/logout`,
        { refresh_token: '' },
        {
          withCredentials: true,
          headers: { Authorization: `Bearer ${token}` },
        },
      );
    } catch {
      // La fermeture locale de la session plateforme mobile reste autoritaire.
    }
  };

  if (gate === 'login') {
    return (
      <main data-testid="mobile-superadmin-login" className="min-h-[100dvh] bg-slate-950 px-5 pb-10 pt-[max(20px,env(safe-area-inset-top))] text-white">
        <div className="mx-auto w-full max-w-md">
          <button
            type="button"
            onClick={goBack}
            className="mb-8 inline-flex min-h-11 items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 text-sm font-bold text-slate-200"
          >
            <ArrowLeft size={17} /> Retour
          </button>

          <section className="overflow-hidden rounded-[32px] border border-white/10 bg-white/[0.07] p-6 shadow-2xl backdrop-blur-2xl">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-500/15 text-blue-300 ring-1 ring-blue-300/20">
              <Crown size={28} aria-hidden="true" />
            </div>
            <p className="mt-6 text-[11px] font-black uppercase tracking-[0.24em] text-blue-300">Digital Crown</p>
            <h1 className="mt-2 text-3xl font-black tracking-tight">Tour de contrôle</h1>
            <p className="mt-3 text-sm font-medium leading-6 text-slate-300">
              La session cabinet ne donne aucun droit plateforme. Connectez l’identité Superadmin séparément.
            </p>

            <div className="mt-5 grid grid-cols-2 gap-3 text-[11px] font-bold text-slate-300">
              <div className="rounded-2xl border border-white/10 bg-black/10 p-3">
                <ShieldCheck className="mb-2 text-emerald-300" size={18} /> Session séparée
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/10 p-3">
                <Fingerprint className="mb-2 text-blue-300" size={18} /> Passkey sur mutation
              </div>
            </div>

            <form className="mt-7 space-y-4" onSubmit={login}>
              <label className="block">
                <span className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-400">Email plateforme</span>
                <input
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  type="email"
                  autoComplete="username"
                  required
                  disabled={!topology.ready}
                  className="min-h-14 w-full rounded-2xl border border-white/10 bg-white/10 px-4 text-base font-bold text-white outline-none placeholder:text-slate-500 focus:border-blue-400 disabled:opacity-50"
                  placeholder="owner@..."
                />
              </label>
              <label className="block">
                <span className="mb-2 block text-xs font-black uppercase tracking-wider text-slate-400">Mot de passe</span>
                <input
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  type="password"
                  autoComplete="current-password"
                  required
                  disabled={!topology.ready}
                  className="min-h-14 w-full rounded-2xl border border-white/10 bg-white/10 px-4 text-base font-bold text-white outline-none placeholder:text-slate-500 focus:border-blue-400 disabled:opacity-50"
                  placeholder="••••••••••••"
                />
              </label>
              {error && <p role="alert" className="rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm font-bold text-rose-200">{error}</p>}
              <button
                type="submit"
                disabled={busy || !topology.ready || !email.trim() || !password}
                className="flex min-h-14 w-full items-center justify-center gap-2 rounded-2xl bg-blue-500 px-4 text-sm font-black text-white shadow-lg shadow-blue-950/30 disabled:opacity-50"
              >
                <LockKeyhole size={18} /> {busy ? 'Vérification…' : 'Ouvrir la Tour de contrôle'}
              </button>
            </form>
          </section>

          <p className="mt-5 px-2 text-center text-[11px] font-semibold leading-5 text-slate-500">
            Aucun secret de signature n’est stocké sur ce téléphone. Les actions sensibles exigent une vérification WebAuthn récente.
          </p>
        </div>
      </main>
    );
  }

  return (
    <div data-testid="mobile-superadmin-authorized" className="min-h-[100dvh] bg-slate-50">
      <header className="border-b border-slate-200 bg-slate-950 px-4 pb-4 pt-[max(14px,env(safe-area-inset-top))] text-white">
        <div className="mx-auto flex max-w-7xl items-center gap-3">
          <button
            type="button"
            aria-label="Retour"
            onClick={goBack}
            className="grid h-11 w-11 place-items-center rounded-2xl border border-white/10 bg-white/10"
          >
            <ArrowLeft size={19} />
          </button>
          <div className="min-w-0 flex-1">
            <p className="text-[9px] font-black uppercase tracking-[0.22em] text-blue-300">Session plateforme</p>
            <p className="truncate text-base font-black">Tour de contrôle</p>
          </div>
          <button
            type="button"
            aria-label="Fermer la session plateforme"
            onClick={() => void logoutPlatform()}
            className="grid h-11 w-11 place-items-center rounded-2xl border border-white/10 bg-white/10 text-rose-200"
          >
            <LogOut size={18} />
          </button>
        </div>
      </header>
      <SuperAdminAccessBoundary />
    </div>
  );
}
