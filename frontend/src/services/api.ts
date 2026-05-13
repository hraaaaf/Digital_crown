import axios from 'axios';

export const API_BASE = (import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');

export const api = axios.create({
  baseURL: `${API_BASE}/api`,
  timeout: 30000,
});

// Token injector
api.interceptors.request.use((config) => {
  try {
    const token = localStorage.getItem('token') || sessionStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  } catch { /* ignore */ }
  return config;
});

let _refreshing: Promise<boolean> | null = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;

    if (!error.response) {
      console.error('CRITICAL: Backend offline at', API_BASE);
      return Promise.reject(error);
    }

    const { status, data, config: cfg } = error.response;
    console.group(`API Error [${status}]`);
    console.error('Path:', cfg?.url);
    console.error('Details:', data?.detail || data || error.message);
    if (data?.detail && Array.isArray(data.detail)) console.table(data.detail);
    console.groupEnd();

    // Auto-refresh/Sync on 401
    if (status === 401 && !original._retried && !original.url?.includes('/auth/')) {
      original._retried = true;
      
      if (!_refreshing) {
        _refreshing = (async () => {
          const { authService } = await import('./auth');
          const user = await authService.getCurrentUser();
          const token = await authService.getToken(); // Supabase token if local is missing
          
          if (user?.email && token) {
            // Tentative de re-synchro silencieuse avec le backend local
            return await authService.syncWithBackend(token, user.email);
          }
          return false;
        })().finally(() => { _refreshing = null; });
      }
      
      const ok = await _refreshing;
      if (ok) return api(original);
      
      // Échec total → logout
      localStorage.removeItem('token');
      if (window.location.pathname !== '/login') window.location.href = '/login';
    }


    return Promise.reject(error);
  }
);
