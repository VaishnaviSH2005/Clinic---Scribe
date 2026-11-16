"use client";

import { motion } from "framer-motion";

import { EASE_OUT, PAGE_MS } from "@/components/motion/primitives";

// `template.tsx` re-mounts on every navigation (unlike layout.tsx), which is
// what gives each dashboard route its page transition: a plain fade, 250ms
// (PRD Ch5.25 "Page — Fade", Ch2.15 "Page transitions: 250ms").
export default function DashboardTemplate({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: PAGE_MS, ease: EASE_OUT }}
    >
      {children}
    </motion.div>
  );
}
