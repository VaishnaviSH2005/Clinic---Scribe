// Central route constants (PRD Ch4.10). Never hardcode route strings in components.
export const ROUTES = {
  home: "/",
  login: "/login",
  forgotPassword: "/forgot-password",
  resetPassword: "/reset-password",
  dashboard: "/dashboard",
  hospitals: "/hospitals",
  licenses: "/licenses",
  auditLogs: "/audit-logs",
  patients: "/patients",
  appointments: "/appointments",
  consultations: "/consultations",
  reports: "/reports",
  analytics: "/analytics",
  settings: "/settings",
  profile: "/profile",
} as const;
