// User roles fixed for Version 1 (PRD Ch6.3 / Ch7.3). Do not add roles here without a PRD update.
export const ROLES = {
  superAdmin: "super_admin",
  hospitalAdmin: "hospital_admin",
  doctor: "doctor",
  receptionist: "receptionist",
} as const;

export type Role = (typeof ROLES)[keyof typeof ROLES];
