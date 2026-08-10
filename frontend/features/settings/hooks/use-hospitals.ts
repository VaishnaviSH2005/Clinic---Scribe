"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import type {
  HospitalCreatePayload,
  HospitalStatus,
  HospitalUpdatePayload,
} from "@/types/hospital";

import { hospitalService } from "../services/hospital.service";

export function useHospitals(page: number, pageSize: number) {
  return useQuery({
    queryKey: ["hospitals", page, pageSize],
    queryFn: () => hospitalService.list(page, pageSize),
  });
}

export function useHospitalMutations() {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["hospitals"] });

  const create = useMutation({
    mutationFn: (payload: HospitalCreatePayload) => hospitalService.create(payload),
    onSuccess: () => {
      toast.success("Hospital created successfully.");
      void invalidate();
    },
    onError: () => toast.error("Unable to create hospital. Please try again."),
  });

  const update = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: HospitalUpdatePayload }) =>
      hospitalService.update(id, payload),
    onSuccess: () => {
      toast.success("Hospital updated successfully.");
      void invalidate();
    },
    onError: () => toast.error("Unable to update hospital. Please try again."),
  });

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: HospitalStatus }) =>
      hospitalService.updateStatus(id, status),
    onSuccess: () => {
      toast.success("Hospital status updated successfully.");
      void invalidate();
    },
    onError: () => toast.error("Unable to update hospital status."),
  });

  const uploadLogo = useMutation({
    mutationFn: ({ id, file }: { id: string; file: File }) => hospitalService.uploadLogo(id, file),
    onSuccess: () => {
      toast.success("Hospital logo updated successfully.");
      void invalidate();
    },
    onError: () => toast.error("Unable to upload hospital logo."),
  });

  return { create, update, updateStatus, uploadLogo };
}
