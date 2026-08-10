"use client";

import { useState } from "react";
import { AlertTriangle } from "lucide-react";

import { ConfirmDialog } from "@/components/dialogs/confirm-dialog";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

import { useAudioRecorder } from "../hooks/use-audio-recorder";
import {
  useConsultationActions,
  useConsultationWorkspace,
} from "../hooks/use-consultation-workspace";
import { AiAssistantPanel } from "./ai-assistant-panel";
import { ConsultationHeader } from "./consultation-header";
import { ConsultationNotesPanel } from "./consultation-notes-panel";
import { ConsultationToolbar } from "./consultation-toolbar";
import { PatientContextPanel } from "./patient-context-panel";
import { RecordingStatusCard } from "./recording-status-card";
import { TranscriptPanel } from "./transcript-panel";

export function ConsultationWorkspaceView({ consultationId }: { consultationId: string }) {
  const { data, isLoading, isError } = useConsultationWorkspace(consultationId);
  const actions = useConsultationActions(consultationId);
  const recorder = useAudioRecorder();
  const [cancelOpen, setCancelOpen] = useState(false);

  const isBusy =
    actions.pause.isPending ||
    actions.resume.isPending ||
    actions.stop.isPending ||
    actions.saveDraft.isPending ||
    actions.approve.isPending ||
    actions.cancel.isPending;

  if (isLoading) {
    return (
      <div className="flex h-full flex-col gap-4 p-6">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
            <AlertTriangle className="h-6 w-6 text-danger" />
            <p className="text-body-lg font-medium text-text-primary">Consultation not found</p>
            <p className="text-body text-text-secondary">
              This consultation could not be located, or you do not have access to it.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { consultation, transcript, patient, ai_status, soap, summary, entities, recommendations } =
    data;
  const isReadOnly = consultation.status === "approved" || consultation.status === "pending_review";
  const aiContentReadOnly = consultation.status === "approved";

  const handleStartRecording = async () => {
    if (consultation.status === "draft") {
      await actions.resume.mutateAsync();
    }
    await recorder.start();
  };

  const handlePause = () => {
    recorder.pause();
    actions.pause.mutate();
  };

  const handleResume = () => {
    recorder.resume();
    actions.resume.mutate();
  };

  const handleStop = async () => {
    const blob = await recorder.stop();
    await actions.stop.mutateAsync({ audioBlob: blob, durationSeconds: recorder.elapsedSeconds });
  };

  const handleSaveDraft = async () => {
    if (recorder.status === "recording" || recorder.status === "paused") {
      const blob = await recorder.stop();
      await actions.stop.mutateAsync({ audioBlob: blob, durationSeconds: recorder.elapsedSeconds });
    }
    await actions.saveDraft.mutateAsync();
  };

  return (
    <div className="flex h-full flex-col">
      <ConsultationHeader consultation={consultation} patient={patient} />

      {recorder.errorMessage && (
        <div className="flex items-center gap-2 bg-danger/10 px-6 py-2 text-body text-danger">
          <AlertTriangle className="h-4 w-4" /> {recorder.errorMessage}
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        <PatientContextPanel patient={patient} />

        <main className="flex min-w-0 flex-1 flex-col gap-4 overflow-y-auto p-6">
          <RecordingStatusCard
            status={recorder.status}
            elapsedSeconds={recorder.elapsedSeconds}
            audioLevel={recorder.audioLevel}
          />
          <TranscriptPanel
            transcript={transcript}
            recorderStatus={recorder.status}
            aiStatus={ai_status}
          />
          <ConsultationNotesPanel consultation={consultation} readOnly={isReadOnly} />
        </main>

        <AiAssistantPanel
          aiStatus={ai_status}
          soap={soap}
          summary={summary}
          entities={entities}
          recommendations={recommendations}
          readOnly={aiContentReadOnly}
          onRetry={(stage) => actions.retryStage.mutate(stage)}
          retryPending={actions.retryStage.isPending}
          onSaveSoap={(payload) => actions.updateSoap.mutate(payload)}
          savingSoap={actions.updateSoap.isPending}
          onSaveSummary={(payload) => actions.updateSummary.mutate(payload)}
          savingSummary={actions.updateSummary.isPending}
        />
      </div>

      <ConsultationToolbar
        consultationStatus={consultation.status}
        recorderStatus={recorder.status}
        isBusy={isBusy}
        onStartRecording={() => void handleStartRecording()}
        onPause={handlePause}
        onResume={handleResume}
        onStop={() => void handleStop()}
        onSaveDraft={() => void handleSaveDraft()}
        onApprove={() => actions.approve.mutate()}
        onCancel={() => setCancelOpen(true)}
      />

      <ConfirmDialog
        open={cancelOpen}
        onOpenChange={setCancelOpen}
        title="Cancel consultation?"
        description="This consultation will be discarded. This cannot be undone."
        confirmLabel="Cancel consultation"
        danger
        loading={actions.cancel.isPending}
        onConfirm={() => actions.cancel.mutate()}
      />
    </div>
  );
}
