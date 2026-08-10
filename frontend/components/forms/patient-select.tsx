"use client";

import { useEffect, useState } from "react";

import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { patientService } from "@/features/patients/services/patient.service";
import type { Patient } from "@/types/patient";

interface PatientSelectProps {
  value: string;
  onChange: (patientId: string) => void;
  error?: boolean;
}

// Lightweight search-then-select (PRD Ch5.19 realtime validation). Shared
// across Appointments and Consultation — a full autocomplete/combobox
// isn't warranted for this scope.
export function PatientSelect({ value, onChange, error }: PatientSelectProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Patient[]>([]);

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      return;
    }
    const timeout = setTimeout(() => {
      patientService
        .search(query)
        .then(setResults)
        .catch(() => setResults([]));
    }, 250);
    return () => clearTimeout(timeout);
  }, [query]);

  return (
    <div className="flex flex-col gap-2">
      <Input
        placeholder="Search by name, UHID, or mobile number…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <Select value={value} error={error} onChange={(e) => onChange(e.target.value)}>
        <option value="">Select a patient</option>
        {results.map((p) => (
          <option key={p.id} value={p.id}>
            {p.full_name} ({p.uhid})
          </option>
        ))}
      </Select>
    </div>
  );
}
