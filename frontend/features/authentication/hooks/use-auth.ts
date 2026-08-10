"use client";

import { useCallback } from "react";
import { useRouter } from "next/navigation";

import { ROUTES } from "@/constants/routes";
import { useAuthStore } from "@/store/auth.store";

import { authService } from "../services/auth.service";

export function useAuth() {
  const router = useRouter();
  const status = useAuthStore((s) => s.status);
  const user = useAuthStore((s) => s.user);
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated);
  const setUnauthenticated = useAuthStore((s) => s.setUnauthenticated);

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } finally {
      setUnauthenticated();
      router.push(ROUTES.login);
    }
  }, [router, setUnauthenticated]);

  return {
    status,
    user,
    isAuthenticated: status === "authenticated",
    isLoading: status === "loading",
    setAuthenticated,
    logout,
  };
}
