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
 * If NEXT_PUBLIC_API_URL lacks a protocol (e.g. Render's property: host providing host without https://),
 * it safely prefixes https://.
 */
export function getApiBaseUrl(): string {
  const raw = (process.env.NEXT_PUBLIC_API_URL || '').trim();
  if (!raw) return 'http://localhost:8000';
  if (raw.startsWith('http://') || raw.startsWith('https://') || raw.startsWith('/')) {
    return raw;
  }
  return `https://${raw}`;
}

const api = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 45000,
});

// ─── Request Interceptor ─────────────────────────────────────────────────────
// Automatically attach the JWT token from storage to every request.

api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = getStoredToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
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
    if (error.code === 'ECONNABORTED' || !error.response) {
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
