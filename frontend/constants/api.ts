// Backend API base configuration (PRD Ch4.11: /api/v1/ versioning).
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
export const API_VERSION_PREFIX = "/api/v1";
