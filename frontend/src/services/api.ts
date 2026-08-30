import axios from 'axios';
import toast from 'react-hot-toast';
import { MobileStorage } from './zka/MobileStorage';
import { ensurePlatformStepUp } from './platformPasskey';

const defaultApiUrl = typeof window !== 'undefined'
  ? `${window.location.protocol}//${window.location.hostname}:8005`
  : 'http://127.0.0.1:8005';
const viteEnv = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env;
export const API_BASE = (viteEnv?.VITE_API_URL ?? defaultApiUrl).replace(/\/$/, '');

export const api = axios.create({
  baseURL: `${API_BASE}/api`,
  timeout: 30000,
  withCredentials: true,  // Envoie les cookies HttpOnly automatiquement
});

// Synchronisation du token entre onglets (BroadcastChannel)
const _authChannel = typeof BroadcastChannel !== 'undefined'
  ? new BroadcastChannel('dc_auth')
  : null;

function storeTokens(token: string, refresh?: string) {
  // Sauvegarde dans le localStorage comme fallback indispensable pour le développement local (cross-origin)
  localStorage.setItem('token', token);
  if (refresh) {
      localStorage.setItem('refresh_token', refresh);
  }
  _authChannel?.postMessage({ type: 'TOKEN_REFRESH', token, refresh });
}

if (_authChannel) {
  _authChannel.onmessage = (e) => {
    if (e.data?.type === 'TOKEN_REFRESH') {
      // Cookies HttpOnly posés par le backend — pas d'écriture localStorage ici
    } else if (e.data?.type === 'LOGOUT') {
      // Un autre onglet a déclenché le logout — on coupe aussi ici
      _authFailed = true;
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      if (window.location.pathname !== '/login') window.location.href = '/login';
    }
  };
}

let _refreshing: Promise<boolean> | null = null;
// Coupe-circuit : dès qu'un logout est déclenché, toutes les requêtes suivantes
// sont annulées immédiatement sans toucher le serveur.
let _authFailed = false;

export function resetAuthState() {
  _authFailed = false;
}

/**
 * Token d'autorisation courant. Sur les routes mobiles, un step-up biométrique
 * doit rester mémoire-only mais primer sur le JWT durable pour TOUS les clients
 * partagés (Axios, SSE, WebSocket). Desktop conserve exactement le contrat web.
 */
export function getRuntimeAuthToken(): string | null {
  if (typeof window !== 'undefined' && window.location.pathname.startsWith('/mobile')) {
    const uvToken = MobileStorage.getBiometricAccessToken();
    if (uvToken) return uvToken;
  }
  try {
    return localStorage.getItem('token') || sessionStorage.getItem('token');
  } catch {
    return null;
  }
}

function propagateMobileBiometricLock(): void {
  if (typeof window === 'undefined' || !window.location.pathname.startsWith('/mobile')) return;
  MobileStorage.lockBiometricVault();
  window.dispatchEvent(new CustomEvent('digitalcrown:mobile-biometric-locked'));
}

function isSuperAdminMutation(url: unknown, method: unknown): boolean {
  if (typeof url !== 'string') return false;
  const normalizedMethod = String(method || 'get').toLowerCase();
  return url.startsWith('/superadmin/')
    && !url.startsWith('/superadmin/passkey/')
    && ['post', 'put', 'patch', 'delete'].includes(normalizedMethod);
}

