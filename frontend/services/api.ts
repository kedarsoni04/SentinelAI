import axios, { AxiosError, AxiosResponse } from 'axios';

/**
 * Centralized Axios instance for all SentinelAI API requests.
 *
 * Base URL is configured via NEXT_PUBLIC_API_URL environment variable.
 * All components and services must use this instance — never hardcode URLs.
 */
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// ─── Request Interceptor ─────────────────────────────────────────────────────
// Automatically attach the JWT token from localStorage to every request.

api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('sentinel_token');
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

    // 401: Token expired or invalid — clear local auth state
    if (error.response.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('sentinel_token');
        localStorage.removeItem('sentinel_user');
        // Redirect to login if not already there
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login';
        }
      }
    }

    return Promise.reject(error);
  }
);

export default api;
