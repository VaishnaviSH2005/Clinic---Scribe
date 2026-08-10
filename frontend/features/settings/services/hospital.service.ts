import { apiClient } from "@/lib/api-client";
import type {
  Hospital,
  HospitalCreatePayload,
  HospitalUpdatePayload,
  HospitalStatus,
} from "@/types/hospital";

export const hospitalService = {
  list: (page: number, pageSize: number) =>
    apiClient.getList<Hospital>(`/hospitals?page=${page}&pageSize=${pageSize}`),
  get: (id: string) => apiClient.get<Hospital>(`/hospitals/${id}`),
  create: (payload: HospitalCreatePayload) => apiClient.post<Hospital>("/hospitals", payload),
  update: (id: string, payload: HospitalUpdatePayload) =>
    apiClient.patch<Hospital>(`/hospitals/${id}`, payload),
  updateStatus: (id: string, status: HospitalStatus) =>
    apiClient.patch<Hospital>(`/hospitals/${id}/status`, { status }),
  uploadLogo: (id: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiClient.postForm<Hospital>(`/hospitals/${id}/logo`, formData);
  },
};
