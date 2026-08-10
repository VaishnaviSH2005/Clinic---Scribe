"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { ApiClientError } from "@/lib/api-client";
import type {
  DoctorCreatePayload,
  ReceptionistCreatePayload,
  UserStatus,
  UserUpdatePayload,
} from "@/types/user";

import { doctorService, receptionistService, userService } from "../services/staff.service";

interface StaffListArgs {
  page: number;
  pageSize: number;
  search?: string;
  status?: UserStatus;
  departmentId?: string;
}

export function useAllStaff(args: StaffListArgs) {
  return useQuery({
    queryKey: ["staff", "all", args],
    queryFn: () => userService.list(args),
  });
}

export function useDoctors(args: StaffListArgs) {
  return useQuery({
    queryKey: ["staff", "doctors", args],
    queryFn: () => doctorService.list(args),
  });
}

export function useReceptionists(args: StaffListArgs) {
  return useQuery({
    queryKey: ["staff", "receptionists", args],
    queryFn: () => receptionistService.list(args),
  });
}

function friendlyErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiClientError) {
    if (error.errorCode === "DUPLICATE_USER") return "A user with this email already exists.";
    if (error.errorCode === "FORBIDDEN_TARGET_ROLE") return "This account cannot be modified.";
    return error.message || fallback;
  }
  return fallback;
}

export function useStaffMutations() {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["staff"] });

  const createDoctor = useMutation({
    mutationFn: (payload: DoctorCreatePayload) => doctorService.create(payload),
    onSuccess: () => {
      toast.success("Doctor created and invited successfully.");
      void invalidate();
    },
    onError: (error: unknown) =>
      toast.error(friendlyErrorMessage(error, "Unable to create doctor.")),
  });

  const createReceptionist = useMutation({
    mutationFn: (payload: ReceptionistCreatePayload) => receptionistService.create(payload),
    onSuccess: () => {
      toast.success("Receptionist created and invited successfully.");
      void invalidate();
    },
    onError: (error: unknown) =>
      toast.error(friendlyErrorMessage(error, "Unable to create receptionist.")),
  });

  const updateDoctor = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UserUpdatePayload }) =>
      doctorService.update(id, payload),
    onSuccess: () => {
      toast.success("Doctor updated successfully.");
      void invalidate();
    },
    onError: (error: unknown) =>
      toast.error(friendlyErrorMessage(error, "Unable to update doctor.")),
  });

  const updateReceptionist = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UserUpdatePayload }) =>
      receptionistService.update(id, payload),
    onSuccess: () => {
      toast.success("Receptionist updated successfully.");
      void invalidate();
    },
    onError: (error: unknown) =>
      toast.error(friendlyErrorMessage(error, "Unable to update receptionist.")),
  });

  const updateDoctorStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: UserStatus }) =>
      doctorService.updateStatus(id, status),
    onSuccess: () => {
      toast.success("Doctor status updated successfully.");
      void invalidate();
    },
    onError: (error: unknown) =>
      toast.error(friendlyErrorMessage(error, "Unable to update doctor status.")),
  });

  const updateReceptionistStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: UserStatus }) =>
      receptionistService.updateStatus(id, status),
    onSuccess: () => {
      toast.success("Receptionist status updated successfully.");
      void invalidate();
    },
    onError: (error: unknown) =>
      toast.error(friendlyErrorMessage(error, "Unable to update receptionist status.")),
  });

  return {
    createDoctor,
    createReceptionist,
    updateDoctor,
    updateReceptionist,
    updateDoctorStatus,
    updateReceptionistStatus,
  };
}
