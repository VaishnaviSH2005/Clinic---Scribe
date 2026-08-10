"use client";

import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";

import { FormField } from "@/components/forms/form-field";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { PatientSelect } from "@/components/forms/patient-select";
import { useDepartments } from "@/features/settings/hooks/use-departments";
import { useDoctors } from "@/features/settings/hooks/use-staff";

import { useAppointmentMutations } from "../hooks/use-appointments";
import { appointmentFormSchema, type AppointmentFormValues } from "../utils/schemas";

interface AppointmentFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  defaultPatientId?: string;
}

export function AppointmentFormDialog({
  open,
  onOpenChange,
  defaultPatientId,
}: AppointmentFormDialogProps) {
  const { create } = useAppointmentMutations();
  const { data: departmentsData } = useDepartments(1, 100);
  const { data: doctorsData } = useDoctors({ page: 1, pageSize: 100 });
  const departments = departmentsData?.data ?? [];
  const doctors = doctorsData?.data ?? [];

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<AppointmentFormValues>({ resolver: zodResolver(appointmentFormSchema) });

  useEffect(() => {
    if (open) {
      reset({
        patient_id: defaultPatientId ?? "",
        doctor_id: "",
        department_id: "",
        scheduled_at: "",
      });
    }
  }, [open, defaultPatientId, reset]);

  const onSubmit = (values: AppointmentFormValues) => {
    create.mutate(
      { ...values, scheduled_at: new Date(values.scheduled_at).toISOString() },
      { onSuccess: () => onOpenChange(false) },
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Schedule appointment</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
          <FormField label="Patient" htmlFor="patient_id" error={errors.patient_id?.message}>
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
          </FormField>
          <FormField
            label="Department"
            htmlFor="department_id"
            error={errors.department_id?.message}
          >
            <Select
              id="department_id"
              error={!!errors.department_id}
              {...register("department_id")}
            >
              <option value="">Select a department</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField label="Doctor" htmlFor="doctor_id" error={errors.doctor_id?.message}>
            <Select id="doctor_id" error={!!errors.doctor_id} {...register("doctor_id")}>
              <option value="">Select a doctor</option>
              {doctors.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.full_name}
                  {d.specialization ? ` — ${d.specialization}` : ""}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField
            label="Date & time"
            htmlFor="scheduled_at"
            error={errors.scheduled_at?.message}
          >
            <Input
              id="scheduled_at"
              type="datetime-local"
              error={!!errors.scheduled_at}
              {...register("scheduled_at")}
            />
          </FormField>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" loading={create.isPending}>
              Schedule appointment
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
