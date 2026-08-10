export type DocumentFileType = "pdf" | "jpg" | "png";

export interface PatientDocument {
  id: string;
  patient_id: string;
  consultation_id: string | null;
  file_name: string;
  file_type: DocumentFileType;
  file_url: string;
  file_size_bytes: number;
  document_category: string | null;
  created_at: string;
}
