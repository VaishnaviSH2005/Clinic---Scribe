export type AppointmentStatus = "upcoming" | "checked_in" | "completed" | "cancelled" | "missed";

export interface Appointment {
  id: string;
  hospital_id: string;
  patient_id: string;
  doctor_id: string;
  department_id: string;
  scheduled_at: string;
  status: AppointmentStatus;
  checked_in_at: string | null;
  created_at: string;
}

export interface AppointmentCreatePayload {
  patient_id: string;
  doctor_id: string;
  department_id: string;
  scheduled_at: string;
  // true once the user confirmed booking a time that has already passed
  allow_past?: boolean;
}

export interface AppointmentReschedulePayload {
  scheduled_at: string;
  allow_past?: boolean;
}
