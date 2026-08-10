"use client";

import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { ROUTES } from "@/constants/routes";
import { ApiClientError } from "@/lib/api-client";
import type { AiRetryStage, SoapEditPayload, SummaryEditPayload } from "@/types/ai";
import type { ConsultationUpdatePayload, ConsultationWorkspace } from "@/types/consultation";

import { consultationService } from "../services/consultation.service";

const AI_PROCESSING_POLL_MS = 4000;

export function useConsultationWorkspace(id: string) {
  return useQuery({
    queryKey: ["consultations", id],
    queryFn: () => consultationService.getWorkspace(id),
    enabled: !!id,
    refetchOnWindowFocus: false,
    // A doctor can leave and re-enter the workspace while AI processing is
    // still running (Ch10.14) — polling here, rather than only on mount,
    // is what makes the processing/failed/completed state stay live
    // without a manual refresh.
    refetchInterval: (query) => {
      const data = query.state.data as ConsultationWorkspace | undefined;
      return data?.consultation.status === "ai_processing" ? AI_PROCESSING_POLL_MS : false;
    },
  });
}

function friendlyError(error: unknown, fallback: string): string {
  if (error instanceof ApiClientError) return error.message || fallback;
  return fallback;
}

export function useConsultationActions(id: string) {
  const queryClient = useQueryClient();
  const router = useRouter();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["consultations", id] });

  const updateNotes = useMutation({
    mutationFn: (payload: ConsultationUpdatePayload) => consultationService.update(id, payload),
    onError: (error: unknown) => toast.error(friendlyError(error, "Unable to save changes.")),
  });

  const pause = useMutation({
    mutationFn: () => consultationService.pause(id),
    onError: (error: unknown) => toast.error(friendlyError(error, "Unable to pause recording.")),
  });

  const resume = useMutation({
    mutationFn: () => consultationService.resume(id),
    onError: (error: unknown) => toast.error(friendlyError(error, "Unable to resume recording.")),
  });

  const saveDraft = useMutation({
    mutationFn: () => consultationService.saveDraft(id),
    onSuccess: () => {
      toast.success("Consultation saved as draft.");
      void invalidate();
      router.push(ROUTES.consultations);
    },
    onError: (error: unknown) => toast.error(friendlyError(error, "Unable to save draft.")),
  });

  const stop = useMutation({
    mutationFn: ({
      audioBlob,
      durationSeconds,
    }: {
      audioBlob: Blob | null;
      durationSeconds: number;
    }) => consultationService.stop(id, audioBlob, durationSeconds),
    onSuccess: () => {
      toast.success("Recording stopped. Ready for review.");
      void invalidate();
    },
    onError: (error: unknown) => toast.error(friendlyError(error, "Unable to stop recording.")),
  });

  const approve = useMutation({
    mutationFn: () => consultationService.approve(id),
    onSuccess: () => {
      toast.success("Consultation approved successfully.");
      void invalidate();
      router.push(ROUTES.consultations);
    },
    onError: (error: unknown) =>
      toast.error(friendlyError(error, "Unable to approve consultation.")),
  });

  const cancel = useMutation({
    mutationFn: () => consultationService.cancel(id),
    onSuccess: () => {
      toast.success("Consultation cancelled.");
      router.push(ROUTES.consultations);
    },
    onError: (error: unknown) =>
      toast.error(friendlyError(error, "Unable to cancel consultation.")),
  });

  const retryStage = useMutation({
    mutationFn: (stage: AiRetryStage) => consultationService.retryStage(id, stage),
    onSuccess: () => {
      toast.success("Regeneration started.");
      void invalidate();
    },
    onError: (error: unknown) => toast.error(friendlyError(error, "Unable to start regeneration.")),
  });

  const updateSoap = useMutation({
    mutationFn: (payload: SoapEditPayload) => consultationService.updateSoap(id, payload),
    onSuccess: () => {
      toast.success("SOAP note saved.");
      void invalidate();
    },
    onError: (error: unknown) => toast.error(friendlyError(error, "Unable to save SOAP note.")),
  });

  const updateSummary = useMutation({
    mutationFn: (payload: SummaryEditPayload) => consultationService.updateSummary(id, payload),
    onSuccess: () => {
      toast.success("Clinical summary saved.");
      void invalidate();
    },
    onError: (error: unknown) =>
      toast.error(friendlyError(error, "Unable to save clinical summary.")),
  });

  return {
    updateNotes,
    pause,
    resume,
    saveDraft,
    stop,
    approve,
    cancel,
    retryStage,
    updateSoap,
    updateSummary,
  };
}
