import { API_BASE_URL, API_VERSION_PREFIX } from "@/constants/api";
import { apiClient } from "@/lib/api-client";
import type { Appointment } from "@/types/appointment";
import type { PatientDocument } from "@/types/document";
import type {
  MedicalProfile,
  Patient,
  PatientCreatePayload,
  PatientUpdatePayload,
} from "@/types/patient";
import type { TimelineEvent } from "@/types/timeline";

function buildQuery(params: Record<string, string | number | boolean | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  return search.toString();
}

export const patientService = {
  register: (payload: PatientCreatePayload) => apiClient.post<Patient>("/patients", payload),

  list: (params: { page: number; pageSize: number; search?: string; includeArchived?: boolean }) =>
    apiClient.getList<Patient>(
      `/patients?${buildQuery({
        page: params.page,
        pageSize: params.pageSize,
        search: params.search,
        include_archived: params.includeArchived,
      })}`,
    ),

  search: (q: string) => apiClient.get<Patient[]>(`/patients/search?${buildQuery({ q })}`),

  get: (id: string) => apiClient.get<Patient>(`/patients/${id}`),

  update: (id: string, payload: PatientUpdatePayload) =>
    apiClient.patch<Patient>(`/patients/${id}`, payload),

  archive: (id: string) => apiClient.delete<Patient>(`/patients/${id}`),

  restore: (id: string) => apiClient.post<Patient>(`/patients/${id}/restore`),

  getMedicalProfile: (id: string) =>
    apiClient.get<MedicalProfile | null>(`/patients/${id}/medical-profile`),

  updateMedicalProfile: (id: string, payload: Partial<MedicalProfile>) =>
    apiClient.patch<MedicalProfile>(`/patients/${id}/medical-profile`, payload),

  getTimeline: (id: string) => apiClient.get<TimelineEvent[]>(`/patients/${id}/timeline`),

  getAppointments: (id: string) => apiClient.get<Appointment[]>(`/patients/${id}/appointments`),

  getDocuments: (id: string) => apiClient.get<PatientDocument[]>(`/patients/${id}/documents`),

  uploadDocument: (id: string, file: File, category?: string) => {
    const formData = new FormData();
    formData.append("file", file);
    if (category) formData.append("category", category);
    return apiClient.postForm<PatientDocument>(`/patients/${id}/documents`, formData);
  },

  documentDownloadUrl: (patientId: string, documentId: string) =>
    `${API_BASE_URL}${API_VERSION_PREFIX}/patients/${patientId}/documents/${documentId}/download`,
};
