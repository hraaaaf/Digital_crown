import axios from 'axios';
import { API_BASE } from './api';

const API_URL = `${API_BASE}/api`;

export const authService = {
  /**
   * Login (Local API, qui vérifiera la licence Firebase via le middleware)
   */
  async login(email: string, password: string) {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    const response = await axios.post(`${API_URL}/auth/login`, formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });

    const data = response.data;
    if (data.access_token) {
      localStorage.setItem('token', data.access_token);
    }
    if (data.refresh_token) {
      localStorage.setItem('refresh_token', data.refresh_token);
    }
    
    return data;
  },

  /**
   * Logout (Local)
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
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  },

  /**
   * Récupérer le token actuel (Access Token Local)
   */
  getToken() {
    return localStorage.getItem('token') || null;
  },

  /**
   * Vérifie si un JWT local est expiré
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
    const token = this.getToken();
    if (!token) return false;
    
    if (this.isTokenExpired(token)) {
        // Tentative de refresh
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) return false;
        try {
            const response = await axios.post(`${API_URL}/auth/refresh`, { refresh_token: refreshToken });
            if (response.data.access_token) {
                localStorage.setItem('token', response.data.access_token);
                if (response.data.refresh_token) {
                    localStorage.setItem('refresh_token', response.data.refresh_token);
                }
                return true;
            }
        } catch {
            return false;
        }
    }
    
    return true;
  },

  /**
   * Récupérer l'utilisateur actuel
   */
  async getCurrentUser() {
    const token = this.getToken();
    if (!token) return null;
    try {
      const response = await axios.get(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data;
    } catch {
      return null;
    }
  },

  /**
   * Récupérer le profil complet
   */
  async getFullProfile() {
    return await this.getCurrentUser();
  },

  /**
   * Envoyer un email de réinitialisation de mot de passe
   */
  async resetPassword(email: string) {
    // A remplacer par un appel API local ou Firebase si nécessaire
    console.log("Password reset disabled during Firebase migration for", email);
  },

  /**
   * Créer un nouveau compte (Cloud/SaaS)
   */
  async register(email: string, password: string, fullName: string) {
    const response = await axios.post(`${API_URL}/auth/signup`, {
      email,
      password,
      nom_complet: fullName,
    });
    return response.data;
  }
};
