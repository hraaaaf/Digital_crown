import axios from 'axios';
import { API_BASE } from './api';

const API_URL = `${API_BASE}/api`;

const KEYS = { access: 'token', refresh: 'refresh_token' };

const store = {
  get: (key: string) => {
    try { return localStorage.getItem(key) || sessionStorage.getItem(key); } catch { return null; }
  },
  set: (key: string, value: string, persistent: boolean) => {
    try { (persistent ? localStorage : sessionStorage).setItem(key, value); } catch { /* ignore */ }
  },
  remove: (key: string) => {
    try { localStorage.removeItem(key); sessionStorage.removeItem(key); } catch { /* ignore */ }
  },
};

export const authService = {
  async login(email: string, password: string, rememberMe: boolean = true) {
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);

    const response = await axios.post(`${API_URL}/auth/login`, params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    const { access_token, refresh_token } = response.data;
    if (access_token) store.set(KEYS.access, access_token, rememberMe);
    if (refresh_token) store.set(KEYS.refresh, refresh_token, rememberMe);

    return response.data;
  },

  async logout() {
    const refresh_token = store.get(KEYS.refresh);
    try {
      const token = store.get(KEYS.access);
      if (token && refresh_token) {
        await axios.post(
          `${API_URL}/auth/logout`,
          { refresh_token },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      }
    } catch { /* best-effort */ }
    store.remove(KEYS.access);
    store.remove(KEYS.refresh);
    window.location.href = '/login';
  },

  async refresh() {
    const refresh_token = store.get(KEYS.refresh);
    if (!refresh_token) return false;
    try {
      const response = await axios.post(`${API_URL}/auth/refresh`, { refresh_token });
      const { access_token, refresh_token: new_refresh } = response.data;
      const persistent = !!localStorage.getItem(KEYS.refresh);
      store.set(KEYS.access, access_token, persistent);
      store.set(KEYS.refresh, new_refresh, persistent);
      return true;
    } catch {
      store.remove(KEYS.access);
      store.remove(KEYS.refresh);
      return false;
    }
  },

  getToken() {
    return store.get(KEYS.access);
  },

  async getCurrentUser() {
    const token = this.getToken();
    if (!token) return null;
    try {
      const response = await axios.get(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data;
    } catch {
      await this.logout();
      return null;
    }
  },

  isAuthenticated() {
    return !!this.getToken();
  },
};
