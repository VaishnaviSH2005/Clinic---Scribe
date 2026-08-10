export interface TimeSeriesPoint {
  date: string;
  count: number;
}

export interface NamedCount {
  name: string;
  count: number;
}

export interface Analytics {
  date_from: string;
  date_to: string;
  consultations_by_status: Record<string, number>;
  consultations_per_day: TimeSeriesPoint[];
  appointments_by_status: Record<string, number>;
  new_patients_per_day: TimeSeriesPoint[];
  ai_processing_outcomes: Record<string, number>;
  consultations_by_doctor: NamedCount[];
  consultations_by_department: NamedCount[];
  reports_generated: number;
  missed_appointment_rate: number;
}
