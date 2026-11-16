export interface AuditLog {
  id: string;
  hospital_id: string | null;
  user_id: string | null;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  ip_address: string | null;
  created_at: string;
  // Resolved server-side so the UI never has to show raw UUIDs.
  user_name: string | null;
  user_email: string | null;
  hospital_name: string | null;
}
