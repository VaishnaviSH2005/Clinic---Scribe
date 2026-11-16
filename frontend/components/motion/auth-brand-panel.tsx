"use client";

import { motion } from "framer-motion";

import { EASE_OUT } from "./primitives";

// Left brand panel for the authentication screens. Slow drifting colour
// blobs (palette tokens only), a "listening" waveform that echoes the
// product tagline, and word-by-word headline reveal.
const BARS = 28;
const FEATURES = ["Live transcription", "SOAP notes", "Doctor-approved"];

function Waveform() {
  return (
    <div className="flex h-16 items-end gap-1.5" aria-hidden="true">
      {Array.from({ length: BARS }).map((_, i) => {
        // Deterministic pseudo-random heights (no Math.random -> no hydration mismatch).
        const peak = 0.35 + ((Math.sin(i * 1.7) + 1) / 2) * 0.65;
        return (
          <motion.span
            key={i}
            className="w-1.5 origin-bottom rounded-full bg-white/40"
            style={{ height: "100%" }}
            initial={{ scaleY: 0.12 }}
            animate={{ scaleY: [0.12, peak, 0.2, peak * 0.7, 0.12] }}
            transition={{
              duration: 1.8 + (i % 5) * 0.25,
              repeat: Infinity,
              ease: "easeInOut",
              delay: i * 0.05,
            }}
          />
        );
      })}
    </div>
  );
}

function Headline({ text, className, delay }: { text: string; className?: string; delay: number }) {
  return (
    <p className={className}>
      {text.split(" ").map((word, i) => (
        <motion.span
          key={`${word}-${i}`}
          className="mr-[0.28em] inline-block"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: delay + i * 0.05, ease: EASE_OUT }}
        >
          {word}
        </motion.span>
      ))}
    </p>
  );
}

export function AuthBrandPanel() {
  return (
    <div className="relative hidden flex-col justify-between overflow-hidden bg-sidebar p-12 text-white lg:flex">
      <motion.div
        aria-hidden="true"
        className="absolute -left-24 -top-24 h-96 w-96 rounded-full bg-secondary/30 blur-3xl"
        animate={{ x: [0, 60, 0], y: [0, 40, 0] }}
        transition={{ duration: 16, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        aria-hidden="true"
        className="absolute -bottom-32 -right-24 h-[28rem] w-[28rem] rounded-full bg-accent/30 blur-3xl"
        animate={{ x: [0, -50, 0], y: [0, -50, 0] }}
        transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        aria-hidden="true"
        className="absolute left-1/3 top-1/3 h-72 w-72 rounded-full bg-primary/50 blur-3xl"
        animate={{ scale: [1, 1.25, 1], opacity: [0.5, 0.8, 0.5] }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
      />

      <motion.div
        className="relative"
        initial={{ opacity: 0, x: -16 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.25, ease: EASE_OUT }}
      >
        <span className="text-h4 font-semibold">CliniScribe AI</span>
      </motion.div>

      <div className="relative space-y-8">
        <div className="space-y-3">
          <Headline text="AI That Listens." className="text-h2 font-semibold" delay={0.1} />
          <Headline
            text="Doctors Who Decide."
            className="text-h2 font-semibold text-white/70"
            delay={0.35}
          />
        </div>
        <Waveform />
        <motion.ul
          className="flex flex-wrap gap-2"
          initial="hidden"
          animate="show"
          variants={{
            hidden: {},
            show: { transition: { staggerChildren: 0.06, delayChildren: 0.6 } },
          }}
        >
          {FEATURES.map((label) => (
            <motion.li
              key={label}
              className="rounded-full border border-white/20 bg-white/10 px-3 py-1 text-caption text-white/80 backdrop-blur"
              variants={{
                hidden: { opacity: 0, y: 10 },
                show: { opacity: 1, y: 0, transition: { duration: 0.25, ease: EASE_OUT } },
              }}
            >
              {label}
            </motion.li>
          ))}
        </motion.ul>
      </div>

      <p className="relative text-caption text-white/50">Version 1.0 — CliniScribe AI</p>
    </div>
  );
}
