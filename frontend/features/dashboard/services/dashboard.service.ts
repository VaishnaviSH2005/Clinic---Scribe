import { apiClient } from "@/lib/api-client";
import type { Dashboard } from "@/types/dashboard";

export const dashboardService = {
  get: () => apiClient.get<Dashboard>("/dashboard"),
};
