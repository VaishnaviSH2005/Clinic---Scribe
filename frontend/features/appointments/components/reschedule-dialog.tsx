"use client";

import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { FormField } from "@/components/forms/form-field";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import type { Appointment } from "@/types/appointment";

import { useAppointmentMutations } from "../hooks/use-appointments";
import { rescheduleFormSchema, type RescheduleFormValues } from "../utils/schemas";

interface RescheduleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  appointment: Appointment | null;
}

export function RescheduleDialog({ open, onOpenChange, appointment }: RescheduleDialogProps) {
  const { reschedule } = useAppointmentMutations();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<RescheduleFormValues>({ resolver: zodResolver(rescheduleFormSchema) });

  useEffect(() => {
    if (open && appointment) {
      reset({ scheduled_at: appointment.scheduled_at.slice(0, 16) });
    }
  }, [open, appointment, reset]);

  const onSubmit = (values: RescheduleFormValues) => {
    if (!appointment) return;
    reschedule.mutate(
      { id: appointment.id, scheduledAt: new Date(values.scheduled_at).toISOString() },
      { onSuccess: () => onOpenChange(false) },
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Reschedule appointment</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
          <FormField
            label="New date & time"
            htmlFor="scheduled_at"
            error={errors.scheduled_at?.message}
          >
            <Input
              id="scheduled_at"
              type="datetime-local"
              autoFocus
              error={!!errors.scheduled_at}
              {...register("scheduled_at")}
            />
          </FormField>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" loading={reschedule.isPending}>
              Save changes
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
