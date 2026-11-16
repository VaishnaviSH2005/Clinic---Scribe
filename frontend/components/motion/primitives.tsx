"use client";

import { motion, type Variants } from "framer-motion";

import { cn } from "@/lib/utils";

// Shared motion kit — PRD Ch2.15 / Ch5.25 / Ch6.17: "Motion should communicate
// state changes, not attract attention." Cards fade up in 180ms, nothing
// exceeds 300ms, ease-out entries, no bouncing/spring/elastic effects.
// Reduced-motion users get no movement at all (`MotionConfig reducedMotion="user"`).
export const EASE_OUT = [0, 0, 0.2, 1] as const; // CSS ease-out
export const CARD_MS = 0.18;
export const PAGE_MS = 0.25;

export function FadeIn({
  children,
  className,
  delay = 0,
  y = 8,
  duration = CARD_MS,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  y?: number;
  duration?: number;
}) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration, delay, ease: EASE_OUT }}
    >
      {children}
    </motion.div>
  );
}

const containerVariants = (step: number, delay: number): Variants => ({
  hidden: {},
  show: { transition: { staggerChildren: step, delayChildren: delay } },
});

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0, transition: { duration: CARD_MS, ease: EASE_OUT } },
};

/** Container whose `StaggerItem` children fade up one after another. */
export function Stagger({
  children,
  className,
  step = 0.04,
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  step?: number;
  delay?: number;
}) {
  return (
    <motion.div
      className={className}
      variants={containerVariants(step, delay)}
      initial="hidden"
      animate="show"
    >
      {children}
    </motion.div>
  );
}

export function StaggerItem({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <motion.div className={className} variants={itemVariants}>
      {children}
    </motion.div>
  );
}

/** Card with a gentle 3px lift on hover (PRD Ch2.15: 2-4px). */
export function HoverLiftCard({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <motion.div
      className={cn("h-full", className)}
      variants={itemVariants}
      whileHover={{ y: -3 }}
      transition={{ duration: CARD_MS, ease: EASE_OUT }}
    >
      {children}
    </motion.div>
  );
}
