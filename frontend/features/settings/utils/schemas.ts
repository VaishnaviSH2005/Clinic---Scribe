import { z } from "zod";

export const hospitalFormSchema = z.object({
  name: z.string().min(1, "Hospital name is required."),
  registration_number: z.string().min(1, "Registration number is required."),
  email: z.string().min(1, "Email is required.").email("Enter a valid email address."),
  phone: z.string().min(1, "Phone number is required."),
  address_line: z.string().optional(),
  city: z.string().optional(),
  state: z.string().optional(),
  country: z.string().optional(),
});
export type HospitalFormValues = z.infer<typeof hospitalFormSchema>;

export const departmentFormSchema = z.object({
  name: z.string().min(1, "Department name is required."),
});
export type DepartmentFormValues = z.infer<typeof departmentFormSchema>;

export const doctorFormSchema = z.object({
  full_name: z.string().min(1, "Full name is required."),
  email: z.string().min(1, "Email is required.").email("Enter a valid email address."),
  phone: z.string().min(1, "Phone number is required."),
  department_id: z.string().min(1, "Department is required."),
  qualification: z.string().optional(),
  specialization: z.string().optional(),
  medical_registration_number: z.string().optional(),
});
export type DoctorFormValues = z.infer<typeof doctorFormSchema>;

export const receptionistFormSchema = z.object({
  full_name: z.string().min(1, "Full name is required."),
  email: z.string().min(1, "Email is required.").email("Enter a valid email address."),
  phone: z.string().min(1, "Phone number is required."),
});
export type ReceptionistFormValues = z.infer<typeof receptionistFormSchema>;
