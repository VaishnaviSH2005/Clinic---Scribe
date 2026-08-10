"use client";

import { useEffect, useState } from "react";

import { FormField } from "@/components/forms/form-field";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { Consultation } from "@/types/consultation";

import { useConsultationActions } from "../hooks/use-consultation-workspace";

interface ConsultationNotesPanelProps {
  consultation: Consultation;
  readOnly: boolean;
}

// Consultation Notes Panel (PRD Ch9.6 — "Manual notes entered by doctor. AI
// never overwrites manual notes."). Saved on blur so nothing is lost while
// the doctor is still typing, without needing a modal "Save" step.
export function ConsultationNotesPanel({ consultation, readOnly }: ConsultationNotesPanelProps) {
  const { updateNotes } = useConsultationActions(consultation.id);
  const [chiefComplaint, setChiefComplaint] = useState(consultation.chief_complaint ?? "");
  const [notes, setNotes] = useState(consultation.doctor_notes ?? "");

  useEffect(() => {
    setChiefComplaint(consultation.chief_complaint ?? "");
    setNotes(consultation.doctor_notes ?? "");
  }, [consultation.id, consultation.chief_complaint, consultation.doctor_notes]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Consultation notes</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <FormField label="Chief complaint" htmlFor="chief_complaint">
          <Input
            id="chief_complaint"
            value={chiefComplaint}
            disabled={readOnly}
            onChange={(e) => setChiefComplaint(e.target.value)}
            onBlur={() => {
              if (chiefComplaint !== (consultation.chief_complaint ?? "")) {
                updateNotes.mutate({ chief_complaint: chiefComplaint });
              }
            }}
          />
        </FormField>
        <FormField label="Notes" htmlFor="doctor_notes">
          <textarea
            id="doctor_notes"
            value={notes}
            disabled={readOnly}
            onChange={(e) => setNotes(e.target.value)}
            onBlur={() => {
              if (notes !== (consultation.doctor_notes ?? "")) {
                updateNotes.mutate({ doctor_notes: notes });
              }
            }}
            rows={8}
            className="w-full rounded-md border border-border bg-surface p-4 text-body text-text-primary transition-colors duration-micro focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-60"
            placeholder="Enter consultation notes…"
          />
        </FormField>
      </CardContent>
    </Card>
  );
}
