import { apiClient } from "@/lib/api-client";
import type {
  Appointment,
  AppointmentCreatePayload,
  AppointmentReschedulePayload,
  AppointmentStatus,
} from "@/types/appointment";

interface AppointmentListParams {
  page: number;
  pageSize: number;
  dateFrom?: string;
  dateTo?: string;
  doctorId?: string;
  departmentId?: string;
  status?: AppointmentStatus;
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  return search.toString();
}

export const appointmentService = {
  list: ({
    page,
    pageSize,
    dateFrom,
    dateTo,
    doctorId,
    departmentId,
    status,
  }: AppointmentListParams) =>
    apiClient.getList<Appointment>(
      `/appointments?${buildQuery({
        page,
        pageSize,
        date_from: dateFrom,
        date_to: dateTo,
        doctor_id: doctorId,
        department_id: departmentId,
        status,
      })}`,
    ),
  get: (id: string) => apiClient.get<Appointment>(`/appointments/${id}`),
  create: (payload: AppointmentCreatePayload) =>
    apiClient.post<Appointment>("/appointments", payload),
  reschedule: (id: string, payload: AppointmentReschedulePayload) =>
    apiClient.patch<Appointment>(`/appointments/${id}`, payload),
  checkIn: (id: string) => apiClient.patch<Appointment>(`/appointments/${id}/check-in`),
  cancel: (id: string) => apiClient.patch<Appointment>(`/appointments/${id}/cancel`),
};
