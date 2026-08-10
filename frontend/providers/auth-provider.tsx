"use client";

import { useEffect } from "react";

import { authService } from "@/features/authentication/services/auth.service";
import { useAuthStore } from "@/store/auth.store";

/**
 * Hydrates the Authentication Context on app startup (PRD Ch19 —
 * "Application Startup": GET /auth/me -> Validate Session -> Load User
 * Profile -> Render Application). The backend remains the sole source of
 * truth; this only mirrors its answer into client state.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated);
  const setUnauthenticated = useAuthStore((s) => s.setUnauthenticated);

  useEffect(() => {
    let cancelled = false;

    authService
      .me()
      .then((user) => {
        if (!cancelled) setAuthenticated(user);
      })
      .catch(() => {
        if (!cancelled) setUnauthenticated();
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return <>{children}</>;
}
