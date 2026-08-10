export type ReportType =
  "consultation_report" | "soap_report" | "clinical_summary" | "patient_history_report";

export interface Report {
  id: string;
  hospital_id: string;
  patient_id: string;
  consultation_id: string;
  report_type: ReportType;
  doctor_remarks: string | null;
  follow_up_date: string | null;
  follow_up_notes: string | null;
  pdf_url: string | null;
  current_version: number;
  is_locked: boolean;
  created_at: string;
}

export interface ReportVersion {
  id: string;
  version_number: number;
  pdf_url: string | null;
  created_by: string;
  created_at: string;
}

export interface ReportUpdatePayload {
  doctor_remarks?: string;
  follow_up_date?: string;
  follow_up_notes?: string;
}
