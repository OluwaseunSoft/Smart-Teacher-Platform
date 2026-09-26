import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { api } from "./api/client";
import {
  clearTokens,
  getAccessToken,
  setTokens,
} from "./api/authToken";
import type { User } from "./types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, displayName: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    if (!getAccessToken()) {
      setLoading(false);
      return;
    }
    api
      .me()
      .then((u) => active && setUser(u))
      .catch(() => active && setUser(null))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const onUnauthorized = () => setUser(null);
    window.addEventListener("suhail:unauthorized", onUnauthorized);
    return () =>
      window.removeEventListener("suhail:unauthorized", onUnauthorized);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await api.login(email, password);
    setTokens(tokens.access_token, tokens.refresh_token);
    setUser(await api.me());
  }, []);

  const signup = useCallback(
    async (email: string, password: string, displayName: string) => {
      const tokens = await api.signup({
        email,
        password,
        display_name: displayName,
      });
      setTokens(tokens.access_token, tokens.refresh_token);
      setUser(await api.me());
    },
    [],
  );

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } catch {
      /* token may already be invalid */
    }
    clearTokens();
    setUser(null);
  }, []);

  const refresh = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      return;
    }
    setUser(await api.me());
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, loading, login, signup, logout, refresh }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (ctx === null) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
