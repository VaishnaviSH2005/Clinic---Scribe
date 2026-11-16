import { useRef } from "react";
import { Mic, Pause, Play, Save, Square, Upload, X, Check } from "lucide-react";

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
  onUploadRecording: (file: File) => void;
  onSaveDraft: () => void;
  onApprove: () => void;
  onCancel: () => void;
}

const ACCEPTED_AUDIO_TYPES = "audio/webm,audio/ogg,audio/mp4,audio/mpeg,audio/wav,audio/x-wav";

// Bottom Toolbar (PRD Ch9.11). Approve is only enabled in `pending_review`.
// Recording buttons are hidden during `ai_processing` — the audio has already
// been submitted; the doctor must wait for the AI pipeline to complete before
// the consultation is ready for review actions.
export function ConsultationToolbar({
  consultationStatus,
  recorderStatus,
  isBusy,
  onStartRecording,
  onPause,
  onResume,
  onStop,
  onUploadRecording,
  onSaveDraft,
  onApprove,
  onCancel,
}: ConsultationToolbarProps) {
  const isReadOnly = consultationStatus === "approved";
  const isAiProcessing = consultationStatus === "ai_processing";
  const canRecord = !isReadOnly && !isAiProcessing && consultationStatus !== "pending_review";
  const canApprove = consultationStatus === "pending_review";
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (file) onUploadRecording(file);
  };

  return (
    <div className="flex items-center justify-between border-t border-border bg-surface px-6 py-4">
      <div className="flex gap-2">
        {canRecord && recorderStatus === "idle" && (
          <Button onClick={onStartRecording} loading={isBusy}>
            <Mic className="h-4 w-4" /> Start recording
          </Button>
        )}
        {canRecord && recorderStatus === "idle" && (
          <>
            <Button
              variant="secondary"
              onClick={() => fileInputRef.current?.click()}
              loading={isBusy}
            >
              <Upload className="h-4 w-4" /> Upload recording
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED_AUDIO_TYPES}
              className="hidden"
              onChange={handleFileChange}
            />
          </>
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
        {!isReadOnly && !isAiProcessing && consultationStatus !== "pending_review" && (
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
