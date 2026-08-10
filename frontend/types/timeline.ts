export type TimelineEventType =
  | "registration"
  | "appointment"
  | "consultation"
  | "diagnosis"
  | "uploaded_report"
  | "follow_up"
  | "surgery";

export interface TimelineEvent {
  id: string;
  event_type: TimelineEventType;
  event_date: string;
  title: string;
  description: string | null;
  reference_id: string | null;
}
