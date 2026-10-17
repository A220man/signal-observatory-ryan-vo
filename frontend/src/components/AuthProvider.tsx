/**
 * Authentication context provider. Manages demo-mode JWT tokens in memory.
 * Tokens are never persisted to localStorage.
 */
import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { AuthContextType, TokenResponse, UserRole } from "../types";

export const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = (): AuthContextType => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [role, setRole] = useState<UserRole | null>(null);

  useEffect(() => {
    // Restore token from sessionStorage (transient, cleared on browser close)
    // This is acceptable for demo mode. Production uses Keycloak OIDC.
    const stored = sessionStorage.getItem("auth_token");
    const storedRole = sessionStorage.getItem("auth_role") as UserRole | null;
    if (stored && storedRole) {
      setToken(stored);
      setRole(storedRole);
    }
  }, []);

  const login = async (roleVal: UserRole, password: string) => {
    const resp: TokenResponse = await api.login({ role: roleVal, password });
    setToken(resp.access_token);
    setRole(resp.role);
    sessionStorage.setItem("auth_token", resp.access_token);
    sessionStorage.setItem("auth_role", resp.role);
  };

  const logout = () => {
    setToken(null);
    setRole(null);
    sessionStorage.removeItem("auth_token");
    sessionStorage.removeItem("auth_role");
  };

  const value = useMemo(
    () => ({ token, role, login, logout }),
    [token, role],
  );

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
};