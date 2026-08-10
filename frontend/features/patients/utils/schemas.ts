import { z } from "zod";

// Registration fields per PRD Ch8.4.
export const patientRegistrationSchema = z.object({
  full_name: z.string().min(1, "Full name is required."),
  date_of_birth: z.string().min(1, "Date of birth is required."),
  gender: z.enum(["male", "female", "other"], { required_error: "Gender is required." }),
  blood_group: z.string().optional(),
  mobile_number: z
    .string()
    .min(1, "Mobile number is required.")
    .regex(/^[0-9+\-\s]{7,20}$/, "Enter a valid mobile number."),
  email: z.string().email("Enter a valid email address.").optional().or(z.literal("")),
  aadhaar_number: z.string().optional(),
  emergency_contact_name: z.string().optional(),
  emergency_contact_number: z.string().optional(),
  address_line: z.string().optional(),
  city: z.string().optional(),
  state: z.string().optional(),
  country: z.string().optional(),
  pin_code: z.string().optional(),
});
export type PatientRegistrationFormValues = z.infer<typeof patientRegistrationSchema>;

// Editable fields only (PRD Ch8.16).
export const patientEditSchema = z.object({
  mobile_number: z
    .string()
    .min(1, "Mobile number is required.")
    .regex(/^[0-9+\-\s]{7,20}$/, "Enter a valid mobile number."),
  email: z.string().email("Enter a valid email address.").optional().or(z.literal("")),
  address_line: z.string().optional(),
  city: z.string().optional(),
  state: z.string().optional(),
  country: z.string().optional(),
  pin_code: z.string().optional(),
  emergency_contact_name: z.string().optional(),
  emergency_contact_number: z.string().optional(),
});
export type PatientEditFormValues = z.infer<typeof patientEditSchema>;

export const medicalProfileSchema = z.object({
  known_allergies: z.string().optional(),
  chronic_diseases: z.string().optional(),
  current_medications: z.string().optional(),
  previous_surgeries: z.string().optional(),
  family_history: z.string().optional(),
  lifestyle_smoking: z.boolean().optional(),
  lifestyle_alcohol: z.boolean().optional(),
  lifestyle_tobacco: z.boolean().optional(),
  height_cm: z.string().optional(),
  weight_kg: z.string().optional(),
});
export type MedicalProfileFormValues = z.infer<typeof medicalProfileSchema>;
