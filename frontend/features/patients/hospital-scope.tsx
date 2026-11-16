"use client";

import { useAuth } from "@/features/authentication/hooks/use-auth";

// The hospital-scope plumbing is shared with Reports; re-exported here so the
// patient components keep a single local import.
export { HospitalScopeProvider, useHospitalScope } from "@/features/hospital-scope/hospital-scope";

/** Super Admin can view patients (PRD Ch6.15) but never change them (Ch6.3). */
export function useCanModifyPatients(): boolean {
  const { user } = useAuth();
  return user?.role !== "super_admin";
}
