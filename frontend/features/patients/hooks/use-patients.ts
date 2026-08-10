"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { ApiClientError } from "@/lib/api-client";
import type { PatientCreatePayload } from "@/types/patient";

import { patientService } from "../services/patient.service";

export function usePatients(params: {
  page: number;
  pageSize: number;
  search?: string;
  includeArchived?: boolean;
}) {
  return useQuery({
    queryKey: ["patients", params],
    queryFn: () => patientService.list(params),
  });
}

export function usePatientMutations() {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["patients"] });

  const register = useMutation({
    mutationFn: (payload: PatientCreatePayload) => patientService.register(payload),
    onSuccess: () => {
      toast.success("Patient registered successfully.");
      void invalidate();
    },
    onError: (error: unknown) => {
      if (error instanceof ApiClientError && error.errorCode === "DUPLICATE_PATIENT") {
        toast.error("A patient with this mobile number already exists.");
      } else {
        toast.error("Unable to register patient. Please try again.");
      }
    },
  });

  const archive = useMutation({
    mutationFn: (id: string) => patientService.archive(id),
    onSuccess: () => {
      toast.success("Patient archived successfully.");
      void invalidate();
    },
    onError: () => toast.error("Unable to archive patient."),
  });

  const restore = useMutation({
    mutationFn: (id: string) => patientService.restore(id),
    onSuccess: () => {
      toast.success("Patient restored successfully.");
      void invalidate();
    },
    onError: () => toast.error("Unable to restore patient."),
  });

  return { register, archive, restore };
}
