// Browser-side audio plumbing for live captions (PRD Ch9.6). Framework-free so it
// can be unit-tested: converts the microphone's native-rate float samples into the
// 16 kHz mono signed-16-bit PCM frames the backend's live WebSocket expects.

export const TARGET_RATE = 16_000;

/** One-second frames: small enough for low latency, large enough to keep the socket quiet. */
export const FRAME_SAMPLES = TARGET_RATE;

/**
 * Runs inside an AudioWorklet (a separate audio thread): batches the 128-sample render
 * quanta into ~2048-sample blocks and posts them to the main thread. Kept as a string so
 * no extra static file has to be served.
 */
export const PCM_WORKLET_NAME = "cliniscribe-pcm-tap";
export const PCM_WORKLET_CODE = `
class PcmTap extends AudioWorkletProcessor {
  constructor() { super(); this.buf = new Float32Array(2048); this.n = 0; }
  process(inputs) {
    const channel = inputs[0] && inputs[0][0];
    if (channel) {
      for (let i = 0; i < channel.length; i++) {
        this.buf[this.n++] = channel[i];
        if (this.n === this.buf.length) {
          this.port.postMessage(this.buf.slice(0));
          this.n = 0;
        }
      }
    }
    return true;
  }
}
registerProcessor("${PCM_WORKLET_NAME}", PcmTap);
`;

/**
 * Streaming resampler + packer: feed it successive blocks at `inputRate`; it calls
 * `onFrame` with each completed 16 kHz mono Int16 frame. Linear interpolation is plenty
 * for speech recognition, and the fractional read position is carried across blocks so
 * there are no clicks or drift at block boundaries.
 */
export class PcmStreamer {
  private pos = 0;
  private tail: number | null = null;
  private frame = new Int16Array(FRAME_SAMPLES);
  private filled = 0;

  constructor(
    private readonly inputRate: number,
    private readonly onFrame: (frame: ArrayBuffer) => void,
  ) {}

  push(block: Float32Array): void {
    if (block.length === 0) return;
    // Prepend the previous block's last sample so interpolation spans the boundary.
    let buf = block;
    if (this.tail !== null) {
      buf = new Float32Array(block.length + 1);
      buf[0] = this.tail;
      buf.set(block, 1);
    }
    const step = this.inputRate / TARGET_RATE;
    while (this.pos + 1 < buf.length) {
      const i = Math.floor(this.pos);
      const frac = this.pos - i;
      const a = buf[i] ?? 0;
      const b = buf[i + 1] ?? a;
      this.write(a * (1 - frac) + b * frac);
      this.pos += step;
    }
    this.pos -= buf.length - 1;
    this.tail = buf[buf.length - 1] ?? 0;
  }

  /** Emit whatever is left (a partial frame) — call when the recording ends. */
  flush(): void {
    if (this.filled > 0) {
      this.onFrame(this.frame.slice(0, this.filled).buffer as ArrayBuffer);
      this.filled = 0;
    }
  }

  private write(sample: number): void {
    const clipped = Math.max(-1, Math.min(1, sample));
    this.frame[this.filled++] = clipped < 0 ? clipped * 0x8000 : clipped * 0x7fff;
    if (this.filled === FRAME_SAMPLES) {
      this.onFrame(this.frame.slice(0).buffer as ArrayBuffer);
      this.filled = 0;
    }
  }
}
