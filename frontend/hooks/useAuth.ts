'use client';

import { useState, useEffect, useCallback } from 'react';
import type { User } from '@/types';
import {
  getCurrentUser,
  getStoredToken,
  getStoredUser,
  saveAuthData,
  clearAuthData,
  login as loginService,
  register as registerService,
  logout as logoutService,
} from '@/services/auth';
import type { LoginRequest, RegisterRequest } from '@/types';

interface UseAuthReturn {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

/**
 * Central auth hook — manages user state, login, register, and logout.
 * Validates the stored token on mount by calling /api/auth/me.
 */
export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount: restore from localStorage, then validate token with backend
  useEffect(() => {
    const initAuth = async () => {
      const token = getStoredToken();
      const storedUser = getStoredUser();

      if (!token) {
        setIsLoading(false);
        return;
      }

      // Optimistically set stored user for instant UI
      if (storedUser) setUser(storedUser);

      try {
        const freshUser = await getCurrentUser();
        setUser(freshUser);
        // Refresh stored user data in case it changed
        localStorage.setItem('sentinel_user', JSON.stringify(freshUser));
      } catch {
        // Token invalid or expired — clear everything
        clearAuthData();
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = useCallback(async (data: LoginRequest) => {
    const response = await loginService(data);
    saveAuthData(response.access_token, response.user);
    // Also set a cookie for middleware-level route protection
    document.cookie = `sentinel_token=${response.access_token}; path=/; max-age=${60 * 60}; SameSite=Strict`;
    setUser(response.user);
  }, []);

  const register = useCallback(async (data: RegisterRequest) => {
    await registerService(data);
    // Automatically log the user in upon successful registration
    const response = await loginService({ email: data.email, password: data.password });
    saveAuthData(response.access_token, response.user);
    document.cookie = `sentinel_token=${response.access_token}; path=/; max-age=${60 * 60}; SameSite=Strict`;
    setUser(response.user);
  }, []);

  const logout = useCallback(async () => {
    await logoutService();
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const freshUser = await getCurrentUser();
      setUser(freshUser);
    } catch {
      clearAuthData();
      setUser(null);
    }
  }, []);

  return {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
  };
}
