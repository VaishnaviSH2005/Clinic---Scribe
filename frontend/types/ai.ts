export type ConfidenceLevel = "high" | "medium" | "low";

export interface TranscriptSegment {
  speaker: "doctor" | "patient" | "unknown";
  text: string;
  timestamp_start: number;
  timestamp_end: number;
  confidence: number;
}

export interface AiEntityItem {
  text: string;
  negated?: boolean;
  severity?: string | null;
}

export interface AiVitals {
  blood_pressure?: string;
  pulse?: string;
  temperature?: string;
  spo2?: string;
  respiratory_rate?: string;
}

export interface AiEntities {
  id: string;
  symptoms: AiEntityItem[];
  medications: AiEntityItem[];
  allergies: AiEntityItem[];
  medical_history: AiEntityItem[];
  vitals: AiVitals | null;
  extraction_confidence: ConfidenceLevel | null;
  created_at: string;
  updated_at: string;
}

export interface SoapNote {
  id: string;
  subjective: string | null;
  objective: string | null;
  assessment: string | null;
  plan: string | null;
  ai_generated: boolean;
  edited_by_doctor: boolean;
  created_at: string;
  updated_at: string;
}

export interface SoapEditPayload {
  subjective?: string;
  objective?: string;
  assessment?: string;
  plan?: string;
}

export interface ClinicalSummary {
  id: string;
  chief_complaint: string | null;
  history_of_present_illness: string | null;
  key_findings: string | null;
  assessment: string | null;
  plan: string | null;
  word_count: number | null;
  edited_by_doctor: boolean;
  created_at: string;
  updated_at: string;
}

export interface SummaryEditPayload {
  chief_complaint?: string;
  history_of_present_illness?: string;
  key_findings?: string;
  assessment?: string;
  plan?: string;
}

export type RecommendationType =
  "possible_diagnosis" | "recommended_test" | "follow_up" | "red_flag";

export interface AiRecommendation {
  id: string;
  type: RecommendationType;
  content: string;
  explanation: string | null;
  confidence: ConfidenceLevel | null;
  is_red_flag: boolean;
  created_at: string;
}

export interface AiStatus {
  consultation_status: string;
  stage: string;
  degraded: boolean;
  reason?: string | null;
  failed_stage?: string | null;
  retry_available: boolean;
}

export interface AiHistoryEntry {
  action: string;
  created_at: string;
  user_id: string | null;
  metadata: Record<string, unknown> | null;
}

export type AiRetryStage = "transcribe" | "entities" | "soap" | "summary" | "recommendations";
