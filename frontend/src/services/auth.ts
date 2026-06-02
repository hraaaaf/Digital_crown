import { supabase } from '../lib/supabase';
import axios from 'axios';
import { API_BASE } from './api';

const API_URL = `${API_BASE}/api`;

export const authService = {
  /**
   * Login via Supabase (Cloud Auth)
   */
  async login(email: string, password: string) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) throw error;

    // Une fois connecté au Cloud, on synchronise avec le backend local
    // pour vérifier la licence et obtenir un token local si nécessaire.
    if (data.session && data.user?.email) {
      await this.syncWithBackend(data.session.access_token, data.user.email);
    }

    return data;
  },

  /**
   * Synchroniser la session Supabase avec le backend local
   */
  async syncWithBackend(accessToken: string, email: string) {
    try {
      const response = await axios.post(`${API_URL}/auth/sync-supabase`, {
        access_token: accessToken,
        email: email,
      });
      if (response.data.token) {
        // Le backend pose les cookies HttpOnly — pas d'écriture localStorage
        // Le token reçu reste disponible en mémoire si besoin de fallback legacy
        return true;
      }
    } catch (err: any) {
      const status = err?.response?.status;
      if (status === 500) {
        console.error('[Auth] Supabase non configuré sur le serveur. Vérifiez SUPABASE_URL et SUPABASE_ANON_KEY dans le .env backend.');
      } else if (status === 401) {
        console.warn('[Auth] Session Cloud expirée ou invalide, re-connexion requise.');
      } else {
        console.error('[Auth] Échec de la synchronisation backend:', err?.message ?? err);
      }
    }
    return false;
  },


  /**
   * Login via Google (OAuth)
   */
  async loginWithGoogle() {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: window.location.origin + '/dashboard',
      }
    });
    if (error) throw error;
    return data;
  },

  /**
   * Logout (Cloud + Local)
   */
  async logout() {
    const token = localStorage.getItem('token');
    const refreshToken = localStorage.getItem('refresh_token');
    if (token && refreshToken) {
      try {
        await axios.post(`${API_URL}/auth/logout`, { refresh_token: refreshToken }, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } catch { /* blacklist best-effort */ }
    }
    await supabase.auth.signOut();
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  },

  /**
   * Récupérer le token actuel (Supabase Access Token)
   */
  async getToken() {
    // On priorise le token local pour le backend
    const localToken = localStorage.getItem('token');
    if (localToken) return localToken;
    
    // Fallback sur la session Supabase si besoin
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || null;
  },

  /**
   * Récupérer l'utilisateur actuel
   */
  async getCurrentUser() {
    const { data: { user } } = await supabase.auth.getUser();
    return user;
  },

  /**
   * Vérifie si un JWT local est expiré (lecture du payload uniquement, sans vérif de signature)
   */
  isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp * 1000 < Date.now();
    } catch {
      return true;
    }
  },

  /**
   * Vérifier si l'utilisateur est authentifié
   */
  async isAuthenticated() {
    const { data: { session } } = await supabase.auth.getSession();
    if (session) {
      const localToken = localStorage.getItem('token');
      // Pas de token local → sync via Supabase
      if (!localToken && session.user?.email) {
        return await this.syncWithBackend(session.access_token, session.user.email);
      }
      // Token local expiré → sync pour en obtenir un frais
      if (localToken && this.isTokenExpired(localToken) && session.user?.email) {
        return await this.syncWithBackend(session.access_token, session.user.email);
      }
      return true;
    }
    return false;
  },

  /**
   * Récupérer le profil complet (Cloud + Local)
   */
  async getFullProfile() {
    const user = await this.getCurrentUser();
    if (!user) return null;

    try {
      const token = await this.getToken();
      const response = await axios.get(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return { ...user, ...response.data };
    } catch {
      return user;
    }
  },

  /**
   * Envoyer un email de réinitialisation de mot de passe
   */
  async resetPassword(email: string) {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: window.location.origin + '/reset-password',
    });
    if (error) throw error;
  },

  /**
   * Créer un nouveau compte (Cloud + sync Backend)
   */
  async register(email: string, password: string, fullName: string) {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { full_name: fullName },
      },
    });

    if (error) throw error;

    // Synchroniser avec le backend local après la création du compte
    if (data.session && data.user?.email) {
      await this.syncWithBackend(data.session.access_token, data.user.email);
    }

    return data;
  }
};

