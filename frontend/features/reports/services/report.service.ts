import { API_BASE_URL, API_VERSION_PREFIX } from "@/constants/api";
import { apiClient } from "@/lib/api-client";
import type { Report, ReportUpdatePayload, ReportVersion } from "@/types/report";

export const reportService = {
  list: (params: { page: number; pageSize: number; patientId?: string }) =>
    apiClient.getList<Report>(
      `/reports?page=${params.page}&pageSize=${params.pageSize}${
        params.patientId ? `&patient_id=${params.patientId}` : ""
      }`,
    ),

  get: (id: string) => apiClient.get<Report>(`/reports/${id}`),

  update: (id: string, payload: ReportUpdatePayload) =>
    apiClient.patch<Report>(`/reports/${id}`, payload),

  versions: (id: string) => apiClient.get<ReportVersion[]>(`/reports/${id}/versions`),

  downloadUrl: (id: string) => `${API_BASE_URL}${API_VERSION_PREFIX}/reports/${id}/download`,

  versionDownloadUrl: (id: string, versionNumber: number) =>
    `${API_BASE_URL}${API_VERSION_PREFIX}/reports/${id}/versions/${versionNumber}/download`,
};
