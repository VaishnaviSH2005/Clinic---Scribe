import type { Role } from "@/constants/roles";

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: Role;
  hospitalId: string | null;
}

export interface Profile {
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
  status: "active" | "inactive";
}

export interface ProfileUpdatePayload {
  full_name?: string;
  phone?: string;
  profile_photo_url?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface ForgotPasswordPayload {
  email: string;
}

export interface ResetPasswordPayload {
  token: string;
  password: string;
}

export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
}

export interface SessionInfo {
  id: string;
  device_info: string | null;
  ip_address: string | null;
  created_at: string;
  last_activity_at: string;
  expires_at: string;
  is_current: boolean;
}
