"use client";

import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { StatusBadge } from "@/components/badges/status-badge";
import { Button } from "@/components/ui/button";
import type { Consultation, ConsultationPatientContext } from "@/types/consultation";

interface ConsultationHeaderProps {
  consultation: Consultation;
  patient: ConsultationPatientContext;
}

export function ConsultationHeader({ consultation, patient }: ConsultationHeaderProps) {
  const router = useRouter();

  return (
    <div className="flex items-center justify-between border-b border-border bg-surface px-6 py-4">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push("/consultations")}
          aria-label="Back"
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-h4 text-text-primary">{patient.full_name}</h1>
          <p className="text-caption text-text-secondary">
            {patient.uhid} · {patient.age} yrs · {patient.gender}
          </p>
        </div>
      </div>
      <StatusBadge status={consultation.status} />
    </div>
  );
}
