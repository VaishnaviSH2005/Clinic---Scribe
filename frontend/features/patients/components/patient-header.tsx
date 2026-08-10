"use client";

import { useState } from "react";
import { Pencil, Stethoscope } from "lucide-react";

import { StatusBadge } from "@/components/badges/status-badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { StartConsultationDialog } from "@/features/consultation/components/start-consultation-dialog";
import { useAuth } from "@/features/authentication/hooks/use-auth";
import type { Patient } from "@/types/patient";

import { PatientEditDialog } from "./patient-edit-dialog";

export function PatientHeader({ patient }: { patient: Patient }) {
  const { user } = useAuth();
  const [editOpen, setEditOpen] = useState(false);
  const [consultationOpen, setConsultationOpen] = useState(false);

  return (
    <Card className="flex flex-wrap items-center justify-between gap-4">
      <div className="flex items-center gap-4">
        <div className="bg-muted flex h-16 w-16 items-center justify-center rounded-full text-h4 font-semibold text-text-secondary">
          {patient.full_name.charAt(0).toUpperCase()}
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-h3 text-text-primary">{patient.full_name}</h1>
            <StatusBadge status={patient.status} />
          </div>
          <p className="text-body text-text-secondary">
            {patient.uhid} · {patient.age} yrs · {patient.gender} ·{" "}
            {patient.blood_group ?? "Blood group unknown"}
          </p>
          <p className="text-body text-text-secondary">
            {patient.mobile_number}
            {patient.email ? ` · ${patient.email}` : ""}
          </p>
        </div>
      </div>
      <div className="flex gap-2">
        {user?.role === "doctor" && (
          <Button onClick={() => setConsultationOpen(true)}>
            <Stethoscope className="h-4 w-4" /> Start consultation
          </Button>
        )}
        <Button variant="secondary" onClick={() => setEditOpen(true)}>
          <Pencil className="h-4 w-4" /> Edit details
        </Button>
      </div>
      <PatientEditDialog open={editOpen} onOpenChange={setEditOpen} patient={patient} />
      <StartConsultationDialog
        open={consultationOpen}
        onOpenChange={setConsultationOpen}
        defaultPatientId={patient.id}
      />
    </Card>
  );
}
