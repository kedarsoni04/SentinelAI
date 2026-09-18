import { AxiosError } from 'axios';
import api from './api';
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '@/types';

const TOKEN_KEY = 'sentinel_token';
const USER_KEY = 'sentinel_user';

// ─── Storage Helpers ──────────────────────────────────────────────────────────

export function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp('(^|;\\s*)(' + name + ')=([^;]*)'));
  return match ? decodeURIComponent(match[3]) : null;
}

export function saveAuthData(token: string, user: User): void {
  if (typeof window !== 'undefined') {
    try {
      localStorage.setItem(TOKEN_KEY, token);
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    } catch {
      // ignore
    }
    // 24-hour cookie for edge middleware route protection
    document.cookie = `${TOKEN_KEY}=${encodeURIComponent(token)}; path=/; max-age=${60 * 60 * 24}; SameSite=Lax`;
  }
}

export function clearAuthData(): void {
  if (typeof window !== 'undefined') {
    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    } catch {
      // ignore
    }
    // Explicitly expire the cookie across all paths
    document.cookie = `${TOKEN_KEY}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; max-age=0; SameSite=Lax`;
  }
}

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  const localToken = localStorage.getItem(TOKEN_KEY);
  if (localToken && localToken !== 'undefined' && localToken !== 'null') {
    return localToken;
  }
  const cookieToken = getCookie(TOKEN_KEY);
  if (cookieToken && cookieToken !== 'undefined' && cookieToken !== 'null') {
    try {
      localStorage.setItem(TOKEN_KEY, cookieToken);
    } catch {
      // ignore
    }
    return cookieToken;
  }
  return null;
}

export function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw || raw === 'undefined' || raw === 'null') return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

// ─── Error Extraction ─────────────────────────────────────────────────────────

export function extractErrorMessage(error: unknown): string {
  if (error instanceof Error && !(error instanceof AxiosError)) {
    return error.message;
  }
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      return detail[0]?.msg || 'Validation error';
    }
  }
  return 'An unexpected error occurred. Please try again.';
}

// ─── Auth API Calls ───────────────────────────────────────────────────────────

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>('/api/auth/login', data);
  return response.data;
}

export async function register(data: RegisterRequest): Promise<User> {
  const response = await api.post<User>('/api/auth/register', data);
  return response.data;
}

export async function getCurrentUser(): Promise<User> {
  const response = await api.get<User>('/api/auth/me');
  return response.data;
}

export async function logout(): Promise<void> {
  clearAuthData();
}

export async function checkHealth(): Promise<{ status: string; service: string }> {
  const response = await api.get('/api/health');
  return response.data;
}
