"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import type { ReportUpdatePayload } from "@/types/report";

import { reportService } from "../services/report.service";

export function useReports(params: { page: number; pageSize: number; patientId?: string }) {
  return useQuery({
    queryKey: ["reports", params],
    queryFn: () => reportService.list(params),
  });
}

export function useReport(id: string) {
  return useQuery({
    queryKey: ["reports", id],
    queryFn: () => reportService.get(id),
    enabled: !!id,
  });
}

export function useReportVersions(id: string) {
  return useQuery({
    queryKey: ["reports", id, "versions"],
    queryFn: () => reportService.versions(id),
    enabled: !!id,
  });
}

export function useUpdateReport(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ReportUpdatePayload) => reportService.update(id, payload),
    onSuccess: () => {
      toast.success("Report updated. A new version was generated.");
      void queryClient.invalidateQueries({ queryKey: ["reports", id] });
    },
    onError: () => toast.error("Unable to update this report."),
  });
}
