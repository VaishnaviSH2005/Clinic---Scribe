import type {
  AiEntities,
  AiRecommendation,
  AiStatus,
  ClinicalSummary,
  SoapNote,
  TranscriptSegment,
} from "./ai";

export type ConsultationStatus =
  "draft" | "in_progress" | "ai_processing" | "pending_review" | "approved";

export interface Consultation {
  id: string;
  hospital_id: string;
  patient_id: string;
  doctor_id: string;
  appointment_id: string | null;
  department_id: string;
  status: ConsultationStatus;
  chief_complaint: string | null;
  doctor_notes: string | null;
  started_at: string | null;
  ended_at: string | null;
  approved_at: string | null;
  approved_by: string | null;
  created_at: string;
}

export interface ConsultationTranscript {
  id: string;
  raw_transcript: TranscriptSegment[];
  cleaned_transcript: TranscriptSegment[] | null;
  audio_file_url: string | null;
  audio_duration_seconds: number | null;
  manually_edited: boolean;
}

export interface MedicalAlerts {
  known_allergies: string[];
  chronic_diseases: string[];
  current_medications: string[];
}

export interface PreviousConsultation {
  id: string;
  started_at: string | null;
  chief_complaint: string | null;
  status: ConsultationStatus;
}

export interface ConsultationPatientContext {
  id: string;
  full_name: string;
  uhid: string;
  age: number;
  gender: string;
  blood_group: string | null;
  medical_alerts: MedicalAlerts;
  previous_consultations: PreviousConsultation[];
}

export interface ConsultationWorkspace {
  consultation: Consultation;
  transcript: ConsultationTranscript;
  patient: ConsultationPatientContext;
  ai_status: AiStatus;
  entities: AiEntities | null;
  soap: SoapNote | null;
  summary: ClinicalSummary | null;
  recommendations: AiRecommendation[];
}

export interface ConsultationStartPayload {
  patient_id: string;
  appointment_id?: string;
  chief_complaint?: string;
}

export interface ConsultationUpdatePayload {
  chief_complaint?: string;
  doctor_notes?: string;
}

export type ConsultationScope = "active" | "previous" | "drafts";
