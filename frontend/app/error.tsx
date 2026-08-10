"use client";

import { Button } from "@/components/ui/button";

// Global Error Boundary (PRD Ch4.13). Never expose stack traces (Ch5.23).
export default function RootError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background text-center">
      <h1 className="text-h3 text-text-primary">Something went wrong</h1>
      <p className="max-w-md text-body text-text-secondary">
        An unexpected error occurred. Please try again, or contact support if the problem persists.
      </p>
      <div className="flex gap-3">
        <Button onClick={reset}>Retry</Button>
        <Button variant="secondary" onClick={() => (window.location.href = "/")}>
          Back to Home
        </Button>
      </div>
    </div>
  );
}
