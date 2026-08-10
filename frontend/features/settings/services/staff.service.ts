import { apiClient } from "@/lib/api-client";
import type { Role } from "@/constants/roles";
import type {
  DoctorCreatePayload,
  ReceptionistCreatePayload,
  StaffUser,
  UserStatus,
  UserUpdatePayload,
} from "@/types/user";

interface StaffListParams {
  page: number;
  pageSize: number;
  search?: string;
  status?: UserStatus;
  departmentId?: string;
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  return search.toString();
}

export const doctorService = {
  list: ({ page, pageSize, search, status, departmentId }: StaffListParams) =>
    apiClient.getList<StaffUser>(
      `/doctors?${buildQuery({ page, pageSize, search, status, department_id: departmentId })}`,
    ),
  create: (payload: DoctorCreatePayload) => apiClient.post<StaffUser>("/doctors", payload),
  update: (id: string, payload: UserUpdatePayload) =>
    apiClient.patch<StaffUser>(`/doctors/${id}`, payload),
  updateStatus: (id: string, status: UserStatus) =>
    apiClient.patch<StaffUser>(`/doctors/${id}/status`, { status }),
};

export const receptionistService = {
  list: ({ page, pageSize, search, status }: StaffListParams) =>
    apiClient.getList<StaffUser>(
      `/receptionists?${buildQuery({ page, pageSize, search, status })}`,
    ),
  create: (payload: ReceptionistCreatePayload) =>
    apiClient.post<StaffUser>("/receptionists", payload),
  update: (id: string, payload: UserUpdatePayload) =>
    apiClient.patch<StaffUser>(`/receptionists/${id}`, payload),
  updateStatus: (id: string, status: UserStatus) =>
    apiClient.patch<StaffUser>(`/receptionists/${id}/status`, { status }),
};

export const userService = {
  list: ({
    page,
    pageSize,
    search,
    status,
    departmentId,
    role,
  }: StaffListParams & { role?: Role }) =>
    apiClient.getList<StaffUser>(
      `/users?${buildQuery({ page, pageSize, search, status, department_id: departmentId, role })}`,
    ),
};
