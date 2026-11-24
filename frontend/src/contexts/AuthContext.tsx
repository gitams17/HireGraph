"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

import { api } from "@/lib/api";
import type { User } from "@/types";

// ---------------------------------------------------------------------------
// Context shape
// ---------------------------------------------------------------------------

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (credentials: { email: string; password: string }) => Promise<User>;
  register: (data: any) => Promise<User>;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    // Prime the CSRF cookie first so mutation requests work immediately.
    try {
      await api.get<{ csrfToken: string }>("/api/v1/auth/csrf/");
    } catch {
      // Not fatal — the CSRF cookie may already be set.
    }

    try {
      const me = await api.get<User>("/api/v1/auth/me/");
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = useCallback(async (credentials: { email: string; password: string }) => {
    const loggedInUser = await api.post<User>("/api/v1/auth/login/", credentials);
    setUser(loggedInUser);
    return loggedInUser;
  }, []);

  const register = useCallback(async (data: any) => {
    const registeredUser = await api.post<User>("/api/v1/auth/register/", data);
    setUser(registeredUser);
    return registeredUser;
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post("/api/v1/auth/logout/", {});
    } finally {
      setUser(null);
      // Hard-navigate to clear client state.
      window.location.href = "/login";
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, refresh: fetchUser, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>.");
  return ctx;
}
