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
        localStorage.setItem('token', response.data.token);
        if (response.data.refresh_token) {
          localStorage.setItem('refresh_token', response.data.refresh_token);
        }
        return true;
      }
    } catch (err) {
      console.error('Échec de la synchronisation backend:', err);
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
   * Vérifier si l'utilisateur est authentifié
   */
  async isAuthenticated() {
    const { data: { session } } = await supabase.auth.getSession();
    return !!session;
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

