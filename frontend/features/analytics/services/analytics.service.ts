import { apiClient } from "@/lib/api-client";
import type { Analytics } from "@/types/analytics";

export const analyticsService = {
  get: (params: { dateFrom?: string; dateTo?: string }) => {
    const search = new URLSearchParams();
    if (params.dateFrom) search.set("date_from", params.dateFrom);
    if (params.dateTo) search.set("date_to", params.dateTo);
    const qs = search.toString();
    return apiClient.get<Analytics>(`/analytics${qs ? `?${qs}` : ""}`);
  },
};
