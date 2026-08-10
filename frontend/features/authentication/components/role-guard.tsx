"use client";

import type { Role } from "@/constants/roles";

import { useAuth } from "../hooks/use-auth";

interface RoleGuardProps {
  allow: Role[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * Role Guard (PRD Ch7.15/Ch19). UI-only convenience for hiding sections the
 * current role shouldn't see — never authoritative. The backend re-checks
 * every request via `require_roles` (Ch18) regardless of what this renders.
 */
export function RoleGuard({ allow, children, fallback = null }: RoleGuardProps) {
  const { user } = useAuth();
  if (!user || !allow.includes(user.role)) {
    return <>{fallback}</>;
  }
  return <>{children}</>;
}
