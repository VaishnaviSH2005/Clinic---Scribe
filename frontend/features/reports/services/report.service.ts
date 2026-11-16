import { API_BASE_URL, API_VERSION_PREFIX } from "@/constants/api";
import { apiClient } from "@/lib/api-client";
import type { Report, ReportUpdatePayload, ReportVersion } from "@/types/report";

// Super Admin reads are scoped to one chosen hospital via `hospital_id`
// (hospital staff never need it; the backend ignores it for them).
const withHospital = (path: string, hospitalId?: string) =>
  hospitalId ? `${path}${path.includes("?") ? "&" : "?"}hospital_id=${hospitalId}` : path;

export const reportService = {
  list: (params: { page: number; pageSize: number; patientId?: string; hospitalId?: string }) =>
    apiClient.getList<Report>(
      withHospital(
        `/reports?page=${params.page}&pageSize=${params.pageSize}${
          params.patientId ? `&patient_id=${params.patientId}` : ""
        }`,
        params.hospitalId,
      ),
    ),

  get: (id: string, hospitalId?: string) =>
    apiClient.get<Report>(withHospital(`/reports/${id}`, hospitalId)),

  update: (id: string, payload: ReportUpdatePayload) =>
    apiClient.patch<Report>(`/reports/${id}`, payload),

  versions: (id: string, hospitalId?: string) =>
    apiClient.get<ReportVersion[]>(withHospital(`/reports/${id}/versions`, hospitalId)),

  downloadUrl: (id: string, hospitalId?: string) =>
    `${API_BASE_URL}${API_VERSION_PREFIX}${withHospital(`/reports/${id}/download`, hospitalId)}`,

  versionDownloadUrl: (id: string, versionNumber: number, hospitalId?: string) =>
    `${API_BASE_URL}${API_VERSION_PREFIX}${withHospital(
      `/reports/${id}/versions/${versionNumber}/download`,
      hospitalId,
    )}`,
};
