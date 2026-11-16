"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import type { ReportUpdatePayload } from "@/types/report";

import { useHospitalScope } from "@/features/hospital-scope/hospital-scope";

import { reportService } from "../services/report.service";

export function useReports(params: {
  page: number;
  pageSize: number;
  patientId?: string;
  hospitalId?: string;
  enabled?: boolean;
}) {
  const { enabled = true, ...query } = params;
  return useQuery({
    queryKey: ["reports", query],
    queryFn: () => reportService.list(query),
    enabled,
  });
}

export function useReport(id: string) {
  const hospitalId = useHospitalScope();
  return useQuery({
    queryKey: ["reports", id, hospitalId ?? null],
    queryFn: () => reportService.get(id, hospitalId),
    enabled: !!id,
  });
}

export function useReportVersions(id: string) {
  const hospitalId = useHospitalScope();
  return useQuery({
    queryKey: ["reports", id, "versions", hospitalId ?? null],
    queryFn: () => reportService.versions(id, hospitalId),
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
