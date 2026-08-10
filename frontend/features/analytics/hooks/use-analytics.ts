"use client";

import { useQuery } from "@tanstack/react-query";

import { analyticsService } from "../services/analytics.service";

export function useAnalytics(params: { dateFrom?: string; dateTo?: string }) {
  return useQuery({
    queryKey: ["analytics", params],
    queryFn: () => analyticsService.get(params),
  });
}
