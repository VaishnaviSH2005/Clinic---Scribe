"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { ApiClientError } from "@/lib/api-client";
import type { ConsultationScope, ConsultationStartPayload } from "@/types/consultation";

import { consultationService } from "../services/consultation.service";

export function useConsultations(scope: ConsultationScope, page: number, pageSize: number) {
  return useQuery({
    queryKey: ["consultations", scope, page, pageSize],
    queryFn: () => consultationService.list({ scope, page, pageSize }),
  });
}

export function useStartConsultation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ConsultationStartPayload) => consultationService.start(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["consultations"] });
    },
    onError: (error: unknown) => {
      if (error instanceof ApiClientError) {
        toast.error(error.message || "Unable to start consultation.");
      } else {
        toast.error("Unable to start consultation. Please try again.");
      }
    },
  });
}
