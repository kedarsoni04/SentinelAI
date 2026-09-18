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

  // On mount: restore from localStorage/cookie, then validate token with backend
  useEffect(() => {
    let isMounted = true;

    const initAuth = async () => {
      const token = getStoredToken();
      const storedUser = getStoredUser();

      if (!token) {
        clearAuthData();
        if (isMounted) setIsLoading(false);
        return;
      }

      // Optimistically set stored user for instant UI feedback
      if (storedUser && isMounted) {
        setUser(storedUser);
      }

      try {
        const freshUser = await getCurrentUser();
        if (isMounted) {
          setUser(freshUser);
          saveAuthData(token, freshUser);
        }
      } catch {
        // Token invalid or expired — clear storage and cookies
        clearAuthData();
        if (isMounted) setUser(null);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    initAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  const login = useCallback(async (data: LoginRequest) => {
    const response = await loginService(data);
    saveAuthData(response.access_token, response.user);
    setUser(response.user);
  }, []);

  const register = useCallback(async (data: RegisterRequest) => {
    await registerService(data);
    // Automatically log the user in upon successful registration
    const response = await loginService({ email: data.email, password: data.password });
    saveAuthData(response.access_token, response.user);
    setUser(response.user);
  }, []);

  const logout = useCallback(async () => {
    await logoutService();
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const freshUser = await getCurrentUser();
      const token = getStoredToken();
      if (token) saveAuthData(token, freshUser);
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
