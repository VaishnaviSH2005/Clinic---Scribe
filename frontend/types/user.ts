import type { Role } from "@/constants/roles";

export type UserStatus = "active" | "inactive";

export interface StaffUser {
  id: string;
  hospital_id: string | null;
  department_id: string | null;
  role: Role;
  full_name: string;
  email: string;
  phone: string;
  profile_photo_url: string | null;
  employee_id: string | null;
  qualification: string | null;
  specialization: string | null;
  medical_registration_number: string | null;
  experience_years: number | null;
  status: UserStatus;
}

export interface DoctorCreatePayload {
  full_name: string;
  email: string;
  phone: string;
  department_id: string;
  employee_id?: string;
  qualification?: string;
  specialization?: string;
  medical_registration_number?: string;
  experience_years?: number;
}

export interface ReceptionistCreatePayload {
  full_name: string;
  email: string;
  phone: string;
  department_id?: string;
  employee_id?: string;
}

export interface UserUpdatePayload {
  full_name?: string;
  phone?: string;
  department_id?: string;
  qualification?: string;
  specialization?: string;
  medical_registration_number?: string;
  experience_years?: number;
}
