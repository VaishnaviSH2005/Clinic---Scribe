export interface DashboardCard {
  key: string;
  label: string;
  value: number;
  hint?: string | null;
}

export interface AppointmentSummary {
  id: string;
  patient_name: string;
  scheduled_at: string;
  status: string;
}

export interface ConsultationSummary {
  id: string;
  patient_name: string;
  status: string;
  created_at: string;
}

export interface Dashboard {
  role: string;
  cards: DashboardCard[];
  appointments_today: AppointmentSummary[];
  recent_consultations: ConsultationSummary[];
}
