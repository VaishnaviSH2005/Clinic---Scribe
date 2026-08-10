import { Mic, Pause, Play, Save, Square, X, Check } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { ConsultationStatus } from "@/types/consultation";

import type { RecorderStatus } from "../hooks/use-audio-recorder";

interface ConsultationToolbarProps {
  consultationStatus: ConsultationStatus;
  recorderStatus: RecorderStatus;
  isBusy: boolean;
  onStartRecording: () => void;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  onSaveDraft: () => void;
  onApprove: () => void;
  onCancel: () => void;
}

// Bottom Toolbar (PRD Ch9.11). Approve remains disabled until the
// consultation reaches `pending_review` (i.e. recording has been stopped) —
// the same gate the PRD describes for AI completion, adapted since no AI
// pipeline exists yet in this milestone.
export function ConsultationToolbar({
  consultationStatus,
  recorderStatus,
  isBusy,
  onStartRecording,
  onPause,
  onResume,
  onStop,
  onSaveDraft,
  onApprove,
  onCancel,
}: ConsultationToolbarProps) {
  const isReadOnly = consultationStatus === "approved";
  const canRecord = !isReadOnly && consultationStatus !== "pending_review";
  const canApprove = consultationStatus === "pending_review";

  return (
    <div className="flex items-center justify-between border-t border-border bg-surface px-6 py-4">
      <div className="flex gap-2">
        {canRecord && recorderStatus === "idle" && (
          <Button onClick={onStartRecording} loading={isBusy}>
            <Mic className="h-4 w-4" /> Start recording
          </Button>
        )}
        {canRecord && recorderStatus === "recording" && (
          <Button variant="secondary" onClick={onPause} loading={isBusy}>
            <Pause className="h-4 w-4" /> Pause
          </Button>
        )}
        {canRecord && recorderStatus === "paused" && (
          <Button variant="secondary" onClick={onResume} loading={isBusy}>
            <Play className="h-4 w-4" /> Resume
          </Button>
        )}
        {canRecord && (recorderStatus === "recording" || recorderStatus === "paused") && (
          <Button variant="danger" onClick={onStop} loading={isBusy}>
            <Square className="h-4 w-4" /> Stop recording
          </Button>
        )}
      </div>

      <div className="flex gap-2">
        {!isReadOnly && (
          <Button variant="ghost" onClick={onCancel} loading={isBusy}>
            <X className="h-4 w-4" /> Cancel
          </Button>
        )}
        {!isReadOnly && consultationStatus !== "pending_review" && (
          <Button variant="secondary" onClick={onSaveDraft} loading={isBusy}>
            <Save className="h-4 w-4" /> Save as draft
          </Button>
        )}
        {!isReadOnly && (
          <Button onClick={onApprove} disabled={!canApprove} loading={isBusy}>
            <Check className="h-4 w-4" /> Approve consultation
          </Button>
        )}
      </div>
    </div>
  );
}
