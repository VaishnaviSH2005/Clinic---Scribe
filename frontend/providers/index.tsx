"use client";

import { MotionConfig } from "framer-motion";
import { Toaster } from "sonner";

import { AuthProvider } from "./auth-provider";
import { QueryProvider } from "./query-provider";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    // reducedMotion="user": honour the OS "reduce motion" setting everywhere.
    <MotionConfig reducedMotion="user">
      <QueryProvider>
        <AuthProvider>{children}</AuthProvider>
        <Toaster position="top-right" duration={4000} />
      </QueryProvider>
    </MotionConfig>
  );
}
