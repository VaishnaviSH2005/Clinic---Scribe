export type Gender = "male" | "female" | "other";
export type PatientStatus = "active" | "archived";

export interface Patient {
  id: string;
  hospital_id: string;
  uhid: string;
  full_name: string;
  date_of_birth: string;
  age: number;
  gender: Gender;
  blood_group: string | null;
  mobile_number: string;
  email: string | null;
  aadhaar_number: string | null;
  emergency_contact_name: string | null;
  emergency_contact_number: string | null;
  address_line: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  pin_code: string | null;
  photo_url: string | null;
  status: PatientStatus;
  created_at: string;
}

export interface MedicalProfile {
  known_allergies: string[];
  chronic_diseases: string[];
  current_medications: string[];
  previous_surgeries: string[];
  family_history: string | null;
  lifestyle_smoking: boolean | null;
  lifestyle_alcohol: boolean | null;
  lifestyle_tobacco: boolean | null;
  height_cm: number | null;
  weight_kg: number | null;
}

export interface PatientCreatePayload {
  full_name: string;
  date_of_birth: string;
  gender: Gender;
  blood_group?: string;
  mobile_number: string;
  email?: string;
  aadhaar_number?: string;
  emergency_contact_name?: string;
  emergency_contact_number?: string;
  address_line?: string;
  city?: string;
  state?: string;
  country?: string;
  pin_code?: string;
  medical_info?: Partial<MedicalProfile>;
}

export interface PatientUpdatePayload {
  mobile_number?: string;
  email?: string;
  address_line?: string;
  city?: string;
  state?: string;
  country?: string;
  pin_code?: string;
  emergency_contact_name?: string;
  emergency_contact_number?: string;
}
