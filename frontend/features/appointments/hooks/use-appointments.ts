"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { ApiClientError } from "@/lib/api-client";
import type { AppointmentCreatePayload, AppointmentStatus } from "@/types/appointment";

import { appointmentService } from "../services/appointment.service";

interface AppointmentListArgs {
  page: number;
  pageSize: number;
  dateFrom?: string;
  dateTo?: string;
  doctorId?: string;
  departmentId?: string;
  status?: AppointmentStatus;
}

export function useAppointments(args: AppointmentListArgs) {
  return useQuery({
    queryKey: ["appointments", args],
    queryFn: () => appointmentService.list(args),
  });
}

function friendlyError(error: unknown, fallback: string): string {
  if (error instanceof ApiClientError) {
    if (error.errorCode === "DOCTOR_UNAVAILABLE")
      return "This doctor already has an appointment at that time.";
    if (error.errorCode === "INVALID_APPOINTMENT_STATE") return error.message;
    return error.message || fallback;
  }
  return fallback;
}

export function useAppointmentMutations() {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["appointments"] });

  const create = useMutation({
    mutationFn: (payload: AppointmentCreatePayload) => appointmentService.create(payload),
    onSuccess: () => {
      toast.success("Appointment scheduled successfully.");
      void invalidate();
    },
    onError: (error: unknown) =>
      toast.error(friendlyError(error, "Unable to schedule appointment.")),
  });

  const reschedule = useMutation({
    mutationFn: ({ id, scheduledAt }: { id: string; scheduledAt: string }) =>
      appointmentService.reschedule(id, { scheduled_at: scheduledAt }),
    onSuccess: () => {
      toast.success("Appointment rescheduled successfully.");
      void invalidate();
    },
    onError: (error: unknown) =>
      toast.error(friendlyError(error, "Unable to reschedule appointment.")),
  });

  const checkIn = useMutation({
    mutationFn: (id: string) => appointmentService.checkIn(id),
    onSuccess: () => {
      toast.success("Patient checked in successfully.");
      void invalidate();
    },
    onError: (error: unknown) => toast.error(friendlyError(error, "Unable to check in patient.")),
  });

  const cancel = useMutation({
    mutationFn: (id: string) => appointmentService.cancel(id),
    onSuccess: () => {
      toast.success("Appointment cancelled successfully.");
      void invalidate();
    },
    onError: (error: unknown) => toast.error(friendlyError(error, "Unable to cancel appointment.")),
  });

  return { create, reschedule, checkIn, cancel };
}
