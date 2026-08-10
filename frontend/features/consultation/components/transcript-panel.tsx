import { AlertTriangle, FileAudio, Loader2 } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { AiStatus } from "@/types/ai";
import type { ConsultationTranscript } from "@/types/consultation";

import type { RecorderStatus } from "../hooks/use-audio-recorder";

interface TranscriptPanelProps {
  transcript: ConsultationTranscript;
  recorderStatus: RecorderStatus;
  aiStatus: AiStatus;
}

// Live Transcript (PRD Ch9.6). Renders the AI-generated transcript once the
// pipeline has produced one; falls back to an honest processing/empty state
// otherwise (Ch9.19) — never fabricated content.
export function TranscriptPanel({ transcript, recorderStatus, aiStatus }: TranscriptPanelProps) {
  const segments = transcript.cleaned_transcript ?? transcript.raw_transcript;

  if (segments.length > 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Transcript</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {segments.map((segment, index) => (
            <div key={index} className="flex gap-3 rounded-md border border-border p-3">
              <span className="w-16 shrink-0 text-caption text-text-secondary">
                {formatTimestamp(segment.timestamp_start)}
              </span>
              <div className="flex-1">
                <p
                  className={cn(
                    "text-body text-text-primary",
                    segment.confidence < 0.5 && "italic text-text-secondary",
                  )}
                >
                  {segment.text}
                </p>
                {segment.confidence < 0.5 && (
                  <p className="mt-1 text-caption text-warning">Low-confidence transcription</p>
                )}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  let message = "Recording has not started.";
  let icon = <FileAudio className="h-6 w-6 text-text-secondary" />;

  if (recorderStatus === "recording" || recorderStatus === "paused") {
    message = "Audio is being captured. Transcription will begin once the recording is stopped.";
  } else if (aiStatus.stage.startsWith("processing") || aiStatus.stage === "queued") {
    message = "Transcribing the consultation recording…";
    icon = <Loader2 className="h-6 w-6 animate-spin text-primary" />;
  } else if (aiStatus.stage === "failed") {
    message = aiStatus.reason ?? "Transcription failed. Use Retry in the AI panel to try again.";
    icon = <AlertTriangle className="h-6 w-6 text-danger" />;
  } else if (transcript.audio_file_url) {
    message = "Recording captured. Transcription has not run for this consultation yet.";
  } else if (aiStatus.stage === "no_ai_content") {
    message = "No audio was captured for this consultation, so no transcript is available.";
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Transcript</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center justify-center gap-3 rounded-md border border-dashed border-border p-8 text-center">
          {icon}
          <p className="text-body text-text-secondary">{message}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function formatTimestamp(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}
