"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { API_BASE_URL, API_VERSION_PREFIX } from "@/constants/api";
import { PcmStreamer } from "@/lib/live-audio";

export interface LiveCaption {
  id: number;
  text: string;
}

// "off": not recording · "connecting": socket opening · "live": connected, captions flowing
// "unavailable": could not connect (the recording itself is unaffected).
export type LiveCaptionState = "off" | "connecting" | "live" | "unavailable";

const MAX_RECONNECTS = 3;

/**
 * Live captions during a consultation (PRD Ch9.6). Streams the microphone audio to the
 * backend's live WebSocket and collects the captions it sends back.
 *
 * Strictly best-effort: the normal recording/upload path never depends on it. If the
 * socket cannot be opened or drops, `state` becomes "unavailable", the doctor keeps
 * recording, and the accurate transcript is still produced after Stop.
 */
export function useLiveCaptions(consultationId: string) {
  const [captions, setCaptions] = useState<LiveCaption[]>([]);
  const [state, setState] = useState<LiveCaptionState>("off");

  const socketRef = useRef<WebSocket | null>(null);
  const streamerRef = useRef<PcmStreamer | null>(null);
  const wantedRef = useRef(false); // true while the doctor is recording
  const attemptsRef = useRef(0);
  const nextIdRef = useRef(1);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const open = useCallback(() => {
    const url = `${API_BASE_URL.replace(/^http/, "ws")}${API_VERSION_PREFIX}/consultations/${consultationId}/live`;
    setState("connecting");
    let socket: WebSocket;
    try {
      socket = new WebSocket(url); // the auth cookie is sent automatically
    } catch {
      setState("unavailable");
      return;
    }
    socket.binaryType = "arraybuffer";
    socketRef.current = socket;

    socket.onopen = () => {
      attemptsRef.current = 0;
      streamerRef.current = null; // a fresh stream starts with the new connection
      setState("live");
    };
    socket.onmessage = (event) => {
      if (typeof event.data !== "string") return;
      try {
        const message = JSON.parse(event.data) as { type?: string; text?: string };
        if (message.type === "caption" && message.text) {
          const text = message.text;
          setCaptions((prev) => [...prev, { id: nextIdRef.current++, text }]);
        }
      } catch {
        /* ignore a malformed message */
      }
    };
    socket.onclose = () => {
      if (socketRef.current === socket) socketRef.current = null;
      if (!wantedRef.current) return;
      if (attemptsRef.current < MAX_RECONNECTS) {
        attemptsRef.current += 1;
        reconnectTimer.current = setTimeout(open, 1500 * attemptsRef.current);
      } else {
        setState("unavailable");
      }
    };
  }, [consultationId]);

  /** Call when recording starts. */
  const connect = useCallback(() => {
    wantedRef.current = true;
    attemptsRef.current = 0;
    streamerRef.current = null;
    setCaptions([]);
    nextIdRef.current = 1;
    open();
  }, [open]);

  /** Call when recording stops (or the workspace closes): flushes the tail and ends the stream. */
  const disconnect = useCallback(() => {
    wantedRef.current = false;
    if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    streamerRef.current?.flush();
    streamerRef.current = null;
    const socket = socketRef.current;
    socketRef.current = null;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send("end");
      socket.close();
    } else {
      socket?.close();
    }
    setState((current) => (current === "unavailable" ? current : "off"));
  }, []);

  /** Feed one block of microphone samples (at the AudioContext's sample rate). */
  const pushAudio = useCallback((block: Float32Array, sampleRate: number) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    if (!streamerRef.current) {
      streamerRef.current = new PcmStreamer(sampleRate, (frame) => {
        if (socket.readyState === WebSocket.OPEN) socket.send(frame);
      });
    }
    streamerRef.current.push(block);
  }, []);

  // Never leave a socket open if the workspace is closed mid-recording.
  useEffect(() => disconnect, [disconnect]);

  return { captions, state, connect, disconnect, pushAudio };
}
