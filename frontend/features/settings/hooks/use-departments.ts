"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { ApiClientError } from "@/lib/api-client";
import type {
  DepartmentCreatePayload,
  DepartmentStatus,
  DepartmentUpdatePayload,
} from "@/types/department";

import { departmentService } from "../services/department.service";

export function useDepartments(page: number, pageSize: number) {
  return useQuery({
    queryKey: ["departments", page, pageSize],
    queryFn: () => departmentService.list(page, pageSize),
  });
}

export function useDepartmentMutations() {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["departments"] });

  const create = useMutation({
    mutationFn: (payload: DepartmentCreatePayload) => departmentService.create(payload),
    onSuccess: () => {
      toast.success("Department created successfully.");
      void invalidate();
    },
    onError: () => toast.error("Unable to create department. Please try again."),
  });

  const update = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: DepartmentUpdatePayload }) =>
      departmentService.update(id, payload),
    onSuccess: () => {
      toast.success("Department updated successfully.");
      void invalidate();
    },
    onError: () => toast.error("Unable to update department. Please try again."),
  });

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: DepartmentStatus }) =>
      departmentService.updateStatus(id, status),
    onSuccess: () => {
      toast.success("Department status updated successfully.");
      void invalidate();
    },
    onError: (error: unknown) => {
      if (error instanceof ApiClientError && error.errorCode === "DEPARTMENT_HAS_ACTIVE_DOCTORS") {
        toast.error("This department has active doctors assigned and cannot be disabled.");
      } else {
        toast.error("Unable to update department status.");
      }
    },
  });

  return { create, update, updateStatus };
}
