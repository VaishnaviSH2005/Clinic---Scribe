"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { PatientSelect } from "@/components/forms/patient-select";
import { FormField } from "@/components/forms/form-field";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { usePatient } from "@/features/patients/hooks/use-patient-detail";

import { useStartConsultation } from "../hooks/use-consultations";

const schema = z.object({
  patient_id: z.string().min(1, "Patient is required."),
  chief_complaint: z.string().optional(),
});
type FormValues = z.infer<typeof schema>;

interface StartConsultationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  defaultPatientId?: string;
  appointmentId?: string;
}

export function StartConsultationDialog({
  open,
  onOpenChange,
  defaultPatientId,
  appointmentId,
}: StartConsultationDialogProps) {
  const router = useRouter();
  const start = useStartConsultation();
  const { data: preselectedPatient } = usePatient(defaultPatientId ?? "");
  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  useEffect(() => {
    if (open) reset({ patient_id: defaultPatientId ?? "", chief_complaint: "" });
  }, [open, defaultPatientId, reset]);

  const onSubmit = (values: FormValues) => {
    start.mutate(
      {
        patient_id: values.patient_id,
        chief_complaint: values.chief_complaint || undefined,
        appointment_id: appointmentId,
      },
      {
        onSuccess: (consultation) => {
          onOpenChange(false);
          router.push(`/consultations/${consultation.id}`);
        },
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Start consultation</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
          <FormField label="Patient" htmlFor="patient_id" error={errors.patient_id?.message}>
            {defaultPatientId ? (
              <Input
                disabled
                readOnly
                value={
                  preselectedPatient
                    ? `${preselectedPatient.full_name} (${preselectedPatient.uhid})`
                    : "Loading…"
                }
              />
            ) : (
              <Controller
                control={control}
                name="patient_id"
                render={({ field }) => (
                  <PatientSelect
                    value={field.value}
                    onChange={field.onChange}
                    error={!!errors.patient_id}
                  />
                )}
              />
            )}
          </FormField>
          <FormField label="Chief complaint (optional)" htmlFor="chief_complaint">
            <Input id="chief_complaint" {...register("chief_complaint")} />
          </FormField>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" loading={start.isPending}>
              Start consultation
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
