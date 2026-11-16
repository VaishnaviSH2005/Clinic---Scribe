"use client";

import { createContext, useContext, useEffect, useState } from "react";

import { Card, CardContent } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { useHospitals } from "@/features/settings/hooks/use-hospitals";

// Super Admin has no hospital of their own. Wherever they may VIEW a hospital's
// data (patients, reports) they first choose exactly one hospital; the backend
// enforces that choice (`hospital_id` query parameter, 422 when missing) and
// hospital staff are always pinned to their own hospital regardless.
const HospitalScopeContext = createContext<string | undefined>(undefined);

export const HospitalScopeProvider = HospitalScopeContext.Provider;

/** The hospital currently being viewed (set by the page for Super Admin). */
export function useHospitalScope(): string | undefined {
  return useContext(HospitalScopeContext);
}

const STORAGE_KEY = "cliniscribe.scope.hospital";

/** The Super Admin's chosen hospital, remembered for the browser session. */
export function useHospitalChoice(enabled: boolean) {
  const [hospitalId, setHospitalId] = useState("");

  useEffect(() => {
    if (!enabled) return;
    try {
      const saved = sessionStorage.getItem(STORAGE_KEY);
      if (saved) setHospitalId(saved);
    } catch {
      /* storage unavailable: the choice just won't persist */
    }
  }, [enabled]);

  const choose = (id: string) => {
    setHospitalId(id);
    try {
      sessionStorage.setItem(STORAGE_KEY, id);
    } catch {
      /* ignore */
    }
  };

  return { hospitalId, choose };
}

export function HospitalSelector({
  value,
  onChange,
}: {
  value: string;
  onChange: (id: string) => void;
}) {
  const { data: hospitals } = useHospitals(1, 100);
  return (
    <Card>
      <CardContent className="flex flex-col gap-2 sm:max-w-md">
        <label htmlFor="hospital-select" className="text-body font-medium text-text-primary">
          Hospital
        </label>
        <Select id="hospital-select" value={value} onChange={(e) => onChange(e.target.value)}>
          <option value="">Select a hospital…</option>
          {(hospitals?.data ?? []).map((h) => (
            <option key={h.id} value={h.id}>
              {h.name}
            </option>
          ))}
        </Select>
      </CardContent>
    </Card>
  );
}
