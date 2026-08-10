import { apiClient } from "@/lib/api-client";
import type {
  AiEntities,
  AiHistoryEntry,
  AiRecommendation,
  AiRetryStage,
  AiStatus,
  ClinicalSummary,
  SoapEditPayload,
  SoapNote,
  SummaryEditPayload,
} from "@/types/ai";
import type {
  Consultation,
  ConsultationScope,
  ConsultationStartPayload,
  ConsultationUpdatePayload,
  ConsultationWorkspace,
} from "@/types/consultation";

const AI_RETRY_PATHS: Record<AiRetryStage, string> = {
  transcribe: "transcribe",
  entities: "entities",
  soap: "soap",
  summary: "summary",
  recommendations: "recommendations",
};

export const consultationService = {
  start: (payload: ConsultationStartPayload) =>
    apiClient.post<Consultation>("/consultations/start", payload),

  list: (params: { scope: ConsultationScope; page: number; pageSize: number }) =>
    apiClient.getList<Consultation>(
      `/consultations?scope=${params.scope}&page=${params.page}&pageSize=${params.pageSize}`,
    ),

  getWorkspace: (id: string) => apiClient.get<ConsultationWorkspace>(`/consultations/${id}`),

  update: (id: string, payload: ConsultationUpdatePayload) =>
    apiClient.patch<Consultation>(`/consultations/${id}`, payload),

  pause: (id: string) => apiClient.post<Consultation>(`/consultations/${id}/pause`),

  resume: (id: string) => apiClient.post<Consultation>(`/consultations/${id}/resume`),

  saveDraft: (id: string) => apiClient.post<Consultation>(`/consultations/${id}/draft`),

  stop: (id: string, audioBlob: Blob | null, durationSeconds: number) => {
    const formData = new FormData();
    if (audioBlob) {
      const extension = audioBlob.type.includes("webm") ? "webm" : "ogg";
      formData.append("audio_file", audioBlob, `recording.${extension}`);
    }
    formData.append("audio_duration_seconds", String(Math.round(durationSeconds)));
    return apiClient.postForm<Consultation>(`/consultations/${id}/stop`, formData);
  },

  approve: (id: string) => apiClient.post<Consultation>(`/consultations/${id}/approve`),

  cancel: (id: string) => apiClient.post<null>(`/consultations/${id}/cancel`),

  getAiStatus: (id: string) => apiClient.get<AiStatus>(`/consultations/${id}/ai/status`),

  getAiHistory: (id: string) =>
    apiClient.getList<AiHistoryEntry>(`/consultations/${id}/ai/history`),

  getAiEntities: (id: string) =>
    apiClient.get<AiEntities | null>(`/consultations/${id}/ai/entities`),

  getSoap: (id: string) => apiClient.get<SoapNote | null>(`/consultations/${id}/ai/soap`),

  updateSoap: (id: string, payload: SoapEditPayload) =>
    apiClient.patch<SoapNote>(`/consultations/${id}/ai/soap`, payload),

  getSummary: (id: string) =>
    apiClient.get<ClinicalSummary | null>(`/consultations/${id}/ai/summary`),

  updateSummary: (id: string, payload: SummaryEditPayload) =>
    apiClient.patch<ClinicalSummary>(`/consultations/${id}/ai/summary`, payload),

  getRecommendations: (id: string) =>
    apiClient.get<AiRecommendation[]>(`/consultations/${id}/ai/recommendations`),

  retryStage: (id: string, stage: AiRetryStage) =>
    apiClient.post<null>(`/consultations/${id}/ai/${AI_RETRY_PATHS[stage]}`),
};
