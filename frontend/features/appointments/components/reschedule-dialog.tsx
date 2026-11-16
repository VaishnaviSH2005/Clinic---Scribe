"use client";

import { useEffect, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { FormField } from "@/components/forms/form-field";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import type { Appointment } from "@/types/appointment";

import { isPastTimeError, useAppointmentMutations } from "../hooks/use-appointments";
import { PastTimeDialog } from "./past-time-dialog";
import { rescheduleFormSchema, type RescheduleFormValues } from "../utils/schemas";

interface RescheduleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  appointment: Appointment | null;
}

export function RescheduleDialog({ open, onOpenChange, appointment }: RescheduleDialogProps) {
  const { reschedule } = useAppointmentMutations();
  const [pastTime, setPastTime] = useState<string | null>(null);
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
    const scheduledAt = new Date(values.scheduled_at).toISOString();
    reschedule.mutate(
      { id: appointment.id, scheduledAt },
      {
        onSuccess: () => onOpenChange(false),
        onError: (error) => {
          if (isPastTimeError(error)) setPastTime(scheduledAt);
        },
      },
    );
  };

  const bookAnyway = () => {
    if (!appointment || !pastTime) return;
    reschedule.mutate(
      { id: appointment.id, scheduledAt: pastTime, allowPast: true },
      {
        onSuccess: () => {
          setPastTime(null);
          onOpenChange(false);
        },
      },
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
      <PastTimeDialog
        open={pastTime !== null}
        onChooseAnother={() => setPastTime(null)}
        onBookAnyway={bookAnyway}
        loading={reschedule.isPending}
      />
    </Dialog>
  );
}
