import axios, { AxiosError, AxiosResponse } from 'axios';

/**
 * Centralized Axios instance for all SentinelAI API requests.
 *
 * Base URL is configured via NEXT_PUBLIC_API_URL environment variable.
 * All components and services must use this instance — never hardcode URLs.
 */
import { clearAuthData, getStoredToken } from './auth';

/**
 * Normalizes the API base URL.
 *
 * Resolution order:
 * 1. NEXT_PUBLIC_API_URL env var (set in .env.local or Vercel/Render dashboard).
 * 2. If running in a browser on a non-localhost origin, use the Render production
 *    backend URL automatically — so Vercel deployments work without manual config.
 * 3. Fall back to http://localhost:8000 for local development.
 *
 * If the env var is set but lacks a protocol (Render sometimes supplies host-only),
 * https:// is prepended automatically.
 */
export function getApiBaseUrl(): string {
  const raw = (process.env.NEXT_PUBLIC_API_URL || '').trim();

  if (raw) {
    if (raw.startsWith('http://') || raw.startsWith('https://') || raw.startsWith('/')) {
      return raw;
    }
    return `https://${raw}`;
  }

  // Auto-detect production: if running in a browser on a non-localhost origin,
  // default to the Render backend rather than localhost (which is always unreachable).
  if (
    typeof window !== 'undefined' &&
    window.location.hostname !== 'localhost' &&
    window.location.hostname !== '127.0.0.1'
  ) {
    return 'https://sentinelai-backend-s3cz.onrender.com';
  }

  return 'http://localhost:8000';
}

const api = axios.create({
  baseURL: '',          // resolved dynamically in the request interceptor below
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 45000,
});

// ─── Request Interceptor ─────────────────────────────────────────────────────
// Automatically attach the JWT token from storage to every request.

api.interceptors.request.use(
  (config) => {
    // Dynamically resolve the base URL on each request so the runtime window
    // check in getApiBaseUrl() correctly detects non-localhost origins.
    if (!config.baseURL && config.url && !config.url.startsWith('http')) {
      config.url = `${getApiBaseUrl()}${config.url}`;
    }

    if (typeof window !== 'undefined') {
      const token = getStoredToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    // For FormData requests, remove explicit Content-Type to let browser/Axios compute boundary
    if (typeof FormData !== 'undefined' && config.data instanceof FormData) {
      delete config.headers['Content-Type'];
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response Interceptor ────────────────────────────────────────────────────
// Normalize error messages for consistent handling across the app.

api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.code === 'ECONNABORTED') {
      return Promise.reject(
        new Error(
          'Request timed out while communicating with SentinelAI services. The backend may be spinning up from sleep; please try again.'
        )
      );
    }

    if (!error.response) {
      return Promise.reject(
        new Error(
          'Unable to connect to SentinelAI services. Please check your connection and try again.'
        )
      );
    }

    // 401: Token expired or invalid — clear both localStorage & cookies to prevent redirect loops
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        clearAuthData();
        // Redirect to login if not already there
        if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/register')) {
          window.location.href = '/login';
        }
      }
    }

    return Promise.reject(error);
  }
);

export default api;
