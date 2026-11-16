"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { PCM_WORKLET_CODE, PCM_WORKLET_NAME } from "@/lib/live-audio";

export type RecorderStatus =
  "idle" | "requesting-permission" | "recording" | "paused" | "stopped" | "error";

interface UseAudioRecorderResult {
  status: RecorderStatus;
  elapsedSeconds: number;
  audioLevel: number;
  errorMessage: string | null;
  start: () => Promise<void>;
  pause: () => void;
  resume: () => void;
  stop: () => Promise<Blob | null>;
  reset: () => void;
}

const CANDIDATE_MIME_TYPES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/ogg;codecs=opus",
  "audio/ogg",
];

function pickSupportedMimeType(): string | undefined {
  if (typeof MediaRecorder === "undefined") return undefined;
  return CANDIDATE_MIME_TYPES.find((type) => MediaRecorder.isTypeSupported(type));
}

interface UseAudioRecorderOptions {
  /**
   * Optional tap on the live microphone signal (used for live captions). Receives raw
   * float blocks plus the AudioContext sample rate; called only while actually recording
   * (not while paused). Purely additive: recording works identically without it.
   */
  onPcm?: (block: Float32Array, sampleRate: number) => void;
}

/**
 * Real MediaRecorder + Web Audio API recording pipeline (PRD Ch9.6/9.11 —
 * Recording Status, Timer, Pause/Resume/Stop, Audio Level). This milestone
 * only captures and uploads the audio; transcription happens in the AI
 * Engine milestone (Ch10/17).
 */
export function useAudioRecorder(options: UseAudioRecorderOptions = {}): UseAudioRecorderResult {
  const [status, setStatus] = useState<RecorderStatus>("idle");
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const elapsedBeforePauseRef = useRef(0);
  const segmentStartRef = useRef<number>(0);
  const pcmNodeRef = useRef<AudioWorkletNode | null>(null);
  const forwardPcmRef = useRef(false);
  const onPcmRef = useRef(options.onPcm);
  onPcmRef.current = options.onPcm;

  const stopLevelMeter = useCallback(() => {
    if (animationFrameRef.current !== null) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    setAudioLevel(0);
  }, []);

  const runLevelMeter = useCallback(() => {
    const analyser = analyserRef.current;
    if (!analyser) return;
    const data = new Uint8Array(analyser.frequencyBinCount);

    const tick = () => {
      analyser.getByteTimeDomainData(data);
      let sumSquares = 0;
      for (const value of data) {
        const normalized = (value - 128) / 128;
        sumSquares += normalized * normalized;
      }
      const rms = Math.sqrt(sumSquares / data.length);
      setAudioLevel(Math.min(1, rms * 4));
      animationFrameRef.current = requestAnimationFrame(tick);
    };
    animationFrameRef.current = requestAnimationFrame(tick);
  }, []);

  const stopTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const startTimer = useCallback(() => {
    segmentStartRef.current = Date.now();
    timerRef.current = setInterval(() => {
      const segmentElapsed = (Date.now() - segmentStartRef.current) / 1000;
      setElapsedSeconds(elapsedBeforePauseRef.current + segmentElapsed);
    }, 250);
  }, []);

  const cleanup = useCallback(() => {
    stopTimer();
    stopLevelMeter();
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      void audioContextRef.current.close();
    }
    audioContextRef.current = null;
    analyserRef.current = null;
    recorderRef.current = null;
    forwardPcmRef.current = false;
    pcmNodeRef.current?.port.close();
    pcmNodeRef.current = null;
  }, [stopLevelMeter, stopTimer]);

  useEffect(() => cleanup, [cleanup]);

  // Warn before an accidental tab close/refresh loses an unsaved recording.
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (status === "recording" || status === "paused") {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [status]);

  const start = useCallback(async () => {
    setErrorMessage(null);
    setStatus("requesting-permission");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;

      // Tap the same signal for live captions. Best-effort: if AudioWorklet is unavailable
      // the recording is unaffected and captions simply do not appear.
      if (onPcmRef.current && audioContext.audioWorklet) {
        try {
          const moduleUrl = URL.createObjectURL(
            new Blob([PCM_WORKLET_CODE], { type: "application/javascript" }),
          );
          await audioContext.audioWorklet.addModule(moduleUrl);
          URL.revokeObjectURL(moduleUrl);
          const tap = new AudioWorkletNode(audioContext, PCM_WORKLET_NAME);
          tap.port.onmessage = (event: MessageEvent<Float32Array>) => {
            if (forwardPcmRef.current) onPcmRef.current?.(event.data, audioContext.sampleRate);
          };
          source.connect(tap);
          // Some browsers only run a worklet that reaches the destination: route it through a muted gain.
          const mute = audioContext.createGain();
          mute.gain.value = 0;
          tap.connect(mute);
          mute.connect(audioContext.destination);
          pcmNodeRef.current = tap;
        } catch {
          /* live captions unavailable; recording continues */
        }
      }

      chunksRef.current = [];
      elapsedBeforePauseRef.current = 0;
      setElapsedSeconds(0);

      const mimeType = pickSupportedMimeType();
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorderRef.current = recorder;
      recorder.start(1000);

      startTimer();
      runLevelMeter();
      forwardPcmRef.current = true;
      setStatus("recording");
    } catch {
      setStatus("error");
      setErrorMessage("Unable to access the microphone. Please check your browser permissions.");
    }
  }, [runLevelMeter, startTimer]);

  const pause = useCallback(() => {
    if (recorderRef.current?.state !== "recording") return;
    recorderRef.current.pause();
    forwardPcmRef.current = false;
    elapsedBeforePauseRef.current = elapsedSeconds;
    stopTimer();
    stopLevelMeter();
    setStatus("paused");
  }, [elapsedSeconds, stopLevelMeter, stopTimer]);

  const resume = useCallback(() => {
    if (recorderRef.current?.state !== "paused") return;
    recorderRef.current.resume();
    forwardPcmRef.current = true;
    startTimer();
    runLevelMeter();
    setStatus("recording");
  }, [runLevelMeter, startTimer]);

  const stop = useCallback((): Promise<Blob | null> => {
    return new Promise((resolve) => {
      const recorder = recorderRef.current;
      if (!recorder || recorder.state === "inactive") {
        resolve(null);
        return;
      }
      forwardPcmRef.current = false;
      recorder.onstop = () => {
        const blob =
          chunksRef.current.length > 0
            ? new Blob(chunksRef.current, { type: recorder.mimeType })
            : null;
        cleanup();
        setStatus("stopped");
        resolve(blob);
      };
      recorder.stop();
    });
  }, [cleanup]);

  const reset = useCallback(() => {
    cleanup();
    chunksRef.current = [];
    elapsedBeforePauseRef.current = 0;
    setElapsedSeconds(0);
    setErrorMessage(null);
    setStatus("idle");
  }, [cleanup]);

  return { status, elapsedSeconds, audioLevel, errorMessage, start, pause, resume, stop, reset };
}
