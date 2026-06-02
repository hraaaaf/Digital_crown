import axios from 'axios';
import toast from 'react-hot-toast';

export const API_BASE = (import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8005').replace(/\/$/, '');

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
  // Ne plus écrire en localStorage — le backend pose les cookies HttpOnly
  // BroadcastChannel maintenu pour synchroniser les onglets via fallback legacy
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

// Request interceptor — annule toute requête si la session est terminée
api.interceptors.request.use((config) => {
  if (_authFailed) {
    return Promise.reject(new axios.Cancel('Session expirée — requête annulée.'));
  }
  try {
    const token = localStorage.getItem('token') || sessionStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  } catch { /* ignore */ }
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
        toast.error('Serveur injoignable', { id: 'network-error' });
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

    // Auto-refresh/Sync on 401
    if (status === 401 && !original._retried && !original.url?.includes('/auth/')) {
      original._retried = true;

      if (!_refreshing) {
        _refreshing = (async () => {
          // 1. Essayer le refresh token local (rotation côté backend)
          const refreshToken = localStorage.getItem('refresh_token');
          if (refreshToken) {
            try {
              const res = await axios.post(`${API_BASE}/api/auth/refresh`, {
                refresh_token: refreshToken
              });
              const { access_token, refresh_token: newRefresh } = res.data;
              if (access_token) {
                // Le backend pose les nouveaux cookies HttpOnly — pas de stockage local
                // BroadcastChannel pour notifier les autres onglets (fallback)
                storeTokens(access_token, newRefresh);
                return true;
              }
            } catch {
              localStorage.removeItem('refresh_token');
            }
          }

          // 2. Fallback : re-sync via session Supabase active
          localStorage.removeItem('token');
          const { authService } = await import('./auth');
          const { supabase } = await import('../lib/supabase');

          const { data: { session } } = await supabase.auth.getSession();
          if (session?.access_token && session.user?.email) {
            return await authService.syncWithBackend(session.access_token, session.user.email);
          }

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
      _authFailed = true;
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      _authChannel?.postMessage({ type: 'LOGOUT' });
      if (window.location.pathname !== '/login') window.location.href = '/login';
    } else if (status === 402) {
      // Licence expirée ou invalide (Soft-Lock)
      if (window.location.pathname !== '/login' && !(window as any)._isRedirecting402) {
        (window as any)._isRedirecting402 = true;
        window.location.href = '/login?locked=true';
      }
    } else if (status >= 500) {
      toast.error('Erreur Serveur (500)', { id: 'server-error' });
    }


    return Promise.reject(error);
  }
);
