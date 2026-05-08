import axios from 'axios';

export const API_BASE = (import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');

export const api = axios.create({
  baseURL: `${API_BASE}/api`,
  timeout: 30000,
  // Note: Do NOT set Content-Type here — let axios auto-detect for FormData
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      console.error('CRITICAL: Backend offline at', API_BASE);
    } else {
      const { status, data, config: cfg } = error.response;
      console.group(`API Error [${status}]`);
      console.error('Path:', cfg?.url);
      console.error('Details:', data?.detail || data || error.message);
      if (data?.detail && Array.isArray(data.detail)) console.table(data.detail);
      console.groupEnd();
      if (status === 401) {
        localStorage.removeItem('token');
        sessionStorage.removeItem('token');
        if (window.location.pathname !== '/login') window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