// Request interceptor — annule toute requête si la session est terminée
api.interceptors.request.use(async (config) => {
  if (_authFailed) {
    return Promise.reject(new axios.Cancel('Session expirée — requête annulée.'));
  }

  // Les PDFs fraîchement générés par Document Studio sont déjà exposés sous
  // forme d'URL blob: locale. Axios/XHR ne les traite pas de façon fiable dans
  // tous les navigateurs headless ; un adapter fetch natif garde le même contrat
  // responseType:'blob' sans repasser par le backend ni ouvrir un onglet fallback.
  if (typeof config.url === 'string' && config.url.startsWith('blob:')) {
    config.baseURL = undefined;
    config.adapter = async (adapterConfig) => {
      const response = await fetch(adapterConfig.url!);
      if (!response.ok) {
        throw new Error(`Impossible de lire le PDF local (${response.status})`);
      }
      const data = adapterConfig.responseType === 'blob'
        ? await response.blob()
        : await response.arrayBuffer();
      return {
        data,
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        config: adapterConfig,
        request: null,
      };
    };
  }

  // SEC-1 : toute mutation SuperAdmin passe d'abord par une cérémonie WebAuthn
  // dédiée. La preuve reste un cookie HttpOnly de 5 minutes, jamais un JWT
  // primaire ni une valeur stockée par le frontend.
  if (isSuperAdminMutation(config.url, config.method)) {
    await ensurePlatformStepUp(API_BASE);
  }

  const token = getRuntimeAuthToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Requête annulée par le coupe-circuit — ne rien faire
    if (axios.isCancel(error)) return Promise.reject(error);

    const original = error.config;

    if (!error.response) {
      if (!_authFailed) {
        const method = original?.method?.toLowerCase() || 'get';
        if (!navigator.onLine && ['post', 'put', 'patch', 'delete'].includes(method)) {
          toast.error('Mode hors-ligne : sauvegarde impossible sans confirmation serveur.', { id: 'offline-write-blocked', duration: 4000 });
          return Promise.reject(error);
        } else {
          toast.error('Serveur injoignable', { id: 'network-error' });
        }
      }
      return Promise.reject(error);
    }

    const { status, data, config: cfg } = error.response;
    if (!_authFailed) {
      console.group(`API Error [${status}]`);
      console.error('Path:', cfg?.url);
      console.error('Details:', data?.detail || data || error.message);
      if (data?.detail && Array.isArray(data.detail)) console.table(data.detail);
      console.groupEnd();
    }

    if (status === 423 && typeof window !== 'undefined' && window.location.pathname.startsWith('/mobile')) {
      propagateMobileBiometricLock();
      return Promise.reject(error);
    }

    // Certaines routes partagées historiques normalisent le verrou mobile en 401.
    // Après UNE tentative de refresh device-bound, un second 401 avec coffre
    // biométrique présent signifie que la session UV n'est plus valable : relock.
    // Une vraie révocation n'arrive pas ici : le refresh 401/403 invalide d'abord
    // la session et renvoie vers l'onboarding.
    if (status === 401 && typeof window !== 'undefined' && window.location.pathname.startsWith('/mobile') && original?._mobileRetried) {
      const vault = await MobileStorage.getBiometricVaultEnvelope().catch(() => null);
      if (vault) propagateMobileBiometricLock();
      return Promise.reject(error);
    }

    // Une session mobile a un refresh device-bound distinct du refresh web.
    if (status === 401 && window.location.pathname.startsWith('/mobile') && !original._mobileRetried) {
      original._mobileRetried = true;
      // Un JWT UV de 5 min peut simplement avoir expiré. Il ne faut surtout pas
      // le réutiliser après refresh : la requête durable suivante doit être refusée
      // par le gate biométrique puis reverrouiller l'interface.
      if (MobileStorage.getBiometricAccessToken()) MobileStorage.clearBiometricAccessToken();
      const previousToken = localStorage.getItem('token');
      const refreshed = await MobileStorage.refreshCredentials();
      if (refreshed?.access_token && refreshed.access_token !== previousToken) {
        localStorage.setItem('token', refreshed.access_token);
        original.headers = original.headers ?? {};
        original.headers['Authorization'] = `Bearer ${refreshed.access_token}`;
        return api(original);
      }
      return Promise.reject(error);
    }

    // Auto-refresh/Sync web on 401
    if (status === 401 && !window.location.pathname.startsWith('/mobile') && !original._retried && !original.url?.includes('/auth/')) {
      original._retried = true;

      if (!_refreshing) {
        _refreshing = (async () => {
          // 1. Essayer le refresh via token local ou cookie HttpOnly
          const refreshToken = localStorage.getItem('refresh_token') || '';
          try {
            const res = await axios.post(`${API_BASE}/api/auth/refresh`, {
              refresh_token: refreshToken
            }, { withCredentials: true });
            const { access_token, refresh_token: newRefresh } = res.data;
            if (access_token) {
              storeTokens(access_token, newRefresh);
              return true;
            }
          } catch {
            localStorage.removeItem('refresh_token');
          }

          // 2. Fallback : redirect to login since Supabase is gone
          localStorage.removeItem('token');
          return false;
        })().finally(() => { _refreshing = null; });
      }

      const ok = await _refreshing;
      if (ok) {
        // Cookies HttpOnly rafraîchis par le backend — withCredentials les envoie automatiquement
        // Fallback localStorage pour sessions mobiles/transitoires encore actives
        const fallbackToken = localStorage.getItem('token');
        if (fallbackToken) original.headers['Authorization'] = `Bearer ${fallbackToken}`;
        return api(original);
      }

      // Échec total → coupe-circuit ON + logout immédiat
      // Sur le dashboard mobile, ne pas rediriger — la session mobile n'a pas de refresh token standard
      if (window.location.pathname.startsWith('/mobile')) {
        return Promise.reject(error);
      }
      _authFailed = true;
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      _authChannel?.postMessage({ type: 'LOGOUT' });
      if (window.location.pathname !== '/login') window.location.href = '/login';
    } else if (status === 402) {
      // Licence expirée ou invalide (Soft-Lock) — ne pas interrompre la session mobile
      if (window.location.pathname !== '/login' && !(window as any)._isRedirecting402 && !window.location.pathname.startsWith('/mobile')) {
        (window as any)._isRedirecting402 = true;
        window.location.href = '/login?locked=true';
      }
    } else if (status >= 500) {
      toast.error('Erreur Serveur (500)', { id: 'server-error' });
    }


    return Promise.reject(error);
  }
);
