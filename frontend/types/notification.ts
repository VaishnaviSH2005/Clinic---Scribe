export type NotificationType =
  | "appointment_reminder"
  | "consultation_pending"
  | "ai_processing_complete"
  | "report_generated"
  | "system";

export interface AppNotification {
  id: string;
  type: NotificationType;
  title: string;
  message: string | null;
  reference_id: string | null;
  is_read: boolean;
  created_at: string;
}
