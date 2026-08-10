import { apiClient } from "@/lib/api-client";
import type {
  Department,
  DepartmentCreatePayload,
  DepartmentStatus,
  DepartmentUpdatePayload,
} from "@/types/department";

export const departmentService = {
  list: (page: number, pageSize: number) =>
    apiClient.getList<Department>(`/departments?page=${page}&pageSize=${pageSize}`),
  create: (payload: DepartmentCreatePayload) => apiClient.post<Department>("/departments", payload),
  update: (id: string, payload: DepartmentUpdatePayload) =>
    apiClient.patch<Department>(`/departments/${id}`, payload),
  updateStatus: (id: string, status: DepartmentStatus) =>
    apiClient.patch<Department>(`/departments/${id}/status`, { status }),
};
