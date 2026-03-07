import axios from 'axios';

// Rigueur CTO : Point de terminaison Backend synchronisé (Port 8000)
// Utilisation de 127.0.0.1 pour une résolution directe et rapide
const API_BASE_URL = 'http://127.0.0.1:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // Timeout augmenté à 30s pour l'inférence du modèle IA
  // Note: Do NOT set Content-Type header here - let axios auto-detect for FormData
});

// Intercepteur pour gestion d'erreurs globale et notification système
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      // Cas critique : Le serveur Backend ne répond pas du tout
      console.error("ERREUR CRITIQUE : Le serveur Backend est hors ligne sur " + API_BASE_URL);
    } else {
      // Erreur retournée par l'API (4xx, 5xx)
      console.error(
        `Erreur API [${error.response.status}]:`, 
        error.response.data || error.message
      );
    }
    return Promise.reject(error);
  }
);