import { z } from "zod";

export const appointmentFormSchema = z.object({
  patient_id: z.string().min(1, "Patient is required."),
  doctor_id: z.string().min(1, "Doctor is required."),
  department_id: z.string().min(1, "Department is required."),
  scheduled_at: z.string().min(1, "Date and time are required."),
});
export type AppointmentFormValues = z.infer<typeof appointmentFormSchema>;

export const rescheduleFormSchema = z.object({
  scheduled_at: z.string().min(1, "Date and time are required."),
});
export type RescheduleFormValues = z.infer<typeof rescheduleFormSchema>;
