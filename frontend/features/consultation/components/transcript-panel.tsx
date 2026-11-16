import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, FileAudio, Loader2 } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { AiStatus } from "@/types/ai";
import type { ConsultationTranscript } from "@/types/consultation";

import type { RecorderStatus } from "../hooks/use-audio-recorder";
import type { LiveCaption, LiveCaptionState } from "../hooks/use-live-captions";

interface TranscriptPanelProps {
  transcript: ConsultationTranscript;
  recorderStatus: RecorderStatus;
  aiStatus: AiStatus;
  liveCaptions: LiveCaption[];
  liveState: LiveCaptionState;
}

// Live Transcript (PRD Ch9.6). Renders the AI-generated transcript once the
// pipeline has produced one; falls back to an honest processing/empty state
// otherwise (Ch9.19) — never fabricated content.
export function TranscriptPanel({
  transcript,
  recorderStatus,
  aiStatus,
  liveCaptions,
  liveState,
}: TranscriptPanelProps) {
  const segments = transcript.cleaned_transcript ?? transcript.raw_transcript;
  const recording = recorderStatus === "recording" || recorderStatus === "paused";

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

  // Live captions: a quick preview while recording (and until the accurate transcript is
  // ready after Stop). The final transcript above always takes over once it exists.
  if (liveCaptions.length > 0) {
    return <LiveTranscript captions={liveCaptions} recording={recording} />;
  }

  let message = "Recording has not started.";
  let icon = <FileAudio className="h-6 w-6 text-text-secondary" />;

  if (recording && (liveState === "connecting" || liveState === "live")) {
    message = "Listening… live captions will appear here within a few seconds.";
    icon = <Loader2 className="h-6 w-6 animate-spin text-primary" />;
  } else if (recording) {
    message =
      "Audio is being captured. Live captions are unavailable right now; the full transcript is prepared when you stop recording.";
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

// Live Transcript (PRD Ch9.6/Ch9.23): lines fade in one by one, with a pulsing red dot
// while recording. Auto-scrolls to the newest line.
function LiveTranscript({ captions, recording }: { captions: LiveCaption[]; recording: boolean }) {
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "nearest" });
  }, [captions.length]);

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Transcript</CardTitle>
        <span className="flex items-center gap-2 text-caption text-text-secondary">
          {recording ? (
            <>
              <span className="relative flex h-2.5 w-2.5" aria-hidden="true">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-danger opacity-75" />
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-danger" />
              </span>
              Live
            </>
          ) : (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" aria-hidden="true" />
              Preparing the accurate transcript…
            </>
          )}
        </span>
      </CardHeader>
      <CardContent>
        <div className="flex max-h-80 flex-col gap-2 overflow-y-auto" aria-live="polite">
          {captions.map((caption) => (
            <motion.p
              key={caption.id}
              className="text-body text-text-primary"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.18 }}
            >
              {caption.text}
            </motion.p>
          ))}
          <div ref={endRef} />
        </div>
        <p className="mt-3 text-caption text-text-secondary">
          Live captions are a quick preview and may mishear words. The accurate transcript replaces
          them when you stop recording.
        </p>
      </CardContent>
    </Card>
  );
}
