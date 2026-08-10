import { Mic } from "lucide-react";

import { cn } from "@/lib/utils";

import type { RecorderStatus } from "../hooks/use-audio-recorder";

function formatTimer(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.floor(totalSeconds % 60);
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

interface RecordingStatusCardProps {
  status: RecorderStatus;
  elapsedSeconds: number;
  audioLevel: number;
}

const STATUS_LABEL: Record<RecorderStatus, string> = {
  idle: "Not started",
  "requesting-permission": "Requesting microphone access…",
  recording: "Recording",
  paused: "Paused",
  stopped: "Recording stopped",
  error: "Microphone error",
};

// Recording Status / Timer / Audio Level Indicator (PRD Ch9.6/9.23 — pulsing
// red dot while recording, skeleton-free live meter).
export function RecordingStatusCard({
  status,
  elapsedSeconds,
  audioLevel,
}: RecordingStatusCardProps) {
  const isRecording = status === "recording";
  const barCount = 20;
  const activeBars = Math.round(audioLevel * barCount);

  return (
    <div className="flex items-center justify-between rounded-card border border-border bg-surface p-6 shadow-level-1">
      <div className="flex items-center gap-3">
        <span className="relative flex h-3 w-3">
          {isRecording && (
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-danger opacity-75" />
          )}
          <span
            className={cn(
              "relative inline-flex h-3 w-3 rounded-full",
              isRecording ? "bg-danger" : status === "paused" ? "bg-warning" : "bg-disabled",
            )}
          />
        </span>
        <div>
          <p className="text-body-lg font-medium text-text-primary">{STATUS_LABEL[status]}</p>
          <p className="text-h3 font-semibold tabular-nums text-text-primary">
            {formatTimer(elapsedSeconds)}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Mic className={cn("h-5 w-5", isRecording ? "text-primary" : "text-text-secondary")} />
        <div className="flex h-8 items-end gap-0.5" aria-hidden="true">
          {Array.from({ length: barCount }).map((_, i) => (
            <span
              key={i}
              className={cn(
                "w-1 rounded-full transition-colors duration-micro",
                i < activeBars ? "bg-accent" : "bg-border",
              )}
              style={{ height: `${8 + (i % 4) * 4}px` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
