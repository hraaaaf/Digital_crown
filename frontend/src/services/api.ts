import axios from 'axios';

// CTO Rigor: Synchronized Backend endpoint (Port 8000)
// Using 127.0.0.1 for direct and fast resolution
const API_BASE_URL = 'http://127.0.0.1:8000/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // Timeout increased to 30s for AI model inference
  // Note: Do NOT set Content-Type header here - let axios auto-detect for FormData
});

// Interceptor to inject JWT token automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor for global error handling and system notification
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      // Critical case: Backend server is not responding
      console.error("CRITICAL ERROR: Backend server is offline at " + API_BASE_URL);
    } else {
      // Error returned by the API (4xx, 5xx)
      const errorData = error.response.data;
      console.group(`Elite API Error [${error.response.status}]`);
      console.error("Path:", error.config?.url);
      console.error("Details:", errorData?.detail || errorData || error.message);
      if (errorData?.detail && Array.isArray(errorData.detail)) {
        console.table(errorData.detail);
      }
      console.groupEnd();
      if (error.response.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('token');
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);