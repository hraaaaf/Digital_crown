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

    // Auto-refresh on 401 (once per request, skip the /auth/ endpoints)
    if (status === 401 && !original._retried && !original.url?.includes('/auth/')) {
      original._retried = true;
      if (!_refreshing) {
        // Import lazily to avoid circular dependency
        _refreshing = import('./auth').then(m => m.authService.refresh()).finally(() => { _refreshing = null; });
      }
      const ok = await _refreshing;
      if (ok) return api(original);
      // Refresh failed → force logout
      try { localStorage.removeItem('token'); sessionStorage.removeItem('token'); } catch { /* ignore */ }
      if (window.location.pathname !== '/login') window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);
