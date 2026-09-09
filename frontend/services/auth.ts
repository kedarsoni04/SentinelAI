import { AxiosError } from 'axios';
import api from './api';
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '@/types';

const TOKEN_KEY = 'sentinel_token';
const USER_KEY = 'sentinel_user';

// ─── Storage Helpers ──────────────────────────────────────────────────────────

export function saveAuthData(token: string, user: User): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuthData(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
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
  // Set a cookie to signal middleware the user is logged out
  document.cookie = 'sentinel_token=; path=/; max-age=0';
}

export async function checkHealth(): Promise<{ status: string; service: string }> {
  const response = await api.get('/api/health');
  return response.data;
}
