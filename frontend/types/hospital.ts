export type HospitalStatus = "active" | "inactive" | "suspended";

export interface Hospital {
  id: string;
  name: string;
  registration_number: string;
  email: string;
  phone: string;
  address_line: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  logo_url: string | null;
  status: HospitalStatus;
  working_hours: Record<string, unknown> | null;
}

export interface HospitalCreatePayload {
  name: string;
  registration_number: string;
  email: string;
  phone: string;
  address_line?: string;
  city?: string;
  state?: string;
  country?: string;
  logo_url?: string;
}

export interface HospitalUpdatePayload {
  name?: string;
  email?: string;
  phone?: string;
  address_line?: string;
  city?: string;
  state?: string;
  country?: string;
  logo_url?: string;
}
